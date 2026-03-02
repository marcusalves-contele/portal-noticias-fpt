#!/usr/bin/env python3
"""
Render Brief Cards — Gera PNG de cada nutella via Remotion.

Lê o JSON do suggest.py e renderiza um card 1920x1080 por nutella.
Os cards podem ser enviados no grupo como preview visual do brief.

Uso:
  python3 render_cards.py output/ra-GUivQnso_nutellas.json
  python3 render_cards.py output/ra-GUivQnso_nutellas.json --send-group
"""

import sys
import json
import argparse
import subprocess
import tempfile
import os
import requests
from pathlib import Path

REMOTION_DIR = Path(__file__).parent.parent.parent / "assistant-sexta-feira" / "remotion-video"
OUTPUT_DIR = Path(__file__).parent / "output"

# WhatsApp pessoal
WA_API = "http://localhost:3847"
WA_KEY = "sexta-feira-2026"
GROWTH_GROUP_JID = "120363424539843742@g.us"


def time_to_seconds(t: str) -> int:
    parts = t.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(parts[0]) * 60 + int(parts[1])


def render_card(nutella: dict, video_id: str) -> Path | None:
    """Renderiza um brief card PNG via Remotion still."""
    rank = nutella["rank"]
    out_path = OUTPUT_DIR / f"{video_id}_brief_{rank}.png"

    # Monta props JSON para passar ao Remotion
    props = {
        "rank": nutella["rank"],
        "tipo": nutella.get("tipo", "educacional"),
        "clip_entrada": nutella["clip_entrada"],
        "clip_saida": nutella["clip_saida"],
        "hook_second": nutella.get("hook_second", nutella["clip_entrada"]),
        "titulo_seo": nutella["titulo_seo"],
        "titulo_ctr": nutella["titulo_ctr"],
        "titulo_shorts": nutella.get("titulo_shorts", ""),
        "shorts_possivel": nutella.get("shorts_possivel", False),
        "shorts_entrada": nutella.get("shorts_entrada", ""),
        "shorts_saida": nutella.get("shorts_saida", ""),
        "thumbnail_texto": nutella["thumbnail_texto"],
        "expressao_julio": nutella.get("expressao_julio", ""),
        "objetivo_primario": nutella.get("objetivo_primario", ""),
        "por_que_viraliza": nutella.get("por_que_viraliza", ""),
        "video_id": video_id,
    }

    # Salva props temporário
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(props, f, ensure_ascii=False)
        props_file = f.name

    try:
        cmd = [
            "npx", "remotion", "still",
            "src/index.ts",
            "NutellaBriefCard",
            str(out_path),
            "--props", props_file,
        ]
        print(f"  Renderizando #{rank}...")
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"  #{rank} OK → {out_path.name}")
            return out_path
        else:
            print(f"  #{rank} ERRO: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  #{rank} timeout")
        return None
    finally:
        os.unlink(props_file)


def send_image_to_group(image_path: Path, caption: str) -> bool:
    """Envia imagem para o grupo via daemon pessoal."""
    try:
        with open(image_path, "rb") as f:
            files = {"image": (image_path.name, f, "image/png")}
            data = {"recipient": GROWTH_GROUP_JID, "caption": caption}
            resp = requests.post(
                f"{WA_API}/send-image",
                headers={"x-api-key": WA_KEY},
                files=files,
                data=data,
                timeout=30,
            )
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"  Erro ao enviar: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Renderiza brief cards PNG via Remotion")
    parser.add_argument("input", help="JSON gerado pelo suggest.py")
    parser.add_argument("--send-group", action="store_true", help="Envia cards no grupo IA - Growth Contele")
    parser.add_argument("--rank", type=int, help="Renderizar apenas nutella específica (por rank)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    video_id = data["video_id"]
    nutellas = data["nutellas"]

    if args.rank:
        nutellas = [n for n in nutellas if n["rank"] == args.rank]
        if not nutellas:
            print(f"Nutella #{args.rank} não encontrada.")
            sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"\nRenderizando {len(nutellas)} brief cards — {video_id}\n")

    rendered = []
    for n in nutellas:
        path = render_card(n, video_id)
        if path:
            rendered.append((n, path))

    print(f"\n{len(rendered)}/{len(nutellas)} cards renderizados.")

    if args.send_group and rendered:
        print("\nEnviando para o grupo IA - Growth Contele...")
        for n, path in rendered:
            caption = f"Live {video_id} — Nutella #{n['rank']}\n{n['titulo_ctr']}"
            ok = send_image_to_group(path, caption)
            print(f"  #{n['rank']} {'✓' if ok else '✗'}")

    if rendered:
        print("\nPara abrir os cards:")
        for _, path in rendered:
            print(f"  open {path}")


if __name__ == "__main__":
    main()
