#!/usr/bin/env python3
"""
Nutella Creator — Análise completa de clips virais com brief de produção.

Saída por nutella:
  - Timestamps IN/OUT horizontal + Shorts (tighter)
  - Hook moment (primeiros 3 segundos de ouro)
  - Título SEO + Título CTR + Título Shorts
  - Texto thumbnail + composição visual
  - Expressão Julio + tipo + objetivo
  - Por que viraliza

Uso:
  python3 suggest.py <URL_OU_VIDEO_ID>
  python3 suggest.py ra-GUivQnso
  python3 suggest.py https://youtube.com/watch?v=XXXX --json
"""

import os
import sys
import re
import json
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

_LOCAL_ENV = Path(__file__).parent / ".env"
_THUMB_ENV = Path(__file__).parent.parent / "thumbnail-ai-creator" / ".env"
ENV_PATH = _LOCAL_ENV if _LOCAL_ENV.exists() else _THUMB_ENV
OUTPUT_DIR = Path(__file__).parent / "output"
GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_FLASH_MODEL = "gemini-3-flash-preview"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

logger = logging.getLogger("prism.suggest")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_api_key() -> str:
    # Prefer env var (Railway)
    key = os.environ.get("GEMINI_NANO_BANANA_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("GEMINI_NANO_BANANA_KEY"):
                    return line.split("=", 1)[1].strip().strip('"')
    raise ValueError("GEMINI_NANO_BANANA_KEY não encontrada")


# -------------------------------------------------------------------
# YouTube
# -------------------------------------------------------------------

def extract_video_id(url_or_id: str) -> str:
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
    for pattern in [
        r"(?:youtube\.com/(?:watch\?v=|live/)|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"v=([a-zA-Z0-9_-]{11})",
    ]:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"Não foi possível extrair video_id de: {url_or_id}")


def fmt_time(seconds: float) -> str:
    s = int(seconds)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def time_to_seconds(t: str) -> int:
    parts = t.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(parts[0]) * 60 + int(parts[1])


