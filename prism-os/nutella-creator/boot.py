#!/usr/bin/env python3
"""boot.py — Credential bootstrap for production.
Decodes base64-encoded pickle tokens from env vars to /tmp/ files.
Run before dashboard.py in production.
"""
import os, base64, sys
from pathlib import Path

TOKENS = {
    "YOUTUBE_TOKEN_B64": "/tmp/token_youtube.pickle",
    "SHEETS_TOKEN_B64": "/tmp/token_sheets.pickle",
}

def bootstrap():
    for env_var, dest_path in TOKENS.items():
        b64 = os.environ.get(env_var)
        if b64:
            data = base64.b64decode(b64)
            Path(dest_path).write_bytes(data)
            print(f"Decoded {env_var} -> {dest_path} ({len(data)} bytes)")
            # Set env vars so other modules find them
            if "YOUTUBE" in env_var:
                os.environ["YOUTUBE_TOKEN_PATH"] = dest_path
            elif "SHEETS" in env_var:
                os.environ["SHEETS_TOKEN_PATH"] = dest_path
        else:
            print(f"No {env_var} env var, skipping (local dev mode)")

    # Gemini key: ensure it's available even without .env file
    gemini_key = os.environ.get("GEMINI_NANO_BANANA_KEY")
    if gemini_key:
        print("GEMINI_NANO_BANANA_KEY found in env")

if __name__ == "__main__":
    bootstrap()
