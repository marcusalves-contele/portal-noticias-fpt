#!/usr/bin/env python3
"""
Nutella Dashboard v2 — Pipeline completo: URL → Análise → Build → Review → Upload.

Servidor HTTP local com:
- API REST para cada etapa do pipeline
- SSE (Server-Sent Events) para progresso em tempo real
- Estado persistido em state.json (não localStorage)
- Frontend profissional servido de static/

Uso:
  python3 dashboard.py                    # Abre dashboard na tela inicial
  python3 dashboard.py --port 8800        # Porta custom
"""

import os
import sys
import json
import uuid
import argparse
import threading
import http.server
import webbrowser
import time
import io
import re
import queue
import base64
import email.parser
import email.policy
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR  = PROJECT_DIR / "output"
STATIC_DIR  = PROJECT_DIR / "static"
VERSION     = (PROJECT_DIR / "VERSION").read_text().strip() if (PROJECT_DIR / "VERSION").exists() else "dev"

# Progress queues per job
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _cleanup_old_jobs():
    """Remove completed/errored jobs older than 5 minutes."""
    while True:
        time.sleep(60)
        cutoff = time.time() - 300
        with _jobs_lock:
            to_remove = [jid for jid, j in _jobs.items()
                        if j["status"] in ("complete", "error") and j["created"] < cutoff]
            for jid in to_remove:
                del _jobs[jid]

threading.Thread(target=_cleanup_old_jobs, daemon=True).start()

# Per-directory locks for state.json atomicity
_state_locks: dict[str, threading.Lock] = {}
_state_locks_lock = threading.Lock()


def _get_state_lock(cuts_dir: Path) -> threading.Lock:
    key = str(cuts_dir)
    with _state_locks_lock:
        if key not in _state_locks:
            _state_locks[key] = threading.Lock()
        return _state_locks[key]


# -------------------------------------------------------------------
# Pipeline functions (import from existing scripts)
# -------------------------------------------------------------------

def run_analyze(url: str, job_id: str):
    """Roda suggest.py pipeline e reporta progresso."""
    try:
        _emit(job_id, "progress", {"step": "transcript", "message": "Buscando transcrição..."})
        from suggest import extract_video_id, get_transcript_with_timestamps, build_transcript_text
        from suggest import call_gemini, load_api_key, save_output

        video_id = extract_video_id(url)
        _emit(job_id, "progress", {"step": "transcript", "message": f"Transcrição de {video_id}..."})

        # Busca título do vídeo via yt-dlp
        video_title = ""
        try:
            import subprocess as _sp
            r = _sp.run(
                ["yt-dlp", "--get-title", f"https://youtube.com/watch?v={video_id}"],
                capture_output=True, text=True, timeout=15
            )
            video_title = r.stdout.strip()
        except Exception:
            pass

        segments = get_transcript_with_timestamps(video_id)
        transcript_text = build_transcript_text(segments, chunk_size=90)
        if len(transcript_text) > 22000:
            transcript_text = transcript_text[:22000] + "\n[...transcrição truncada...]"

        _emit(job_id, "progress", {
            "step": "analysis",
            "message": f"Analisando com IA ({len(segments)} segmentos)..."
        })

        api_key = load_api_key()
        from suggest import NUTELLA_PROMPT
        prompt = NUTELLA_PROMPT.format(transcript=transcript_text)
        raw = call_gemini(api_key, prompt)

        json_match = re.search(r"\[[\s\S]*\]", raw)
        if not json_match:
            _emit(job_id, "error", {"message": "IA não retornou JSON válido"})
            return

        nutellas = json.loads(json_match.group())

        result = {
            "video_id": video_id,
            "video_title": video_title,
            "youtube_url": f"https://youtube.com/watch?v={video_id}",
            "generated_at": datetime.now().isoformat(),
            "segments_total": len(segments),
            "nutellas": nutellas,
        }

        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / f"{video_id}_nutellas.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        _emit(job_id, "complete", {
            "video_id": video_id,
            "count": len(nutellas),
            "path": str(out_path),
        })

    except Exception as e:
        _emit(job_id, "error", {"message": str(e)})


def run_build(video_id: str, ranks: list[int], job_id: str):
    """Roda build.py pipeline e reporta progresso."""
    try:
        json_path = OUTPUT_DIR / f"{video_id}_nutellas.json"
        if not json_path.exists():
            _emit(job_id, "error", {"message": f"JSON não encontrado: {json_path}"})
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        nutellas = data["nutellas"]
        if ranks:
            nutellas = [n for n in nutellas if n["rank"] in ranks]

        if not nutellas:
            _emit(job_id, "error", {"message": "Nenhuma nutella selecionada"})
            return

        from build import (download_video, get_live_number, build_nutella,
                          find_font, DOWNLOADS_DIR, OUTPUT_DIR as BUILD_OUT)
        import tempfile
        import shutil

        _emit(job_id, "progress", {"step": "download", "message": "Baixando vídeo..."})
        source = download_video(video_id)

        live_num = get_live_number(video_id)
        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
        cuts_dir.mkdir(parents=True, exist_ok=True)

        tmp_dir = Path(tempfile.mkdtemp(prefix="nutella_build_"))
        font = find_font()
        shared = {}
        results = []

        try:
            for i, n in enumerate(nutellas):
                _emit(job_id, "progress", {
                    "step": "build",
                    "message": f"Construindo #{n['rank']} ({i+1}/{len(nutellas)})...",
                    "current": i + 1,
                    "total": len(nutellas),
                })
                meta = build_nutella(n, source, live_num, cuts_dir, tmp_dir,
                                    shared, True, font)
                results.append(meta)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        _emit(job_id, "complete", {
            "video_id": video_id,
            "count": len(results),
            "cuts_dir": str(cuts_dir),
        })

    except Exception as e:
        _emit(job_id, "error", {"message": str(e)})


# -------------------------------------------------------------------
# Job/Progress management
# -------------------------------------------------------------------

def _create_job() -> str:
    job_id = str(uuid.uuid4())[:8]
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "events": queue.Queue(),
            "created": time.time(),
        }
    return job_id


def _emit(job_id: str, event_type: str, data: dict):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job:
            job["events"].put({"type": event_type, "data": data})
            if event_type in ("complete", "error"):
                job["status"] = event_type


# -------------------------------------------------------------------
# State management
# -------------------------------------------------------------------

def load_state(cuts_dir: Path) -> dict:
    state_path = cuts_dir / "state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(cuts_dir: Path, state: dict):
    state_path = cuts_dir / "state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def update_state(cuts_dir: Path, updates: dict) -> dict:
    """Atomically read-modify-write state.json."""
    lock = _get_state_lock(cuts_dir)
    with lock:
        state = load_state(cuts_dir)
        state.update(updates)
        save_state(cuts_dir, state)
        return state


def load_metas(cuts_dir: Path) -> list[dict]:
    metas = []
    for f in sorted(cuts_dir.glob("*_meta.json")):
        with open(f, encoding="utf-8") as fh:
            metas.append(json.load(fh))
    return metas


