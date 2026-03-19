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

    # Persistent volume: symlink output/ and downloads/ to volume mount
    # Volume mounted at /app/nutella-creator/data by Railway
    volume_path = Path("/app/nutella-creator/data")
    project_dir = Path(__file__).parent
    if volume_path.exists() and os.environ.get("RAILWAY_ENVIRONMENT"):
        for dirname in ["output", "downloads"]:
            vol_dir = volume_path / dirname
            local_dir = project_dir / dirname
            vol_dir.mkdir(parents=True, exist_ok=True)
            # Remove existing dir/symlink and create symlink to volume
            if local_dir.is_symlink():
                pass  # Already linked
            elif local_dir.is_dir():
                # Move any existing files to volume first
                import shutil
                for item in local_dir.iterdir():
                    dest = vol_dir / item.name
                    if not dest.exists():
                        shutil.move(str(item), str(dest))
                local_dir.rmdir()
                local_dir.symlink_to(vol_dir)
                print(f"Linked {dirname}/ -> {vol_dir} (moved existing files)")
            else:
                local_dir.symlink_to(vol_dir)
                print(f"Linked {dirname}/ -> {vol_dir}")
        # Also persist operational_memory.json
        mem_vol = volume_path / "operational_memory.json"
        mem_local = project_dir / "operational_memory.json"
        if mem_vol.exists() and not mem_local.exists():
            mem_local.symlink_to(mem_vol)
            print(f"Linked operational_memory.json -> {mem_vol}")
        elif mem_local.exists() and not mem_local.is_symlink():
            shutil.copy2(str(mem_local), str(mem_vol))
            mem_local.unlink()
            mem_local.symlink_to(mem_vol)
            print(f"Migrated operational_memory.json -> {mem_vol}")

if __name__ == "__main__":
    bootstrap()
