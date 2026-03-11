#!/usr/bin/env python3
"""
Re-autenticação YouTube — adiciona escopo Analytics.

Substitui o token_youtube_write.pickle atual pelo novo token com:
  - youtube.force-ssl  (upload, gestão de vídeos — já tinha)
  - yt-analytics.readonly  (NOVO: views por hora/dia, audiência, retenção)

Uso:
  python3 reauth_youtube_analytics.py

O browser abre automaticamente. Faça login com a conta do canal Frota Para Todos.
"""

import os
import pickle
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CREDENTIALS_FILE = Path("/Users/marcofassa/Documents/credenciais-somente-LOCAL/"
                         "client_secret_621578997991-29tf5n699oov060gsoq1id1javnm8hbb"
                         ".apps.googleusercontent.com.json")

_PROJECT_DIR = Path(__file__).parent

def _read_env_token_path() -> str | None:
    """Lê YOUTUBE_TOKEN_PATH do .env local (sem python-dotenv)."""
    env_file = _PROJECT_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("YOUTUBE_TOKEN_PATH"):
                    return line.split("=", 1)[1].strip().strip('"')
    return None

TOKEN_PATH = Path(
    os.getenv("YOUTUBE_TOKEN_PATH")
    or _read_env_token_path()
    or str(_PROJECT_DIR.parent.parent.parent / "assistant-sexta-feira" / "token_youtube_write.pickle")
)


def main():
    print("Re-autenticação YouTube + Analytics")
    print(f"Token destino: {TOKEN_PATH}")
    print()

    if not CREDENTIALS_FILE.exists():
        print(f"ERRO: credentials não encontrado em {CREDENTIALS_FILE}")
        sys.exit(1)

    # Força novo flow ignorando token antigo (escopo novo)
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    print()
    print(f"Token salvo em: {TOKEN_PATH}")
    print(f"Escopos: {creds.scopes}")
    print()

    # Valida acesso Analytics
    try:
        from googleapiclient.discovery import build
        analytics = build("youtubeAnalytics", "v2", credentials=creds)
        resp = analytics.reports().query(
            ids="channel==UCz31CtOANqSFuLEdFTi1iCQ",
            startDate="2026-01-01",
            endDate="2026-03-02",
            metrics="views",
            dimensions="dayOfWeek",
        ).execute()
        print("Analytics API: OK")
        print(f"  {len(resp.get('rows', []))} linhas retornadas")
    except Exception as e:
        print(f"Analytics API: ERRO — {e}")

    print()
    print("Pronto. O sistema agora pode usar YouTube Analytics para agendamento inteligente.")


if __name__ == "__main__":
    main()
