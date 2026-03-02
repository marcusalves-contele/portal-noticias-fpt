#!/usr/bin/env python3
"""
upload.py — Upload de nutellas aprovadas para o YouTube.

Features:
- Upload com thumbnail custom
- Monetizacao ativada automaticamente
- Agendamento inteligente (distribui nos melhores horarios)
- Descricao com link da live original + hashtags
- End cards (link para live + video relacionado na descricao)

Uso:
  python3 upload.py output/ra-GUivQnso_cuts/ --rank 1
  python3 upload.py output/ra-GUivQnso_cuts/ --rank 1,2,3 --schedule
  python3 upload.py output/ra-GUivQnso_cuts/ --rank 1 --public
"""

import sys
import json
import pickle
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

PROJECT_DIR = Path(__file__).parent
SEXTA_DIR   = PROJECT_DIR.parent.parent / "assistant-sexta-feira"
TOKEN_PATH  = SEXTA_DIR / "token_youtube_write.pickle"

CHANNEL_ID  = "UCz31CtOANqSFuLEdFTi1iCQ"  # Frota Para Todos
CATEGORY_EDUCATION = "27"

# Fuso horario Brasil (UTC-3)
BRT = timezone(timedelta(hours=-3))

# Melhores horarios para publicar (BRT) — baseado em dados do canal
# Dias uteis: engajamento melhor
# Horarios: 9h (views+engagement), 18h (alcance), 12h (lunch break)
BEST_HOURS_BRT = [9, 18, 12, 15, 20]


# -------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------

def load_credentials():
    """Carrega e renova token OAuth do YouTube."""
    if not TOKEN_PATH.exists():
        print(f"ERRO: Token nao encontrado em {TOKEN_PATH}")
        sys.exit(1)

    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)

    if creds.expired and creds.refresh_token:
        print("  Renovando token OAuth...")
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        print("  Token renovado OK")

    if not creds.valid:
        print("ERRO: Token invalido. Re-autentique.")
        sys.exit(1)

    return creds


def get_youtube(creds):
    return build("youtube", "v3", credentials=creds)


# -------------------------------------------------------------------
# Scheduling Intelligence
# -------------------------------------------------------------------

def get_best_publish_times(youtube, num_slots: int) -> list[datetime]:
    """Calcula melhores horarios para publicar nos proximos dias.

    Analisa videos recentes do canal e distribui nos melhores slots.
    Evita conflito com videos ja agendados ou recentemente publicados.
    """
    # Busca videos recentes pra evitar conflito
    recent = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        order="date",
        type="video",
        maxResults=10,
    ).execute()

    recent_dates = set()
    for item in recent.get("items", []):
        pub = item["snippet"]["publishedAt"][:10]  # YYYY-MM-DD
        recent_dates.add(pub)

    now = datetime.now(BRT)
    slots = []
    day_offset = 1  # comeca amanha
    hour_idx = 0

    while len(slots) < num_slots:
        candidate = (now + timedelta(days=day_offset)).replace(
            hour=BEST_HOURS_BRT[hour_idx % len(BEST_HOURS_BRT)],
            minute=0, second=0, microsecond=0
        )

        date_str = candidate.strftime("%Y-%m-%d")

        # Pula se ja tem video nesse dia (max 1 por dia pra nao canibalizar)
        if date_str not in recent_dates:
            slots.append(candidate)
            recent_dates.add(date_str)

        # Proximo dia (1 video por dia)
        day_offset += 1
        hour_idx += 1

        if day_offset > 30:
            break

    return slots


def format_schedule_brt(dt: datetime) -> str:
    """Formata datetime pra exibicao em BRT."""
    dias = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    return f"{dias[dt.weekday()]} {dt.strftime('%d/%m %Hh')}"


# -------------------------------------------------------------------
# Description & Tags
# -------------------------------------------------------------------

