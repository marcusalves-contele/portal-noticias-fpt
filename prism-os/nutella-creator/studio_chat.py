#!/usr/bin/env python3
"""
studio_chat.py — Conversational thumbnail generation for PRISM OS Studio.

Receives natural language messages, interprets intent via Gemini Flash,
auto-selects references, builds prompts, and generates/edits images.
"""

import os
import json
import base64
import time
import requests
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "output"
_THUMB_REFS = PROJECT_DIR.parent / "thumbnail-ai-creator" / "referencias"
REFS_DIR = _THUMB_REFS if _THUMB_REFS.exists() else PROJECT_DIR / "referencias"

MODEL_FLASH = "gemini-3-flash-preview"
MODEL_IMAGE_PRO = "gemini-3-pro-image-preview"
MODEL_IMAGE_EDIT = "gemini-3.1-flash-image-preview"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
TIMEOUT = 180

# In-memory session storage
_sessions: dict[str, list[dict]] = {}


def _flash_url():
    return f"{API_BASE}/{MODEL_FLASH}:generateContent"


def _image_url(model: str):
    return f"{API_BASE}/{model}:generateContent"


def _call_flash(prompt: str, api_key: str, system_prompt: str = None, max_tokens: int = 1024) -> str:
    """Call Gemini Flash for text generation."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    resp = requests.post(
        _flash_url(),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return json.dumps(data.get("error", {}))


_MODE_SYSTEM_PROMPTS = {
    "research": (
        "Voce e um analista de conteudo YouTube especialista em gestao de frotas. "
        "Analise dados, tendencias, videos, audiencia. "
        "Use os docs de referencia para embasar analises. Responda em portugues."
    ),
    "script": (
        "Voce e um roteirista e copywriter para o canal Frota Para Todos. "
        "Crie roteiros, titulos, descricoes, copies seguindo o tom Sage Pragmatico. "
        "Use as personas para direcionar a linguagem. Responda em portugues."
    ),
    "strategy": (
        "Voce e um estrategista de conteudo para Frota Para Todos. "
        "Planeje calendario, analise performance, sugira melhorias baseado nos dados dos docs. "
        "Responda em portugues."
    ),
    "question": (
        "Voce e o assistente PRISM Studio, especialista no sistema de producao de conteudo FPT. "
        "Responda duvidas sobre a marca, sistema, pipeline, configuracoes. Responda em portugues."
    ),
}


def parse_intent(message: str, history: list, api_key: str, mode_hint: str = None) -> dict:
    """Parse user message into structured intent via Gemini Flash."""

    history_text = ""
    if history:
        last_msgs = history[-6:]
        for msg in last_msgs:
            role = "User" if msg["role"] == "user" else "AI"
            text = msg.get("text", "")[:200]
            has_img = "yes" if msg.get("image_path") else "no"
            history_text += f"{role}: {text} [has_image: {has_img}]\n"

    prompt = f"""You are an intent parser for a YouTube thumbnail generation system.

The system creates thumbnails for two channels:
- Fleet (host: Julio Cesar, fleet management, purple brand)
- Teams (host: Leonardo Gazolli, field teams, blue brand)

Parse this user message into a structured JSON intent.

CONVERSATION HISTORY:
{history_text}

USER MESSAGE: {message}

Return ONLY valid JSON with these fields:
{{
  "action": "generate" | "edit" | "question",
  "channel": "fleet" | "teams",
  "host_expression": "surpreso" | "serio" | "pensativo" | "sorrindo" | "assertivo" | "explicando" | "confiante" | "ironico",
  "guest_name": null or "Name",
  "title_text": "text to show on thumbnail" or null,
  "subtitle_text": "secondary line" or null,
  "background_desc": "background description" or null,
  "live_number": "323" or null,
  "edit_feedback": "what to change" or null,
  "summary": "1-line Portuguese summary of what was understood",
  "mode": "thumbnail" | "research" | "script" | "strategy" | "question"
}}

Rules:
- If user references a previous image or says "muda", "ajusta", "melhora", "mais escuro", action is "edit"
- If no channel mentioned, default to "fleet"
- If no expression mentioned, default to "pensativo"
- If user asks a question (not requesting generation), action is "question"
- Extract any live number mentioned
- title_text should be the text the user wants ON the thumbnail
- edit_feedback captures what to change from the previous generation
- summary should be in Portuguese, concise

