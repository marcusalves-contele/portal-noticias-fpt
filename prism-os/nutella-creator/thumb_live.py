#!/usr/bin/env python3
"""
thumb_live.py — Gerador de Thumbnails para Lives (A/B) via planilha Google Sheets.

Módulo usado pelo dashboard.py. Funções principais:
  - fetch_queue(creds)                      → lista de lives "A Fazer" da planilha
  - generate_angles(briefing, api_key)      → gera ângulos A e B com Gemini Flash
  - generate_ab(briefing, channel, live_id, api_key) → gera 2 thumbnails em paralelo
  - transcribe_audio(audio_bytes, api_key)  → transcreve áudio e extrai 3 respostas
  - save_guest_photo(...)                   → salva foto de convidado nas refs
  - load_state() / save_state(data)         → persistência em thumb_live_state.json
  - approve_thumb(live_id, choice, path)    → salva aprovação no state
"""

import json
import base64
import pickle
import requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------------------------------------------
# Paths & Constants
# -------------------------------------------------------------------

PROJECT_DIR   = Path(__file__).parent
OUTPUT_DIR    = PROJECT_DIR / "output"
THUMB_PROJECT = PROJECT_DIR.parent / "thumbnail-ai-creator"
REFS_DIR      = THUMB_PROJECT / "referencias"
GUESTS_DIR    = REFS_DIR / "convidados"
STATE_FILE    = OUTPUT_DIR / "thumb_live_state.json"
TOKEN_PATH    = PROJECT_DIR.parent.parent / "assistant-sexta-feira" / "token_youtube_write.pickle"

SPREADSHEET_ID = "1lluvZ8SKQNThV4o4OzWqmsttP-BgRC1FU3AqwvfJbqI"
SHEET_GID      = "25167001"

MODEL_IMAGE  = "gemini-3.1-flash-image-preview"   # Nano Banana v2
MODEL_FLASH  = "gemini-3-flash-preview"
MODEL_AUDIO  = "gemini-3-flash-preview"

API_BASE     = "https://generativelanguage.googleapis.com/v1beta/models"
IMAGE_URL    = f"{API_BASE}/{MODEL_IMAGE}:generateContent"
FLASH_URL    = f"{API_BASE}/{MODEL_FLASH}:generateContent"
TIMEOUT      = 180

STATUS_COL   = "Status"
STATUS_AFAZER = "A Fazer"

# -------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------

def load_google_creds():
    """Carrega credenciais OAuth do token pickle."""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError(f"Token não encontrado: {TOKEN_PATH}. Rode reauth_sheets.py.")
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)

    # Refresh se necessário
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    # Verifica scope Sheets
    sheets_scope = "https://www.googleapis.com/auth/spreadsheets.readonly"
    if hasattr(creds, "scopes") and creds.scopes and sheets_scope not in creds.scopes:
        raise PermissionError(
            "Token não possui scope Sheets. Rode: python3 reauth_sheets.py"
        )
    return creds


def load_api_key() -> str:
    """Carrega GEMINI_NANO_BANANA_KEY do .env local ou do thumbnail-ai-creator."""
    local_env   = PROJECT_DIR / ".env"
    parent_env  = THUMB_PROJECT / ".env"
    env_path    = local_env if local_env.exists() else parent_env

    if not env_path.exists():
        raise FileNotFoundError(f".env não encontrado em {env_path}")

    with open(env_path) as f:
        for line in f:
            if line.startswith("GEMINI_NANO_BANANA_KEY"):
                return line.split("=", 1)[1].strip().strip('"')
    raise ValueError("GEMINI_NANO_BANANA_KEY não encontrada no .env")


# -------------------------------------------------------------------
# Google Sheets — fetch queue
# -------------------------------------------------------------------

def _get_sheet_name_by_gid(creds, spreadsheet_id: str, gid: str) -> str | None:
    """Descobre o nome da aba pelo GID via spreadsheets.get."""
    from googleapiclient.discovery import build
    sheets_svc = build("sheets", "v4", credentials=creds)
    meta = sheets_svc.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties"
    ).execute()
    for sheet in meta.get("sheets", []):
        props = sheet["properties"]
        if str(props.get("sheetId")) == str(gid):
            return props["title"]
    return None


def fetch_queue(creds=None) -> list[dict]:
    """
    Lê a planilha e retorna itens com Status = "A Fazer".
    Mapeamento de colunas dinâmico pelo cabeçalho (row 0).
    """
    if creds is None:
        creds = load_google_creds()

    from googleapiclient.discovery import build
    sheets_svc = build("sheets", "v4", credentials=creds)

    sheet_name = _get_sheet_name_by_gid(creds, SPREADSHEET_ID, SHEET_GID)
    if not sheet_name:
        raise ValueError(f"Aba com GID {SHEET_GID} não encontrada na planilha.")

    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{sheet_name}'"
    ).execute()

    rows = result.get("values", [])
    if not rows:
        return []

    headers = [h.strip() for h in rows[0]]
    items = []

    for i, row in enumerate(rows[1:], start=2):
        # Preenche colunas faltando com string vazia
        row_padded = row + [""] * (len(headers) - len(row))
        record = {headers[j]: row_padded[j] for j in range(len(headers))}
        record["_row"] = i  # linha na planilha (para debug)

        if record.get(STATUS_COL, "").strip() == STATUS_AFAZER:
            # Identifica canal e live_id
            record["_channel"] = _detect_channel(record)
            record["_live_id"]  = _make_live_id(record)
            items.append(record)

    return items


