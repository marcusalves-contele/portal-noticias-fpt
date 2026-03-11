#!/usr/bin/env python3
"""
reauth_sheets.py — Adiciona escopos Google Sheets + Drive ao token YouTube.

Substitui token_youtube_write.pickle com novo token que inclui:
  - youtube.force-ssl       (upload/gestão — já tinha)
  - yt-analytics.readonly   (analytics — pode já ter)
  - spreadsheets.readonly   (leitura de planilhas)
  - drive.file              (NOVO: upload de thumbs para pasta no Drive)

Uso (uma única vez):
  python3 reauth_sheets.py

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
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.file",
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
    print("Re-autenticação: YouTube + Analytics + Sheets")
    print(f"Token destino: {TOKEN_PATH}")
    print()

    if not CREDENTIALS_FILE.exists():
        print(f"ERRO: credentials não encontrado em {CREDENTIALS_FILE}")
        sys.exit(1)

    # Verifica se token atual já tem todos os scopes
    if TOKEN_PATH.exists():
        try:
            with open(TOKEN_PATH, "rb") as f:
                old_creds = pickle.load(f)
            existing_scopes = set(old_creds.scopes or [])
            drive_scope = "https://www.googleapis.com/auth/drive.file"
            if drive_scope in existing_scopes:
                print("Token já possui todos os scopes (incluindo Drive). Nada a fazer.")
                print(f"Escopos atuais: {existing_scopes}")
                return
            print(f"Escopos atuais: {existing_scopes}")
            print("Adicionando scopes Sheets + Drive...")
            print()
        except Exception as e:
            print(f"Token existente inválido ({e}), forçando re-auth.")

    # Força novo flow (escopo novo requer consentimento)
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    print()
    print(f"Token salvo em: {TOKEN_PATH}")
    print(f"Escopos: {sorted(creds.scopes)}")
    print()

    # Valida acesso Sheets
    try:
        from googleapiclient.discovery import build
        sheets = build("sheets", "v4", credentials=creds)
        resp = sheets.spreadsheets().get(
            spreadsheetId="1lluvZ8SKQNThV4o4OzWqmsttP-BgRC1FU3AqwvfJbqI",
            fields="sheets.properties"
        ).execute()
        sheet_names = [s["properties"]["title"] for s in resp.get("sheets", [])]
        print(f"Sheets API: OK — abas: {sheet_names}")
    except Exception as e:
        print(f"Sheets API: ERRO — {e}")

    print()
    print("Pronto. thumb_live.py agora pode ler a planilha de lives.")


if __name__ == "__main__":
    main()