Mode detection rules:
- "thumbnail": user wants to generate or edit a YouTube thumbnail image
- "research": user asks about video performance, analytics, trends, audience, what works, comparisons
- "script": user wants to write/create a script, title, description, copy, CTA, or any text content
- "strategy": user asks about content calendar, publishing schedule, best times, content planning, performance strategy
- "question": general questions about the PRISM system, brand rules, pipeline, configurations, how things work

Examples:
- "gera thumb do Julio" -> mode: thumbnail, action: generate
- "quais videos tiveram mais views esse mes?" -> mode: research, action: question
- "escreve um roteiro pra live sobre multas" -> mode: script, action: question
- "qual o melhor dia pra publicar nutella?" -> mode: strategy, action: question
- "como funciona o face-lock?" -> mode: question, action: question
- "muda o fundo pra mais escuro" -> mode: thumbnail, action: edit
- "analisa os tipos de nutella que mais performam" -> mode: research, action: question
- "escreve um titulo SEO pra live sobre rastreador" -> mode: script, action: question
- "quando devo postar pra ter mais alcance?" -> mode: strategy, action: question
"""

    result = _call_flash(prompt, api_key)  # sem system_prompt aqui, manter rapido

    try:
        if "```" in result:
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        return json.loads(result.strip())
    except (json.JSONDecodeError, IndexError):
        return {
            "action": "question",
            "channel": "fleet",
            "summary": "Nao entendi o pedido. Pode reformular?",
        }


def _get_refs(channel: str, expression: str, guest_name: str | None = None) -> list[Path]:
    """Auto-select face references."""
    from thumb_live import get_host_refs

    refs = get_host_refs(channel, expression)

    if guest_name and guest_name.strip():
        guests_dir = REFS_DIR / "convidados"
        if guests_dir.exists():
            name_lower = guest_name.lower().replace(" ", "-")
            for f in guests_dir.iterdir():
                if name_lower in f.name.lower() and f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    refs.append(f)
                    break

    return refs


def _build_prompt(intent: dict) -> str:
    """Build image generation prompt from intent."""
    channel = intent.get("channel", "fleet")
    host_name = "JULIO" if channel == "fleet" else "LEONARDO"
    expression = intent.get("host_expression", "pensativo")
    title = intent.get("title_text", "")
    subtitle = intent.get("subtitle_text", "")
    background = intent.get("background_desc", "dark cinematic background with warm orange accent lighting")
    live_num = intent.get("live_number", "")
    guest = intent.get("guest_name")

    host_desc = {
        "fleet": (
            f"{host_name}: 40-year-old Brazilian man. Salt-and-pepper SHORT stubble beard "
            "(NOT full beard, NOT clean-shaven — only short salt-and-pepper stubble). "
            "Short brown hair, hazel eyes. NO glasses ever. Smooth youthful skin. "
            "ALWAYS wearing solid black polo shirt (NO patterns, NO logos, NO stripes). "
            "Archetype: Sage Pragmatico — wise mentor who learned in the field, not academia."
        ),
        "teams": (
            f"{host_name}: Young professional Brazilian man, confident appearance. "
            "Dark/neutral business casual clothing. Clean-shaven or very light stubble. "
            "Expression: professional, approachable, knowledgeable."
        ),
    }.get(channel, "")

    brand_context = """BRAND SPECS (FOLLOW EXACTLY):
- Primary purple: #8B23E5 | Deep purple: #4E0091 | Light purple: #6C12B9
- NEVER use #7C3AED, #6D28D9 or any other Tailwind purple — ONLY #8B23E5 family
- Typography: Montserrat ONLY (no Comic Sans, no decorative fonts)
- Tone: Sage Pragmatico - mentor acessivel, mao na massa, sem jargao
- Lighting: warm orange cinematic accent from the side

ABSOLUTE RULES (NEVER VIOLATE):
- NEVER white or light backgrounds. ALWAYS dark/cinematic.
- NEVER full beard on Julio. ONLY short salt-and-pepper stubble.
- NEVER glasses on Julio.
- NEVER patterned, striped or logo clothing. Solid colors ONLY.
- NEVER paraphrase or alter the requested text. Reproduce EXACTLY as written.