def _detect_channel(record: dict) -> str:
    """Detecta 'fleet' ou 'teams' — usa coluna 'canal' primeiro, depois texto livre."""
    canal = record.get("canal", "").strip().lower()
    if "fleet" in canal or "frota" in canal:
        return "fleet"
    if "teams" in canal:
        return "teams"
    # fallback: busca no texto completo
    text = " ".join(str(v) for v in record.values()).lower()
    if "teams" in text:
        return "teams"
    return "fleet"


def _make_live_id(record: dict) -> str:
    """
    Gera ID único: extrai video ID da URL (mais confiável),
    ou usa o número de linha como fallback.
    """
    import re
    url = record.get("url", "")
    if url:
        # Extrai video ID do YouTube: watch?v=XXX ou /live/XXX ou youtu.be/XXX
        m = re.search(r'(?:v=|/live/|youtu\.be/)([A-Za-z0-9_-]{11})', url)
        if m:
            return m.group(1)
    # Fallback: primeiros 30 chars do título slugificado
    title = record.get("title", str(record.get("_row", "unknown")))
    return re.sub(r'[^a-z0-9]+', '-', title[:30].lower()).strip('-')


# -------------------------------------------------------------------
# Guest auto-detection
# -------------------------------------------------------------------

def find_guest_by_live_number(title: str) -> dict:
    """
    Extrai o número da live do título e busca fotos em referencias/convidados/.

    Naming convention: convidado_live-{N}-{Nome-Sobrenome}.{ext}
    Retorna {found, name, live_number, all_guests: [{name, filename}]}
    """
    import re

    m = re.search(r'\bLive\s+(\d+)\b', title, re.IGNORECASE)
    if not m:
        return {"found": False}

    live_number = m.group(1)

    if not GUESTS_DIR.exists():
        return {"found": False}

    matches = sorted(GUESTS_DIR.glob(f"*_live-{live_number}-*"))
    if not matches:
        return {"found": False}

    def _parse_name(path: Path) -> str:
        stem = path.stem  # e.g. "convidado_live-321-Nelson-Margarido"
        nm = re.search(r'_live-\d+-(.+)$', stem)
        if not nm:
            return stem
        return nm.group(1).replace('-', ' ').title()

    all_guests = [{"name": _parse_name(p), "filename": p.name} for p in matches]
    first_name = all_guests[0]["name"]

    return {
        "found": True,
        "name": first_name,
        "live_number": live_number,
        "all_guests": all_guests,
    }


# -------------------------------------------------------------------
# Audio transcription
# -------------------------------------------------------------------

def transcribe_audio(audio_bytes: bytes, api_key: str, mime_type: str = "audio/m4a") -> dict:
    """
    Envia áudio ao Gemini Flash e extrai as 3 respostas do briefing.

    Retorna dict com q1, q2, q3 e raw_text.
    """
    audio_b64 = base64.b64encode(audio_bytes).decode()

    prompt = (
        "Você vai receber um áudio de briefing para criação de thumbnail de live de YouTube.\n\n"
        "ETAPA 1 — TRANSCRIÇÃO E AJUSTE:\n"
        "Transcreva o áudio e corrija possíveis erros de reconhecimento de fala "
        "(palavras parecidas, sotaque, termos técnicos de gestão de frotas e logística). "
        "Preserve o sentido original — não invente informações.\n\n"
        "ETAPA 2 — CLASSIFICAÇÃO:\n"
        "A partir da transcrição ajustada, extraia:\n"
        "1. QUEM ASSISTE: Perfil do público-alvo da thumbnail\n"
        "2. OBJETIVO: O que queremos que o espectador sinta ou faça ao ver a thumbnail\n"
        "3. CONTEÚDO: O que acontece na live (tema, convidado, demonstração, etc.)\n\n"
        "Responda SOMENTE com JSON válido (sem markdown, sem ```), assim:\n"
        '{"q1": "perfil do público em 1-2 frases", '
        '"q2": "objetivo em 1-2 frases", '
        '"q3": "conteúdo da live em 2-3 frases"}'
    )

    payload = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": audio_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2000},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    resp = requests.post(FLASH_URL, headers=headers, json=payload, timeout=60)
    result = resp.json()

    if "candidates" not in result:
        err = result.get("error", {}).get("message", str(result)[:200])
        raise RuntimeError(f"Transcrição falhou: {err}")

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Tenta parsear JSON da resposta
    import re
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            parsed["raw_text"] = raw_text
            return parsed
        except json.JSONDecodeError:
            pass

    # Fallback: retorna texto bruto
    return {"q1": "", "q2": "", "q3": "", "raw_text": raw_text}


# -------------------------------------------------------------------
# Guest photo
# -------------------------------------------------------------------