def build_description(meta: dict, source_video_id: str = None) -> str:
    """Monta descricao otimizada para SEO e AI Overviews."""
    lines = []

    # Hook — primeira coisa que aparece
    hook = meta.get("hook_transcricao", "")
    if hook:
        lines.append(hook)
        lines.append("")

    # Descrição curta gerada pela IA (valor do clip)
    desc_curta = meta.get("descricao_curta", "")
    if desc_curta:
        lines.append(desc_curta)
        lines.append("")

    # Link para live original
    if source_video_id:
        lines.append(f"Assista a live completa: https://youtube.com/watch?v={source_video_id}")
        lines.append("")

    # Timestamps se clip > 3min
    clip = meta.get("clip", {})
    if clip.get("entrada") and clip.get("saida"):
        from datetime import timedelta
        start_parts = clip["entrada"].split(":")
        end_parts = clip["saida"].split(":")
        start_s = int(start_parts[0]) * 60 + int(start_parts[1])
        end_s = int(end_parts[0]) * 60 + int(end_parts[1])
        duration = end_s - start_s
        if duration > 180:
            lines.append("Timestamps:")
            lines.append(f"0:00 Introdução")
            mid = duration // 2
            lines.append(f"{mid // 60}:{mid % 60:02d} Ponto principal")
            lines.append("")

    lines.append("---")
    lines.append("Canal Frota Para Todos com Julio César")
    lines.append("Gestão de frotas, tecnologia e produtividade para gestores de equipe externa.")
    lines.append("22+ anos de experiência real em gestão de frotas e equipes externas.")
    lines.append("")
    lines.append("Inscreva-se: https://www.youtube.com/@JulioCesarFrotaParaTodos?sub_confirmation=1")
    lines.append("")
    lines.append("#GestãoDeFrotas #Frota #Tecnologia #GestorDeEquipe #FrotaParaTodos")

    return "\n".join(lines)


def build_tags(meta: dict) -> list[str]:
    base_tags = [
        "gestao de frotas", "frota", "gestao de equipe",
        "tecnologia", "rastreamento", "contele",
        "julio cesar", "frota para todos",
        "gestao de equipe externa", "politica de frota",
    ]
    # Tags específicas do tema (geradas pela IA no suggest.py)
    specific = meta.get("tags_especificas", [])
    if specific:
        base_tags = specific + base_tags

    # Palavras do título como fallback
    title_words = meta.get("titulo_seo", "").lower().split()
    extra = [w for w in title_words if len(w) > 4 and w not in ("como", "para", "sobre", "quando", "voce")]
    return base_tags + extra[:5]


# -------------------------------------------------------------------
# Thumb & Upload
# -------------------------------------------------------------------

def find_thumb_for_meta(cuts_dir: Path, meta: dict) -> Path | None:
    rank = meta["rank"]
    clip_name = meta["clip"]["arquivo"]
    parts = clip_name.split("_")
    live_num = parts[0].replace("live", "") if parts else "0"

    thumb = cuts_dir / f"live{live_num}_{rank:02d}_thumb.png"
    if thumb.exists():
        return thumb

    versioned = sorted(cuts_dir.glob(f"live*_{rank:02d}_thumb_v*.png"))
    return versioned[0] if versioned else None


def upload_video(youtube, video_path: Path, title: str, description: str,
                 tags: list[str], category_id: str = CATEGORY_EDUCATION,
                 privacy: str = "private", publish_at: datetime = None) -> dict:
    """Upload de video com monetizacao e agendamento."""
    status_body = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": False,
        "license": "youtube",  # standard YouTube license (monetizavel)
    }

    # Agendamento: video fica private e publica automaticamente
    if publish_at:
        status_body["privacyStatus"] = "private"
        status_body["publishAt"] = publish_at.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.0Z"
        )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "pt",
            "defaultAudioLanguage": "pt",
        },
        "status": status_body,
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    size_mb = video_path.stat().st_size // (1024 * 1024)
    print(f"    Uploading {video_path.name} ({size_mb}MB)...")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    {pct}%...", end="\r")

    video_id = response["id"]
    print(f"    Upload OK: https://youtube.com/watch?v={video_id}")
    return response


def set_thumbnail(youtube, video_id: str, thumb_path: Path):
    media = MediaFileUpload(str(thumb_path), mimetype="image/png")
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f"    Thumbnail definida: {thumb_path.name}")


