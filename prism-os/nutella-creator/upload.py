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

import os
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
SEXTA_DIR   = PROJECT_DIR.parent.parent.parent / "assistant-sexta-feira"

def _read_env_token_path() -> str | None:
    """Lê YOUTUBE_TOKEN_PATH do .env local (sem python-dotenv)."""
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("YOUTUBE_TOKEN_PATH"):
                    return line.split("=", 1)[1].strip().strip('"')
    return None

TOKEN_PATH = Path(
    os.getenv("YOUTUBE_TOKEN_PATH")
    or _read_env_token_path()
    or str(SEXTA_DIR / "token_youtube_write.pickle")
)

CHANNEL_ID  = "UCz31CtOANqSFuLEdFTi1iCQ"  # Frota Para Todos
CATEGORY_EDUCATION = "27"
PLAYLIST_CORTES = "PLuVWEr9u-IQ044ZxtQj8chOEuJ3P80KoF"  # "Cortes de Lives"

# Fuso horario Brasil (UTC-3)
BRT = timezone(timedelta(hours=-3))

# Ranking de slots — validado em 3 análises independentes (mar/2026):
#   1. Histórico de publicação (2.873 vídeos, 2024–2026)
#   2. Score orgânico (mediana × engajamento), últimos 6 meses
#   3. Confirmação em 12 meses (649 vídeos, mar/25–fev/26)
#
# NUTELLAS (clips 16:9 > 90s) — (weekday, hour, minute):
#   1º qui 15h00 — score 31.819, eng=9.91%, n=64 — CONFIRMADO
#   2º sex 17h00 — score 13.169, eng=4.40%,  n=9  — CONFIRMADO
#   3º sáb 06h30 — TESTE (dados de sáb orgânico prometem; manhã cedo evita competição)
#   4º dom 08h00 — TESTE (mesmo raciocínio)
#   5º ter 15h00 — overflow (score fraco mas melhor que não publicar)
#   6º seg 15h00 — overflow extremo
#   NUNCA quarta — dia da live semanal (8h BRT)
#
# SHORTS (9:16 ≤ 90s) — dia tem impacto PEQUENO nos 12m (scores próximos):
#   1º ter 18h00 — estratégia: teaseia Nutella de quinta (2 dias antes)
#   2º sex 18h00 — score orgânico ok em 6m
#   3º sáb 18h00 — mediana ok nos 6m
#   4º dom 18h00 — mediana ok
#   5º seg 18h00 — overflow
#   NUNCA quarta
#
# Clips e Shorts compartilham o conjunto de datas ocupadas (max 1 vídeo/dia).
CLIP_PRIORITY = [
    (3, 15,  0),  # qui 15h00
    (4, 17,  0),  # sex 17h00
    (5,  6, 30),  # sáb 06h30
    (6,  8,  0),  # dom 08h00
    (1, 15,  0),  # ter 15h00
    (0, 15,  0),  # seg 15h00
]
SHORT_PRIORITY = [
    (1, 18,  0),  # ter 18h00
    (4, 18,  0),  # sex 18h00
    (5, 18,  0),  # sáb 18h00
    (6, 18,  0),  # dom 18h00
    (0, 18,  0),  # seg 18h00
]

# -------------------------------------------------------------------
# Modo Experimento — Backlog (ativo desde mar/2026, revisão mai/2026)
# -------------------------------------------------------------------
# Objetivo: distribuir os clips do backlog de ~24 lives por TODOS os dias
# (seg/ter/qui/sex/sáb/dom — nunca quarta) em horários variados para
# medir qual combinação dia+hora gera melhor CTR, views e inscritos.
#
# 12 slots de clip × ~2 clips/live × 24 lives = ~48 clips.
# Cada slot recebe ~4 amostras → dados suficientes para comparação em mai/2026.
#
# Slots confirmados (qui 15h, sex 17h) ficam no topo como BASELINE.
# Trocar para False ao concluir o experimento.
EXPERIMENT_MODE = True

