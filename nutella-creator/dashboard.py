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
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR  = PROJECT_DIR / "output"
STATIC_DIR  = PROJECT_DIR / "static"

# Progress queues per job
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


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

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API routes
        if path == "/api/videos":
            self._handle_list_videos()
        elif path.startswith("/api/metas/"):
            video_id = path.split("/api/metas/")[1]
            self._handle_get_metas(video_id)
        elif path.startswith("/api/progress/"):
            job_id = path.split("/api/progress/")[1]
            self._handle_sse(job_id)
        elif path.startswith("/output/"):
            # Serve files from output directory
            rel_path = path[len("/output/"):]
            file_path = OUTPUT_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                self._serve_file(file_path)
            else:
                self._json({"error": "not found"}, 404)
        else:
            # Serve static files (frontend)
            if path == "/" or path == "":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception:
            self._json({"error": "invalid JSON"}, 400)
            return

        path = urlparse(self.path).path

        if path == "/api/analyze":
            self._handle_analyze(body)
        elif path == "/api/build":
            self._handle_build(body)
        elif path == "/api/approve":
            self._handle_approve(body)
        elif path == "/api/generate-thumb":
            self._handle_generate_thumb(body)
        elif path == "/api/regenerate-thumb":
            self._handle_regenerate_thumb(body)
        elif path == "/api/upload-youtube":
            self._handle_upload(body)
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
                videos.append({
                    "video_id": video_id,
                    "url": data.get("youtube_url", ""),
                    "generated_at": data.get("generated_at", ""),
                    "nutellas_count": len(data.get("nutellas", [])),
                    "has_cuts": has_cuts,
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
                            get_best_publish_times)
        try:
            creds = load_credentials()
            youtube = get_youtube(creds)
        except Exception as e:
            self._json({"error": f"auth failed: {e}"}, 500)
            return

        source_video_id = video_id

        publish_times = []
        if schedule:
            publish_times = get_best_publish_times(youtube, len(selected))
            privacy = "private"

        results = []
        errors = []
        for i, meta in enumerate(selected):
            pub_time = publish_times[i] if i < len(publish_times) else None
            try:
                result = upload_nutella(
                    meta, cuts_dir, youtube,
                    privacy=privacy, publish_at=pub_time,
                    source_video_id=source_video_id,
                )
                if result:
                    results.append(result)
                else:
                    errors.append(f"#{meta['rank']} failed")
            except Exception as e:
                errors.append(f"#{meta['rank']}: {e}")

        self._json({"uploaded": results, "errors": errors})

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

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            print(f"  API: {args[0]}")


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Nutella Dashboard v2")
    parser.add_argument("--port", type=int, default=8765, help="Porta do servidor")
    parser.add_argument("--no-open", action="store_true", help="Não abre browser")
    args = parser.parse_args()

    # Ensure directories exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)

    if not (STATIC_DIR / "index.html").exists():
        print(f"AVISO: Frontend não encontrado em {STATIC_DIR}/index.html")
        print(f"Rode o skill frontend-design para gerar o frontend.")

    server = None
    for attempt in range(5):
        try:
            server = http.server.HTTPServer(("127.0.0.1", args.port + attempt), DashboardHandler)
            args.port = args.port + attempt
            break
        except OSError:
            continue
    if not server:
        print(f"ERRO: Não conseguiu bind em portas {args.port}-{args.port + 4}")
        sys.exit(1)

    url = f"http://127.0.0.1:{args.port}"
    print(f"\nNutella Dashboard v2")
    print(f"Servidor: {url}")
    print(f"Output:   {OUTPUT_DIR}")

    if not args.no_open:
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