def save_guest_photo(image_bytes: bytes, live_number: str, guest_name: str,
                     title_type: str = "convidado", ext: str = ".jpg") -> Path:
    """
    Salva foto de convidado em:
    thumbnail-ai-creator/referencias/convidados/{title_type}_live-{N}-{Nome-Sobrenome}{ext}
    """
    GUESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Formata nome: "Maria Silva" → "Maria-Silva"
    name_slug = guest_name.strip().replace(" ", "-").replace("_", "-")
    filename = f"{title_type}_live-{live_number}-{name_slug}{ext}"
    out_path = GUESTS_DIR / filename

    with open(out_path, "wb") as f:
        f.write(image_bytes)

    print(f"  Foto de convidado salva: {out_path.name}")
    return out_path


# -------------------------------------------------------------------
# Refs
# -------------------------------------------------------------------

def get_host_refs(channel: str) -> list[Path]:
    """Retorna lista de referências do apresentador baseado no canal."""
    if channel == "fleet":
        julio_dir = REFS_DIR / "julio"
        if not julio_dir.exists():
            return []
        # Exclui AI-geradas (studio_v1)
        refs = [
            f for f in julio_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png")
            and "studio_v1" not in f.name
        ]
        # Prioriza ref-primary, depois frontal-neutro, depois outros
        primary = [r for r in refs if "ref-primary" in r.name]
        frontal = [r for r in refs if "frontal-neutro" in r.name and "ref-primary" not in r.name]
        others  = [r for r in refs if "ref-primary" not in r.name and "frontal-neutro" not in r.name]
        return (primary + frontal + others)[:3]

    elif channel == "teams":
        leo_dir = REFS_DIR / "leonardo"
        if not leo_dir.exists():
            return []
        # Busca primary em jpg ou png
        for ext in (".png", ".jpg", ".jpeg"):
            primary = leo_dir / f"leo-ref-primary{ext}"
            if primary.exists():
                return [primary]
        # Fallback: fotos reais (exclui studio_v*)
        refs = [
            f for f in leo_dir.iterdir()
            if f.suffix.lower() in (".jpg", ".jpeg", ".png")
            and "studio_v" not in f.name
        ]
        return refs[:3]

    return []


def get_guest_refs(live_number: str) -> list[Path]:
    """Busca foto de convidado para uma live específica."""
    import re
    if not GUESTS_DIR.exists():
        return []

    pattern = re.compile(
        rf'^(\w+)_live-{re.escape(str(live_number))}-(.+)\.(jpg|jpeg|png|webp)$',
        re.IGNORECASE
    )
    for f in GUESTS_DIR.iterdir():
        if pattern.match(f.name):
            return [f]
    return []


def image_to_part(path: Path) -> dict:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    return {"inlineData": {"mimeType": mime, "data": data}}


# -------------------------------------------------------------------
# Auto-briefing from transcript
# -------------------------------------------------------------------

def auto_briefing_from_transcript(transcript: str, title: str, api_key: str) -> dict:
    """
    Usa Gemini Flash para extrair q1/q2/q3 de uma transcrição de live.
    Retorna: {q1, q2, q3}
    """
    prompt = f"""Você é um estrategista de conteúdo B2B para o canal Frota Para Todos (gestão de frotas).

Título da live: {title}

Transcrição (pode estar truncada):
{transcript[:18000]}

A partir dessa transcrição, extraia as 3 informações abaixo em português, com 1-2 frases cada:
- Q1: Quem é o público-alvo que vai assistir? (perfil, cargo, situação)
- Q2: O que eles vão ganhar ao assistir? (resultado concreto, transformação)
- Q3: O que acontece especificamente nessa live? (conteúdo, demonstrações, histórias)

Retorne SOMENTE JSON válido, sem markdown:
{{"q1": "...", "q2": "...", "q3": "..."}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 600},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(FLASH_URL, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "candidates" in result:
            raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            import re as _re
            m = _re.search(r'\{[\s\S]*\}', raw)
            if m:
                return json.loads(m.group())
    except Exception as e:
        print(f"  auto_briefing error: {e}")

    return {"q1": "", "q2": "", "q3": ""}


# -------------------------------------------------------------------
# Angle generation
# -------------------------------------------------------------------

ANGLE_SYSTEM_PROMPT = """You are a YouTube thumbnail creative director for B2B live stream content.

Given the channel, briefing, and guest info, generate 2 visually DISTINCT thumbnail angles (A and B) that stop the target viewer from scrolling.

CHANNEL VISUAL LANGUAGE:
- fleet (Frota Para Todos): trucking/fleet B2B. Dark fleet yards, trucks, industrial tools. Red/orange/crimson dramatic lighting. Feels powerful, urgent, serious.
- teams (Contele Teams): field team management B2B. Modern offices, tech dashboards, smartphones. Purple/magenta/electric-blue lighting. Feels innovative, forward-looking.

