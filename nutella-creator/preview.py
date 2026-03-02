#!/usr/bin/env python3
"""
Nutella Preview — Gera página HTML de review com clips no timestamp certo.

Abre no browser. Cada nutella tem:
  - YouTube embed no timestamp exato (clica e já começa no corte)
  - Shorts embed (corte mais apertado)
  - SEO title + CTR title + Shorts title
  - Thumbnail brief + composição
  - Badges de tipo, duração, objetivo

Uso:
  python3 preview.py output/ra-GUivQnso_nutellas.json
  python3 preview.py output/ra-GUivQnso_nutellas.json --open
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "output"

TIPO_COLOR = {
    "viralização": "#ef4444",
    "autoridade": "#8b5cf6",
    "inscricao": "#10b981",
    "educacional": "#3b82f6",
    "wow_factor": "#f59e0b",
}

TIPO_ICON = {
    "viralização": "🔥",
    "autoridade": "👑",
    "inscricao": "📈",
    "educacional": "📚",
    "wow_factor": "🤯",
}


def time_to_seconds(t: str) -> int:
    parts = t.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(parts[0]) * 60 + int(parts[1])


def duration_label(start: str, end: str) -> str:
    secs = time_to_seconds(end) - time_to_seconds(start)
    return f"{secs//60}:{secs%60:02d}"


def yt_link(video_id: str, start: str) -> str:
    s = time_to_seconds(start)
    return f"https://www.youtube.com/watch?v={video_id}&t={s}s"

def yt_thumb(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


def generate_html(data: dict) -> str:
    video_id = data["video_id"]
    nutellas = data["nutellas"]

    cards = []
    for n in nutellas:
        tipo = n.get("tipo", "")
        color = TIPO_COLOR.get(tipo, "#6b7280")
        icon = TIPO_ICON.get(tipo, "•")
        dur = duration_label(n["clip_entrada"], n["clip_saida"])

        thumb_url = yt_thumb(video_id)
        clip_url = yt_link(video_id, n["clip_entrada"])
        shorts_block = ""
        if n.get("shorts_possivel"):
            s_url = yt_link(video_id, n["shorts_entrada"])
            s_dur = duration_label(n["shorts_entrada"], n["shorts_saida"])
            shorts_block = f"""
            <div class="shorts-col">
              <div class="embed-label">📱 Shorts [{n['shorts_entrada']} → {n['shorts_saida']}] (~{s_dur})</div>
              <a href="{s_url}" target="_blank" class="thumb-link shorts-thumb-link">
                <img src="{thumb_url}" class="thumb-img" alt="Shorts thumbnail">
                <div class="play-btn">▶</div>
                <div class="ts-badge">{n['shorts_entrada']}</div>
              </a>
              <div class="title-row" style="margin-top:8px">
                <span class="label" style="background:#052e16;color:#34d399">SHORTS</span>
                <span class="value shorts-title">{n['titulo_shorts']}</span>
              </div>
            </div>
