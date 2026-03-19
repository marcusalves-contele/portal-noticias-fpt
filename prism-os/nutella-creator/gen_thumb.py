#!/usr/bin/env python3
"""
gen_thumb.py — Gera thumbnails para nutellas via Gemini.

Lê o meta JSON, monta prompt com campos de thumbnail,
chama Gemini (gemini-3.1-flash-image-preview / Nano Banana 2), salva PNGs.

Uso:
  python3 gen_thumb.py output/ra-GUivQnso_cuts/live319_01_meta.json
  python3 gen_thumb.py output/ra-GUivQnso_cuts/ --rank 1
  python3 gen_thumb.py output/ra-GUivQnso_cuts/ --rank 1,2,3
  python3 gen_thumb.py output/ra-GUivQnso_cuts/ --all
"""

import sys
import json
import base64
import argparse
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_DIR   = Path(__file__).parent
THUMB_PROJECT = PROJECT_DIR.parent / "thumbnail-ai-creator"
REFS_DIR      = THUMB_PROJECT / "referencias" / "julio"
GUESTS_DIR    = THUMB_PROJECT / "referencias" / "convidados"
_LOCAL_ENV    = PROJECT_DIR / ".env"
_THUMB_ENV    = THUMB_PROJECT / ".env"
ENV_PATH      = _LOCAL_ENV if _LOCAL_ENV.exists() else _THUMB_ENV

# Mapeamento expressão → keywords no nome do arquivo
# select_refs() varre a pasta dinamicamente — sem hardcode
EXPRESSION_MAP = {
    "serio":      ["frontal-neutro"],
    "neutro":     ["frontal-neutro"],
    "firme":      ["frontal-neutro", "bracos-cruzados"],
    "surpreso":   ["surpreso"],
    "chocado":    ["surpreso"],
    "pensativo":  ["pensativo"],
    "reflexivo":  ["pensativo"],
    "assertivo":  ["dedo-para-cima"],
    "apontando":  ["dedo-para-cima"],
    "autoridade": ["bracos-cruzados", "frontal-neutro"],
    "ironico":      ["perfil-3-4", "pensativo"],
    "critico":      ["bracos-cruzados"],
    "preocupado":   ["pensativo", "frontal-neutro"],
    "serio":        ["frontal-neutro"],
    "desafiador":   ["bracos-cruzados", "dedo-para-cima"],
    "confiante":    ["bracos-cruzados"],
    "sorrindo":   ["sorrindo"],
    "animado":    ["sorrindo"],
    "empolgado":  ["sorrindo", "dedo-para-cima"],
    "explicando": ["gesto-explicando"],
    "ensinando":  ["gesto-explicando"],
    "atencao":    ["mao-aberta"],
}

# -------------------------------------------------------------------
# API
# -------------------------------------------------------------------

MODEL   = "gemini-3.1-flash-image-preview"  # Nano Banana 2
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
TIMEOUT = 180


