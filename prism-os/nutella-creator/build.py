#!/usr/bin/env python3
"""
Nutella Build — Download + Corte + Composição completa.

Para cada nutella no JSON:
  1. Baixa o vídeo completo via yt-dlp (uma vez, reutiliza se já existe)
  2. Detecta face automaticamente (mediapipe) → crop 9:16 inteligente
  3. Compõe 16:9: intro + clip(moldura + tag rodapé) + CTA
  4. Compõe 9:16 Shorts: face-crop + intro + clip(tag) + CTA
  5. Salva: live{N}_{rank:02d}_{slug-seo}.mp4  e  live{N}_{rank:02d}_short_{slug-shorts}.mp4
  6. Gera live{N}_{rank:02d}_meta.json com todos os títulos prontos para upload

Uso:
  python3 build.py output/ra-GUivQnso_nutellas.json
  python3 build.py output/ra-GUivQnso_nutellas.json --ranks 1,2
  python3 build.py output/ra-GUivQnso_nutellas.json --no-shorts
  python3 build.py output/ra-GUivQnso_nutellas.json --no-download   # usa vídeo já baixado
"""

import sys
import re
import os
import json
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path

try:
    import cv2
    import mediapipe as mp
    HAS_FACE_DETECTION = True
except ImportError as _e:
    print(f"  AVISO: face detection indisponivel ({_e}), usando letterbox para Shorts")
    HAS_FACE_DETECTION = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_DIR  = Path(__file__).parent
ASSETS_DIR   = PROJECT_DIR / "assets"
DOWNLOADS_DIR = PROJECT_DIR / "downloads"
OUTPUT_DIR   = PROJECT_DIR / "output"

INTRO  = ASSETS_DIR / "intro-julio-cortes-nutela-v2.mp4"
CTA    = ASSETS_DIR / "cta-final-pronto-v2.mp4"
BADGE  = ASSETS_DIR / "badge-overlay.png"   # 1920×90 RGBA

# 16:9 output
W, H = 1920, 1080
FPS  = 30
BADGE_H = 90   # altura do badge

