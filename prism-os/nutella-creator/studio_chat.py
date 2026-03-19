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
REFS_DIR = PROJECT_DIR.parent / "thumbnail-ai-creator" / "referencias"

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
  "summary": "1-line Portuguese summary of what was understood"
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

Available modes (detect from user message):
- "thumbnail": generate or edit YouTube thumbnails
- "research": analyze content, videos, trends, audience
- "script": write scripts, titles, descriptions, copies
- "strategy": plan content calendar, analyze performance
- "question": general questions about the system or brand

Return additional field: "mode": "thumbnail" | "research" | "script" | "strategy" | "question"
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
            f"{host_name}: 40-year-old man, salt-and-pepper short stubble beard, "
            "short brown hair, hazel eyes, NO glasses. Smooth youthful skin. "
            "Wearing black polo shirt."
        ),
        "teams": (
            f"{host_name}: Professional young man, confident appearance. "
            "Dark/neutral business casual clothing."
        ),
    }.get(channel, "")

    brand_context = """BRAND SPECS (FOLLOW EXACTLY):
- Primary purple: #8B23E5 | Deep purple: #4E0091 | Light purple: #6C12B9
- Typography: Montserrat (on thumbnails)
- Tone: Sage Pragmatico - mentor acessivel, mao na massa, sem jargao
- Background: ALWAYS dark/cinematic. NEVER white backgrounds.
- Host clothing: polo LISA (solid color, no patterns)
- Lighting: warm orange accent, cinematic contrast
"""

    prompt = f"{brand_context}\n\nYouTube thumbnail, 16:9 aspect ratio.\n\n"
    prompt += f"REFERENCE IMAGES: Face references for {host_name}.\n\n"
    prompt += f"{host_desc}\nExpression: {expression}\n\n"
    prompt += f"SCENE: {host_name} on the right, waist up. {background}.\n\n"

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


def run_pipeline(message: str, image_b64: str | None, session_id: str,
                 api_key: str, progress_cb=None) -> dict:
    """
    Main pipeline: message -> intent -> refs -> generate/edit -> result.
    Returns: {"text": str, "image_url": str | None, "error": str | None}
    """

    def emit(step, msg, model=None):
        if progress_cb:
            payload = {"step": step, "msg": msg}
            if model:
                payload["model"] = model
            progress_cb(payload)

    history = get_session(session_id)
    user_entry = {"role": "user", "text": message, "image_path": None, "ts": time.time()}

    # Save uploaded image
    base_image_path = None
    if image_b64:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        img_path = OUTPUT_DIR / f"studio_upload_{session_id}_{ts}.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img_path.write_bytes(base64.b64decode(image_b64))
        user_entry["image_path"] = str(img_path)
        base_image_path = img_path

    history.append(user_entry)

    # Step 1: Parse intent
    emit("intent", "Interpretando pedido...", "Gemini Flash")
    intent = parse_intent(message, history, api_key)
    action = intent.get("action", "question")
    mode = intent.get("mode", "question")
    summary = intent.get("summary", "")
    emit("intent", f"Entendi: {summary}", "Gemini Flash")
    emit("mode", f"Modo: {mode}")

    # Handle questions, research, script, strategy — inject full knowledge
    if action == "question" or action not in ("generate", "edit"):
        from knowledge_base import get_system_prompt
        knowledge_flags = {}  # futuro: receber do frontend
        system = get_system_prompt(mode, knowledge_flags)

        answer = _call_flash(
            f"Responda em portugues de forma clara e objetiva: {message}",
            api_key,
            system_prompt=system if system else None,
            max_tokens=2048,
        )
        result = {"text": answer, "image_url": None}
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
        return {"text": text, "image_url": image_url}
    else:
        text = "Erro na geracao. Tente novamente com instrucoes diferentes."
        history.append({"role": "assistant", "text": text, "image_path": None, "ts": time.time()})
        return {"text": text, "image_url": None, "error": "generation_failed"}