COMPOSITION:
- Host on the RIGHT side, waist up, facing slightly left toward camera
- Text block on the LEFT, large white bold with black drop shadow (line 1)
- Secondary text in red/orange bold (line 2, if any)
- Live number badge (if any): top-left corner, red rounded pill
- Guest (if any): LEFT side, slightly smaller than host
- Aspect ratio: ALWAYS 16:9
- Cinematic warm orange accent lighting from the side
"""

    prompt = f"{brand_context}\n\nYouTube thumbnail, 16:9 aspect ratio.\n\n"
    prompt += f"REFERENCE IMAGES: Face references for {host_name}. Match this person exactly.\n\n"
    prompt += f"{host_desc}\nExpression: {expression}\n\n"
    prompt += f"SCENE: {host_name} on the RIGHT side, waist up. {background}.\n\n"

    if guest:
        prompt += f"GUEST ({guest}): Add on the LEFT side, slightly smaller. Label 'Convidado {guest}'.\n\n"

    if title or subtitle:
        prompt += "TEXT (EXACT, do not change):\n"
        if title:
            prompt += f'Line 1 (large white bold with black shadow): "{title}"\n'
        if subtitle:
            prompt += f'Line 2 (red/orange bold): "{subtitle}"\n'
        prompt += "\n"

    if live_num:
        prompt += f'Top-left corner: red rounded badge "LIVE {live_num}"\n\n'

    prompt += "NO logos. NO watermarks. Clean cinematic composition."
    return prompt


def _generate_image(api_key: str, prompt: str, refs: list[Path], output_name: str) -> Path | None:
    """Generate a thumbnail image using Gemini Pro."""
    from thumb_live import image_to_part

    parts = [image_to_part(r) for r in refs if r.exists()]
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
            "temperature": 0.6,
        },
    }

    try:
        resp = requests.post(
            _image_url(MODEL_IMAGE_PRO),
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=payload, timeout=TIMEOUT,
        )
        data = resp.json()
        if "candidates" not in data:
            return None
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                out_path = OUTPUT_DIR / output_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(img_data)
                return out_path
        return None
    except Exception as e:
        print(f"Studio generate error: {e}")
        return None


def _edit_image(api_key: str, base_image: Path, prompt: str, refs: list[Path], output_name: str) -> Path | None:
    """Edit an existing image using Nano Banana 2."""
    parts = [{"text": prompt}]

    with open(base_image, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = base_image.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    for ref in refs[:2]:
        if ref.exists():
            with open(ref, "rb") as f:
                rb64 = base64.b64encode(f.read()).decode()
            rmime = "image/jpeg" if ref.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            parts.append({"inline_data": {"mime_type": rmime, "data": rb64}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "temperature": 0.8},
    }

    try:
        resp = requests.post(
            _image_url(MODEL_IMAGE_EDIT),
            headers={"Content-Type": "application/json"},
            params={"key": api_key},
            json=payload, timeout=TIMEOUT,
        )
        data = resp.json()
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    out_path = OUTPUT_DIR / output_name
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_bytes(img_data)
                    return out_path
        return None
    except Exception as e:
        print(f"Studio edit error: {e}")
        return None


def get_session(session_id: str) -> list[dict]:
    """Get or create a session."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def delete_session(session_id: str) -> bool:
    """Delete a session from memory. Returns True if it existed."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def list_sessions() -> list[dict]:
    """List all sessions with summary info."""
    result = []
    for sid, msgs in _sessions.items():
        if not msgs:
            continue
        first_msg = next((m for m in msgs if m["role"] == "user"), None)
        last_msg = msgs[-1] if msgs else None
        result.append({
            "session_id": sid,
            "title": (first_msg.get("text", "")[:50] + "...") if first_msg else "Nova conversa",
            "message_count": len(msgs),
            "last_ts": last_msg.get("ts", 0) if last_msg else 0,
            "has_images": any(m.get("image_path") for m in msgs),
        })
    result.sort(key=lambda x: x["last_ts"], reverse=True)
    return result[:20]


def run_pipeline(message: str, image_b64: str | None = None, session_id: str = "",
                 api_key: str = "", progress_cb=None, mode_hint: str = None,
                 images_b64: list[str] | None = None) -> dict:
    """
    Main pipeline: message -> intent -> refs -> generate/edit -> result.
    Returns: {"text": str, "image_url": str | None, "error": str | None, "mode": str}
    mode_hint: if provided by the frontend, overrides the detected mode.
    images_b64: list of base64-encoded images (issue #68). Falls back to image_b64 for retrocompat.
    """

    def emit(step, msg, model=None):
        if progress_cb:
            payload = {"step": step, "msg": msg}
            if model:
                payload["model"] = model
            progress_cb(payload)

    # Issue #68: normalize to list (retrocompat with single image_b64)
    all_images = images_b64 or []
    if not all_images and image_b64:
        all_images = [image_b64]

    history = get_session(session_id)
    user_entry = {"role": "user", "text": message, "image_path": None, "image_paths": [], "ts": time.time()}

    # Save uploaded images
    base_image_path = None
    uploaded_paths = []
    for idx, img_b64 in enumerate(all_images):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = f"_{idx}" if idx > 0 else ""
        img_path = OUTPUT_DIR / f"studio_upload_{session_id}_{ts}{suffix}.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img_path.write_bytes(base64.b64decode(img_b64))
        uploaded_paths.append(img_path)
        if idx == 0:
            base_image_path = img_path

    if uploaded_paths:
        user_entry["image_path"] = str(uploaded_paths[0])
        user_entry["image_paths"] = [str(p) for p in uploaded_paths]

    history.append(user_entry)

    # Step 1: Parse intent
    emit("intent", "Interpretando pedido...", "Gemini Flash")
    intent = parse_intent(message, history, api_key)
    action = intent.get("action", "question")
    # mode_hint from frontend overrides detected mode
    mode = mode_hint or intent.get("mode", "question")
    summary = intent.get("summary", "")
    emit("intent", f"Entendi: {summary}", "Gemini Flash")
    emit("mode", f"Modo: {mode}")

    # Handle questions, research, script, strategy — inject full knowledge + mode-specific prompt
    if action in ("question", "research", "script", "strategy") or action not in ("generate", "edit"):
        from knowledge_base import get_system_prompt
        knowledge_flags = {}  # futuro: receber do frontend
        knowledge_system = get_system_prompt(mode, knowledge_flags)

        # Use mode-specific system prompt, fall back to knowledge_base system if available
        mode_system = _MODE_SYSTEM_PROMPTS.get(mode, _MODE_SYSTEM_PROMPTS["question"])
        # Combine: mode persona first, then knowledge docs if available
        if knowledge_system:
            system = f"{mode_system}\n\n{knowledge_system}"
        else:
            system = mode_system

        answer = _call_flash(
            f"Responda em portugues de forma clara e objetiva: {message}",
            api_key,
            system_prompt=system,
            max_tokens=2048,
        )
        result = {"text": answer, "image_url": None, "mode": mode}
        history.append({"role": "assistant", "text": answer, "image_path": None, "ts": time.time()})
        return result

    # Step 2: Select refs
    channel = intent.get("channel", "fleet")
    expression = intent.get("host_expression", "pensativo")
    guest = intent.get("guest_name")
    emit("refs", f"Selecionando referencias ({channel}, {expression})...")
    refs = _get_refs(channel, expression, guest)
    ref_names = [r.name for r in refs]
    emit("refs", f"Refs: {', '.join(ref_names[:3])}")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_name = f"studio_{session_id}_{ts}.png"

    if action == "edit":
        # Find last generated image
        if not base_image_path:
            for entry in reversed(history[:-1]):
                if entry.get("image_path") and Path(entry["image_path"]).exists():
                    base_image_path = Path(entry["image_path"])
                    break

        if not base_image_path:
            result = {"text": "Nenhuma imagem anterior pra editar. Gere uma primeiro.", "image_url": None}
            history.append({"role": "assistant", "text": result["text"], "image_path": None, "ts": time.time()})
            return result

        feedback = intent.get("edit_feedback", message)
        edit_prompt = (
            f"TASK: Edit this image based on feedback.\n"
            f"Image 1 is the current thumbnail to modify.\n"
            f"CHANGES REQUESTED: {feedback}\n"
            f"Keep everything else the same. Only apply the requested changes."
        )
        emit("generate", "Editando imagem...", "Nano Banana 2")
        result_path = _edit_image(api_key, base_image_path, edit_prompt, refs[:2], output_name)
    else:
        emit("prompt", "Montando prompt...")
        prompt = _build_prompt(intent)
        emit("generate", "Gerando thumbnail...", "Gemini Pro")
        result_path = _generate_image(api_key, prompt, refs, output_name)

    if result_path:
        image_url = f"/output/{result_path.name}"
        text = f"Pronto! {summary}"
        history.append({"role": "assistant", "text": text, "image_path": str(result_path), "ts": time.time()})
        return {"text": text, "image_url": image_url, "mode": mode}
    else:
        text = "Erro na geracao. Tente novamente com instrucoes diferentes."
        history.append({"role": "assistant", "text": text, "image_path": None, "ts": time.time()})
        return {"text": text, "image_url": None, "error": "generation_failed", "mode": mode}