"""

        cards.append(f"""
    <section class="nutella-card" id="nutella-{n['rank']}">
      <div class="card-header" style="border-left: 4px solid {color}">
        <div class="card-header-left">
          <span class="rank">#{n['rank']}</span>
          <span class="tipo-badge" style="background:{color}">{icon} {tipo.upper()}</span>
          <span class="duration">🕒 {n['clip_entrada']} → {n['clip_saida']} (~{dur})</span>
          <span class="hook-badge">⚡ Hook: {n['hook_second']}</span>
        </div>
        <div class="objetivo">{n['objetivo_primario']}</div>
      </div>

      <div class="embeds-row">
        <div class="main-col">
          <div class="embed-label">🎬 Clip [{n['clip_entrada']} → {n['clip_saida']}] — clique para abrir no YouTube</div>
          <a href="{clip_url}" target="_blank" class="thumb-link">
            <img src="{thumb_url}" class="thumb-img" alt="Thumbnail">
            <div class="play-btn">▶</div>
            <div class="ts-badge">{n['clip_entrada']}</div>
          </a>
        </div>
        {shorts_block}
      </div>

      <div class="brief-grid">
        <div class="brief-col titles-col">
          <div class="section-label">TÍTULOS</div>

          <div class="title-row">
            <span class="label seo-label">SEO</span>
            <span class="value">{n['titulo_seo']}</span>
          </div>
          <div class="title-row">
            <span class="label ctr-label">CTR</span>
            <span class="value ctr-value">{n['titulo_ctr']}</span>
          </div>

          <div class="section-label mt">HOOK (primeiras frases do clip)</div>
          <div class="hook-quote">"{n['hook_transcricao']}"</div>

          <div class="section-label mt">POR QUE VIRALIZA</div>
          <div class="viral-reason">{n['por_que_viraliza']}</div>
        </div>

        <div class="brief-col thumb-col">
          <div class="section-label">THUMBNAIL</div>

          <div class="thumb-text-preview" style="border-color:{color}">
            {n['thumbnail_texto']}
          </div>

          <div class="thumb-row">
            <span class="label">EXPRESSÃO</span>
            <span class="value">{n['expressao_julio']}</span>
          </div>
          <div class="thumb-row">
            <span class="label">PAIRING</span>
            <span class="value">{n['thumbnail_pairing']}</span>
          </div>
          <div class="section-label mt">COMPOSIÇÃO</div>
          <div class="composicao">{n['thumbnail_composicao']}</div>
        </div>
      </div>

      <div class="card-footer">
        <a href="https://youtube.com/watch?v={video_id}&t={time_to_seconds(n['clip_entrada'])}s"
           target="_blank" class="yt-link">▶ Abrir no YouTube</a>
      </div>
    </section>