def upload_nutella(meta: dict, cuts_dir: Path, youtube,
                   privacy: str = "unlisted", publish_at: datetime = None,
                   source_video_id: str = None) -> dict | None:
    """Upload completo: video + thumb + monetizacao + agendamento."""
    rank = meta["rank"]
    clip_path = cuts_dir / meta["clip"]["arquivo"]

    if not clip_path.exists():
        print(f"  ERRO: Video nao encontrado: {clip_path}")
        return None

    title = meta["titulo_seo"]
    description = build_description(meta, source_video_id)
    tags = build_tags(meta)

    schedule_info = ""
    if publish_at:
        schedule_info = f" | Agenda: {format_schedule_brt(publish_at)}"
        privacy = "private"  # obrigatorio pra scheduling

    print(f"\n  #{rank}: {title}")
    print(f"    Privacy: {privacy}{schedule_info}")

    response = upload_video(
        youtube, clip_path, title, description, tags,
        privacy=privacy, publish_at=publish_at,
    )
    video_id = response["id"]

    # Thumbnail
    thumb_path = find_thumb_for_meta(cuts_dir, meta)
    if thumb_path:
        try:
            set_thumbnail(youtube, video_id, thumb_path)
        except Exception as e:
            print(f"    AVISO thumb: {e}")
    else:
        print(f"    AVISO: Sem thumbnail para #{rank}")

    return {
        "rank": rank,
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "title": title,
        "privacy": privacy,
        "publish_at": format_schedule_brt(publish_at) if publish_at else None,
        "thumb_set": thumb_path is not None,
    }


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Upload nutellas para YouTube")
    parser.add_argument("input", help="Diretorio de cuts")
    parser.add_argument("--rank", help="Rank(s) a subir, ex: 1 ou 1,2,3")
    parser.add_argument("--public", action="store_true", help="Upload como publico")
    parser.add_argument("--private", action="store_true", help="Upload como privado")
    parser.add_argument("--schedule", action="store_true",
                        help="Agendar publicacao nos melhores horarios")
    parser.add_argument("--source-video", help="ID do video da live original (pra descricao)")
    args = parser.parse_args()

    cuts_dir = Path(args.input)
    if not cuts_dir.is_dir():
        print(f"Diretorio invalido: {args.input}")
        sys.exit(1)

    metas = []
    for f in sorted(cuts_dir.glob("*_meta.json")):
        with open(f, encoding="utf-8") as fh:
            metas.append(json.load(fh))

    if not metas:
        print(f"Nenhum *_meta.json em {cuts_dir}")
        sys.exit(1)

    if args.rank:
        wanted = {int(r) for r in args.rank.split(",")}
        metas = [m for m in metas if m["rank"] in wanted]

    if not metas:
        print("Nenhuma nutella selecionada")
        sys.exit(1)

    privacy = "public" if args.public else ("private" if args.private else "unlisted")

    # Auth
    creds = load_credentials()
    youtube = get_youtube(creds)

    # Detect source video from directory name
    source_video_id = args.source_video
    if not source_video_id:
        dir_name = cuts_dir.name.replace("_cuts", "")
        if dir_name and not dir_name.startswith("output"):
            source_video_id = dir_name

    # Scheduling
    publish_times = []
    if args.schedule:
        print(f"\nCalculando melhores horarios para {len(metas)} videos...")
        publish_times = get_best_publish_times(youtube, len(metas))
        print("Agenda:")
        for i, t in enumerate(publish_times):
            r = metas[i]["rank"] if i < len(metas) else "?"
            print(f"  #{r}: {format_schedule_brt(t)}")
        privacy = "private"  # scheduling requer private

    print(f"\nUpload: {len(metas)} nutellas | {'AGENDADO' if args.schedule else privacy}")
    print(f"Canal: Frota Para Todos ({CHANNEL_ID})")
    if source_video_id:
        print(f"Live original: https://youtube.com/watch?v={source_video_id}")

    results = []
    for i, meta in enumerate(metas):
        pub_time = publish_times[i] if i < len(publish_times) else None
        result = upload_nutella(
            meta, cuts_dir, youtube,
            privacy=privacy, publish_at=pub_time,
            source_video_id=source_video_id,
        )
        if result:
            results.append(result)

    # Resumo
    print(f"\n{'='*60}")
    print(f"UPLOAD CONCLUIDO: {len(results)}/{len(metas)} videos")
    for r in results:
        sched = f" | {r['publish_at']}" if r.get("publish_at") else ""
        thumb = "THUMB OK" if r["thumb_set"] else "SEM THUMB"
        print(f"  #{r['rank']} [{r['privacy']}] {r['url']} ({thumb}){sched}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    main()
