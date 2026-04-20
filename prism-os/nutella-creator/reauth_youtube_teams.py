#!/usr/bin/env python3
"""
Re-autenticacao YouTube CANAL TEAMS (Leonardo Gazolli).

Gera token_youtube_teams.pickle usado pelo blog.py/suggest.py pra extrair
legendas dos videos do canal Eng. Leonardo Gazolli - Equipes Externas via
YouTube Data API (Tier 3 do fallback).

Pre-requisito: marcoantonio@contele.com.br com permissao de GERENTE ou OWNER
no canal Teams. No fluxo OAuth, selecionar o BRAND ACCOUNT do canal Teams
(nao a conta pessoal).

Uso:
  python3 reauth_youtube_teams.py

O browser abre. Logar com marcoantonio@contele.com.br, escolher o brand
account do canal Teams quando o picker aparecer.

Saida:
  - token_youtube_teams.pickle na pasta do script
  - validacao: lista captions de um video Teams de teste
  - base64 pra colar em YOUTUBE_TEAMS_TOKEN_B64 no Railway
"""

import base64
import pickle
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CREDENTIALS_FILE = Path(
    "/Users/marcofassa/Documents/credenciais-somente-LOCAL/"
    "client_secret_621578997991-29tf5n699oov060gsoq1id1javnm8hbb"
    ".apps.googleusercontent.com.json"
)

PROJECT_DIR = Path(__file__).parent
TOKEN_PATH = PROJECT_DIR / "token_youtube_teams.pickle"

TEST_VIDEO_ID = "OptcPLCSDRM"


def main():
    print("Re-autenticacao YouTube CANAL TEAMS (Leonardo)")
    print(f"Token destino: {TOKEN_PATH}")
    print()
    print("ATENCAO: no browser, escolha o BRAND ACCOUNT do canal Teams.")
    print("Nao use a conta pessoal marcoantonio@contele.com.br direto.")
    print()

    if not CREDENTIALS_FILE.exists():
        print(f"ERRO: credentials nao encontrado em {CREDENTIALS_FILE}")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    print()
    print(f"Token salvo: {TOKEN_PATH}")
    print(f"Escopos: {creds.scopes}")
    print()

    print(f"Validando captions.list em video Teams {TEST_VIDEO_ID}...")
    try:
        youtube = build("youtube", "v3", credentials=creds)
        resp = youtube.captions().list(part="snippet", videoId=TEST_VIDEO_ID).execute()
        items = resp.get("items", [])
        if not items:
            print(f"Captions vazio pro video {TEST_VIDEO_ID}. Token valido, mas sem legendas no video ou acesso negado.")
        else:
            print(f"Captions.list OK ({len(items)} legendas disponiveis):")
            for it in items:
                sn = it["snippet"]
                print(f"  - {sn.get('language')} / {sn.get('trackKind')} / {sn.get('name', '')}")

            first_id = items[0]["id"]
            print(f"\nTestando captions.download (id={first_id})...")
            try:
                data = youtube.captions().download(id=first_id, tfmt="srt").execute()
                size = len(data) if data else 0
                print(f"  download OK ({size} bytes). Permissao OWNER/MANAGER confirmada.")
            except Exception as dl_err:
                print(f"  download FALHOU: {dl_err}")
                print("  Provavel causa: MANAGER nao basta, precisa OWNER. Avaliar solucao alternativa.")
    except Exception as e:
        print(f"Validacao falhou: {e}")
        print("Provavel: brand account errado no picker, ou sem permissao. Re-rodar escolhendo o canal certo.")

    print()
    print("=" * 60)
    print("Base64 pra setar em YOUTUBE_TEAMS_TOKEN_B64 no Railway:")
    print("=" * 60)
    b64 = base64.b64encode(TOKEN_PATH.read_bytes()).decode()
    print(b64)
    print()
    print("Proximo passo:")
    print("  1. Copiar o base64 acima")
    print("  2. Railway > growth > prism-os > Variables")
    print("  3. Adicionar YOUTUBE_TEAMS_TOKEN_B64 = <base64>")
    print("  4. Redeploy")


if __name__ == "__main__":
    main()
