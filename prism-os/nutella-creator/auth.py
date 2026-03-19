"""
auth.py — Google OAuth for PRISM OS (no Flask, pure http.server).

Uses signed cookies for session, Google OAuth via requests.
Domain restricted to @contele.com.br.
"""

import os
import json
import hashlib
import hmac
import time
import base64
import secrets
from urllib.parse import urlencode, parse_qs
import requests as req

# Config
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
_env_secret = os.environ.get("SECRET_KEY")
if not _env_secret:
    import secrets as _secrets
    _env_secret = _secrets.token_urlsafe(32)
    print("WARNING: SECRET_KEY not set, using random key (sessions reset on restart)")
SECRET_KEY = _env_secret
DEV_NO_AUTH = os.environ.get("DEV_NO_AUTH", "") == "1"
EMAILS_EXCECAO = ["mantoniofassa@gmail.com"]
COOKIE_NAME = "prism_session"
COOKIE_MAX_AGE = 86400 * 7  # 7 days

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _sign(data: str) -> str:
    """HMAC-sign a string."""
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]


def create_session_cookie(email: str, name: str) -> str:
    """Create a signed session cookie value."""
    payload = json.dumps({"email": email, "name": name, "exp": int(time.time()) + COOKIE_MAX_AGE})
    b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = _sign(b64)
    return f"{b64}.{sig}"


def verify_session_cookie(cookie_value: str) -> dict | None:
    """Verify and decode a session cookie. Returns user dict or None."""
    if not cookie_value:
        return None
    try:
        parts = cookie_value.split(".")
        if len(parts) != 2:
            return None
        b64, sig = parts
        if not hmac.compare_digest(_sign(b64), sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b64))
        if payload.get("exp", 0) < time.time():
            return None
        return {"email": payload["email"], "name": payload["name"]}
    except Exception:
        return None


def get_cookie_from_headers(handler) -> str:
    """Extract session cookie from request headers."""
    cookie_header = handler.headers.get("Cookie", "")
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(f"{COOKIE_NAME}="):
            return part[len(f"{COOKIE_NAME}="):]
    return ""


def is_authenticated(handler) -> dict | None:
    """Check if request has valid session. Returns user dict or None."""
    if DEV_NO_AUTH:
        return {"email": "dev@contele.com.br", "name": "Dev Mode"}
    cookie = get_cookie_from_headers(handler)
    return verify_session_cookie(cookie)


def oauth_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def get_login_url(redirect_uri: str) -> str:
    """Build Google OAuth authorization URL."""
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "hd": "contele.com.br",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, redirect_uri: str) -> dict | None:
    """Exchange authorization code for user info."""
    try:
        # Get token
        resp = req.post(GOOGLE_TOKEN_URL, data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=10)
        if resp.status_code != 200:
            return None
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return None

        # Get user info
        resp = req.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}"
        }, timeout=10)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def is_email_allowed(email: str) -> bool:
    """Check if email is allowed (Contele domain or exception list)."""
    return email.endswith("@contele.com.br") or email in EMAILS_EXCECAO
