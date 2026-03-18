#!/usr/bin/env python3
"""
edit_thumb_cameras.py — Edição incremental de thumbnail com Nano Banana 2.

Adiciona câmeras reais (referências) a uma thumb existente usando
gemini-3.1-flash-image-preview (melhor pra edição de imagem).

Uso:
  python3 edit_thumb_cameras.py \
    --base output/live323_v2_etapa1_v1.png \
    --cameras output/refs/jimi_jc182.jpg output/refs/jimi_jc400.jpg ... \
    --prompt "Add these vehicular cameras floating around the person..." \
    --variations 3 --prefix live323_final
"""

import argparse
import base64
import json
import os
import requests
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "output"

MODEL = "gemini-3.1-flash-image-preview"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
URL = f"{API_BASE}/{MODEL}:generateContent"


def load_api_key() -> str:
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env not found at {env_path}")
    with open(env_path) as f:
        for line in f:
            if line.startswith("GEMINI_NANO_BANANA_KEY"):
                return line.split("=", 1)[1].strip().strip('"')
    raise ValueError("GEMINI_NANO_BANANA_KEY not found in .env")


def img_to_b64(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    ext = path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp"}.get(ext.lstrip("."), "image/jpeg")
    return base64.b64encode(data).decode(), mime


def generate(api_key: str, base_img: Path, camera_imgs: list[Path],
             prompt: str, variations: int = 3, prefix: str = "edited") -> list[Path]:
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    # Build parts: prompt text + base image + camera reference images
    parts = [{"text": prompt}]

    # Base thumbnail
    b64, mime = img_to_b64(base_img)
    parts.append({
        "inline_data": {"mime_type": mime, "data": b64}
    })

    # Camera references
    for cam_path in camera_imgs:
        b64, mime = img_to_b64(cam_path)
        parts.append({
            "inline_data": {"mime_type": mime, "data": b64}
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 0.8,
        }
    }

    results = []
    for i in range(1, variations + 1):
        print(f"  Variação {i}...", end=" ", flush=True)
        try:
            resp = requests.post(URL, headers=headers, params=params,
                                 json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()

            # Extract image from response
            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        img_data = base64.b64decode(part["inlineData"]["data"])
                        out_path = OUTPUT_DIR / f"{prefix}_v{i}.png"
                        out_path.write_bytes(img_data)
                        results.append(out_path)
                        print(f"OK → {out_path.name}")
                        break
                else:
                    print("NO IMAGE in response")
        except Exception as e:
            print(f"ERRO: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Edit thumb: add real cameras")
    parser.add_argument("--base", required=True, help="Base thumbnail to edit")
    parser.add_argument("--cameras", nargs="+", required=True, help="Camera reference images")
    parser.add_argument("--prompt", required=True, help="Edit prompt")
    parser.add_argument("--variations", type=int, default=3)
    parser.add_argument("--prefix", default="edited")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    api_key = load_api_key()
    base = Path(args.base)
    cameras = [Path(c) for c in args.cameras]

    print(f"Base: {base.name}")
    for c in cameras:
        print(f"  Camera ref: {c.name}")
    print(f"Gerando {args.variations} variações com {MODEL}...")

    results = generate(api_key, base, cameras, args.prompt, args.variations, args.prefix)

    print(f"\n{len(results)} imagens geradas")
    for r in results:
        print(f"  {r}")

    if args.open and results:
        import subprocess
        subprocess.run(["open"] + [str(r) for r in results])


if __name__ == "__main__":
    main()
