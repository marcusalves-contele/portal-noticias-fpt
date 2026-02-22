#!/usr/bin/env python3
"""
Retry loop para gerar hero FPT com gemini-3-pro-image-preview.
Tenta até 10x com intervalo de 60s. Quando gerar, abre a imagem e para.
"""
import base64, requests, os, time, subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
ENV_PATH = PROJECT_DIR / ".env"
OUTPUT_DIR = PROJECT_DIR / "output"
PROMPT_FILE = PROJECT_DIR / "prompts" / "fpt_hero_v5.txt"

# Carregar API key
with open(ENV_PATH) as f:
    for line in f:
        if line.startswith('GEMINI_NANO_BANANA_KEY'):
            API_KEY = line.split('=', 1)[1].strip().strip('"')
            break

# Carregar refs
REFS = [
    PROJECT_DIR / "referencias/julio/julio-ref-01.JPEG",
    PROJECT_DIR / "referencias/julio/julio-ref-02.JPEG",
    PROJECT_DIR / "referencias/julio/julio_ref-sorrindo.jpg",
]

# Montar parts
parts = []
for r in REFS:
    with open(r, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    ext = r.suffix.lower()
    mime = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
    parts.append({'inlineData': {'mimeType': mime, 'data': data}})

with open(PROMPT_FILE) as f:
    prompt = f.read()
parts.append({'text': prompt})

MODEL = 'gemini-3-pro-image-preview'
URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
HEADERS = {'x-goog-api-key': API_KEY, 'Content-Type': 'application/json'}
PAYLOAD = {
    'contents': [{'parts': parts}],
    'generationConfig': {
        'responseModalities': ['IMAGE'],
        'imageConfig': {'aspectRatio': '16:9'},
        'temperature': 0
    }
}

MAX_RETRIES = 10
INTERVAL = 60  # segundos

OUTPUT_DIR.mkdir(exist_ok=True)

for attempt in range(1, MAX_RETRIES + 1):
    print(f"[{time.strftime('%H:%M:%S')}] Tentativa {attempt}/{MAX_RETRIES}...")

    try:
        resp = requests.post(URL, headers=HEADERS, json=PAYLOAD, timeout=240)
        result = resp.json()

        if 'error' in result:
            msg = result['error'].get('message', '')[:80]
            print(f"  Erro: {msg}")
        elif 'candidates' in result:
            for part in result['candidates'][0]['content']['parts']:
                if 'inlineData' in part:
                    img_data = base64.b64decode(part['inlineData']['data'])
                    out_path = OUTPUT_DIR / "fpt_hero_v5_pro.png"
                    with open(out_path, 'wb') as f:
                        f.write(img_data)
                    print(f"  SUCESSO! {out_path} ({len(img_data)} bytes)")
                    # Abrir imagem
                    subprocess.run(['open', str(out_path)])
                    exit(0)
            print("  Resposta sem imagem")
        else:
            print(f"  Resposta inesperada: {list(result.keys())}")

    except Exception as e:
        print(f"  Exception: {e}")

    if attempt < MAX_RETRIES:
        print(f"  Aguardando {INTERVAL}s...")
        time.sleep(INTERVAL)

print(f"FALHOU após {MAX_RETRIES} tentativas.")
exit(1)