EXPERIMENT_CLIPS = [
    (3, 15,  0),  # qui 15h — baseline #1 (confirmado, n=64)
    (4, 17,  0),  # sex 17h — baseline #2 (confirmado, n=9)
    (1, 12,  0),  # ter 12h — teste horário almoço
    (0, 17,  0),  # seg 17h — teste tarde início de semana
    (5,  7,  0),  # sáb 07h — teste manhã cedo fim de semana
    (6, 10,  0),  # dom 10h — teste manhã domingo
    (3, 19,  0),  # qui 19h — teste noite quinta
    (4, 10,  0),  # sex 10h — teste manhã sexta
    (1, 19,  0),  # ter 19h — teste noite terça
    (0,  9,  0),  # seg 09h — teste manhã segunda
    (5, 15,  0),  # sáb 15h — teste tarde sábado
    (6, 17,  0),  # dom 17h — teste tarde domingo
]
EXPERIMENT_SHORTS = [
    (1, 18,  0),  # ter 18h — baseline
    (4, 18,  0),  # sex 18h — alternativo
    (5, 18,  0),  # sáb 18h
    (6, 18,  0),  # dom 18h
    (0, 18,  0),  # seg 18h
    (3, 18,  0),  # qui 18h
]


# -------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------

def load_credentials():
    """Carrega e renova token OAuth do YouTube. Valida canal."""
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
    yt = build("youtube", "v3", credentials=creds)
    # Validar que o token pertence ao canal correto (fail-closed)
    try:
        resp = yt.channels().list(mine=True, part="id,snippet").execute()
        items = resp.get("items", [])
        if not items:
            print(f"ERRO CRITICO: Token nao retornou nenhum canal.")
            print(f"  Token path: {TOKEN_PATH}")
            print(f"  ABORTANDO. Re-autentique como julio.cesar@contele.com.br.")
            sys.exit(1)
        token_channel = items[0]["id"]
        token_name = items[0]["snippet"]["title"]
        if token_channel != CHANNEL_ID:
            print(f"ERRO CRITICO: Token autenticado como '{token_name}' ({token_channel})")
            print(f"  Esperado: Frota Para Todos ({CHANNEL_ID})")
            print(f"  Token path: {TOKEN_PATH}")
            print(f"  ABORTANDO para nao subir video no canal errado.")
            sys.exit(1)
        print(f"  Canal validado: {token_name} ({token_channel})")
    except Exception as e:
        print(f"ERRO CRITICO: Nao foi possivel validar canal: {e}")
        print(f"  ABORTANDO. Sem validacao, upload nao e seguro.")
        sys.exit(1)
    return yt


# -------------------------------------------------------------------
# Scheduling Intelligence
# -------------------------------------------------------------------