def find_thumb(cuts_dir: Path, meta: dict) -> str | None:
    rank = meta["rank"]
    clip_name = meta["clip"]["arquivo"]
    parts = clip_name.split("_")
    live_num = parts[0].replace("live", "") if parts else "0"

    new_thumb = cuts_dir / f"live{live_num}_{rank:02d}_thumb.png"
    if new_thumb.exists():
        return new_thumb.name

    versioned = sorted(cuts_dir.glob(f"live*_{rank:02d}_thumb_v*.png"))
    return versioned[0].name if versioned else None


# -------------------------------------------------------------------
# HTTP Handler
# -------------------------------------------------------------------

class DashboardHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def _check_auth(self):
        """Check Google OAuth session cookie."""
        from auth import is_authenticated, oauth_configured
        if not oauth_configured():
            return True  # No OAuth configured = allow all (local dev)
        user = is_authenticated(self)
        if user:
            return True
        # Not authenticated
        parsed = urlparse(self.path)
        path = parsed.path
        # Allow auth routes, static assets, favicon, feedback
        if path.startswith("/auth/") or path == "/login" or path == "/favicon.svg" or path == "/favicon.ico" or path == "/api/feedback":
            return True
        # API calls get 401
        if path.startswith("/api/"):
            self._json({"error": "unauthorized"}, 401)
            return False
        # Everything else: redirect to login
        self.send_response(302)
        self.send_header("Location", "/login")
        self.end_headers()
        return False

    def do_GET(self):
        if not self._check_auth():
            return

        parsed = urlparse(self.path)
        path = parsed.path

        # Auth routes
        if path == "/login":
            login_file = STATIC_DIR / "login.html"
            if login_file.exists():
                self._serve_file(login_file)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Login</h1><a href='/auth/login'>Login with Google</a>")
            return
        elif path == "/auth/login":
            from auth import get_login_url, oauth_configured
            if not oauth_configured():
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
                return
            # Build redirect URI
            host = self.headers.get("Host", "localhost:8765")
            scheme = "https" if os.environ.get("RAILWAY_ENVIRONMENT") else "http"
            redirect_uri = f"{scheme}://{host}/auth/callback"
            url = get_login_url(redirect_uri)
            self.send_response(302)
            self.send_header("Location", url)
            self.end_headers()
            return
        elif path == "/auth/callback":
            from auth import exchange_code, is_email_allowed, create_session_cookie, COOKIE_NAME, COOKIE_MAX_AGE
            qs = parse_qs(parsed.query)
            code = qs.get("code", [None])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter")
                return
            host = self.headers.get("Host", "localhost:8765")
            scheme = "https" if os.environ.get("RAILWAY_ENVIRONMENT") else "http"
            redirect_uri = f"{scheme}://{host}/auth/callback"
            user = exchange_code(code, redirect_uri)
            if not user:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"OAuth exchange failed")
                return
            email = user.get("email", "")
            if not is_email_allowed(email):
                self.send_response(403)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Acesso restrito ao dominio contele.com.br</h2><a href='/login'>Tentar novamente</a>")
                return
            cookie = create_session_cookie(email, user.get("name", ""))
            is_prod = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
            cookie_attrs = f"{COOKIE_NAME}={cookie}; Path=/; Max-Age={COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax"
            if is_prod:
                cookie_attrs += "; Secure"
            self.send_response(302)
            self.send_header("Set-Cookie", cookie_attrs)
            self.send_header("Location", "/")
            self.end_headers()
            return
        elif path == "/auth/logout":
            from auth import COOKIE_NAME
            self.send_response(302)
            self.send_header("Set-Cookie", f"{COOKIE_NAME}=; Path=/; Max-Age=0")
            self.send_header("Location", "/login")
            self.end_headers()
            return

        # API routes
        if path == "/api/health":
            self._json({"ok": True})
        elif path == "/api/version":
            self._json({"version": VERSION, "changelog": "https://github.com/contele/growth/releases"})
        elif path == "/api/videos":
            self._handle_list_videos()
        elif path == "/api/video-title":
            self._handle_video_title(parsed.query)
        elif path == "/api/thumb-queue":
            self._handle_thumb_queue()
        elif path == "/api/studio/sessions":
            from studio_chat import list_sessions
            self._json({"sessions": list_sessions()})
        elif path.startswith("/api/studio/session/"):
            session_id = path.split("/api/studio/session/")[1]
            from studio_chat import get_session
            msgs = get_session(session_id)
            # Strip image data, keep URLs
            clean = []
            for m in msgs:
                entry = {"role": m["role"], "text": m.get("text", ""), "ts": m.get("ts", 0)}
                if m.get("image_path"):
                    p = Path(m["image_path"])
                    entry["image_url"] = f"/output/{p.name}" if p.exists() else None
                clean.append(entry)
            self._json({"session_id": session_id, "messages": clean})
        elif path == "/api/thumb-guest-check":
            self._handle_thumb_guest_check(parsed.query)
        elif path.startswith("/api/metas/"):
            video_id = path.split("/api/metas/")[1]
            self._handle_get_metas(video_id)
        elif path.startswith("/api/progress/"):
            job_id = path.split("/api/progress/")[1]
            self._handle_sse(job_id)
        elif path.startswith("/thumb-refs/"):
            # Serve guest reference photos from thumbnail-ai-creator/referencias/
            rel_path = path[len("/thumb-refs/"):]
            refs_dir = PROJECT_DIR.parent / "thumbnail-ai-creator" / "referencias"
            file_path = (refs_dir / rel_path).resolve()
            # Safety: ensure path stays inside refs_dir
            if str(file_path).startswith(str(refs_dir.resolve())) and file_path.exists() and file_path.is_file():
                self._serve_file(file_path)
            else:
                self._json({"error": "not found"}, 404)
        elif path.startswith("/output/"):
            # Serve files from output directory
            rel_path = path[len("/output/"):]
            file_path = (OUTPUT_DIR / rel_path).resolve()
            # Safety: ensure path stays inside OUTPUT_DIR
            if str(file_path).startswith(str(OUTPUT_DIR.resolve())) and file_path.exists() and file_path.is_file():
                self._serve_file(file_path)
            else:
                self._json({"error": "not found"}, 404)
        elif path == "/api/studio/knowledge":
            from knowledge_base import list_knowledge, get_tokens_summary
            parsed_qs = parse_qs(parsed.query)
            mode = parsed_qs.get("mode", ["question"])[0]
            self._json({
                "docs": list_knowledge(),
                "summary": get_tokens_summary(mode),
            })
        elif path == "/api/studio/memories":
            from knowledge_base import list_memories
            self._json({"memories": list_memories()})
        else:
            # Serve static files (frontend)
            if path == "/" or path == "":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        if not self._check_auth():
            return

        path = urlparse(self.path).path
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))

        # Multipart (file upload)
        if content_type.startswith("multipart/form-data"):
            if path == "/api/thumb-upload-guest":
                raw = self.rfile.read(length)
                self._handle_thumb_upload_guest_multipart(raw, content_type)
                return
            self._json({"error": "not found"}, 404)
            return

        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception:
            self._json({"error": "invalid JSON"}, 400)
            return

        if path == "/api/analyze":
            self._handle_analyze(body)
        elif path == "/api/auto-briefing":
            self._handle_auto_briefing(body)
        elif path == "/api/build":
            self._handle_build(body)
        elif path == "/api/build-custom":
            self._handle_build_custom(body)
        elif path == "/api/approve":
            self._handle_approve(body)
        elif path == "/api/generate-thumb":
            self._handle_generate_thumb(body)
        elif path == "/api/regenerate-thumb":
            self._handle_regenerate_thumb(body)
        elif path == "/api/upload-youtube":
            self._handle_upload(body)
        elif path == "/api/generate-titles":
            self._handle_generate_titles(body)
        elif path == "/api/briefing-from-text":
            self._handle_briefing_from_text(body)
        elif path == "/api/thumb-transcribe":
            self._handle_thumb_transcribe(body)
        elif path == "/api/thumb-generate":
            self._handle_thumb_generate(body)
        elif path == "/api/thumb-feedback":
            self._handle_thumb_feedback(body)
        elif path == "/api/thumb-approve":
            self._handle_thumb_approve(body)
        elif path == "/api/thumb-drive-upload":
            self._handle_thumb_drive_upload(body)
        elif path == "/api/upload-drive":
            self._handle_upload_drive(body)
        elif path == "/api/youtube-update-title":
            self._handle_youtube_update_title(body)
        elif path == "/api/youtube-update-thumb":
            self._handle_youtube_update_thumb(body)
        elif path == "/api/feedback":
            self._handle_feedback(body)
        elif path == "/api/studio/chat":
            self._handle_studio_chat(body)
        elif path.startswith("/api/studio/session/") and path.endswith("/delete"):
            session_id = path.split("/api/studio/session/")[1].removesuffix("/delete")
            from studio_chat import delete_session
            deleted = delete_session(session_id)
            self._json({"ok": True, "deleted": deleted})
        elif path == "/api/studio/knowledge/toggle":
            from knowledge_base import set_flag
            doc_id = body.get("doc_id", "")
            enabled = body.get("enabled", True)
            set_flag(doc_id, enabled)
            self._json({"ok": True, "doc_id": doc_id, "enabled": enabled})
        elif path == "/api/studio/feedback":
            from knowledge_base import add_memory
            feedback_type = body.get("type", "feedback")  # approval, rejection, feedback
            content = body.get("content", "")
            metadata = body.get("metadata", {})
            if content:
                add_memory(feedback_type, content, metadata)
            self._json({"ok": True})
        elif path == "/api/blog-generate":
            self._handle_blog_generate(body)
        else:
            self._json({"error": "not found"}, 404)

    # --- API Handlers ---

    def _handle_list_videos(self):
        """Lista todos os vídeos processados."""
        videos = []
        if OUTPUT_DIR.exists():
            for f in sorted(OUTPUT_DIR.glob("*_nutellas.json"), reverse=True):
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                video_id = data["video_id"]
                cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
                has_cuts = cuts_dir.exists() and any(cuts_dir.glob("*.mp4"))
                # Verifica se todos os clips foram enviados pro YouTube
                all_uploaded = False
                if has_cuts:
                    state = load_state(cuts_dir)
                    num_nutellas = len(data.get("nutellas", []))
                    uploaded_count = sum(1 for k, v in state.items()
                                        if not k.startswith("_") and v == "uploaded")
                    all_uploaded = num_nutellas > 0 and uploaded_count >= num_nutellas
                videos.append({
                    "video_id": video_id,
                    "video_title": data.get("video_title", ""),
                    "url": data.get("youtube_url", ""),
                    "generated_at": data.get("generated_at", ""),
                    "nutellas_count": len(data.get("nutellas", [])),
                    "has_cuts": has_cuts,
                    "all_uploaded": all_uploaded,
                })
        self._json({"videos": videos})

    def _handle_get_metas(self, video_id: str):
        """Retorna metas + state + thumbs para um vídeo."""
        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"

        # Check if we have nutellas JSON but no cuts yet
        nutellas_json = OUTPUT_DIR / f"{video_id}_nutellas.json"
        nutellas = []
        if nutellas_json.exists():
            with open(nutellas_json, encoding="utf-8") as f:
                data = json.load(f)
            nutellas = data.get("nutellas", [])

        metas = []
        thumbs = {}
        state = {}

        if cuts_dir.exists():
            metas = load_metas(cuts_dir)
            state = load_state(cuts_dir)
            for m in metas:
                t = find_thumb(cuts_dir, m)
                if t:
                    thumbs[str(m["rank"])] = t

        self._json({
            "video_id": video_id,
            "nutellas": nutellas,
            "metas": metas,
            "state": state,
            "thumbs": thumbs,
            "has_cuts": len(metas) > 0,
        })

    def _handle_analyze(self, body):
        url = body.get("url", "").strip()
        if not url:
            self._json({"error": "URL required"}, 400)
            return

        job_id = _create_job()
        thread = threading.Thread(target=run_analyze, args=(url, job_id), daemon=True)
        thread.start()
        self._json({"job_id": job_id})

    def _handle_build(self, body):
        video_id = body.get("video_id", "")
        ranks = body.get("ranks", [])
        if not video_id:
            self._json({"error": "video_id required"}, 400)
            return

        job_id = _create_job()
        thread = threading.Thread(target=run_build, args=(video_id, ranks, job_id), daemon=True)
        thread.start()
        self._json({"job_id": job_id})

    def _handle_build_custom(self, body: dict):
        """POST /api/build-custom - corte manual por timestamp."""
        video_url    = body.get("video_url", "").strip()
        clip_entrada = body.get("clip_entrada", "").strip()
        clip_saida   = body.get("clip_saida", "").strip()
        title        = body.get("title", "Corte Manual").strip()
        thumb_text   = body.get("thumb_text", "").strip()

        # Extract video_id from URL
        video_id = None
        m = re.search(r'(?:v=|youtu\.be/|live/)([a-zA-Z0-9_-]{11})', video_url)
        if m:
            video_id = m.group(1)

        if not video_id:
            self._json({"error": "URL do YouTube invalida"}, 400)
            return

        if not clip_entrada or not clip_saida:
            self._json({"error": "Timestamps de inicio e fim sao obrigatorios"}, 400)
            return

        # Validate timestamp format (MM:SS or HH:MM:SS)
        def valid_ts(ts):
            return bool(re.match(r'^(\d{1,2}:)?\d{1,2}:\d{2}$', ts))

        if not valid_ts(clip_entrada) or not valid_ts(clip_saida):
            self._json({"error": "Formato de timestamp invalido. Use MM:SS ou HH:MM:SS"}, 400)
            return

        job_id = _create_job()
        self._json({"job_id": job_id, "video_id": video_id})

        def _run():
            try:
                import sys
                print(f"[build-custom] Starting: {video_id} {clip_entrada}-{clip_saida}", flush=True)
                _emit(job_id, "progress", {"step": "init", "message": f"Preparando corte {clip_entrada} - {clip_saida}..."})
                from build import run_custom_build
                print(f"[build-custom] Module loaded, calling run_custom_build", flush=True)
                _emit(job_id, "progress", {"step": "download", "message": "Iniciando download do video..."})
                run_custom_build(
                    video_id=video_id,
                    clip_entrada=clip_entrada,
                    clip_saida=clip_saida,
                    title=title,
                    thumb_text=thumb_text,
                    progress_cb=lambda data: _emit(job_id, "progress", data),
                )
                _emit(job_id, "complete", {
                    "video_id": video_id,
                    "message": f"Corte manual pronto: {clip_entrada} - {clip_saida}",
                })
            except RuntimeError as e:
                msg = str(e)
                print(f"[build-custom] ERROR: {msg}", flush=True)
                _emit(job_id, "error", {"message": msg})
            except Exception as e:
                msg = str(e)
                print(f"[build-custom] ERROR: {msg}", flush=True)
                # Mensagens mais claras para erros comuns
                if "timeout" in msg.lower():
                    msg = "Download travou (timeout). Tente novamente em alguns minutos."
                elif "403" in msg or "forbidden" in msg.lower():
                    msg = "YouTube bloqueou o acesso. Tente novamente em 5 minutos."
                _emit(job_id, "error", {"message": msg})

        threading.Thread(target=_run, daemon=True).start()

    def _handle_approve(self, body):
        video_id = body.get("video_id", "")
        rank = body.get("rank")
        status = body.get("status", "")  # approved, rejected, pending

        if not video_id or rank is None:
            self._json({"error": "video_id and rank required"}, 400)
            return

        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
        if not cuts_dir.exists():
            cuts_dir.mkdir(parents=True, exist_ok=True)

        lock = _get_state_lock(cuts_dir)
        with lock:
            state = load_state(cuts_dir)
            if status == "pending":
                state.pop(str(rank), None)
            else:
                state[str(rank)] = status
            save_state(cuts_dir, state)

        self._json({"ok": True, "state": state})

    def _handle_generate_thumb(self, body):
        video_id = body.get("video_id", "")
        rank = body.get("rank")

        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
        metas = load_metas(cuts_dir)
        meta = next((m for m in metas if m["rank"] == rank), None)

        if not meta:
            self._json({"error": f"rank {rank} not found"}, 404)
            return

        from gen_thumb import generate_single, load_api_key
        api_key = load_api_key()
        result = generate_single(meta, cuts_dir, api_key)

        if result:
            self._json({"thumb": result.name})
        else:
            self._json({"error": "generation failed"}, 500)

    def _handle_regenerate_thumb(self, body):
        video_id = body.get("video_id", "")
        rank = body.get("rank")
        feedback = body.get("feedback", "")

        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
        metas = load_metas(cuts_dir)
        meta = next((m for m in metas if m["rank"] == rank), None)

        if not meta:
            self._json({"error": f"rank {rank} not found"}, 404)
            return

        from gen_thumb import generate_single, load_api_key
        api_key = load_api_key()
        result = generate_single(meta, cuts_dir, api_key, feedback=feedback)

        if result:
            self._json({"thumb": result.name})
        else:
            self._json({"error": "regeneration failed"}, 500)

    def _handle_upload(self, body):
        video_id = body.get("video_id", "")
        ranks = body.get("ranks", [])
        privacy = body.get("privacy", "unlisted")
        schedule = body.get("schedule", False)

        cuts_dir = OUTPUT_DIR / f"{video_id}_cuts"
        metas = load_metas(cuts_dir)
        selected = [m for m in metas if m["rank"] in ranks]

        if not selected:
            self._json({"error": "no valid ranks"}, 400)
            return

        from upload import (load_credentials, get_youtube, upload_nutella,
                            upload_short, get_best_publish_times)
        try:
            creds = load_credentials()
            youtube = get_youtube(creds)
        except Exception as e:
            self._json({"error": f"auth failed: {e}"}, 500)
            return

        source_video_id = video_id

        # Slots data-driven: clips em qui/sex, shorts em ter/seg (jamais quarta)
        clip_times  = []
        short_times = []
        if schedule:
            times = get_best_publish_times(youtube, len(selected), len(selected))
            clip_times  = times["clips"]
            short_times = times["shorts"]
            privacy = "private"

        results = []
        errors = []
        for i, meta in enumerate(selected):
            rank = meta["rank"]
            clip_result = None
            short_result = None

            # Clip 16:9
            pub_time = clip_times[i] if schedule and i < len(clip_times) else None
            try:
                clip_result = upload_nutella(
                    meta, cuts_dir, youtube,
                    privacy=privacy, publish_at=pub_time,
                    source_video_id=source_video_id,
                )
                if clip_result:
                    results.append(clip_result)
                else:
                    errors.append(f"#{rank} failed")
            except Exception as e:
                errors.append(f"#{rank}: {e}")

            # Short 9:16
            pub_time_s = short_times[i] if schedule and i < len(short_times) else None
            try:
                short_result = upload_short(
                    meta, cuts_dir, youtube,
                    privacy=privacy, publish_at=pub_time_s,
                    source_video_id=source_video_id,
                )
                if short_result:
                    results.append(short_result)
            except Exception as e:
                errors.append(f"#{rank} short: {e}")

            # Persiste estado "uploaded" no state.json (atomic)
            if clip_result:
                upload_info = {
                    "clip_url":      clip_result.get("url", ""),
                    "clip_schedule": clip_result.get("publish_at", ""),
                    "short_url":     short_result.get("url", "") if short_result else "",
                    "short_schedule": short_result.get("publish_at", "") if short_result else "",
                }
                lock = _get_state_lock(cuts_dir)
                with lock:
                    state = load_state(cuts_dir)
                    state[str(rank)] = "uploaded"
                    uploads = state.setdefault("_uploads", {})
                    uploads[str(rank)] = upload_info
                    save_state(cuts_dir, state)

        self._json({"uploaded": results, "errors": errors})

    # --- Video title ---

    def _handle_video_title(self, query_string: str):
        """GET /api/video-title?url=... — busca título do vídeo via yt-dlp."""
        from urllib.parse import parse_qs as _pqs
        params = _pqs(query_string)
        url = (params.get("url") or [""])[0]
        if not url:
            self._json({"error": "url required"}, 400)
            return
        try:
            from suggest import extract_video_id
            video_id = extract_video_id(url)
            import subprocess as _sp
            r = _sp.run(
                ["yt-dlp", "--get-title", f"https://youtube.com/watch?v={video_id}"],
                capture_output=True, text=True, timeout=15
            )
            title = r.stdout.strip()
            self._json({"title": title, "video_id": video_id})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    # --- Auto-briefing ---

    def _handle_auto_briefing(self, body: dict):
        """POST /api/auto-briefing — transcreve vídeo e extrai q1/q2/q3 automaticamente."""
        video_url = body.get("video_url", "").strip()
        title     = body.get("title", "")
        if not video_url:
            self._json({"error": "video_url required"}, 400)
            return
        try:
            from suggest import extract_video_id, get_transcript_with_timestamps, build_transcript_text
            from thumb_live import auto_briefing_from_transcript, load_api_key

            video_id = extract_video_id(video_url)
            segments = get_transcript_with_timestamps(video_id)
            transcript = build_transcript_text(segments, chunk_size=90)

            api_key = load_api_key()
            briefing = auto_briefing_from_transcript(transcript, title, api_key)
            self._json({"ok": True, **briefing, "transcript": transcript[:8000]})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    # --- Thumb Live Handlers ---

    def _handle_thumb_queue(self):
        """GET /api/thumb-queue — lista lives 'A Fazer' da planilha."""
        try:
            from thumb_live import fetch_queue, load_sheets_creds, load_state
            creds = load_sheets_creds()
            items = fetch_queue(creds)
            state = load_state()
            # Enriquece com estado local
            for item in items:
                live_id = item.get("_live_id", "")
                local = state.get("items", {}).get(live_id, {})
                item["_approved"] = local.get("approved", "")
            self._json({"items": items, "count": len(items)})
        except PermissionError as e:
            self._json({"error": str(e), "code": "no_sheets_scope"}, 403)
        except FileNotFoundError as e:
            self._json({"error": str(e), "code": "no_token"}, 401)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_thumb_guest_check(self, query_string: str):
        """GET /api/thumb-guest-check?title=... — detecta convidado pelo número da live."""
        from urllib.parse import parse_qs
        params  = parse_qs(query_string)
        title   = params.get("title", [""])[0]
        if not title:
            self._json({"found": False, "error": "title required"})
            return
        try:
            from thumb_live import find_guest_by_live_number
            result = find_guest_by_live_number(title)
            # Injeta preview_url para cada convidado
            if result.get("found"):
                for g in result.get("all_guests", []):
                    g["preview_url"] = f"/thumb-refs/convidados/{g['filename']}"
            self._json(result)
        except Exception as e:
            self._json({"found": False, "error": str(e)}, 500)

    def _handle_generate_titles(self, body: dict):
        """POST /api/generate-titles — gera 3 sugestões de título com estratégias diferentes."""
        q1       = body.get("q1", "")
        q2       = body.get("q2", "")
        q3       = body.get("q3", "")
        channel  = body.get("channel", "fleet")
        tema     = body.get("tema", "")
        current  = body.get("current_title", "")
        script   = body.get("script", "")  # roteiro/transcricao se disponivel

        if not q1 and not q2 and not q3 and not tema and not script:
            self._json({"error": "Preencha o briefing ou tema antes"}, 400)
            return

        channel_context = {
            "fleet": """CANAL: Frota Para Todos (FPT)
- Nicho: gestao de frotas B2B (transporte, logistica, entregas)
- Apresentador: Julio Cesar (autoridade no setor, 300+ lives)
- Publico: gestores de frota, donos de transportadora, coordenadores de logistica, diretores de operacoes
- Tom: direto, pratico, sem enrolacao. Fala como quem ja resolveu o problema
- Palavras-chave do nicho: frota, rastreamento, combustivel, manutencao, gestao de frotas, motorista, custo operacional, telemetria, abastecimento
- Concorrentes fracos no YouTube: FPT domina o nicho em portugues
- Formato tipico de titulo: frase curta que revela o beneficio ou o problema. Ex: "Como reduzir 30%% do combustivel", "O erro que custa R$5 mil por mes na sua frota"
- NUNCA usar jargao academico. Usar linguagem de quem gerencia frota no dia a dia""",
            "teams": """CANAL: Contele Teams
- Nicho: gestao de equipes externas/campo B2B
- Apresentador: Leonardo Gazolli
- Publico: gestores de equipes de campo, supervisores, donos de empresas de servicos (manutencao, limpeza, telecom, seguranca)
- Tom: moderno, tecnico mas acessivel
- Palavras-chave: equipe externa, produtividade, roteirizacao, ordem de servico, gestao de campo
- Formato tipico: foco em resultado mensuravel e dor do gestor"""
        }

        # Monta bloco de contexto do video
        video_context_parts = []
        if script:
            video_context_parts.append(f"ROTEIRO/TRANSCRICAO (trecho):\n{script[:6000]}")
        if q1:
            video_context_parts.append(f"PUBLICO-ALVO (Q1): {q1}")
        if q2:
            video_context_parts.append(f"OBJETIVO DO VIDEO (Q2): {q2}")
        if q3:
            video_context_parts.append(f"CONTEUDO DO VIDEO (Q3): {q3}")
        if tema:
            video_context_parts.append(f"TEMA: {tema}")
        if current:
            video_context_parts.append(f"TITULO ATUAL (pode melhorar): {current}")

        creative_note = body.get("creative_note", "")
        if creative_note:
            video_context_parts.append(f"DIRECAO CRIATIVA DO PRODUTOR (PRIORIDADE ALTA): {creative_note}")

        video_context = "\n".join(video_context_parts)

        prompt = f"""Voce e um diretor criativo de YouTube especializado em CTR e SEO para canais B2B.

{channel_context.get(channel, channel_context['fleet'])}

--- CONTEXTO DO VIDEO ---
{video_context}

--- SUA TAREFA ---

Gere EXATAMENTE 3 titulos para este video. Cada um com uma estrategia diferente:

1. **CTR** (strategy: "ctr")
   Maximiza cliques no feed/recomendados. Usa curiosidade, urgencia, contraste ou revelacao parcial.
   O titulo deve criar um "gap de informacao" que so se fecha assistindo.
   Funciona melhor com: numeros, superlativos, consequencias, "como/por que".

2. **SEO** (strategy: "seo")
   Otimizado para busca no YouTube e Google. Contem a palavra-chave principal de forma natural nos primeiros 40 caracteres.
   Prioriza termos que o publico realmente digita (pense como gestor de frota pesquisando).
   Funciona melhor com: "como + verbo", "o que e", "guia", palavra-chave exata.

3. **AUTORIDADE** (strategy: "authority")
   Posiciona o apresentador como referencia no assunto. Tom serio, confiante, de quem ja resolveu.
   Ideal para quem ja conhece o canal e respeita a opiniao do apresentador.
   Funciona melhor com: afirmacoes diretas, dados, perspectiva unica.

--- PASSO 1: ANTES DE ESCREVER QUALQUER TITULO ---
Leia o roteiro/transcricao e identifique:
- Numeros e dados concretos mencionados (valores, porcentagens, datas)
- Nomes proprios, eventos, lugares especificos
- O DIFERENCIAL unico deste video vs outros sobre o mesmo tema
- A emocao dominante do apresentador (medo, urgencia, oportunidade, ironia)
Cada titulo DEVE usar pelo menos um desses elementos. Titulo generico = titulo ruim.

BAD: "Como economizar combustivel na frota" (serve pra qualquer video)
GOOD: "Diesel subiu 75 centavos e voce vai pagar R$300 a mais" (so serve pra ESTE video)

--- REGRAS ABSOLUTAS ---
- Maximo 60 caracteres (YouTube CORTA apos isso, titulo fica ilegivel)
- DEVE conter dado especifico do video (numero, nome, fato)
- Portugues BR natural (como gestor de frota fala, nao como academico escreve)
- Sem emojis
- Primeira letra maiuscula, resto minusculo (exceto siglas como FPT, GPS, KM)
- NAO usar dois-pontos (reformule com virgula ou reestruture)
- NAO repetir palavras entre os 3 titulos
- O titulo COMPLEMENTA a thumbnail (nao repete). Titulo e thumb sao um PAR que funciona junto.
- "why" DEVE ter no maximo 10 palavras

--- FORMATO ---
JSON puro, sem markdown. "why" curto (max 10 palavras):
{{"titles": [{{"title": "...", "strategy": "ctr", "why": "max 10 palavras"}}, {{"title": "...", "strategy": "seo", "why": "max 10 palavras"}}, {{"title": "...", "strategy": "authority", "why": "max 10 palavras"}}]}}"""

        try:
            from thumb_live import load_api_key, FLASH_URL
            import requests as _requests

            api_key = load_api_key()
            headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

            # Retry ate 2x se JSON invalido
            for attempt in range(2):
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7 if attempt == 0 else 0.3,
                        "maxOutputTokens": 4000,
                    },
                }
                resp = _requests.post(FLASH_URL, headers=headers, json=payload, timeout=30)
                result = resp.json()

                if "candidates" not in result:
                    continue

                parts = result["candidates"][0]["content"]["parts"]
                raw = ""
                for part in parts:
                    if "text" in part:
                        raw += part["text"]
                raw = raw.strip()
                import re as _re
                # Limpa markdown code fences se existirem
                raw = _re.sub(r'^```json\s*', '', raw)
                raw = _re.sub(r'\s*```\s*$', '', raw)

                m = _re.search(r'\{[\s\S]*\}', raw)
                if m:
                    json_str = m.group()
                    # Tenta parsear, com fixes pra JSON truncado
                    data = None
                    for suffix in ['', '"}]}', '}]}', ']}']:
                        try:
                            data = json.loads(json_str + suffix)
                            break
                        except (json.JSONDecodeError, ValueError):
                            pass
                    if data and "titles" in data and len(data["titles"]) >= 2:
                        # Normaliza strategy
                        for i, t in enumerate(data["titles"]):
                            s = t.get("strategy", "").lower().strip()
                            if s not in ("ctr", "seo", "authority"):
                                s = ["ctr", "seo", "authority"][i] if i < 3 else "ctr"
                            t["strategy"] = s
                        self._json({"ok": True, **data})
                        return

            self._json({"error": "Gemini nao retornou titulos validos apos 2 tentativas"}, 500)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_briefing_from_text(self, body: dict):
        """POST /api/briefing-from-text — extrai q1/q2/q3 de roteiro/transcrição em texto."""
        text  = body.get("text", "").strip()
        title = body.get("title", "")
        if not text:
            self._json({"error": "text required"}, 400)
            return
        try:
            from thumb_live import auto_briefing_from_transcript, load_api_key
            api_key = load_api_key()
            briefing = auto_briefing_from_transcript(text, title, api_key)
            self._json({"ok": True, **briefing})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_thumb_transcribe(self, body: dict):
        """POST /api/thumb-transcribe — transcreve áudio base64, retorna q1/q2/q3."""
        audio_b64 = body.get("audio_base64", "")
        mime_type  = body.get("mime_type", "audio/m4a")
        if not audio_b64:
            self._json({"error": "audio_base64 required"}, 400)
            return
        try:
            from thumb_live import transcribe_audio, load_api_key
            api_key = load_api_key()
            audio_bytes = base64.b64decode(audio_b64)
            result = transcribe_audio(audio_bytes, api_key, mime_type)
            self._json(result)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_thumb_generate(self, body: dict):
        """POST /api/thumb-generate — inicia geração A+B, retorna job_id para SSE."""
        briefing   = body.get("briefing", {})
        live_id    = body.get("live_id", "") or f"roteiro-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        divergence = int(body.get("divergence", 6))

        job_id = _create_job()
        self._json({"job_id": job_id})   # Responde imediatamente

        def _run():
            try:
                from thumb_live import generate_ab, load_api_key, upsert_item

                api_key = load_api_key()

                upsert_item(live_id, {
                    "live_id": live_id,
                    "title": briefing.get("title", ""),
                    "channel": briefing.get("channel", "fleet"),
                    "briefing": briefing,
                    "pasta_drive": body.get("pasta_drive", ""),
                    "divergence": divergence,
                })

                def progress_cb(data: dict):
                    _emit(job_id, "progress", data)

                path_a, path_b = generate_ab(briefing, live_id, api_key, progress_cb,
                                             divergence=divergence)

                paths = {}
                if path_a:
                    paths["thumb_a"] = f"output/{path_a.name}"
                    upsert_item(live_id, {"thumb_a": f"output/{path_a.name}"})
                if path_b:
                    paths["thumb_b"] = f"output/{path_b.name}"
                    upsert_item(live_id, {"thumb_b": f"output/{path_b.name}"})

                if not paths:
                    _emit(job_id, "error", {"message": "Geração falhou para A e B"})
                else:
                    _emit(job_id, "complete", {"ok": True, **paths})

            except Exception as e:
                _emit(job_id, "error", {"message": str(e)})

        threading.Thread(target=_run, daemon=True).start()

    def _handle_thumb_feedback(self, body: dict):
        """POST /api/thumb-feedback — recebe feedback, regera 1 thumb."""
        live_id  = body.get("live_id", "")
        angle    = body.get("angle", "A")
        feedback = body.get("feedback", "")
        if not live_id or not feedback:
            self._json({"error": "live_id and feedback required"}, 400)
            return
        try:
            from thumb_live import (regenerate_one, load_api_key,
                                     load_state, add_feedback, upsert_item)
            api_key = load_api_key()
            state   = load_state()
            item    = state.get("items", {}).get(live_id, {})
            briefing = item.get("briefing", {"live_id": live_id, "channel": "fleet"})

            add_feedback(live_id, angle, feedback)
            path = regenerate_one(briefing, live_id, angle, feedback, api_key)

            if not path:
                self._json({"error": "regeneration failed"}, 500)
                return

            key = f"thumb_{angle.lower()}"
            upsert_item(live_id, {key: f"output/{path.name}"})
            self._json({"ok": True, key: f"output/{path.name}"})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_thumb_approve(self, body: dict):
        """POST /api/thumb-approve — salva aprovação."""
        live_id = body.get("live_id", "")
        choice  = body.get("choice", "")
        path    = body.get("path", "")
        if not live_id or choice not in ("A", "B"):
            self._json({"error": "live_id and choice (A|B) required"}, 400)
            return
        try:
            from thumb_live import approve_thumb
            item = approve_thumb(live_id, choice, path)
            self._json({"ok": True, "item": item})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_thumb_drive_upload(self, body: dict):
        """POST /api/thumb-drive-upload — faz upload da thumb aprovada para o Drive."""
        live_id = body.get("live_id", "")
        angle   = body.get("angle", "").upper()
        if not live_id or angle not in ("A", "B"):
            self._json({"error": "live_id and angle (A|B) required"}, 400)
            return
        try:
            from thumb_live import load_sheets_creds, load_state, upload_to_drive_folder
            state = load_state()
            item  = state.get("items", {}).get(live_id)
            if not item:
                self._json({"error": "item not found in state"}, 404)
                return

            key        = f"thumb_{angle.lower()}"
            thumb_rel  = item.get(key, "")
            if not thumb_rel:
                self._json({"error": f"thumb_{angle.lower()} not found in state"}, 404)
                return

            # Caminho absoluto — pode ser "output/..." ou path completo
            # Strip cache-busting query string (ex: "output/foo.png?t=123" → "output/foo.png")
            from pathlib import Path
            thumb_rel_clean = thumb_rel.split("?")[0]
            if Path(thumb_rel_clean).is_absolute():
                thumb_path = Path(thumb_rel_clean)
            else:
                rel = thumb_rel_clean.removeprefix("output/").lstrip("/")
                thumb_path = OUTPUT_DIR / rel
            if not thumb_path.exists():
                self._json({"error": f"arquivo não encontrado: {thumb_path}"}, 404)
                return

            folder_link = item.get("pasta_drive", "")
            if not folder_link:
                self._json({"error": "Pasta Drive não definida para este item. Verifique a planilha."}, 400)
                return

            creds  = load_sheets_creds()
            result = upload_to_drive_folder(thumb_path, folder_link, creds)
            self._json({"ok": True, "drive": result})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_upload_drive(self, body: dict):
        """POST /api/upload-drive — upload genérico de arquivo para pasta no Drive."""
        image_path = body.get("image_path", "")
        folder_id  = body.get("folder_id", "")
        filename   = body.get("filename", "")
        if not image_path or not folder_id:
            self._json({"error": "image_path and folder_id required"}, 400)
            return
        try:
            from thumb_live import load_sheets_creds, upload_to_drive_folder
            p = Path(image_path)
            if not p.is_absolute():
                p = PROJECT_DIR / p
            if not p.exists():
                self._json({"error": f"arquivo nao encontrado: {p}"}, 404)
                return

            # Se filename fornecido, renomear temporariamente para upload
            actual_path = p
            renamed = False
            if filename and filename != p.name:
                tmp = p.parent / filename
                import shutil
                shutil.copy2(p, tmp)
                actual_path = tmp
                renamed = True

            creds  = load_sheets_creds()
            result = upload_to_drive_folder(actual_path, folder_id, creds)

            if renamed and actual_path.exists():
                actual_path.unlink()

            self._json({"success": True, "link": result.get("link", ""), "drive": result})
        except FileNotFoundError as e:
            self._json({"success": False, "error": "Google Drive credentials not configured"}, 500)
        except Exception as e:
            self._json({"success": False, "error": str(e)}, 500)

    def _handle_youtube_update_title(self, body: dict):
        """POST /api/youtube-update-title — atualiza titulo de video no YouTube."""
        video_id  = body.get("video_id", "")
        new_title = body.get("new_title", "")
        if not video_id or not new_title:
            self._json({"error": "video_id and new_title required"}, 400)
            return
        try:
            from upload import load_credentials, get_youtube
            creds   = load_credentials()
            youtube = get_youtube(creds)

            # Busca snippet atual para preservar campos obrigatorios
            resp = youtube.videos().list(part="snippet", id=video_id).execute()
            items = resp.get("items", [])
            if not items:
                self._json({"success": False, "error": f"Video {video_id} nao encontrado"}, 404)
                return

            snippet = items[0]["snippet"]
            snippet["title"] = new_title
            # categoryId é obrigatório no update
            youtube.videos().update(
                part="snippet",
                body={"id": video_id, "snippet": snippet}
            ).execute()

            self._json({"success": True})
        except FileNotFoundError:
            self._json({"success": False, "error": "YouTube credentials not configured. Rode reauth_youtube_analytics.py"}, 500)
        except SystemExit:
            self._json({"success": False, "error": "YouTube token invalido. Rode reauth_youtube_analytics.py"}, 500)
        except Exception as e:
            self._json({"success": False, "error": str(e)}, 500)

    def _handle_youtube_update_thumb(self, body: dict):
        """POST /api/youtube-update-thumb — atualiza thumbnail de video no YouTube."""
        video_id   = body.get("video_id", "")
        image_path = body.get("image_path", "")
        if not video_id or not image_path:
            self._json({"error": "video_id and image_path required"}, 400)
            return
        try:
            from upload import load_credentials, get_youtube
            from googleapiclient.http import MediaFileUpload

            p = Path(image_path)
            if not p.is_absolute():
                p = PROJECT_DIR / p
            if not p.exists():
                self._json({"success": False, "error": f"arquivo nao encontrado: {p}"}, 404)
                return

            # Redimensiona se > 2MB
            if p.stat().st_size > 2 * 1024 * 1024:
                from PIL import Image
                img = Image.open(p)
                img.thumbnail((1280, 720), Image.LANCZOS)
                resized = p.parent / f"_resized_{p.name}"
                img.save(resized, quality=90)
                p = resized

            creds   = load_credentials()
            youtube = get_youtube(creds)

            media = MediaFileUpload(str(p), mimetype="image/png", resumable=False)
            youtube.thumbnails().set(videoId=video_id, media_body=media).execute()

            # Limpa arquivo temporário se redimensionado
            if p.name.startswith("_resized_") and p.exists():
                p.unlink()

            self._json({"success": True})
        except FileNotFoundError:
            self._json({"success": False, "error": "YouTube credentials not configured. Rode reauth_youtube_analytics.py"}, 500)
        except SystemExit:
            self._json({"success": False, "error": "YouTube token invalido. Rode reauth_youtube_analytics.py"}, 500)
        except Exception as e:
            self._json({"success": False, "error": str(e)}, 500)

    def _handle_thumb_upload_guest_multipart(self, raw: bytes, content_type: str):
        """POST /api/thumb-upload-guest (multipart) — salva foto de convidado."""
        try:
            boundary = ""
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part[len("boundary="):].strip('"')
                    break

            if not boundary:
                self._json({"error": "boundary not found"}, 400)
                return

            # Parse manual de multipart simples
            fields = {}
            files  = {}
            delimiter = f"--{boundary}".encode()
            parts_raw = raw.split(delimiter)

            for p in parts_raw[1:]:
                if p.strip() in (b"", b"--", b"--\r\n"):
                    continue
                # Separa headers do body
                if b"\r\n\r\n" in p:
                    header_section, file_body = p.split(b"\r\n\r\n", 1)
                    # Remove trailing --\r\n
                    file_body = file_body.rstrip(b"\r\n--")
                else:
                    continue

                header_str = header_section.decode("utf-8", errors="ignore")
                # Extrai name e filename
                name_match = re.search(r'name="([^"]+)"', header_str)
                file_match = re.search(r'filename="([^"]+)"', header_str)
                field_name = name_match.group(1) if name_match else ""

                if file_match:
                    files[field_name] = {
                        "filename": file_match.group(1),
                        "data": file_body,
                    }
                else:
                    fields[field_name] = file_body.decode("utf-8", errors="ignore").strip()

            live_id    = fields.get("live_id", "")
            guest_name = fields.get("guest_name", "Convidado")
            title_type = fields.get("title_type", "convidado")

            # Se live_id parece um YouTube video ID (não número), não serve pra save_guest_photo
            # Tenta extrair número da live do guest_name ou usa live_id como está
            import re as _re
            if not _re.match(r'^\d+$', live_id):
                # Tenta pegar do título via campo extra "title" no multipart
                title_for_num = fields.get("title", "")
                m = _re.search(r'\bLive\s+(\d+)\b', title_for_num, _re.IGNORECASE)
                if m:
                    live_id = m.group(1)

            if "photo" not in files:
                self._json({"error": "photo field required"}, 400)
                return

            photo_file = files["photo"]
            ext = "." + photo_file["filename"].rsplit(".", 1)[-1].lower() if "." in photo_file["filename"] else ".jpg"

            from thumb_live import save_guest_photo
            path = save_guest_photo(
                photo_file["data"], live_id, guest_name, title_type, ext
            )
            self._json({"ok": True, "path": str(path), "name": path.name})

        except Exception as e:
            self._json({"error": str(e)}, 500)

    # --- SSE Stream ---

    def _handle_sse(self, job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            self._json({"error": "job not found"}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            while True:
                try:
                    event = job["events"].get(timeout=30)
                    data = json.dumps(event["data"])
                    self.wfile.write(f"event: {event['type']}\ndata: {data}\n\n".encode())
                    self.wfile.flush()
                    if event["type"] in ("complete", "error"):
                        break
                except queue.Empty:
                    # Send keepalive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    # --- Helpers ---

    def _serve_file(self, file_path: Path):
        ext = file_path.suffix.lower()
        mime_map = {
            ".mp4": "video/mp4",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".json": "application/json",
            ".html": "text/html",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        stat = file_path.stat()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                self.wfile.write(chunk)

    def _handle_feedback(self, body: dict):
        """POST /api/feedback -- creates GitHub issue from user feedback."""
        title = body.get("title", "").strip()
        description = body.get("description", "").strip()
        category = body.get("category", "bug")  # bug, enhancement, question
        user_name = body.get("user_name", "Anonimo")
        screenshot_b64 = body.get("screenshot", "")

        if not title:
            self._json({"error": "title required"}, 400)
            return

        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            self._json({"error": "GITHUB_TOKEN not configured"}, 500)
            return

        # Build issue body
        issue_body = f"**Reportado por**: {user_name}\n"
        issue_body += f"**Categoria**: {category}\n\n"
        issue_body += f"## Descricao\n{description}\n"

        if screenshot_b64:
            issue_body += f"\n## Screenshot\n![screenshot](data:image/png;base64,{screenshot_b64[:100]}...)\n"
            issue_body += "\n_Screenshot anexado como base64 (ver dados raw do issue)_\n"

        label_map = {"bug": "bug", "enhancement": "enhancement", "question": "question"}
        labels = ["prism-os", label_map.get(category, "bug")]

        try:
            import requests as req
            resp = req.post(
                "https://api.github.com/repos/contele/growth/issues",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "title": f"[Feedback] {title}",
                    "body": issue_body,
                    "labels": labels,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            self._json({"ok": True, "issue_url": data.get("html_url", ""), "issue_number": data.get("number")})
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _handle_blog_generate(self, body: dict):
        """POST /api/blog-generate -- gera post de blog a partir de video YouTube."""
        video_url = body.get("video_url", "").strip()
        blog = body.get("blog", "fleet").strip().lower()
        transcript = body.get("transcript", "").strip() or None

        if not video_url:
            self._json({"error": "video_url required"}, 400)
            return

        try:
            from suggest import extract_video_id
            video_id = extract_video_id(video_url)
        except Exception:
            self._json({"error": "URL do YouTube invalida"}, 400)
            return

        if blog not in ("fleet", "teams"):
            self._json({"error": "blog deve ser 'fleet' ou 'teams'"}, 400)
            return

        job_id = _create_job()
        self._json({"job_id": job_id, "video_id": video_id})

        def _run():
            try:
                from blog import generate_blog_post
                result = generate_blog_post(
                    video_id=video_id,
                    blog=blog,
                    transcript=transcript,
                    progress_cb=lambda data: _emit(job_id, "progress", data),
                )
                _emit(job_id, "complete", result)
            except Exception as e:
                _emit(job_id, "error", {"message": str(e)})

        threading.Thread(target=_run, daemon=True).start()

    def _handle_studio_chat(self, body: dict):
        """POST /api/studio/chat -- conversational thumbnail generation."""
        message = body.get("message", "").strip()
        image_b64 = body.get("image_b64")
        session_id = body.get("session_id", str(uuid.uuid4())[:8])
        mode_hint = body.get("mode") or None  # optional frontend override

        if not message:
            self._json({"error": "message required"}, 400)
            return

        job_id = _create_job()
        self._json({"job_id": job_id, "session_id": session_id})

        def _run():
            try:
                from studio_chat import run_pipeline
                from thumb_live import load_api_key
                api_key = load_api_key()

                def progress_cb(data):
                    _emit(job_id, "progress", data)

                result = run_pipeline(message, image_b64, session_id, api_key, progress_cb, mode_hint=mode_hint)
                _emit(job_id, "complete", result)
            except Exception as e:
                _emit(job_id, "error", {"message": str(e)})

        threading.Thread(target=_run, daemon=True).start()

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        try:
            first = str(args[0]) if args else ""
            if "/api/" in first:
                print(f"  API: {first}")
        except Exception:
            pass


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Nutella Dashboard v2")
    parser.add_argument("--port", type=int, default=None, help="Porta do servidor")
    parser.add_argument("--no-open", action="store_true", help="Não abre browser")
    args = parser.parse_args()

    port = args.port or int(os.environ.get("PORT", 8765))

    # Bootstrap credentials in production
    from boot import bootstrap
    bootstrap()

    # Ensure directories exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)

    if not (STATIC_DIR / "index.html").exists():
        print(f"AVISO: Frontend não encontrado em {STATIC_DIR}/index.html")
        print(f"Rode o skill frontend-design para gerar o frontend.")

    server = None
    for attempt in range(5):
        try:
            server = http.server.ThreadingHTTPServer(("0.0.0.0", port + attempt), DashboardHandler)
            port = port + attempt
            break
        except OSError:
            continue
    if not server:
        print(f"ERRO: Não conseguiu bind em portas {port}-{port + 4}")
        sys.exit(1)

    url = f"http://0.0.0.0:{port}"
    print(f"\nNutella Dashboard v2")
    print(f"Servidor: {url}")
    print(f"Output:   {OUTPUT_DIR}")

    if not args.no_open and not os.environ.get("RAILWAY_ENVIRONMENT"):
        webbrowser.open(url)

    print("Dashboard rodando (Ctrl+C para fechar)\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        print("\nServidor fechado.")


if __name__ == "__main__":
    main()