CORE PRINCIPLE — THUMBNAIL SHOWS THE RESULT:
The image communicates what the viewer WILL GET, not just teases curiosity.
Use Q1/Q2/Q3 to decide visuals:
- Q1 (who's watching) → choose visuals from THEIR daily reality
- Q2 (what they'll gain) → background/elements EMBODY that outcome
- Q3 (what happens) → pick props/background directly from the content discussed

ANGLE RULES:
- A: declarative — title shows THE ANSWER/RESULT; visual confirms the payoff
- B: tension — title names THE PROBLEM/CHALLENGE; visual shows the stakes
Both must be visually distinct: different background, color palette, positioning, 3D elements.

TITLE RULES:
- titulo: 2-5 words, ALL CAPS, Portuguese, SPECIFIC (NOT generic "COMO FAZER" — say WHAT exactly)
- subtitulo: 2-4 words, accent color, complements title (can be empty string)

3D ELEMENTS: 2-3 max, small, directly related to content (steering wheel, GPS, speedometer, document, smartphone, truck icon, wrench, tablet, etc.). NOT competing with faces.

Output ONLY valid JSON, no markdown fences:
{
  "angle_a": {
    "titulo": "EXACT TITLE IN CAPS",
    "subtitulo": "SUBTITLE OR EMPTY STRING",
    "host_posicao": "left|center|right",
    "guest_posicao": "left|center|right|null",
    "expressao_host": "serio|surpreso|pensativo|assertivo|sorrindo|ironico|confiante",
    "expressao_guest": "expression keyword or null",
    "background": "detailed background that visually represents the content result — scene, objects, atmosphere",
    "cor_dominante": "specific color palette e.g. dark navy with red/orange drama",
    "iluminacao": "lighting style e.g. dramatic red side-light from left, warm orange haze",
    "elementos_3d": ["content-related prop 1", "content-related prop 2"],
    "rationale": "1 sentence: why this shows the viewer what they will get"
  },
  "angle_b": {
    "titulo": "DIFFERENT TITLE FROM A",
    "subtitulo": "SUBTITLE OR EMPTY STRING",
    "host_posicao": "left|center|right",
    "guest_posicao": "left|center|right|null",
    "expressao_host": "serio|surpreso|pensativo|assertivo|sorrindo|ironico|confiante",
    "expressao_guest": "expression keyword or null",
    "background": "DIFFERENT background from A — distinct visual story",
    "cor_dominante": "DIFFERENT palette from A",
    "iluminacao": "DIFFERENT lighting style from A",
    "elementos_3d": ["different prop 1", "different prop 2"],
    "rationale": "1 sentence: why this shows the problem/challenge"
  }
}"""


_DIVERGENCE_INSTRUCTIONS = {
    "low": (
        "DIVERGENCE LEVEL: LOW (1-3/10). "
        "A and B share the same color family and general environment. "
        "Differ only in: title wording, host expression, and 1-2 different 3D elements. "
        "Think 'same vibe, slightly different angle'."
    ),
    "medium": (
        "DIVERGENCE LEVEL: MEDIUM (4-6/10). "
        "A and B must have clearly different backgrounds (different scene/location), "
        "different dominant color palette, and different lighting direction. "
        "Same brand feel, but viewer immediately notices they are distinct thumbnails."
    ),
    "high": (
        "DIVERGENCE LEVEL: HIGH (7-8/10). "
        "A and B must be strongly contrasted: different environment types "
        "(e.g. industrial yard vs corporate office), opposite color temperatures "
        "(warm orange/red vs cool blue/purple), opposite emotional registers "
        "(urgency vs confidence), and completely different 3D props."
    ),
    "max": (
        "DIVERGENCE LEVEL: MAXIMUM (9-10/10). "
        "A and B must be radical opposites in every dimension: "
        "outdoor vs indoor, night vs day, action vs stillness, "
        "warm vs cold color temperature, problem-focused vs solution-focused composition, "
        "reversed host positioning. A viewer should feel they are completely different thumbnails "
        "for the same content — maximum split-test contrast."
    ),
}

def _divergence_tier(level: int) -> str:
    if level <= 3:   return "low"
    if level <= 6:   return "medium"
    if level <= 8:   return "high"
    return "max"


def generate_angles(briefing: dict, api_key: str, divergence: int = 6) -> dict:
    """
    Usa Gemini Flash para gerar os 2 ângulos criativos (A e B) baseado no briefing.

    briefing: {title, channel, q1, q2, q3, live_id}
    divergence: 1-10 — controla o quão distintos A e B devem ser (default: 6)
    Retorna: {angle_a: {...}, angle_b: {...}}
    """
    import re

    divergence   = max(1, min(10, int(divergence)))
    tier         = _divergence_tier(divergence)
    div_instr    = _DIVERGENCE_INSTRUCTIONS[tier]

    guest_name = briefing.get("guest", "")
    live_number = briefing.get("live_num", briefing.get("live_id", "?"))
    guest_line = (
        f"\nGuest in thumbnail: {guest_name} (appears side-by-side with host)"
        if guest_name else "\nNo guest — host only thumbnail"
    )

    q1 = briefing.get('q1', '').strip()
    q2 = briefing.get('q2', '').strip()
    q3 = briefing.get('q3', '').strip()
    thumb_text = briefing.get('thumb_text', '').strip()

    if q1 or q2 or q3:
        briefing_block = (
            f"Briefing (use to decide visual style — what the viewer will GET from this live):\n"
            f"Q1 — Quem assiste: {q1}\n"
            f"Q2 — O que vão ganhar: {q2}\n"
            f"Q3 — O que acontece na live: {q3}"
        )
    else:
        # Nutella sem briefing — usa título + hook sugerido como âncora criativa
        hook_line = f'Suggested hook/text: "{thumb_text}"' if thumb_text else ""
        briefing_block = (
            f"No detailed briefing available. Use the title and channel context to infer the visuals.\n"
            + (f"{hook_line}\n" if hook_line else "")
            + "Focus on the concrete result the viewer will achieve."
        )

    user_msg = f"""Live title: {briefing.get('title', 'Untitled')}
Channel: {briefing.get('channel', 'fleet')} (fleet=frotas B2B, teams=gestão de equipes)
Live number: {live_number}{guest_line}

{briefing_block}

{div_instr}

Generate angles A and B following the divergence level above."""

    payload = {
        "contents": [{"parts": [{"text": user_msg}]}],
        "systemInstruction": {"parts": [{"text": ANGLE_SYSTEM_PROMPT}]},
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(FLASH_URL, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "candidates" in result:
            raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        print(f"  Angle generation error: {e}")

    # Fallback angles
    return {
        "angle_a": {
            "titulo": "PROVA REAL",
            "subtitulo": "",
            "host_posicao": "center",
            "guest_posicao": None,
            "expressao_host": "assertivo",
            "expressao_guest": None,
            "background": "dark fleet yard with truck silhouettes, industrial red lighting",
            "cor_dominante": "dark navy with red/orange accents",
            "iluminacao": "dramatic red side-light, cinematic",
            "elementos_3d": ["floating GPS device", "speedometer"],
            "rationale": "Shows the payoff directly to the viewer"
        },
        "angle_b": {
            "titulo": "VOCÊ SABE?",
            "subtitulo": "",
            "host_posicao": "right",
            "guest_posicao": None,
            "expressao_host": "surpreso",
            "expressao_guest": None,
            "background": "modern fleet office with monitors showing data, dark blue lighting",
            "cor_dominante": "dark blue with orange accent",
            "iluminacao": "cool blue ambient with warm orange highlight",
            "elementos_3d": ["red warning triangle", "truck icon"],
            "rationale": "Creates curiosity gap about the problem"
        }
    }


# -------------------------------------------------------------------
# Prompt builder for lives
# -------------------------------------------------------------------

HOST_DESCRIPTION = {
    "fleet": (
        "JULIO (HOST) - {posicao} - COPY FROM IMAGES 1-{n}:\n"
        "- WIDER face shape, slightly square jaw — MATCH THE REFERENCE\n"
        "- DENSE gray/white stubble beard covering jaw and chin (salt and pepper, NOT sparse)\n"
        "- Receding hairline with short brown/gray hair — MATCH THE REFERENCE\n"
        "- Deep-set brown/hazel eyes, NO glasses\n"
        "- Age: 37-40 years old, YOUTHFUL and FIT appearance\n"
        "- Skin SMOOTH and FIRM — do NOT add wrinkles, crow's feet, or forehead lines\n"
        "- He looks YOUNGER than his beard suggests — keep face tight and fresh\n"
        "- Dark navy blue polo shirt (plain, no logos)\n"
        "- FACE MUST be recognizable as the same person from reference photos\n"
        "- Expression: {expressao}"
    ),
    "teams": (
        "LEONARDO (HOST) - {posicao} - COPY FROM IMAGES 1-{n}:\n"
        "- Match face from reference photos EXACTLY\n"
        "- Professional, confident appearance\n"
        "- Dark/neutral business casual clothing\n"
        "- FACE MUST be recognizable as the same person from reference photos\n"
        "- Expression: {expressao}"
    ),
}

HOST_SHORT = {"fleet": "JULIO", "teams": "LEONARDO"}


def _parse_guest_name(path) -> str:
    """'convidado_live-317-Nelson-Margarido.jpg' → 'Nelson Margarido'
    'convidado_live-321-Shelton-De-Lima.jpg' → 'Shelton De Lima'"""
    from pathlib import Path as _P
    stem = _P(path).stem
    parts = stem.split("-")
    if len(parts) >= 3:
        # Skip "convidado_live" (index 0) and live number (index 1)
        return " ".join(parts[2:]).title()
    return stem.replace("-", " ").title()


def build_live_prompt(briefing: dict, angle: str, angle_data: dict,
                      host_ref_count: int = 2,
                      guest_refs=None,
                      live_number: str = "") -> str:
    """
    Constrói o prompt de geração de imagem para thumbnail de live.

    host_ref_count : quantas imagens são do host (Images 1..N)
    guest_refs     : lista de Path dos convidados (depois das imgs do host)
    live_number    : "317", "318", etc.
    """
    guest_refs = list(guest_refs or [])
    channel = briefing.get("channel", "fleet")
    host_name = HOST_SHORT.get(channel, "JULIO")

    # ---- CRITICAL face block ------------------------------------------------
    face_lines = []
    if host_ref_count == 1:
        face_lines.append(f"- Image 1: {host_name} (host) — copy this exact face")
    else:
        face_lines.append(
            f"- Images 1-{host_ref_count}: {host_name} (host) — "
            "copy this exact face from ALL reference photos"
        )

    guest_names = []
    for i, g_path in enumerate(guest_refs):
        img_num = host_ref_count + 1 + i
        g_name = _parse_guest_name(g_path)
        guest_names.append(g_name)
        face_lines.append(
            f"- Image {img_num}: {g_name.upper()} (guest) — copy this exact face. "
            "Use ONLY facial features visible in the photo; ignore any artistic effects."
        )

    n_people = 1 + len(guest_refs)
    if n_people == 1:
        people_intro = f"Create a YouTube thumbnail (16:9) with {host_name} from the reference photos."
    elif n_people == 2:
        people_intro = "Create a YouTube thumbnail (16:9) with BOTH people from the reference photos."
    else:
        people_intro = f"Create a YouTube thumbnail (16:9) with ALL {n_people} people from the reference photos."

    face_block = "\n".join(face_lines)

    # ---- Host description ---------------------------------------------------
    host_pos = angle_data.get("host_posicao", "center" if not guest_refs else "right")
    host_expr = angle_data.get("expressao_host", "serio")
    pos_label = f"{host_pos.upper()} SIDE" if host_pos != "center" else "CENTER"
    host_desc = (
        HOST_DESCRIPTION.get(channel, HOST_DESCRIPTION["fleet"])
        .replace("{posicao}", pos_label)
        .replace("{n}", str(host_ref_count))
        .replace("{expressao}", host_expr)
    )

    # ---- Guest descriptions -------------------------------------------------
    guest_sections = []
    for i, g_path in enumerate(guest_refs):
        img_num = host_ref_count + 1 + i
        g_name = guest_names[i]
        if len(guest_refs) == 1:
            g_pos_key = (angle_data.get("guest_posicao") or
                         ("left" if host_pos in ("right", "center") else "right"))
        else:
            g_pos_key = "left" if i == 0 else "right"
        g_pos_label = f"{g_pos_key.upper()} SIDE"
        g_expr = angle_data.get("expressao_guest") or "professional and engaged"
        label_en = "GUEST" if len(guest_refs) == 1 else f"GUEST {i + 1}"
        guest_sections.append(
            f"{g_name.upper()} ({label_en}) - {g_pos_label} - COPY FACE FROM IMAGE {img_num}:\n"
            f"- Use reference photo for all physical features\n"
            f"- {g_expr} expression, professional appearance\n"
            f"- Dark/neutral clothing matching their style in the photo"
        )

    # ---- Composition --------------------------------------------------------
    background = angle_data.get(
        "background",
        "dark fleet yard with industrial red lighting" if channel == "fleet"
        else "modern office with purple/magenta ambient lighting"
    )
    iluminacao = angle_data.get(
        "iluminacao",
        "dramatic red/orange cinematic side-lighting" if channel == "fleet"
        else "cool purple/magenta ambient glow"
    )

    # ---- 3D elements --------------------------------------------------------
    elementos_3d_list = angle_data.get("elementos_3d", [])
    if elementos_3d_list:
        elementos_str = (
            "\n3D ELEMENTS (subtle, max 3 items, small, not competing with faces):\n"
            + "\n".join(f"- {e}" for e in elementos_3d_list[:3])
        )
    else:
        elementos_str = ""

    # ---- Positioning summary ------------------------------------------------
    if n_people == 1:
        positioning = f"- {host_name} centered, dominant composition, medium shot (chest up)"
    elif n_people == 2:
        g_pos_key = angle_data.get("guest_posicao") or "left"
        positioning = (
            f"- {host_name} on {host_pos.upper()} SIDE\n"
            f"- {guest_names[0]} on {g_pos_key.upper()} SIDE\n"
            "- Both medium shot (chest up)"
        )
    else:
        g_pos_list = ["left" if i == 0 else "right" for i in range(len(guest_names))]
        guest_pos_lines = "\n".join(
            f"- {gn} on {gp.upper()} SIDE"
            for gn, gp in zip(guest_names, g_pos_list)
        )
        positioning = (
            f"- {host_name} CENTER (slightly larger, slightly forward)\n"
            f"{guest_pos_lines}\n"
            "- All medium shot (chest up)"
        )

    # ---- TEXT block ---------------------------------------------------------
    titulo = angle_data.get("titulo", "")
    subtitulo = angle_data.get("subtitulo", "")

    text_parts = []
    if live_number:
        text_parts.append(f'- "LIVE {live_number}" bold red badge top-left corner (always present)')
    if titulo:
        text_parts.append(
            f'- "{titulo}" large bold white text with strong black shadow, lower third'
        )
    if subtitulo:
        text_parts.append(
            f'- "{subtitulo}" bold text in bright RED/orange below the main title'
        )
    if guest_names:
        if len(guest_names) == 1:
            guest_label_str = f"Convidado {guest_names[0]}"
        else:
            guest_label_str = "Convidados " + " e ".join(guest_names)
        text_parts.append(
            f'- "{guest_label_str}" medium white text with dark semi-transparent pill/badge '
            "background positioned near guest(s). Clearly readable on mobile, NOT as large as main title."
        )

    text_block = "\n".join(text_parts)

    # ---- Color --------------------------------------------------------------
    cor = angle_data.get(
        "cor_dominante",
        "dark navy/black with aggressive red and orange accents" if channel == "fleet"
        else "deep purple/navy with magenta and electric-blue accents"
    )

    # ---- Guest section string -----------------------------------------------
    guest_block_str = ("\n\n" + "\n\n".join(guest_sections)) if guest_sections else ""

    # ---- Final prompt -------------------------------------------------------
    return f"""CRITICAL - FACE REFERENCE IMAGES:
{face_block}
- Do NOT create different people — faces MUST be recognizable as the same people in the reference photos

{people_intro}

{host_desc}{guest_block_str}

COMPOSITION:
{positioning}
- Background: {background}
- Lighting: {iluminacao}{elementos_str}

TEXT:
{text_block}
- Text positioned in lower third or left/right side — NOT overlapping faces

COLOR: {cor}. High contrast for mobile thumbnails.

STYLE: Professional YouTube thumbnail. Photorealistic faces — FACE ACCURACY is #1 priority. Cinematic lighting. High contrast readable at small sizes. No watermarks, no borders.

BRIEFING CONTEXT (guides visual storytelling — not for text):
- Audience: {briefing.get('q1', '')}
- What they gain: {briefing.get('q2', '')}
- Content: {briefing.get('q3', '')}"""


# -------------------------------------------------------------------
# Image generation
# -------------------------------------------------------------------

def _generate_one(api_key: str, prompt: str, refs: list[Path],
                  output_path: Path, angle: str) -> Path | None:
    """Gera uma thumbnail."""
    parts = [image_to_part(r) for r in refs]
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
            "temperature": 0,
        },
    }
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(IMAGE_URL, headers=headers, json=payload, timeout=TIMEOUT)
        result = resp.json()

        if "candidates" not in result:
            err = result.get("error", {}).get("message", str(result)[:200])
            print(f"  Thumb {angle} ERRO: {err}")
            return None

        for part in result["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_data)
                size_kb = len(img_data) // 1024
                print(f"  Thumb {angle} OK → {output_path.name} ({size_kb}KB)")
                return output_path

        print(f"  Thumb {angle} ERRO: sem imagem na resposta")
        return None

    except requests.Timeout:
        print(f"  Thumb {angle} TIMEOUT ({TIMEOUT}s)")
        return None
    except Exception as e:
        print(f"  Thumb {angle} ERRO: {e}")
        return None


def generate_ab(briefing: dict, live_id: str, api_key: str,
                progress_cb=None, divergence: int = 6) -> tuple[Path | None, Path | None]:
    """
    Gera thumbnails A e B em paralelo.
    progress_cb({"step": str, "msg": str, ...}) é chamado em cada etapa.

    Returns: (path_a, path_b)
    """
    import re, time as _time

    def emit(step: str, msg: str, **kw):
        print(f"  [{step}] {msg}")
        if progress_cb:
            progress_cb({"step": step, "msg": msg, **kw})

    OUTPUT_DIR.mkdir(exist_ok=True)

    channel = briefing.get("channel", "fleet")

    # Extrai número da live do título
    title = briefing.get("title", "")
    m = re.search(r'\bLive\s+(\d+)\b', title, re.IGNORECASE)
    live_number = m.group(1) if m else ""

    # Refs do host
    host_refs = get_host_refs(channel)
    host_label = "Julio (Fleet)" if channel == "fleet" else "Leonardo (Teams)"
    ref_names  = [r.name for r in host_refs]
    emit("refs_host", f"{host_label}: {', '.join(ref_names[:2])}{'…' if len(ref_names)>2 else ''}",
         count=len(host_refs), names=ref_names[:3])

    # Refs do convidado
    guest_refs = get_guest_refs(live_number) if live_number else []
    if guest_refs:
        guest_label = _parse_guest_name(guest_refs[0])
        emit("refs_guest", f"Convidado: {guest_label}", found=True, file=guest_refs[0].name)
        # Enriquecer briefing com nome do convidado (se não veio do frontend)
        if not briefing.get("guest"):
            briefing = {**briefing, "guest": guest_label}
    else:
        guest_label_from_briefing = briefing.get("guest", "")
        emit("refs_guest",
             (f"Sem foto de convidado para Live {live_number}"
              if live_number else "Sem foto de convidado") +
             (f" (nome no briefing: {guest_label_from_briefing})" if guest_label_from_briefing else ""),
             found=False)

    all_refs = host_refs + guest_refs
    if not all_refs:
        emit("refs_host", f"AVISO: nenhuma referência para canal '{channel}'")

    # Gera ângulos com IA
    div_label = f"divergência {divergence}/10 ({_divergence_tier(divergence)})"
    emit("angles_start", f"Gerando ângulos criativos com IA — {div_label}...")
    _t0 = _time.time()
    angles  = generate_angles(briefing, api_key, divergence=divergence)
    angle_a = angles.get("angle_a", {})
    angle_b = angles.get("angle_b", {})
    txt_a   = angle_a.get("titulo", angle_a.get("texto", "A"))
    txt_b   = angle_b.get("titulo", angle_b.get("texto", "B"))
    emit("angles_done", f'A: "{txt_a}" · B: "{txt_b}"',
         elapsed=round(_time.time() - _t0, 1),
         angle_a=angle_a, angle_b=angle_b)

    safe_id = str(live_id).replace("/", "-").replace("\\", "-")[:40]
    path_a  = OUTPUT_DIR / f"thumb_live_{safe_id}_a.png"
    path_b  = OUTPUT_DIR / f"thumb_live_{safe_id}_b.png"

    prompt_a = build_live_prompt(briefing, "A", angle_a,
                                 host_ref_count=len(host_refs),
                                 guest_refs=guest_refs,
                                 live_number=live_number)
    prompt_b = build_live_prompt(briefing, "B", angle_b,
                                 host_ref_count=len(host_refs),
                                 guest_refs=guest_refs,
                                 live_number=live_number)

    emit("gen_parallel", f"Gerando A e B em paralelo — {MODEL_IMAGE}...")

    def _gen_with_progress(angle_label: str, prompt: str, out_path: Path) -> Path | None:
        emit(f"gen_{angle_label.lower()}_start", f"Gerando Thumbnail {angle_label}...")
        _ts = _time.time()
        path = _generate_one(api_key, prompt, all_refs, out_path, angle_label)
        _elapsed = round(_time.time() - _ts, 1)
        if path:
            size_kb = path.stat().st_size // 1024
            emit(f"gen_{angle_label.lower()}_done",
                 f"Thumbnail {angle_label} pronta — {size_kb}KB ({_elapsed}s)",
                 size_kb=size_kb, elapsed=_elapsed)
        else:
            emit(f"gen_{angle_label.lower()}_done",
                 f"Thumbnail {angle_label} falhou ({_elapsed}s)", error=True)
        return path

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(_gen_with_progress, "A", prompt_a, path_a)
        fut_b = pool.submit(_gen_with_progress, "B", prompt_b, path_b)
        result_a = fut_a.result()
        result_b = fut_b.result()

    # Salva angles no state para uso posterior
    state = load_state()
    item = state.get("items", {}).get(live_id, {})
    item["angles"] = angles
    item["prompts"] = {"a": prompt_a, "b": prompt_b}
    state.setdefault("items", {})[live_id] = item
    save_state(state)

    return result_a, result_b


def regenerate_one(briefing: dict, live_id: str, angle: str,
                   feedback: str, api_key: str) -> Path | None:
    """Regera apenas a thumbnail A ou B com feedback."""
    from gen_thumb import adjust_prompt_with_feedback

    state = load_state()
    item = state.get("items", {}).get(live_id, {})
    prompts = item.get("prompts", {})
    original_prompt = prompts.get(angle.lower(), "")

    channel = briefing.get("channel", "fleet")
    import re as _re
    title = briefing.get("title", "")
    _m = _re.search(r'\bLive\s+(\d+)\b', title, _re.IGNORECASE)
    live_number = _m.group(1) if _m else briefing.get("live_num", "")
    host_refs  = get_host_refs(channel)
    guest_refs = get_guest_refs(live_number) if live_number else []

    if not original_prompt:
        # Reconstrói o prompt
        angles = item.get("angles", generate_angles(briefing, api_key))
        angle_data = angles.get(f"angle_{angle.lower()}", {})
        original_prompt = build_live_prompt(
            briefing, angle.upper(), angle_data,
            host_ref_count=len(host_refs),
            guest_refs=guest_refs,
            live_number=live_number,
        )

    print(f"  Ajustando prompt com feedback para {angle}...")
    adjusted = adjust_prompt_with_feedback(original_prompt, feedback, api_key)

    refs = host_refs + guest_refs

    safe_id = str(live_id).replace("/", "-").replace("\\", "-")[:40]
    out_path = OUTPUT_DIR / f"thumb_live_{safe_id}_{angle.lower()}.png"

    return _generate_one(api_key, adjusted, refs, out_path, angle)


# -------------------------------------------------------------------
# Google Drive upload
# -------------------------------------------------------------------

def upload_to_drive_folder(file_path: Path, folder_link: str, creds) -> dict:
    """
    Upload de arquivo PNG para pasta no Google Drive.
    folder_link pode ser URL completo ou só o folder ID.

    Requer scope: https://www.googleapis.com/auth/drive.file
    """
    import re
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    # Extrai folder ID de URL (suporta /folders/ID ou só ID)
    m = re.search(r'folders/([A-Za-z0-9_-]+)', folder_link)
    folder_id = m.group(1) if m else folder_link.strip()

    drive_svc = build("drive", "v3", credentials=creds)
    file_meta = {"name": file_path.name, "parents": [folder_id]}
    media     = MediaFileUpload(str(file_path), mimetype="image/png", resumable=False)
    result    = drive_svc.files().create(
        body=file_meta,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()
    return {
        "id":   result["id"],
        "name": result["name"],
        "link": result.get("webViewLink", ""),
    }


# -------------------------------------------------------------------
# State management
# -------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"items": {}}


def save_state(data: dict):
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def upsert_item(live_id: str, fields: dict) -> dict:
    """Atualiza (merge) campos de um item no state."""
    state = load_state()
    item = state.setdefault("items", {}).setdefault(live_id, {})
    item.update(fields)
    save_state(state)
    return item


def approve_thumb(live_id: str, choice: str, path: str) -> dict:
    """
    Salva aprovação no state.
    choice: "A" ou "B"
    """
    state = load_state()
    item = state.setdefault("items", {}).setdefault(live_id, {})
    item["approved"] = choice.upper()
    item["approved_at"] = datetime.now().isoformat()
    if choice.upper() == "A":
        item["thumb_a"] = path
    else:
        item["thumb_b"] = path
    save_state(state)
    return item


def add_feedback(live_id: str, angle: str, feedback: str) -> dict:
    """Registra feedback no histórico do item."""
    state = load_state()
    item = state.setdefault("items", {}).setdefault(live_id, {})
    history = item.setdefault("feedback_history", [])
    history.append({
        "angle": angle.upper(),
        "feedback": feedback,
        "timestamp": datetime.now().isoformat()
    })
    save_state(state)
    return item
