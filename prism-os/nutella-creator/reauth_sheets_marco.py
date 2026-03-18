#!/usr/bin/env python3
"""
reauth_sheets_marco.py — Token separado para Sheets + Drive (conta Marco).

Gera token_sheets_marco.pickle com:
  - spreadsheets.readonly   (leitura de planilhas)
  - drive.file              (upload de thumbs para pasta no Drive)

NAO afeta token_youtube_julio.pickle (Cesar Responde continua com conta do Julio).

Uso (uma unica vez):
  python3 reauth_sheets_marco.py
  -> Logar com marcoantonio@contele.com.br
"""

import pickle
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

CREDENTIALS_FILE = Path("/Users/marcofassa/Documents/credenciais-somente-LOCAL/"
                         "client_secret_621578997991-29tf5n699oov060gsoq1id1javnm8hbb"
                         ".apps.googleusercontent.com.json")

TOKEN_PATH = Path(__file__).parent / "token_sheets_marco.pickle"


def main():
    print("Auth Sheets + Drive (conta Marco)")
    print(f"Token destino: {TOKEN_PATH}")
    print()

    if not CREDENTIALS_FILE.exists():
        print(f"ERRO: credentials nao encontrado em {CREDENTIALS_FILE}")
        sys.exit(1)

    if TOKEN_PATH.exists():
        try:
            with open(TOKEN_PATH, "rb") as f:
                old_creds = pickle.load(f)
            existing_scopes = set(old_creds.scopes or [])
            needed = set(SCOPES)
            if needed.issubset(existing_scopes):
                print("Token ja possui todos os scopes. Nada a fazer.")
                print(f"Escopos atuais: {existing_scopes}")
                return
            print(f"Escopos atuais: {existing_scopes}")
            print("Re-autenticando...")
            print()
        except Exception as e:
            print(f"Token existente invalido ({e}), forcando re-auth.")

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
    print("Pronto. PRISM OS vai usar este token para ler planilhas e upload Drive.")


if __name__ == "__main__":
    main()