def _find_cookies_path() -> Path | None:
    """Busca cookies.txt: env var (Railway) > local."""
    env_path = os.environ.get("COOKIES_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    local = Path(__file__).parent / "cookies.txt"
    if local.exists():
        return local
    return None


def _get_transcript_ytdlp(video_id: str) -> list[dict]:
    """Fallback 1: extrai legendas via yt-dlp."""
    import subprocess, tempfile
    cookies_file = _find_cookies_path()
    cookies_arg = ["--cookies", str(cookies_file)] if cookies_file else []

    with tempfile.TemporaryDirectory(prefix="transcript_") as tmp:
        tmp_path = Path(tmp)
        # Tenta auto-sub E sub manual
        cmd = [
            "yt-dlp",
            "--write-auto-sub", "--write-sub",
            "--sub-lang", "pt,pt-BR,en",
            "--sub-format", "json3",
            "--skip-download",
            "--remote-components", "ejs:github",
            *cookies_arg,
            "-o", str(tmp_path / "sub"),
            f"https://youtube.com/watch?v={video_id}",
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        sub_files = list(tmp_path.glob("*.json3"))
        if not sub_files:
            raise RuntimeError(
                f"yt-dlp nao conseguiu extrair legendas para {video_id}."
            )

        with open(sub_files[0], encoding="utf-8") as f:
            data = json.load(f)

        segments = []
        for event in data.get("events", []):
            start_ms = event.get("tStartMs", 0)
            dur_ms = event.get("dDurationMs", 0)
            segs = event.get("segs", [])
            text = "".join(s.get("utf8", "") for s in segs).strip()
            if text and text != "\n":
                segments.append({
                    "start": start_ms / 1000.0,
                    "duration": dur_ms / 1000.0,
                    "text": text,
                })
        if not segments:
            raise RuntimeError(f"Legendas vazias para {video_id}")
        return segments


def _load_teams_credentials():
    """Carrega token OAuth do canal Teams (Leonardo), se disponivel."""
    import pickle
    from google.auth.transport.requests import Request
    teams_path = os.environ.get("YOUTUBE_TEAMS_TOKEN_PATH")
    if not teams_path or not Path(teams_path).exists():
        # Fallback: local dev
        local = Path(__file__).parent / "token_youtube_teams.pickle"
        if local.exists():
            teams_path = str(local)
        else:
            return None
    with open(teams_path, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(teams_path, "wb") as f:
            pickle.dump(creds, f)
    return creds if creds.valid else None


def _get_transcript_youtube_api(video_id: str, channel: str = "fleet") -> list[dict]:
    """Fallback 2: YouTube Data API captions (autenticado, ignora IP block)."""
    from googleapiclient.discovery import build

    creds = None
    # Tenta token do canal correto primeiro
    if channel == "teams":
        creds = _load_teams_credentials()
        if creds:
            print(f"  Usando token OAuth Teams (Leonardo)")
    if not creds:
        try:
            from upload import load_credentials, get_youtube
            creds = load_credentials()
            print(f"  Usando token OAuth Fleet (Julio)")
        except Exception:
            raise RuntimeError("YouTube OAuth nao configurado (nem Fleet nem Teams)")

    youtube = build("youtube", "v3", credentials=creds)

    # Lista captions disponiveis
    captions = youtube.captions().list(part="snippet", videoId=video_id).execute()
    items = captions.get("items", [])
    if not items:
        raise RuntimeError(f"Video {video_id} nao tem legendas na API")

    # Prefere pt > pt-BR > en > qualquer
    preferred = None
    for lang in ["pt", "pt-BR", "en"]:
        for item in items:
            if item["snippet"]["language"] == lang:
                preferred = item
                break
        if preferred:
            break
    if not preferred:
        preferred = items[0]

    # Download da caption (SRT format)
    caption_id = preferred["id"]
    srt_data = youtube.captions().download(id=caption_id, tfmt="srt").execute()
    if isinstance(srt_data, bytes):
        srt_data = srt_data.decode("utf-8")

    # Parse SRT
    segments = []
    blocks = srt_data.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = " ".join(lines[2:]).strip()
            # Parse "00:01:23,456 --> 00:01:25,789"
            parts = time_line.split(" --> ")
            if len(parts) == 2:
                def _srt_to_sec(t):
                    h, m, rest = t.split(":")
                    s, ms = rest.split(",")
                    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
                start = _srt_to_sec(parts[0].strip())
                end = _srt_to_sec(parts[1].strip())
                if text:
                    segments.append({
                        "start": start,
                        "duration": end - start,
                        "text": text,
                    })
    if not segments:
        raise RuntimeError(f"Caption vazia para {video_id}")
    return segments


def _get_transcript_gemini_audio(video_id: str, api_key: str) -> list[dict]:
    """
    Tier 4: baixa audio via yt-dlp e transcreve com Gemini Flash em chunks.

    Funciona quando nao ha captions disponiveis (tiers 1-3 falharam). Audio
    e cortado em chunks de 15min (cabe inline base64 <20MB em m4a 64k mono).
    Cada chunk e transcrito em paralelo e os timestamps sao reajustados com
    o offset do chunk.
    """
    import subprocess
    import tempfile
    import base64
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cookies_file = _find_cookies_path()
    cookies_arg = ["--cookies", str(cookies_file)] if cookies_file else []

    with tempfile.TemporaryDirectory(prefix="tier4_audio_") as tmp:
        tmp_path = Path(tmp)
        audio_path = tmp_path / "full.m4a"

        # 1) Baixa audio em m4a 64k mono pra reduzir tamanho
        cmd_dl = [
            "yt-dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio",
            "--extract-audio", "--audio-format", "m4a", "--audio-quality", "5",
            "--postprocessor-args", "-ac 1 -b:a 64k",
            *cookies_arg,
            "-o", str(tmp_path / "full.%(ext)s"),
            f"https://youtube.com/watch?v={video_id}",
        ]
        proc = subprocess.run(cmd_dl, capture_output=True, text=True, timeout=900)
        if proc.returncode != 0 or not audio_path.exists():
            stderr_tail = (proc.stderr or "")[-400:]
            raise RuntimeError(f"yt-dlp audio download falhou: {stderr_tail}")

        # 2) Divide em chunks de 15min via ffmpeg (saida: chunk_000.m4a, chunk_001.m4a, ...)
        chunk_dir = tmp_path / "chunks"
        chunk_dir.mkdir()
        chunk_seconds = 15 * 60
        cmd_split = [
            "ffmpeg", "-y", "-i", str(audio_path),
            "-f", "segment", "-segment_time", str(chunk_seconds),
            "-c", "copy",
            str(chunk_dir / "chunk_%03d.m4a"),
        ]
        proc = subprocess.run(cmd_split, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg segment falhou: {(proc.stderr or '')[-400:]}")

        chunk_files = sorted(chunk_dir.glob("chunk_*.m4a"))
        if not chunk_files:
            raise RuntimeError("ffmpeg nao gerou chunks de audio")

        logger.info("Tier 4: %d chunks de ate %ds pra transcrever", len(chunk_files), chunk_seconds)

        # 3) Transcreve cada chunk em paralelo
        flash_url = f"{GEMINI_API_URL}/{GEMINI_FLASH_MODEL}:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

        prompt = (
            "Transcreva este audio em portugues brasileiro, dividindo em segmentos de "
            "20 a 40 segundos. Preserve o sentido original, corrija erros obvios de "
            "reconhecimento de fala. Contexto: live de canal de gestao de frota e logistica.\n\n"
            "Responda SOMENTE com JSON array valido, sem markdown, sem preambulo, no formato:\n"
            '[{"start": 0.0, "duration": 28.5, "text": "..."}, {"start": 28.5, "duration": 32.0, "text": "..."}]\n\n'
            "Os tempos devem ser relativos ao INICIO DESTE TRECHO (comecando em 0)."
        )

        def _transcribe_chunk(idx: int, path: Path) -> list[dict]:
            offset_sec = idx * chunk_seconds
            data = base64.b64encode(path.read_bytes()).decode()
            payload = {
                "contents": [{
                    "parts": [
                        {"inlineData": {"mimeType": "audio/mp4", "data": data}},
                        {"text": prompt},
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 16000},
            }
            resp = requests.post(flash_url, headers=headers, json=payload, timeout=300)
            result = resp.json()
            if "candidates" not in result:
                err = result.get("error", {}).get("message", str(result)[:300])
                raise RuntimeError(f"chunk {idx}: Gemini falhou: {err}")
            raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            m = re.search(r"\[[\s\S]*\]", raw)
            if not m:
                raise RuntimeError(f"chunk {idx}: sem JSON array na resposta")
            parsed = json.loads(m.group())
            # Ajusta offset global
            for seg in parsed:
                seg["start"] = float(seg.get("start", 0)) + offset_sec
                seg["duration"] = float(seg.get("duration", 0))
                seg["text"] = str(seg.get("text", "")).strip()
            return [s for s in parsed if s["text"]]

        segments: list[dict] = []
        with ThreadPoolExecutor(max_workers=min(4, len(chunk_files))) as pool:
            futures = {pool.submit(_transcribe_chunk, i, p): i for i, p in enumerate(chunk_files)}
            per_chunk: dict[int, list[dict]] = {}
            for fut in as_completed(futures):
                idx = futures[fut]
                per_chunk[idx] = fut.result()
            for i in sorted(per_chunk.keys()):
                segments.extend(per_chunk[i])

        if not segments:
            raise RuntimeError("Tier 4: transcricao vazia apos merge de chunks")
        return segments


def get_transcript_with_timestamps(video_id: str, channel: str = "fleet") -> list[dict]:
    errors: dict[str, str] = {}

    # Tier 1: youtube-transcript-api (rapido, sem auth)
    try:
        cookies_path = _find_cookies_path()
        kwargs = {"languages": ["pt", "pt-BR", "en"]}
        if cookies_path:
            import http.cookiejar
            cj = http.cookiejar.MozillaCookieJar(str(cookies_path))
            cj.load(ignore_discard=True, ignore_expires=True)
            session = requests.Session()
            session.cookies = cj
            api = YouTubeTranscriptApi(http_client=session)
            logger.info("Tier 1: usando cookies de %s", cookies_path)
        else:
            api = YouTubeTranscriptApi()
        result = api.fetch(video_id, **kwargs)
        logger.info("Tier 1 OK: youtube-transcript-api (%d segmentos)", len(result))
        return [{"start": s.start, "duration": s.duration, "text": s.text} for s in result]
    except Exception as e1:
        errors["tier1"] = f"transcript-api: {e1}"
        logger.info("Tier 1 falhou (%s), tentando yt-dlp...", e1)

    # Tier 2: yt-dlp subtitles
    try:
        result = _get_transcript_ytdlp(video_id)
        logger.info("Tier 2 OK: yt-dlp subtitles (%d segmentos)", len(result))
        return result
    except Exception as e2:
        errors["tier2"] = f"yt-dlp: {e2}"
        logger.info("Tier 2 falhou (%s), tentando YouTube Data API...", e2)

    # Tier 3: YouTube Data API captions (autenticado)
    try:
        result = _get_transcript_youtube_api(video_id, channel=channel)
        logger.info("Tier 3 OK: YouTube Data API (%d segmentos)", len(result))
        return result
    except Exception as e3:
        errors["tier3"] = f"youtube-api: {e3}"
        logger.info("Tier 3 falhou (%s), tentando Tier 4 (audio + Gemini)...", e3)

    # Tier 4: baixa audio e transcreve via Gemini Flash
    try:
        api_key = load_api_key()
        result = _get_transcript_gemini_audio(video_id, api_key=api_key)
        logger.info("Tier 4 OK: audio+Gemini (%d segmentos)", len(result))
        return result
    except Exception as e4:
        errors["tier4"] = f"audio+gemini: {e4}"
        logger.warning("Tier 4 falhou: %s", e4)
        detail = " | ".join(f"{k}: {v}" for k, v in errors.items())
        raise RuntimeError(
            f"Todos os tiers de transcricao falharam para {video_id}. "
            f"Cole a transcricao manualmente no campo abaixo e tente novamente. "
            f"Detalhes: {detail}"
        )


def build_transcript_text(segments: list[dict], chunk_size: int = 90) -> str:
    """Agrupa em chunks menores (90s) para mais granularidade nos cortes."""
    if not segments:
        return ""
    lines = []
    chunk_start = segments[0]["start"]
    chunk_texts = []
    for seg in segments:
        chunk_texts.append(seg["text"])
        if seg["start"] - chunk_start >= chunk_size:
            lines.append(f"[{fmt_time(chunk_start)}] {' '.join(chunk_texts)}")
            chunk_start = seg["start"]
            chunk_texts = []
    if chunk_texts:
        lines.append(f"[{fmt_time(chunk_start)}] {' '.join(chunk_texts)}")
    return "\n".join(lines)


# -------------------------------------------------------------------
# Gemini
# -------------------------------------------------------------------

def call_gemini(api_key: str, prompt: str) -> str:
    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Gemini error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


NUTELLA_PROMPT = """Você é um estrategista de conteúdo YouTube especializado em extrair clips virais de lives corporativas.

CANAL: Gestão de frotas e equipes externas (Brasil)
APRESENTADOR: Julio César — 22+ anos de experiência real em frotas, tom direto e educativo
PÚBLICO: Gestores de frota/equipes, 35-55 anos, cargo médio/alto, buscam soluções práticas

---

## FRAMEWORK DE CLIPS VIRAIS

### 1. Hook formula (primeiros 3 segundos)
- **Dor direta**: "Você sabia que [problema real que o gestor tem]?"
- **Contraste brutal**: "Antes: R$2.000 e 2 meses. Agora: grátis em minutos."
- **Desafio**: "Entreviste 10 motoristas agora. O resultado vai te surpreender."
- **Revelação**: "Para surpresa de zero pessoas, eles só assinam."

### 2. Tipos de clip (por objetivo)
- `autoridade` — Julio como referência máxima do nicho
- `viralização` — verdade incômoda que o gestor não fala mas todo mundo sabe
- `inscricao` — conteúdo que prova que o canal entrega mais do que qualquer consultor
- `educacional` — resolve UMA dúvida específica com clareza cirúrgica
- `wow_factor` — demo ao vivo de algo que parece impossível

### 3. SEO title (keyword-first, captura busca ativa)
- Keyword primária DEVE começar nos primeiros 40 chars
- Padrões comprovados no nicho:
  - "Política de Frota: Como [Resolver Problema Específico]"
  - "Gestão de Frotas: [Número] Erros Que Custam Caro"
  - "CUIDADO! [Problema] Pode Virar [Consequência]"
  - "[Tema] para Gestores: Guia Prático 2026"

### 4. CTR title (hook emocional, filtro de público)
- Hook na primeira palavra | ex: "Para Surpresa de Zero Pessoas, Eles Só Assinam"
- Gatilhos: GRÁTIS, SIMPLES, CUIDADO, Passo a Passo, Antes de Comprar

### 5. DURAÇÃO — REGRAS OBRIGATÓRIAS
- **Clip horizontal (16:9)**: PREFERÊNCIA >5 minutos. Mínimo absoluto: 3 minutos.
  - O clip deve agregar conhecimento REAL ao gestor sem precisar assistir a live toda
  - Se o conteúdo for consultivo/direto e ensinar rápido, clips de 3-5 min são aceitáveis
  - Clips de 5-10 minutos são o ideal: profundidade sem cansar
  - Vídeos publicados adicionam ~2min de intro+CTA ao clip
- **Shorts vertical (9:16)**: MÍNIMO 30 segundos, ideal 45-60 segundos
  - Shorts < 30s perdem potencial de retenção
  - Se não conseguir 30s de conteúdo bom, marque shorts_possivel: false

### 6. Horizontal vs Shorts
- **Clip horizontal**: 1:30–4 min | pode ter 30s de setup | thumbnail 16:9
- **Shorts vertical**: 30–60s | hook nos primeiros 3s | sem setup | corte mais tight

### 7. Thumbnail — composição SIMPLES obrigatória
- Máximo 2 elementos visuais (Julio + 1 objeto ou fundo)
- Composições complexas (split screen, múltiplos objetos) degradam qualidade da IA
- Preferir: Julio centralizado + fundo dramático + texto grande
- Texto: máx 4 palavras, alto contraste, legível em tamanho pequeno

### 8. Pairing título + thumbnail
- Modelo A: **título faz pergunta → thumbnail mostra a prova/reação**
- Modelo B: **thumbnail cria tensão visual → título explica o contexto**
- NUNCA título e thumbnail dizendo a mesma coisa — um completa o outro

---

## TRANSCRIÇÃO COM TIMESTAMPS:
{transcript}

---

## REGRAS DE CONTEÚDO
- Cada clip DEVE ser EDUCATIVO (agrega conhecimento ao gestor) ou PROMOCIONAL (Contele ou parceiro oficial indicado na live)
- O clip deve funcionar como conteúdo AUTÔNOMO: quem assiste entende o assunto sem precisar ver a live toda
- NUNCA cortar no meio de um assunto, raciocínio ou palavra. Início e fim devem ser naturais.
- Prefira trechos onde o Julio explica um conceito completo, conta um caso real, ou resolve uma dúvida com clareza

## TAREFA:
Identifique de 2 a 3 nutellas (MÁXIMO 3). Priorize qualidade e profundidade sobre quantidade. Para cada uma, retorne JSON com:

```json
[
  {{
    "rank": 1,
    "tipo": "viralização|autoridade|inscricao|educacional|wow_factor",
    "objetivo_primario": "O que esse clip faz pelo canal em 1 linha",

    "clip_entrada": "MM:SS",
    "clip_saida": "MM:SS",
    "hook_second": "MM:SS",

    "shorts_entrada": "MM:SS",
    "shorts_saida": "MM:SS",
    "shorts_possivel": true,

    "titulo_seo": "Keyword primária nos primeiros 40 chars + completar até 70 chars",
    "titulo_ctr": "Hook emocional na primeira palavra (máx 60 chars)",
    "titulo_shorts": "Título curto para Shorts (máx 50 chars)",

    "tags_especificas": ["tag1 do tema", "tag2 do tema", "tag3", "tag4", "tag5"],
    "descricao_curta": "2-3 frases que resumem o valor deste clip para a descrição do YouTube",

    "thumbnail_texto": "FRASE CURTA (máx 4 palavras, alto contraste)",
    "thumbnail_composicao": "Composição SIMPLES: Julio + máx 1 elemento. Ex: Julio surpreso, fundo escuro com cifra desfocada",
    "expressao_julio": "sorrindo|serio|preocupado|surpreso|ironico|assertivo",
    "thumbnail_pairing": "A|B",

    "por_que_viraliza": "1 linha: mecanismo psicológico + comportamento esperado do espectador",
    "hook_transcricao": "Copie as primeiras 1-2 frases exatas do clip que funcionam como hook"
  }}
]
```

REGRAS FINAIS:
- MÁXIMO 3 nutellas. Prefira 2 excelentes a 3 medianas.
- Cada clip DEVE ter PREFERENCIALMENTE >5 minutos (clip_saida - clip_entrada >= 5:00). Mínimo absoluto: 3 minutos.
- Se um trecho bom é curto, EXPANDA incluindo contexto antes/depois para atingir 5 minutos
- NUNCA cortar no meio de frase, palavra ou raciocínio. O início deve ser um começo natural e o fim uma conclusão natural.
- Shorts DEVEM ter MÍNIMO 30 segundos
- tags_especificas: 5-8 tags específicas do TEMA deste clip (não genéricas)
- thumbnail_composicao: MÁXIMO 2 elementos visuais (Julio + 1 coisa)
- Responda APENAS o JSON, sem texto antes ou depois.
"""


# -------------------------------------------------------------------
# Pipeline
# -------------------------------------------------------------------

def suggest_nutellas(video_id: str) -> dict:
    print(f"\nBuscando transcrição de {video_id}...")
    segments = get_transcript_with_timestamps(video_id)

    transcript_text = build_transcript_text(segments, chunk_size=90)
    if len(transcript_text) > 22000:
        transcript_text = transcript_text[:22000] + "\n[...transcrição truncada...]"

    print(f"Transcrição: {len(segments)} segmentos | {len(transcript_text)} chars")
    print("Analisando com Gemini (framework viral)...")

    api_key = load_api_key()
    prompt = NUTELLA_PROMPT.format(transcript=transcript_text)
    raw = call_gemini(api_key, prompt)

    json_match = re.search(r"\[[\s\S]*\]", raw)
    if not json_match:
        raise ValueError(f"Gemini não retornou JSON válido:\n{raw[:500]}")

    nutellas = json.loads(json_match.group())

    return {
        "video_id": video_id,
        "youtube_url": f"https://youtube.com/watch?v={video_id}",
        "generated_at": datetime.now().isoformat(),
        "segments_total": len(segments),
        "nutellas": nutellas,
    }


def save_output(result: dict) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    video_id = result["video_id"]
    out_path = OUTPUT_DIR / f"{video_id}_nutellas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return out_path


# -------------------------------------------------------------------
# Output formatado
# -------------------------------------------------------------------

TIPO_ICON = {
    "viralização": "🔥",
    "autoridade": "👑",
    "inscricao": "📈",
    "educacional": "📚",
    "wow_factor": "🤯",
}


def print_results(result: dict):
    video_id = result["video_id"]
    nutellas = result["nutellas"]

    print(f"\n{'='*65}")
    print(f"NUTELLAS — {video_id}")
    print(f"{'='*65}")

    for n in nutellas:
        icon = TIPO_ICON.get(n.get("tipo", ""), "•")
        dur_clip = time_to_seconds(n["clip_saida"]) - time_to_seconds(n["clip_entrada"])
        dur_label = f"{dur_clip//60}:{dur_clip%60:02d}"

        print(f"\n{'─'*65}")
        print(f"#{n['rank']} {icon} {n['tipo'].upper()}  [{n['clip_entrada']} → {n['clip_saida']}] (~{dur_label})")
        print(f"OBJETIVO:  {n['objetivo_primario']}")
        print(f"HOOK em:   {n['hook_second']}")
        print(f"")
        print(f"SEO:       {n['titulo_seo']}")
        print(f"CTR:       {n['titulo_ctr']}")
        if n.get("shorts_possivel"):
            print(f"SHORTS:    {n['titulo_shorts']}  [{n['shorts_entrada']} → {n['shorts_saida']}]")
        print(f"")
        print(f"THUMB:     \"{n['thumbnail_texto']}\"")
        print(f"COMPOSI:   {n['thumbnail_composicao']}")
        print(f"EXPRESSÃO: {n['expressao_julio']}  |  PAIRING: {n['thumbnail_pairing']}")
        print(f"")
        print(f"HOOK:      \"{n['hook_transcricao']}\"")
        print(f"VIRAL:     {n['por_que_viraliza']}")

    print(f"\n{'='*65}")
    print(f"Salvo em: output/{video_id}_nutellas.json")
    print(f"Review:   python3 preview.py output/{video_id}_nutellas.json")
    print(f"{'='*65}\n")


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sugere nutellas com brief completo de produção")
    parser.add_argument("url", help="URL ou ID do vídeo YouTube")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Saída em JSON puro")
    args = parser.parse_args()

    try:
        video_id = extract_video_id(args.url)
        result = suggest_nutellas(video_id)
        save_output(result)

        if args.json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_results(result)

    except KeyboardInterrupt:
        print("\nInterrompido.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
