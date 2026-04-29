#!/usr/bin/env bash
# encode_sheets_token.sh — gera SHEETS_TOKEN_B64 pra Railway env var
# Uso: bash scripts/encode_sheets_token.sh
# Output: linha pra colar no Railway dashboard como env var SHEETS_TOKEN_B64

set -e

TOKEN_PATH="$(dirname "$0")/../token_sheets_marco.pickle"

if [[ ! -f "$TOKEN_PATH" ]]; then
  echo "Token nao encontrado em $TOKEN_PATH"
  echo "Rode: python3 reauth_sheets_marco.py"
  exit 1
fi

echo "===== SHEETS_TOKEN_B64 ====="
base64 -i "$TOKEN_PATH" | tr -d '\n'
echo ""
echo ""
echo "Cole o valor acima como env var SHEETS_TOKEN_B64 no Railway dashboard"
echo "do servico prism-os (project: growth)."
