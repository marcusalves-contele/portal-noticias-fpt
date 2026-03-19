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
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


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


def _get_transcript_ytdlp(video_id: str) -> list[dict]:
    """Fallback: extrai legendas via yt-dlp (funciona em IPs de cloud)."""
    import subprocess, tempfile, re as _re
    cookies_file = Path(__file__).parent / "cookies.txt"
    cookies_arg = ["--cookies", str(cookies_file)] if cookies_file.exists() else []

    with tempfile.TemporaryDirectory(prefix="transcript_") as tmp:
        tmp_path = Path(tmp)
        cmd = [
            "yt-dlp",
            "--write-auto-sub", "--sub-lang", "pt,pt-BR,en",
            "--sub-format", "json3",
            "--skip-download",
            *cookies_arg,
            "-o", str(tmp_path / "sub"),
            f"https://youtube.com/watch?v={video_id}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Find the downloaded subtitle file
        sub_files = list(tmp_path.glob("*.json3"))
        if not sub_files:
            raise RuntimeError(
                f"yt-dlp nao conseguiu extrair legendas para {video_id}. "
                f"Verifique se o video tem legendas disponiveis."
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


def get_transcript_with_timestamps(video_id: str) -> list[dict]:
    # Tenta youtube-transcript-api primeiro (mais rapido)
    try:
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id, languages=["pt", "pt-BR", "en"])
        return [{"start": s.start, "duration": s.duration, "text": s.text} for s in result]
    except Exception as e:
        print(f"  youtube-transcript-api falhou ({e}), tentando yt-dlp...")
        return _get_transcript_ytdlp(video_id)


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
- **Clip horizontal (16:9)**: MÍNIMO 90 segundos (1:30), ideal 2-4 minutos
  - Vídeos publicados adicionam ~2min de intro+CTA ao clip
  - Clip < 90s ficaria com mais wrapper que conteúdo → PROIBIDO
  - Se o trecho bom tem < 90s, EXPANDA incluindo contexto antes e depois
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

## TAREFA:
Identifique de 4 a 6 nutellas. Para cada uma, retorne JSON com:

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
- Cada clip DEVE ter MÍNIMO 90 segundos (clip_saida - clip_entrada >= 1:30)
- Se um trecho bom é curto demais, INCLUA contexto antes/depois para atingir 90s
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