def get_best_publish_times(youtube, num_clips: int, num_shorts: int = 0) -> dict:
    """
    Calcula horários de publicação.

    EXPERIMENT_MODE=True  (mar-mai/2026): cicla por 12 slots em 6 dias
    para medir qual dia+hora converte melhor. Baselines (qui 15h, sex 17h)
    ficam no topo do ciclo como referência comparativa.

    EXPERIMENT_MODE=False: usa ranking otimizado histórico
    (qui 15h > sex 17h > sáb 06h30 > dom 08h > ter 15h > seg 15h).

    Nunca quarta — dia da live semanal (8h BRT).
    Clips e Shorts compartilham datas ocupadas: máximo 1 vídeo por dia.
    """
    clip_priority  = EXPERIMENT_CLIPS  if EXPERIMENT_MODE else CLIP_PRIORITY
    short_priority = EXPERIMENT_SHORTS if EXPERIMENT_MODE else SHORT_PRIORITY
    # Datas já ocupadas (vídeos agendados ou recentes)
    recent = youtube.search().list(
        part="snippet", channelId=CHANNEL_ID,
        order="date", type="video", maxResults=20,
    ).execute()
    used = set()
    for item in recent.get("items", []):
        pub = item["snippet"]["publishedAt"][:10]
        used.add(pub)

    now = datetime.now(BRT)

    def next_slots(priority: list[tuple], count: int) -> list[datetime]:
        """
        Aloca 'count' slots a partir da lista de prioridade.

        Modo otimizado (EXPERIMENT_MODE=False):
          wd_map com 1 slot por weekday — varre dias cronologicamente
          e pega o melhor horário disponível para cada dia.

        Modo experimento (EXPERIMENT_MODE=True):
          Cicla pelos slots em ORDEM da lista. Para cada slot (wd, h, m)
          encontra a próxima data livre com aquele weekday. Garante que
          TODOS os 12 slots do experimento sejam usados em sequência,
          incluindo horários alternativos no mesmo dia da semana.
          Resultado é reordenado cronologicamente para exibição.
        """
        if EXPERIMENT_MODE:
            result = []
            slot_idx = 0
            n = len(priority)
            while len(result) < count and slot_idx < n * 10:
                wd, h, m = priority[slot_idx % n]
                slot_idx += 1
                for day_offset in range(1, 91):
                    candidate = now + timedelta(days=day_offset)
                    if candidate.weekday() != wd:
                        continue
                    dt = candidate.replace(hour=h, minute=m, second=0, microsecond=0)
                    date_str = dt.strftime("%Y-%m-%d")
                    if date_str not in used:
                        result.append(dt)
                        used.add(date_str)
                        break
            return sorted(result)
        else:
            # Modo otimizado: 1 slot por weekday, varre dias forward
            wd_map = {}
            for rank, (wd, h, m) in enumerate(priority):
                if wd not in wd_map:
                    wd_map[wd] = (h, m, rank)

            result = []
            day_offset = 1
            while len(result) < count and day_offset <= 90:
                candidate = now + timedelta(days=day_offset)
                wd = candidate.weekday()
                day_offset += 1
                if wd not in wd_map:
                    continue
                h, m, _ = wd_map[wd]
                dt = candidate.replace(hour=h, minute=m, second=0, microsecond=0)
                date_str = dt.strftime("%Y-%m-%d")
                if date_str not in used:
                    result.append(dt)
                    used.add(date_str)
            return result

    clip_times  = next_slots(clip_priority,  num_clips)
    short_times = next_slots(short_priority, num_shorts)

    return {"clips": clip_times, "shorts": short_times}


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
    clip_obj = meta.get("clip") or {}
    clip_name = clip_obj.get("arquivo", "")
    parts = clip_name.split("_") if clip_name else []
    live_num = parts[0].replace("live", "") if parts and parts[0].startswith("live") else "0"

    # Prefere ajustes mais recentes pra que upload pegue a ultima versao
    # aprovada pelo time (issue #89).
    adjusted = list(cuts_dir.glob(f"live*_{rank:02d}_thumb_adj*.png"))
    if adjusted:
        def _adj_idx(p: Path) -> int:
            try:
                return int(p.stem.split("_adj")[-1])
            except (ValueError, IndexError):
                return 0
        return max(adjusted, key=_adj_idx)

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

    # Adiciona à playlist "Cortes de Lives"
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": PLAYLIST_CORTES, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
        ).execute()
        print(f"    Playlist: adicionado a 'Cortes de Lives'")
    except Exception as e:
        print(f"    AVISO playlist: {e}")

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
# Short upload
# -------------------------------------------------------------------

def build_short_description(meta: dict, source_video_id: str = None) -> str:
    lines = []
    desc = meta.get("descricao_curta", "")
    if desc:
        lines.append(desc)
        lines.append("")
    if source_video_id:
        lines.append(f"Live completa: https://youtube.com/watch?v={source_video_id}")
        lines.append("")
    lines.append("#Shorts #GestãoDeFrotas #FrotaParaTodos #Frota #GestorDeEquipe")
    return "\n".join(lines)


def upload_short(meta: dict, cuts_dir: Path, youtube,
                 privacy: str = "unlisted", publish_at: datetime = None,
                 source_video_id: str = None) -> dict | None:
    """Upload do Short 9:16 com título curto e #Shorts."""
    rank = meta["rank"]
    short_info = meta.get("shorts", {})
    short_file = short_info.get("arquivo", "")

    if not short_file:
        print(f"  #{rank}: sem arquivo de Short no meta, pulando")
        return None

    short_path = cuts_dir / short_file
    if not short_path.exists():
        print(f"  ERRO: Short não encontrado: {short_path}")
        return None

    raw_title = meta.get("titulo_shorts", "") or meta.get("titulo_ctr", "")
    title = raw_title[:100]
    description = build_short_description(meta, source_video_id)
    tags = build_tags(meta) + ["shorts", "short"]

    schedule_info = f" | Agenda: {format_schedule_brt(publish_at)}" if publish_at else ""
    print(f"\n  #{rank} SHORT: {title}")
    print(f"    Privacy: {privacy}{schedule_info}")

    response = upload_video(
        youtube, short_path, title, description, tags,
        privacy=privacy, publish_at=publish_at,
    )
    video_id = response["id"]

    return {
        "rank": rank,
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "title": title,
        "type": "short",
        "privacy": privacy,
        "publish_at": format_schedule_brt(publish_at) if publish_at else None,
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