# 9:16 output
SW, SH = 1080, 1920
# Split dinâmico: tela inteira (1920→1080 wide) = 608px, face pega o resto
SCREEN_FIT_H = (SW * H // W // 2) * 2   # 608 (full 16:9 at 1080w, even)
FACE_FIT_H   = SH - SCREEN_FIT_H         # 1312

FREEZE_DURATION = 1.5  # segundos de freeze frame no início do Short

# Badge generation cache
_badge_cache: dict[str, Path] = {}


def generate_badge(live_num: str, tmp_dir: Path) -> Path:
    """
    Gera badge-overlay dinâmico com Pillow usando o número real da live.
    Retorna Path do PNG gerado. Cache por live_num.
    """
    if live_num in _badge_cache and _badge_cache[live_num].exists():
        return _badge_cache[live_num]

    out_path = tmp_dir / f"badge_live{live_num}.png"

    if HAS_PIL:
        img = Image.new("RGBA", (W, BADGE_H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background: dark semi-transparent bar
        draw.rectangle([(0, 0), (W, BADGE_H)], fill=(20, 10, 30, 210))

        # Thin purple accent line at top
        draw.rectangle([(0, 0), (W, 2)], fill=(139, 35, 229, 255))

        # Load fonts
        font_path = None
        for fp in FONT_CANDIDATES:
            if Path(fp).exists():
                font_path = fp
                break
        # Also try Linux/Railway paths
        if not font_path:
            for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
                if Path(fp).exists():
                    font_path = fp
                    break

        try:
            font_small = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
            font_main = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
            font_right = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
            font_right_sm = ImageFont.truetype(font_path, 13) if font_path else ImageFont.load_default()
        except Exception:
            font_small = ImageFont.load_default()
            font_main = ImageFont.load_default()
            font_right = ImageFont.load_default()
            font_right_sm = ImageFont.load_default()

        # Left side: red dot + handle
        x = 24
        draw.ellipse([(x, 28), (x + 12, 40)], fill=(255, 40, 40, 255))
        x += 20
        draw.text((x, 18), "@JULIOCESARFROTAPARATODOS", fill=(180, 180, 180, 255), font=font_small)

        # Main text: CORTE DA LIVE {N}
        x = 24
        y_main = 42
        draw.text((x, y_main), "CORTE DA ", fill=(255, 255, 255, 255), font=font_main)
        corte_w = draw.textlength("CORTE DA ", font=font_main)
        draw.text((x + corte_w, y_main), f"LIVE {live_num}", fill=(139, 35, 229, 255), font=font_main)

        # Right side: CTA
        right_text = "Assista antes que saia do ar"
        right_sub = "LINK NA DESCRICAO"
        rt_w = draw.textlength(right_text, font=font_right)
        rs_w = draw.textlength(right_sub, font=font_right_sm)
        draw.text((W - rt_w - 30, 22), right_text, fill=(220, 220, 220, 255), font=font_right)
        draw.text((W - rs_w - 30, 52), right_sub, fill=(160, 160, 160, 200), font=font_right_sm)

        img.save(out_path)
    else:
        # Fallback: use static badge if Pillow unavailable
        import shutil as _shutil
        _shutil.copy2(BADGE, out_path)

    _badge_cache[live_num] = out_path
    print(f"  Badge gerado: CORTE DA LIVE {live_num}")
    return out_path


# macOS system fonts (tenta em ordem)
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def run(cmd: list, desc: str = "", check: bool = True) -> subprocess.CompletedProcess:
    print(f"  {'[ffmpeg]' if 'ffmpeg' in cmd[0] else '[cmd]'} {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        stderr_tail = result.stderr[-600:].strip()
        print(f"  ERRO: {stderr_tail}")
        raise RuntimeError(f"Falhou: {desc}\n{stderr_tail}")
    return result


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[áàãâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[íìîï]", "i", text)
    text = re.sub(r"[óòõôö]", "o", text)
    text = re.sub(r"[úùûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def t2s(t: str) -> float:
    """MM:SS ou HH:MM:SS → segundos (float)."""
    parts = t.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return int(parts[0]) * 60 + float(parts[1])


def find_font() -> str | None:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return f
    return None


def _ensure_cookies():
    """Decodifica COOKIES_B64 env var em cookies.txt se não existir."""
    cookies_file = PROJECT_DIR / "cookies.txt"
    if cookies_file.exists():
        return
    cookies_b64 = os.environ.get("COOKIES_B64", "")
    if not cookies_b64:
        return
    import base64
    try:
        data = base64.b64decode(cookies_b64)
        cookies_file.write_bytes(data)
        print(f"  cookies.txt criado via COOKIES_B64 ({len(data)} bytes)")
    except Exception as e:
        print(f"  AVISO: falha ao decodificar COOKIES_B64: {e}")


# Decodifica cookies na importação (antes de qualquer download)
_ensure_cookies()


def get_live_number(video_id: str) -> str:
    """Tenta extrair número da live via yt-dlp --get-title."""
    cookies_file = PROJECT_DIR / "cookies.txt"
    cookies_arg = ["--cookies", str(cookies_file)] if cookies_file.exists() else []
    try:
        r = subprocess.run(
            ["yt-dlp", "--get-title", *cookies_arg, f"https://youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=20
        )
        title = r.stdout.strip()
        m = re.search(r"live\s*(\d+)", title, re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return video_id


# -------------------------------------------------------------------
# Download
# -------------------------------------------------------------------

def _parse_ytdlp_error(stderr: str) -> str:
    """Converte stderr do yt-dlp em mensagem amigável."""
    s = stderr.lower()

    if "sign in" in s or "bot" in s or "429" in s or "too many" in s:
        return "YouTube bloqueou o IP por excesso de requests. Tente novamente em 5 minutos ou configure cookies.txt."

    if "403" in s or "forbidden" in s:
        return "YouTube retornou 403 Forbidden. IP pode estar bloqueado. Configure cookies.txt para autenticar."

    if "video unavailable" in s or "private" in s:
        return "Video indisponivel ou privado. Verifique a URL."

    if "removed" in s or "copyright" in s:
        return "Video removido ou bloqueado por direitos autorais."

    if "not a valid url" in s or "unsupported" in s:
        return "URL invalida. Cole a URL completa do YouTube."

    if "unable to download" in s:
        return "Nao conseguiu baixar o video. Verifique se a URL esta correta e tente novamente."

    # Fallback: última linha significativa
    lines = [l.strip() for l in stderr.strip().split("\n") if l.strip() and "WARNING" not in l.upper()]
    if lines:
        return f"Erro yt-dlp: {lines[-1][:200]}"

    return "Erro desconhecido no download. Tente novamente."


def download_video(video_id: str) -> Path:
    import time

    DOWNLOADS_DIR.mkdir(exist_ok=True)
    # Procura arquivo já baixado — ignora .part (incompletos) e .m4a/.webm (áudio puro)
    _AUDIO_ONLY = {".m4a", ".webm", ".opus", ".mp3", ".ogg"}
    existing = [
        f for f in DOWNLOADS_DIR.glob(f"{video_id}.*")
        if not f.name.endswith(".part") and f.suffix.lower() not in _AUDIO_ONLY
    ]
    if existing:
        print(f"  Vídeo já baixado: {existing[0].name}")
        return existing[0]

    url = f"https://youtube.com/watch?v={video_id}"
    out_tmpl = str(DOWNLOADS_DIR / f"{video_id}.%(ext)s")

    # Cookies: env var (Railway) > local
    cookies_path = os.environ.get("COOKIES_PATH")
    if not cookies_path or not Path(cookies_path).exists():
        local_cookies = PROJECT_DIR / "cookies.txt"
        cookies_path = str(local_cookies) if local_cookies.exists() else None
    cookies_arg = ["--cookies", cookies_path] if cookies_path else []

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
        "--merge-output-format", "mp4",
        "--remote-components", "ejs:github",
        "--socket-timeout", "30",
        "--retries", "2",
        *cookies_arg,
        "-o", out_tmpl,
        url,
    ]

    max_retries = 3
    delays = [5, 15, 30]
    last_error = ""

    print(f"  Baixando {video_id} via yt-dlp...")

    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            last_error = "Download travou (timeout 120s). YouTube pode estar bloqueando o IP. Configure cookies.txt para autenticar."
            print(f"  Tentativa {attempt + 1}: timeout")
            if attempt < max_retries - 1:
                time.sleep(delays[attempt])
            continue

        if result.returncode == 0:
            downloaded = list(DOWNLOADS_DIR.glob(f"{video_id}.*"))
            if downloaded:
                return downloaded[0]

        stderr = result.stderr or ""
        last_error = _parse_ytdlp_error(stderr)

        # Erros permanentes: não faz sentido tentar de novo
        if any(x in stderr.lower() for x in ["video unavailable", "private video", "removed", "copyright"]):
            raise RuntimeError(last_error)

        if attempt < max_retries - 1:
            print(f"  Tentativa {attempt + 1} falhou: {last_error}")
            print(f"  Aguardando {delays[attempt]}s antes de nova tentativa...")
            time.sleep(delays[attempt])

    raise RuntimeError(last_error)


# -------------------------------------------------------------------
# Face tracking (mediapipe)
# -------------------------------------------------------------------

def detect_layout(video_path: Path, start_sec: float, end_sec: float) -> dict:
    """
    Amostra frames do clip, detecta o MAIOR rosto (mediapipe).
    Retorna dict com cx, cy, fw, fh do rosto principal e tipo de layout.
    Fallback: centro do frame (letterbox).
    """
    fallback = {"type": "no_face", "cx": W // 2, "cy": H // 2, "fw": 120, "fh": 120,
                "best_frame_sec": start_sec}
    if not HAS_FACE_DETECTION:
        print("  Layout: mediapipe indisponivel, usando letterbox")
        return fallback
    try:
        face_det = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.4
        )
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        sample_interval = max(1, int(fps * 2))

        start_f = int(start_sec * fps)
        end_f   = int(end_sec * fps)
        detections = []  # (cx, cy, fw, fh)

        best_frame_sec   = start_sec
        best_frame_score = 0.0

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
        frame_idx = start_f

        while frame_idx <= end_f:
            ret, frame = cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_det.process(rgb)
            if results.detections:
                # Maior rosto por frame (speaker principal)
                best = max(
                    results.detections,
                    key=lambda d: d.location_data.relative_bounding_box.width
                                * d.location_data.relative_bounding_box.height
                )
                box = best.location_data.relative_bounding_box
                cx = int((box.xmin + box.width  / 2) * W)
                cy = int((box.ymin + box.height / 2) * H)
                fw = int(box.width  * W)
                fh = int(box.height * H)
                detections.append((cx, cy, fw, fh))

                # Rastrear melhor frame: maior área × confiança mediapipe
                score = best.score[0] if best.score else 0.5
                if score * fw * fh > best_frame_score:
                    best_frame_score = score * fw * fh
                    best_frame_sec   = frame_idx / fps

            frame_idx += sample_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        cap.release()
        face_det.close()

        if not detections:
            print("  Layout: nenhum rosto → letterbox")
            return fallback

        mid = len(detections) // 2
        cx = sorted(detections, key=lambda d: d[0])[mid][0]
        cy = sorted(detections, key=lambda d: d[1])[mid][1]
        fw = sorted(detections, key=lambda d: d[2])[mid][2]
        fh = sorted(detections, key=lambda d: d[3])[mid][3]

        # screen_share: rosto pequeno (< 6% do frame) → streaming com tela compartilhada
        # multi_face: rosto grande → conversa, solo speaker, sem tela
        face_ratio = (fw * fh) / (W * H)
        layout_type = "screen_share" if face_ratio < 0.06 else "multi_face"
        print(f"  Layout: {layout_type} | face ({cx},{cy}) {fw}×{fh} | {len(detections)} amostras")
        print(f"  Melhor frame: {best_frame_sec:.1f}s (score×área={best_frame_score:.0f})")
        return {"type": layout_type, "cx": cx, "cy": cy, "fw": fw, "fh": fh,
                "best_frame_sec": best_frame_sec}

    except Exception as e:
        print(f"  Layout erro: {e} → letterbox")
        return fallback


# -------------------------------------------------------------------
# ffmpeg helpers
# -------------------------------------------------------------------

def prepare_segment(
    src: Path,
    out: Path,
    target_w: int,
    target_h: int,
    crop_x: int = 0,
    crop_from_w: int = 0,
    is_source_4k: bool = False,
) -> None:
    """
    Prepara segmento (intro ou CTA) com:
    - Escala para target_w x target_h
    - Se crop_from_w > 0: crop → depois escala (para 9:16)
    - Normaliza áudio: aac, 44100Hz, estéreo
    """
    vf_parts = []

    if crop_from_w > 0:
        src_h = 2160 if is_source_4k else H
        src_crop_w = int(src_h * 9 / 16)
        src_cx = crop_from_w  # passado pelo chamador
        vf_parts.append(f"crop={src_crop_w}:{src_h}:{src_cx}:0")

    vf_parts.append(f"scale={target_w}:{target_h}")
    vf_parts.append(f"fps={FPS}")

    vf = ",".join(vf_parts)

    run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        str(out),
    ], desc=f"prepare {src.name} → {target_w}x{target_h}")


def compose_clip(
    source: Path,
    start_sec: float,
    end_sec: float,
    out: Path,
    target_w: int,
    target_h: int,
    layout: dict | None = None,  # resultado de detect_layout(), para 9:16
    crop_mode: bool = False,      # True = Short 9:16
    badge_path: Path | None = None,  # badge dinâmico (se None, usa estático)
) -> None:
    """
    16:9 → vídeo full + badge de identidade no topo.
    9:16 → split-screen: rosto (topo) + tela (base), sem badge.
           Fallback letterbox quando não há rosto detectado.
    """
    duration = end_sec - start_sec

    if not crop_mode:
        # 16:9: vídeo full + badge no topo (v0.3.0) com suporte a badge dinâmico
        actual_badge = badge_path or BADGE
        badge_y = 0
        filter_complex = (
            f"[0:v]scale={target_w}:{target_h},fps={FPS}[vid];"
            f"[1:v]scale={target_w}:{BADGE_H},format=rgba[badge];"
            f"[vid][badge]overlay=0:{badge_y}[vfinal]"
        )
        run([
            "ffmpeg", "-y",
            "-ss", str(start_sec), "-t", str(duration), "-i", str(source),
            "-i", str(actual_badge),
            "-filter_complex", filter_complex,
            "-map", "[vfinal]", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-ar", "44100", "-ac", "2",
            str(out),
        ], desc=f"compose clip 16:9 [{start_sec:.0f}s → {end_sec:.0f}s]")
    else:
        # 9:16 Short: split-screen — rosto zoom topo, tela INTEIRA embaixo
        lay = layout or {}
        has_face = lay.get("type", "no_face") != "no_face"

        if has_face:
            face_cx = lay["cx"]
            face_cy = lay["cy"]
            face_fw = lay["fw"]
            face_fh = lay["fh"]
            is_ss = lay.get("type") == "screen_share"

            if is_ss:
                # Screen share: split-screen — rosto zoom topo, tela INTEIRA embaixo
                face_h_s   = FACE_FIT_H     # 1312
                screen_h_s = SCREEN_FIT_H   # 608

                src_ratio = SW / face_h_s
                mult = 2.5
                crop_w = max(int(face_fw * mult), 280)
                crop_w = min(crop_w, W // 4)
                crop_w = (crop_w // 2) * 2
                crop_h = (int(crop_w / src_ratio) // 2) * 2
                crop_h = min(crop_h, H)
                crop_w = (int(crop_h * src_ratio) // 2) * 2

                face_top = face_cy - face_fh // 2
                padding_above = max(int(face_fh * 0.6), 30)
                fc_y = max(0, face_top - padding_above)
                fc_y = min(fc_y, H - crop_h)
                fc_x = max(0, min(face_cx - crop_w // 2, W - crop_w))

                screen_filter = f"scale={SW}:{screen_h_s},fps={FPS}"

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{fc_x}:{fc_y},"
                    f"scale={SW}:{face_h_s},fps={FPS}[face];"
                    f"[0:v]{screen_filter}[screen];"
                    f"[face][screen]vstack,setsar=1[vfinal]"
                )
                desc = f"compose clip 9:16 split [{start_sec:.0f}s → {end_sec:.0f}s]"
            else:
                # Multi-face / conversa: crop 9:16 direto centrado no rosto
                # Evita duplicação visual (rosto zoom + rosto no frame inteiro)
                src_crop_w = (H * 9 // 16 // 2) * 2   # 607 → 606
                src_crop_h = H                          # 1080

                # Centraliza o crop no rosto (horizontalmente)
                fc_x = max(0, min(face_cx - src_crop_w // 2, W - src_crop_w))

                filter_complex = (
                    f"[0:v]crop={src_crop_w}:{src_crop_h}:{fc_x}:0,"
                    f"scale={SW}:{SH},fps={FPS},setsar=1[vfinal]"
                )
                desc = f"compose clip 9:16 crop [{start_sec:.0f}s → {end_sec:.0f}s]"
        else:
            # Fallback: letterbox com blur (sem rosto detectado)
            filter_complex = (
                f"[0:v]scale={target_w}:-2,fps={FPS}[main];"
                f"[0:v]scale={target_w}:{target_h},boxblur=20:5,fps={FPS}[blur];"
                f"[blur][main]overlay=(W-w)/2:(H-h)/2,setsar=1[vfinal]"
            )
            desc = f"compose clip 9:16 letterbox [{start_sec:.0f}s → {end_sec:.0f}s]"

        run([
            "ffmpeg", "-y",
            "-ss", str(start_sec), "-t", str(duration), "-i", str(source),
            "-filter_complex", filter_complex,
            "-map", "[vfinal]", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-aspect", "9:16",
            "-c:a", "aac", "-ar", "44100", "-ac", "2",
            str(out),
        ], desc=desc)


def make_freeze_frame(
    source: Path,
    best_sec: float,
    layout: dict,
    out: Path,
    tmp_dir: Path,
    duration: float = FREEZE_DURATION,
) -> None:
    """
    Extrai o melhor frame do clip, aplica o mesmo crop 9:16 do Short,
    e gera um vídeo estático com áudio silencioso para prefixar ao Short.
    YouTube usa o frame 0 como capa de Shorts → esse é o hack.
    """
    lay = layout or {}
    has_face = lay.get("type", "no_face") != "no_face"

    # Step 1: extrai o melhor frame como PNG puro (sem filtros)
    frame_png = tmp_dir / f"freeze_{out.stem}.png"
    run([
        "ffmpeg", "-y",
        "-ss", str(best_sec), "-i", str(source),
        "-vframes", "1",
        str(frame_png),
    ], desc=f"extract best frame @ {best_sec:.1f}s")

    # Step 2: aplica filtro 9:16 idêntico ao compose_clip + loop + silêncio
    if has_face:
        face_cx = lay["cx"]
        face_cy = lay["cy"]
        face_fw = lay["fw"]
        face_fh = lay["fh"]
        is_ss = lay.get("type") == "screen_share"

        if is_ss:
            # Screen share: split-screen (face zoom topo + tela embaixo)
            face_h_s   = FACE_FIT_H
            screen_h_s = SCREEN_FIT_H
            src_ratio  = SW / face_h_s

            mult   = 2.5
            crop_w = max(int(face_fw * mult), 280)
            crop_w = min(crop_w, W // 4)
            crop_w = (crop_w // 2) * 2
            crop_h = (int(crop_w / src_ratio) // 2) * 2
            crop_h = min(crop_h, H)
            crop_w = (int(crop_h * src_ratio) // 2) * 2

            face_top      = face_cy - face_fh // 2
            padding_above = max(int(face_fh * 0.6), 30)
            fc_y = max(0, face_top - padding_above)
            fc_y = min(fc_y, H - crop_h)
            fc_x = max(0, min(face_cx - crop_w // 2, W - crop_w))

            filter_complex = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=disable,split=2[va][vb];"
                f"[va]crop={crop_w}:{crop_h}:{fc_x}:{fc_y},scale={SW}:{face_h_s}[face];"
                f"[vb]scale={SW}:{screen_h_s}[screen];"
                f"[face][screen]vstack,setsar=1,fps={FPS}[vfinal]"
            )
        else:
            # Multi-face: crop 9:16 direto centrado no rosto
            src_crop_w = (H * 9 // 16 // 2) * 2
            fc_x = max(0, min(face_cx - src_crop_w // 2, W - src_crop_w))

            filter_complex = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=disable,"
                f"crop={src_crop_w}:{H}:{fc_x}:0,"
                f"scale={SW}:{SH},setsar=1,fps={FPS}[vfinal]"
            )
    else:
        filter_complex = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=disable,split=2[va][vb];"
            f"[va]scale={SW}:-2[main];"
            f"[vb]scale={SW}:{SH},boxblur=20:5[blur];"
            f"[blur][main]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={FPS}[vfinal]"
        )

    run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(frame_png),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", filter_complex,
        "-map", "[vfinal]", "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        str(out),
    ], desc=f"freeze frame 9:16 ({duration}s)")
    frame_png.unlink(missing_ok=True)


def concat_segments(parts: list[Path], out: Path) -> None:
    """Concatena segmentos em ordem via concat demuxer."""
    list_file = out.with_suffix(".txt")
    with open(list_file, "w") as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy",
        str(out),
    ], desc=f"concat → {out.name}")
    list_file.unlink(missing_ok=True)


# -------------------------------------------------------------------
# Build por nutella
# -------------------------------------------------------------------

def build_nutella(
    n: dict,
    source: Path,
    live_num: str,
    cuts_dir: Path,
    tmp_dir: Path,
    shared: dict,   # cache de segmentos preparados
    make_shorts: bool,
    font: str | None,
) -> dict:
    rank       = n["rank"]
    seo_slug   = slugify(n["titulo_seo"])
    raw_short_title = n.get("titulo_shorts", "") or ""
    if raw_short_title.upper() in ("", "N/A", "NA", "-"):
        raw_short_title = n["titulo_ctr"]
    short_slug = slugify(raw_short_title)

    start = t2s(n["clip_entrada"])
    end   = t2s(n["clip_saida"])

    print(f"\n── Nutella #{rank} [{n['clip_entrada']} → {n['clip_saida']}]")

    # ── 16:9 ───────────────────────────────────────────────────────
    name_h = f"live{live_num}_{rank:02d}_{seo_slug}.mp4"
    out_h  = cuts_dir / name_h

    if not out_h.exists():
        clip_h = tmp_dir / f"nut_{rank}_clip_16x9.mp4"
        badge = generate_badge(live_num, tmp_dir)
        compose_clip(source, start, end, clip_h, W, H, badge_path=badge)

        if "intro_1080" not in shared:
            shared["intro_1080"] = tmp_dir / "intro_1080.mp4"
            prepare_segment(INTRO, shared["intro_1080"], W, H, is_source_4k=True)

        if "cta_1080" not in shared:
            shared["cta_1080"] = tmp_dir / "cta_1080.mp4"
            prepare_segment(CTA, shared["cta_1080"], W, H)

        concat_segments([shared["intro_1080"], clip_h, shared["cta_1080"]], out_h)
        print(f"  ✓ 16:9 → {name_h}")
    else:
        print(f"  → {name_h} já existe, pulando")

    # ── 9:16 Shorts ────────────────────────────────────────────────
    name_s = f"live{live_num}_{rank:02d}_short_{short_slug}.mp4"
    out_s  = cuts_dir / name_s

    shorts_possivel = n.get("shorts_possivel", True)
    if make_shorts and shorts_possivel and not out_s.exists():
        s_start = t2s(n.get("shorts_entrada") or n["clip_entrada"])
        s_end   = t2s(n.get("shorts_saida")   or n["clip_saida"])

        layout = detect_layout(source, s_start, s_end)

        # Freeze frame do melhor momento → frame 0 = capa do Short no YouTube
        freeze_s = tmp_dir / f"nut_{rank}_freeze.mp4"
        make_freeze_frame(source, layout.get("best_frame_sec", s_start),
                          layout, freeze_s, tmp_dir)

        # Clip 9:16 composto (vai para temp, não direto no out_s)
        clip_s = tmp_dir / f"nut_{rank}_clip_9x16.mp4"
        compose_clip(source, s_start, s_end, clip_s,
                     SW, SH, layout=layout, crop_mode=True)

        # Concat: [freeze] + [clip] → Short final
        concat_segments([freeze_s, clip_s], out_s)
        print(f"  ✓ 9:16 → {name_s}")
    elif not make_shorts or not shorts_possivel:
        if not shorts_possivel:
            print(f"  ⊘ Short pulado (shorts_possivel=false)")
        name_s = None
    else:
        print(f"  → {name_s} já existe, pulando")

    # ── Meta JSON ──────────────────────────────────────────────────
    meta_name = f"live{live_num}_{rank:02d}_meta.json"
    meta_path = cuts_dir / meta_name
    meta = {
        "rank": rank,
        "titulo_seo":    n["titulo_seo"],
        "titulo_ctr":    n["titulo_ctr"],
        "titulo_shorts": n.get("titulo_shorts", ""),
        "thumbnail_texto":      n.get("thumbnail_texto", ""),
        "thumbnail_composicao": n.get("thumbnail_composicao", ""),
        "expressao_julio":      n.get("expressao_julio", ""),
        "thumbnail_pairing":    n.get("thumbnail_pairing", ""),
        "por_que_viraliza":     n.get("por_que_viraliza", ""),
        "hook_transcricao":     n.get("hook_transcricao", ""),
        "tags_especificas":     n.get("tags_especificas", []),
        "descricao_curta":      n.get("descricao_curta", ""),
        "clip": {
            "entrada": n["clip_entrada"],
            "saida":   n["clip_saida"],
            "arquivo": name_h,
        },
        "shorts": {
            "entrada": n.get("shorts_entrada", ""),
            "saida":   n.get("shorts_saida", ""),
            "arquivo": name_s or "",
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


# -------------------------------------------------------------------
# Custom build (corte manual por timestamp)
# -------------------------------------------------------------------

def run_custom_build(video_id: str, clip_entrada: str, clip_saida: str,
                     title: str = "Corte Manual", thumb_text: str = "",
                     progress_cb=None):
    """Build a custom clip from manual timestamps."""
    import json as _json
    import tempfile as _tempfile
    import shutil as _shutil

    def emit(step, msg):
        if progress_cb:
            progress_cb({"step": step, "message": msg})

    # Step 1: Download
    emit("download", "Baixando video...")
    source = download_video(video_id)
    emit("download", f"Video baixado: {source.name}")

    # Step 2: Setup output dirs
    cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
    cuts_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(_tempfile.mkdtemp(prefix="nutella_custom_"))

    # Step 3: Create manual nutella entry
    manual_nutella = {
        "rank": 99,
        "titulo_seo": title,
        "titulo_ctr": title,
        "titulo_shorts": title,
        "texto_thumb": thumb_text or title,
        "clip_entrada": clip_entrada,
        "clip_saida": clip_saida,
        "shorts_entrada": clip_entrada,
        "shorts_saida": clip_saida,
        "hook_second": clip_entrada,
        "por_que_viraliza": "Corte manual solicitado pelo time",
        "tipo": "manual",
    }

    # Step 4: Get live number
    live_num = get_live_number(video_id)

    # Step 5: Detect font
    font = find_font()

    # Step 6: Build using existing pipeline
    emit("build", f"Cortando {clip_entrada} - {clip_saida}...")
    shared = {}

    try:
        build_nutella(manual_nutella, source, live_num, cuts_dir, tmp_dir, shared, True, font)
    finally:
        _shutil.rmtree(tmp_dir, ignore_errors=True)

    emit("complete", f"Corte manual pronto: {title}")

    # Step 7: Save manual entry to nutellas JSON
    json_path = OUTPUT_DIR / f"{video_id}_nutellas.json"
    if json_path.exists():
        data = _json.loads(json_path.read_text(encoding="utf-8"))
        data.setdefault("nutellas", [])
        # Remove existing rank 99 entry (replace with new one)
        data["nutellas"] = [n for n in data["nutellas"] if n.get("rank") != 99]
        data["nutellas"].append(manual_nutella)
        json_path.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        # Create minimal JSON so review screen can find the cut
        data = {
            "video_id": video_id,
            "video_title": title,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "generated_at": __import__("datetime").datetime.now().isoformat(),
            "segments_total": 0,
            "nutellas": [manual_nutella],
        }
        OUTPUT_DIR.mkdir(exist_ok=True)
        json_path.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build completo de nutellas")
    parser.add_argument("input", help="JSON gerado pelo suggest.py")
    parser.add_argument("--ranks", help="Nutellas específicas, ex: 1,2,3")
    parser.add_argument("--no-shorts", action="store_true", help="Pula versão 9:16")
    parser.add_argument("--no-download", action="store_true", help="Usa vídeo já baixado")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {args.input}")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    video_id = data["video_id"]
    nutellas = data["nutellas"]

    if args.ranks:
        wanted = {int(r) for r in args.ranks.split(",")}
        nutellas = [n for n in nutellas if n["rank"] in wanted]

    make_shorts = not args.no_shorts
    font = find_font()
    if font:
        print(f"Font: {font}")
    else:
        print("Font: sistema (drawtext sem fontfile)")

    # Download
    if args.no_download:
        existing = list(DOWNLOADS_DIR.glob(f"{video_id}.*"))
        if not existing:
            print(f"Vídeo não encontrado em downloads/. Rode sem --no-download.")
            sys.exit(1)
        source = existing[0]
        print(f"Usando vídeo local: {source.name}")
    else:
        source = download_video(video_id)

    # Número da live para nomenclatura
    live_num = get_live_number(video_id)
    print(f"Live: {live_num} | Vídeo: {video_id}")

    # Pasta de saída dos cortes
    cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
    cuts_dir.mkdir(parents=True, exist_ok=True)

    # Pasta temporária (limpa ao final)
    tmp_dir = Path(tempfile.mkdtemp(prefix="nutella_build_"))
    print(f"Temp: {tmp_dir}")

    shared = {}  # cache de segmentos reutilizáveis (intro, CTA)
    results = []

    try:
        for n in nutellas:
            meta = build_nutella(
                n, source, live_num, cuts_dir, tmp_dir,
                shared, make_shorts, font,
            )
            results.append(meta)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{'='*60}")
    print(f"CONCLUÍDO — {len(results)} nutellas em {cuts_dir}")
    print(f"{'='*60}")
    for r in results:
        print(f"  #{r['rank']} {r['clip']['arquivo']}")
        if r["shorts"]["arquivo"]:
            print(f"       {r['shorts']['arquivo']}")
    print(f"\nPróximo: gerar thumbnails")
    print(f"  cd ../thumbnail-ai-creator && python3 generate.py ...")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
