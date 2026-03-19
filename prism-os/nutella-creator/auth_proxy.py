#!/usr/bin/env python3
"""
auth_proxy.py — Flask auth proxy for PRISM OS.

Handles Google OAuth login, then proxies all requests to the dashboard
HTTP server running on an internal port.

Usage:
  python3 auth_proxy.py          # Starts Flask on $PORT (Railway) or 8765
  DEV_NO_AUTH=1 python3 auth_proxy.py  # Skip auth (local dev)
"""

import os
import sys
import threading
import time
import requests as req
from pathlib import Path
from flask import Flask, request, redirect, session, Response, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth

PROJECT_DIR = Path(__file__).parent
STATIC_DIR = PROJECT_DIR / "static"
VERSION = (PROJECT_DIR / "VERSION").read_text().strip() if (PROJECT_DIR / "VERSION").exists() else "dev"

# Internal port for the dashboard HTTP server
INTERNAL_PORT = 18765

# Config
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "prism-os-dev-key-change-me")
DEV_NO_AUTH = os.environ.get("DEV_NO_AUTH", "") == "1"
EMAILS_EXCECAO = ["mantoniofassa@gmail.com"]

app = Flask(__name__, static_folder=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = SECRET_KEY

# Session config
if os.environ.get("RAILWAY_ENVIRONMENT"):
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
else:
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE="Lax",
    )

# OAuth setup
oauth = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile", "prompt": "select_account"},
        authorize_params={"hd": "contele.com.br", "access_type": "offline"},
    )


LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PRISM OS - Login</title>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #09090b;
      color: #e8e8ec;
      font-family: 'IBM Plex Mono', monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }
    .login-card {
      text-align: center;
      padding: 48px;
    }
    .logo {
      font-family: 'Syne', sans-serif;
      font-size: 32px;
      font-weight: 800;
      letter-spacing: 2px;
      margin-bottom: 8px;
    }
    .logo span { color: #8B23E5; }
    .subtitle {
      color: #56565e;
      font-size: 12px;
      letter-spacing: 3px;
      text-transform: uppercase;
      margin-bottom: 48px;
    }
    .login-btn {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      background: #8B23E5;
      color: white;
      border: none;
      padding: 14px 32px;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.2s;
    }
    .login-btn:hover { background: #6B1CB5; }
    .login-btn svg { width: 20px; height: 20px; }
    .version {
      margin-top: 48px;
      color: #56565e;
      font-size: 11px;
    }
    .error {
      color: #f43f5e;
      margin-bottom: 24px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="login-card">
    <div class="logo"><span>PRISM</span> OS</div>
    <div class="subtitle">Content Production System</div>
    {error}
    <a href="/login" class="login-btn">
      <svg viewBox="0 0 24 24" fill="white"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
      Entrar com Google
    </a>
    <div class="version">PRISM OS v""" + VERSION + """</div>
  </div>
</body>
</html>"""


@app.before_request
def require_login():
    """Auth middleware."""
    if DEV_NO_AUTH:
        return
    # Allow auth routes
    if request.path in ("/login", "/auth", "/logout", "/favicon.svg", "/favicon.ico"):
        return
    # Allow static assets needed for login
    if request.path.startswith("/static/"):
        return
    # Check session
    if "user" in session:
        return
    # Show login page
    if request.path == "/" or not request.path.startswith("/api/"):
        return Response(LOGIN_HTML.format(error=""), content_type="text/html")
    # API calls without auth get 401
    return Response('{"error":"unauthorized"}', status=401, content_type="application/json")


@app.route("/login")
def login():
    if not oauth or not hasattr(oauth, "google"):
        return "OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.", 500
    redirect_uri = request.url_root.rstrip("/") + "/auth"
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        redirect_uri = redirect_uri.replace("http://", "https://")
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth")
def auth_callback():
    if not oauth or not hasattr(oauth, "google"):
        return "OAuth not configured.", 500
    token = oauth.google.authorize_access_token()
    user = token.get("userinfo") or {}
    email = user.get("email", "")
    if not user or (
        not email.endswith("@contele.com.br")
        and email not in EMAILS_EXCECAO
    ):
        error_html = '<div class="error">Acesso restrito ao dominio contele.com.br</div>'
        return Response(LOGIN_HTML.format(error=error_html), content_type="text/html")
    session["user"] = {"email": email, "name": user.get("name", "")}
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    """Proxy all requests to the internal dashboard server."""
    url = f"http://127.0.0.1:{INTERNAL_PORT}/{path}"
    if request.query_string:
        url += f"?{request.query_string.decode()}"

    try:
        resp = req.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=300,
            stream=True,
        )

        # Handle SSE (Server-Sent Events)
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            def generate():
                for chunk in resp.iter_content(chunk_size=None):
                    yield chunk
            return Response(generate(), content_type=content_type)

        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}
        return Response(resp.content, resp.status_code, headers)
    except req.ConnectionError:
        return Response("Dashboard server not ready", status=503)


def start_dashboard_server():
    """Start the internal dashboard HTTP server in a thread."""
    # Save the real PORT for Flask, give dashboard the internal port
    saved_port = os.environ.get("PORT", "8765")
    os.environ["PORT"] = str(INTERNAL_PORT)

    sys.argv = ["dashboard.py", "--port", str(INTERNAL_PORT), "--no-open"]

    import dashboard
    t = threading.Thread(target=dashboard.main, daemon=True)
    t.start()

    # Restore PORT for Flask
    os.environ["PORT"] = saved_port

    # Wait for internal server to be ready
    for i in range(30):
        try:
            req.get(f"http://127.0.0.1:{INTERNAL_PORT}/", timeout=1)
            print(f"Dashboard server ready on internal port {INTERNAL_PORT}")
            return True
        except Exception:
            time.sleep(1)
    print("ERROR: Dashboard server failed to start")
    return False


if __name__ == "__main__":
    from boot import bootstrap
    bootstrap()

    # Determine Flask port (Railway PORT or default 8765)
    flask_port = int(os.environ.get("PORT", 8765))

    print(f"PRISM OS Auth Proxy v{VERSION}")
    print(f"DEV_NO_AUTH: {DEV_NO_AUTH}")
    print(f"OAuth configured: {bool(GOOGLE_CLIENT_ID)}")
    print(f"Flask port: {flask_port}, Dashboard internal port: {INTERNAL_PORT}")

    # Start internal dashboard
    if not start_dashboard_server():
        sys.exit(1)

    # Start Flask proxy on the public port
    app.run(host="0.0.0.0", port=flask_port, threaded=True)