""")

    nav_items = "".join(
        f'<a href="#nutella-{n["rank"]}" class="nav-item" style="border-color:{TIPO_COLOR.get(n.get("tipo",""), "#6b7280")}">'
        f'{TIPO_ICON.get(n.get("tipo",""), "•")} #{n["rank"]} {n["titulo_ctr"][:40]}...</a>'
        for n in nutellas
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nutella Review — {video_id}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f0f0f; color: #e5e5e5; min-height: 100vh;
    }}

    /* NAV */
    .nav {{
      position: sticky; top: 0; z-index: 100;
      background: #1a1a1a; border-bottom: 1px solid #333;
      padding: 12px 24px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
    }}
    .nav-title {{ color: #fff; font-weight: 700; font-size: 14px; margin-right: 8px; white-space: nowrap; }}
    .nav-item {{
      font-size: 12px; padding: 4px 10px; border-radius: 20px;
      border: 1px solid; color: #ccc; text-decoration: none;
      white-space: nowrap; transition: background 0.2s;
    }}
    .nav-item:hover {{ background: #333; color: #fff; }}

    /* MAIN */
    .container {{ max-width: 1400px; margin: 0 auto; padding: 32px 24px; display: flex; flex-direction: column; gap: 40px; }}

    /* CARD */
    .nutella-card {{
      background: #1a1a1a; border-radius: 12px; overflow: hidden;
      border: 1px solid #2a2a2a;
    }}
    .card-header {{
      padding: 16px 20px; background: #222;
      display: flex; flex-direction: column; gap: 8px;
    }}
    .card-header-left {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
    .rank {{ font-size: 22px; font-weight: 800; color: #fff; }}
    .tipo-badge {{
      font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
      color: #fff; letter-spacing: 0.5px;
    }}
    .duration {{ font-size: 13px; color: #aaa; background: #333; padding: 3px 8px; border-radius: 6px; }}
    .hook-badge {{ font-size: 12px; color: #fbbf24; background: #292524; padding: 3px 8px; border-radius: 6px; }}
    .objetivo {{ font-size: 14px; color: #d1d5db; font-style: italic; }}

    /* EMBEDS */
    .embeds-row {{ display: flex; gap: 16px; padding: 20px; align-items: flex-start; }}
    .main-col {{ flex: 1.6; display: flex; flex-direction: column; gap: 8px; }}
    .shorts-col {{ flex: 1; display: flex; flex-direction: column; gap: 8px; max-width: 320px; }}
    .embed-label {{ font-size: 12px; color: #9ca3af; margin-bottom: 4px; }}

    .thumb-link {{
      display: block; position: relative; border-radius: 10px; overflow: hidden;
      text-decoration: none; background: #000;
    }}
    .thumb-link:hover .play-btn {{ transform: translate(-50%, -50%) scale(1.1); background: #ff0000; }}
    .thumb-img {{ width: 100%; display: block; opacity: 0.85; transition: opacity .2s; }}
    .thumb-link:hover .thumb-img {{ opacity: 1; }}
    .play-btn {{
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      width: 64px; height: 44px; background: rgba(0,0,0,.75); border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      color: #fff; font-size: 20px; transition: all .2s;
    }}
    .ts-badge {{
      position: absolute; bottom: 10px; right: 10px;
      background: rgba(0,0,0,.85); color: #fff; font-size: 13px; font-weight: 700;
      padding: 3px 10px; border-radius: 6px;
    }}
    .shorts-thumb-link .thumb-img {{ max-height: 280px; object-fit: cover; }}

    /* BRIEF GRID */
    .brief-grid {{ display: flex; gap: 0; border-top: 1px solid #2a2a2a; }}
    .brief-col {{ flex: 1; padding: 20px; }}
    .titles-col {{ border-right: 1px solid #2a2a2a; }}
    .section-label {{
      font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
      color: #6b7280; text-transform: uppercase; margin-bottom: 10px;
    }}
    .section-label.mt {{ margin-top: 16px; }}

    .title-row {{ display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }}
    .label {{
      font-size: 10px; font-weight: 700; letter-spacing: 1px;
      padding: 2px 6px; border-radius: 4px; white-space: nowrap; margin-top: 2px;
    }}
    .seo-label {{ background: #1d4ed8; color: #93c5fd; }}
    .ctr-label {{ background: #7c3aed; color: #c4b5fd; }}
    .shorts-title {{ color: #34d399; font-size: 13px; }}
    .value {{ font-size: 14px; color: #e5e5e5; line-height: 1.4; }}
    .ctr-value {{ font-size: 16px; color: #fff; font-weight: 600; }}

    .hook-quote {{
      font-size: 13px; color: #fbbf24; font-style: italic;
      background: #1c1917; padding: 10px 14px; border-radius: 8px;
      border-left: 3px solid #f59e0b; line-height: 1.5;
    }}
    .viral-reason {{
      font-size: 13px; color: #d1fae5; background: #052e16;
      padding: 10px 14px; border-radius: 8px; border-left: 3px solid #10b981;
      line-height: 1.5;
    }}

    /* THUMBNAIL COL */
    .thumb-text-preview {{
      font-size: 28px; font-weight: 900; letter-spacing: 1px;
      text-align: center; padding: 20px 16px; border-radius: 10px;
      border: 2px solid; background: #111; color: #fff;
      text-shadow: 2px 2px 6px rgba(0,0,0,.8);
      margin-bottom: 14px;
    }}
    .thumb-row {{ display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; }}
    .composicao {{
      font-size: 13px; color: #d1d5db; line-height: 1.5;
      background: #111; padding: 10px 14px; border-radius: 8px;
    }}

    /* FOOTER */
    .card-footer {{
      padding: 12px 20px; background: #111; border-top: 1px solid #2a2a2a;
      display: flex; gap: 12px;
    }}
    .yt-link {{
      font-size: 13px; color: #f87171; text-decoration: none; font-weight: 600;
    }}
    .yt-link:hover {{ text-decoration: underline; }}

    @media (max-width: 900px) {{
      .embeds-row {{ flex-direction: column; }}
      .brief-grid {{ flex-direction: column; }}
      .titles-col {{ border-right: none; border-bottom: 1px solid #2a2a2a; }}
    }}
  </style>
</head>
<body>
  <nav class="nav">
    <span class="nav-title">Nutellas — {video_id}</span>
    {nav_items}
  </nav>
  <div class="container">
    {''.join(cards)}
  </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Gera página HTML de review para nutellas")
    parser.add_argument("input", help="Arquivo JSON gerado pelo suggest.py")
    parser.add_argument("--open", action="store_true", help="Abre no browser automaticamente")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    html = generate_html(data)

    output_path = input_path.with_suffix(".html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Review gerado: {output_path}")

    if args.open:
        subprocess.run(["open", str(output_path)])
    else:
        print(f"Para abrir: open {output_path}")


if __name__ == "__main__":
    main()