def load_api_key() -> str:
    import os
    # Prefer env var (Railway)
    key = os.environ.get("GEMINI_NANO_BANANA_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("GEMINI_NANO_BANANA_KEY"):
                    return line.split("=", 1)[1].strip().strip('"')
    print("ERRO: GEMINI_NANO_BANANA_KEY não encontrada")
    sys.exit(1)


def image_to_part(path: Path) -> dict:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    return {"inlineData": {"mimeType": mime, "data": data}}


# -------------------------------------------------------------------
# Prompt builder
# -------------------------------------------------------------------

PROMPT_TEMPLATE = """Create a YouTube thumbnail in 16:9 aspect ratio.

CRITICAL - FACE REFERENCE IMAGES:
- Images 1-3 are JULIO's actual face photos - YOU MUST COPY THIS EXACT FACE
- Do NOT create a different person - use the reference photos as the PRIMARY SOURCE
- The man in the thumbnail MUST look like the man in reference images 1-3

JULIO - COPY THE FACE FROM REFERENCE PHOTOS EXACTLY:
- WIDER face shape, slightly square jaw - MATCH THE REFERENCE
- DENSE gray/white stubble beard covering jaw and chin (salt and pepper, NOT sparse)
- Receding hairline with short brown/gray hair - MATCH THE REFERENCE
- Deep-set brown/hazel eyes, NO glasses
- Age: 45+, mature appearance
- Black polo shirt (plain, no logos) — match the reference photos exactly
- The face MUST be recognizable as the same person from the reference photos

SKIN TEXTURE - CRITICAL:
- Keep skin SMOOTH like a fit 45 year old
- Do NOT add excessive wrinkles or age marks
- Forehead SMOOTH, cheeks FIRM

THUMBNAIL COMPOSITION:
{composicao}

JULIO'S EXPRESSION: {expressao}

TEXT ON THUMBNAIL (bold, large, high contrast, readable):
"{texto}"

PAIRING STRATEGY: {pairing_desc}

STYLE:
- Professional YouTube thumbnail quality (1280x720 feel)
- High contrast, vibrant colors, purple/magenta cinematic lighting
- Dark/dramatic background preferred
- Text must be LARGE and READABLE even at small sizes
- No watermarks, no borders
- Fleet management / B2B professional context

IMPORTANT:
- No text overlays besides the specified text
- Julio's face must match the reference images EXACTLY
- Expression must be clearly {expressao}
"""

PAIRING_A_DESC = "Title asks a question, thumbnail shows the PROOF/ANSWER visually"
PAIRING_B_DESC = "Thumbnail creates TENSION/CURIOSITY, title explains the context"


def build_prompt(meta: dict) -> str:
    pairing = meta.get("thumbnail_pairing", "B")
    pairing_desc = PAIRING_A_DESC if pairing == "A" else PAIRING_B_DESC

    return PROMPT_TEMPLATE.format(
        composicao=meta.get("thumbnail_composicao", "Julio centered, dramatic lighting"),
        expressao=meta.get("expressao_julio", "serio"),
        texto=meta.get("thumbnail_texto", ""),
        pairing_desc=pairing_desc,
    )


def select_refs(meta: dict) -> list[Path]:
    """
    Varre REFS_DIR dinamicamente e seleciona até 3 referências do Julio:
    1. Sempre inclui frontal-neutro como âncora facial principal
    2. Adiciona a foto de expressão que melhor corresponde ao meta
    3. Completa com 1 foto de fallback para variedade facial
    Exclui arquivos _studio_v1 (gerados por IA, degradam fidelidade).
    """
    expressao = (meta.get("expressao_julio") or "serio").lower()

    # Scan dinâmico: jpg/png reais, excluindo AI-generated e duplicatas
    available = {
        f.stem.lower(): f
        for f in REFS_DIR.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
        and "studio_v1" not in f.name
        and "ref-primary" not in f.name
    }

    refs = []

    # 1. Âncora facial: frontal-neutro é a melhor ref de face lock
    primary = next((v for k, v in available.items() if "frontal-neutro" in k), None)
    if primary:
        refs.append(primary)

    # 2. Foto de expressão correspondente
    for kw in EXPRESSION_MAP.get(expressao, []):
        match = next((v for k, v in available.items() if kw in k and v not in refs), None)
        if match:
            refs.append(match)
            break

    # 3. Fallback: completa até 3 refs com outras poses para variedade
    FALLBACK_ORDER = ["bracos-cruzados", "dedo-para-cima", "gesto-explicando",
                      "sorrindo", "surpreso", "pensativo", "mao-aberta"]
    for kw in FALLBACK_ORDER:
        if len(refs) >= 3:
            break
        match = next((v for k, v in available.items() if kw in k and v not in refs), None)
        if match:
            refs.append(match)

    print(f"    Refs: {[r.name for r in refs]}")
    return refs


# -------------------------------------------------------------------
# Generation
# -------------------------------------------------------------------

def generate_one(api_key: str, prompt: str, refs: list[Path],
                 output_path: Path, variation: int) -> Path | None:
    """Gera uma variação de thumbnail."""
    parts = [image_to_part(r) for r in refs]
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
            "temperature": 0,  # máxima consistência facial
        },
    }
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
        result = resp.json()

        if "candidates" not in result:
            err = result.get("error", {}).get("message", str(result)[:200])
            print(f"    v{variation} ERRO: {err}")
            return None

        for part in result["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                with open(output_path, "wb") as f:
                    f.write(img_data)
                size_kb = len(img_data) // 1024
                print(f"    v{variation} OK → {output_path.name} ({size_kb}KB)")
                return output_path

        print(f"    v{variation} ERRO: sem imagem na resposta")
        return None

    except requests.Timeout:
        print(f"    v{variation} TIMEOUT ({TIMEOUT}s)")
        return None
    except Exception as e:
        print(f"    v{variation} ERRO: {e}")
        return None


def generate_thumb(meta: dict, cuts_dir: Path, api_key: str,
                   num_variations: int = 2) -> list[Path]:
    """Gera thumbnails para uma nutella."""
    rank = meta["rank"]
    prefix = f"live{cuts_dir.name.split('_')[0].replace('live','')}" if "live" in cuts_dir.name else "thumb"

    # Detecta live number do nome do diretório ou dos arquivos
    clip_name = meta["clip"]["arquivo"]
    # live319_01_xxx.mp4 → 319
    parts = clip_name.split("_")
    if parts:
        live_num = parts[0].replace("live", "")
    else:
        live_num = "0"

    prompt = build_prompt(meta)
    refs = select_refs(meta)

    if not refs:
        print(f"  ERRO: nenhuma referência encontrada em {REFS_DIR}")
        return []

    print(f"\n  Thumbnail #{rank}: \"{meta.get('thumbnail_texto', '')}\"")
    print(f"    Expressão: {meta.get('expressao_julio', '-')}")
    print(f"    Refs: {len(refs)} imagens")
    print(f"    Gerando {num_variations} variações...")

    results = []
    with ThreadPoolExecutor(max_workers=min(num_variations, 3)) as pool:
        futures = {}
        for v in range(1, num_variations + 1):
            out_path = cuts_dir / f"live{live_num}_{rank:02d}_thumb_v{v}.png"
            if out_path.exists():
                print(f"    v{v} já existe, pulando")
                results.append(out_path)
                continue
            fut = pool.submit(generate_one, api_key, prompt, refs, out_path, v)
            futures[fut] = v

        for fut in as_completed(futures):
            path = fut.result()
            if path:
                results.append(path)

    return sorted(results)


# -------------------------------------------------------------------
# Feedback-based regeneration (Gemini Flash)
# -------------------------------------------------------------------

FLASH_MODEL = "gemini-3-flash-preview"
FLASH_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{FLASH_MODEL}:generateContent"


def adjust_prompt_with_feedback(original_prompt: str, feedback: str, api_key: str) -> str:
    """Usa Gemini Flash para ajustar o prompt baseado no feedback do usuário."""
    system_prompt = (
        "You are a prompt engineer for AI-generated YouTube thumbnails. "
        "Given an original image generation prompt and user feedback about the result, "
        "output an ADJUSTED prompt that incorporates the feedback. "
        "Rules: keep same structure/style, only modify what feedback addresses, "
        "output ONLY the adjusted prompt in English, no explanations."
    )
    user_msg = f"ORIGINAL PROMPT:\n{original_prompt}\n\nUSER FEEDBACK:\n{feedback}\n\nAdjusted prompt:"

    payload = {
        "contents": [{"parts": [{"text": user_msg}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2000},
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(FLASH_URL, headers=headers, json=payload, timeout=30)
        result = resp.json()
        if "candidates" in result:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  Feedback adjustment error: {e}")

    return original_prompt + f"\n\nADDITIONAL INSTRUCTIONS: {feedback}"


def generate_single(meta: dict, cuts_dir: Path, api_key: str,
                    feedback: str = None) -> Path | None:
    """Gera 1 thumbnail. Se feedback, ajusta o prompt com IA primeiro."""
    rank = meta["rank"]
    clip_name = meta["clip"]["arquivo"]
    parts_name = clip_name.split("_")
    live_num = parts_name[0].replace("live", "") if parts_name else "0"

    prompt = build_prompt(meta)
    if feedback:
        print(f"  Ajustando prompt com feedback...")
        prompt = adjust_prompt_with_feedback(prompt, feedback, api_key)
        print(f"  Prompt ajustado OK")

    refs = select_refs(meta)
    if not refs:
        print(f"  ERRO: sem referências em {REFS_DIR}")
        return None

    out_path = cuts_dir / f"live{live_num}_{rank:02d}_thumb.png"
    print(f"  Gerando thumbnail #{rank}...")
    return generate_one(api_key, prompt, refs, out_path, variation=1)


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gera thumbnails para nutellas")
    parser.add_argument("input", help="Meta JSON ou diretório de cuts")
    parser.add_argument("--rank", help="Rank(s) específicos, ex: 1 ou 1,2,3")
    parser.add_argument("--all", action="store_true", help="Gera para todas as nutellas")
    parser.add_argument("--variations", type=int, default=2, help="Variações por nutella")
    args = parser.parse_args()

    input_path = Path(args.input)
    api_key = load_api_key()

    # Modo 1: meta JSON direto
    if input_path.is_file() and input_path.suffix == ".json":
        with open(input_path, encoding="utf-8") as f:
            meta = json.load(f)
        cuts_dir = input_path.parent
        results = generate_thumb(meta, cuts_dir, api_key, args.variations)
        print(f"\n  {len(results)} thumbnails geradas")
        return

    # Modo 2: diretório de cuts
    if input_path.is_dir():
        cuts_dir = input_path
    else:
        print(f"Entrada inválida: {args.input}")
        sys.exit(1)

    # Carrega todos os metas
    metas = []
    for f in sorted(cuts_dir.glob("*_meta.json")):
        with open(f, encoding="utf-8") as fh:
            metas.append(json.load(fh))

    if not metas:
        print(f"Nenhum *_meta.json em {cuts_dir}")
        sys.exit(1)

    # Filtra por rank
    if args.rank:
        wanted = {int(r) for r in args.rank.split(",")}
        metas = [m for m in metas if m["rank"] in wanted]
    elif not args.all:
        print(f"Especifique --rank ou --all. Metas disponíveis:")
        for m in metas:
            print(f"  #{m['rank']} — {m['titulo_ctr']}")
        sys.exit(0)

    print(f"Gerando thumbnails: {len(metas)} nutellas, {args.variations} variações cada")

    all_results = []
    for meta in metas:
        results = generate_thumb(meta, cuts_dir, api_key, args.variations)
        all_results.extend(results)

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_results)} thumbnails geradas")
    for r in all_results:
        print(f"  {r.name}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
