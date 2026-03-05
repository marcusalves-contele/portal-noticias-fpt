#!/usr/bin/env python3
"""
Thumbnail AI Creator - Gerador de Thumbnails com Nano Banana Pro
Gera 3 variações de thumbnail baseado em prompt otimizado.

Uso:
    python3 generate.py --prompt "seu prompt aqui" --refs ref1.jpg ref2.jpg
    python3 generate.py --prompt-file prompts/live316.txt --refs referencias/julio/*.JPEG
    python3 generate.py --live 317  # Auto-detecta convidado e refs
"""

import os
import sys
import re
import base64
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuração
PROJECT_DIR = Path(__file__).parent
ENV_PATH = PROJECT_DIR / ".env"
OUTPUT_DIR = PROJECT_DIR / "output"
REFS_DIR = PROJECT_DIR / "referencias"
GUESTS_DIR = REFS_DIR / "convidados"
MODEL = "gemini-3-pro-image-preview"  # Nano Banana Pro


def find_guest_for_live(live_number):
    """
    Busca arquivo de convidado para uma live específica.

    Padrão do arquivo: {titulo}_live-{numero}-{Nome-Completo}.{ext}
    Exemplos:
        - convidado_live-317-Nelson-Margarido.jpg
        - especialista_live-320-Maria-Silva.png
        - gestor_live-325-Joao-Santos.jpeg

    Returns:
        dict com 'path', 'title', 'name' ou None se não encontrar
    """
    if not GUESTS_DIR.exists():
        return None

    # Busca arquivos que contenham o número da live
    pattern = re.compile(rf'^(\w+)_live-{live_number}-(.+)\.(jpg|jpeg|png|webp)$', re.IGNORECASE)

    for file in GUESTS_DIR.iterdir():
        match = pattern.match(file.name)
        if match:
            title = match.group(1).capitalize()  # "convidado" -> "Convidado"
            name_parts = match.group(2).split('-')
            name = ' '.join(name_parts)  # "Nelson-Margarido" -> "Nelson Margarido"

            return {
                'path': str(file),
                'title': title,
                'name': name,
                'display': f"{title} {name}"  # "Convidado Nelson Margarido"
            }

    return None


def get_host_refs(channel='fleet'):
    """Retorna lista de referências do apresentador principal.

    Julio (Fleet): carrega arquivos *-primary-*.jpg em orden — foto real + estúdio Gemini.
    Leonardo (Teams): carrega leo-ref-primary.jpg (estúdio Gemini refinado, Mar/2026).
    Refs antigas (IA geradas) movidas para _old/ — não usar.
    """
    if channel.lower() == 'fleet':
        julio_dir = REFS_DIR / "julio"
        if julio_dir.exists():
            # Prioriza arquivos *-primary-* (foto real + estúdio), depois qualquer .jpg
            primaries = sorted(julio_dir.glob("*-primary-*.jpg"))
            if primaries:
                return [str(f) for f in primaries]
            return sorted([str(f) for f in julio_dir.glob("*.JPEG")] +
                         [str(f) for f in julio_dir.glob("*.jpg")])
    elif channel.lower() == 'teams':
        leo_dir = REFS_DIR / "leonardo"
        # Preferência: .jpg (foto real/estúdio), fallback: .png legado
        primary_jpg = leo_dir / "leo-ref-primary.jpg"
        if primary_jpg.exists():
            return [str(primary_jpg)]
        primary_png = leo_dir / "leo-ref-primary.png"
        if primary_png.exists():
            return [str(primary_png)]
        if leo_dir.exists():
            return sorted([str(f) for f in leo_dir.glob("*.jpg")] +
                         [str(f) for f in leo_dir.glob("*.jpeg")])
    return []

def load_api_key():
    """Carrega API key do .env"""
    env_file = ENV_PATH if ENV_PATH.exists() else Path.home() / ".env"
    with open(env_file) as f:
        for line in f:
            if line.startswith('GEMINI_NANO_BANANA_KEY'):
                return line.split('=', 1)[1].strip().strip('"')
    raise ValueError("GEMINI_NANO_BANANA_KEY não encontrada no .env")

def load_image_base64(image_path):
    """Carrega imagem e converte para base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def get_mime_type(image_path):
    """Retorna MIME type baseado na extensão"""
    ext = Path(image_path).suffix.lower()
    return {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}.get(ext, 'image/jpeg')

def generate_single(api_key, parts, variation_num, output_prefix):
    """Gera uma única thumbnail"""
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"},
            "temperature": 0  # Reduz variação para maior consistência
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        result = response.json()

        if "error" in result:
            return None, f"Erro variação {variation_num}: {result['error'].get('message', 'Unknown')}"

        if "candidates" in result:
            for part in result["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    image_data = base64.b64decode(part["inlineData"]["data"])
                    output_path = OUTPUT_DIR / f"{output_prefix}_v{variation_num}.png"

                    with open(output_path, "wb") as f:
                        f.write(image_data)

                    return str(output_path), None

        return None, f"Variação {variation_num}: Resposta sem imagem"

    except Exception as e:
        return None, f"Variação {variation_num}: {str(e)}"

def generate_thumbnails(prompt, reference_images=None, num_variations=3, output_prefix=None):
    """
    Gera múltiplas variações de thumbnail.

    Args:
        prompt: Prompt completo para geração
        reference_images: Lista de paths para imagens de referência
        num_variations: Número de variações (padrão 3)
        output_prefix: Prefixo para arquivos de saída

    Returns:
        Lista de paths das imagens geradas
    """
    api_key = load_api_key()
    OUTPUT_DIR.mkdir(exist_ok=True)

    if output_prefix is None:
        output_prefix = f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Monta as partes (imagens de referência + prompt)
    parts = []

    if reference_images:
        for img_path in reference_images:
            if os.path.exists(img_path):
                parts.append({
                    "inlineData": {
                        "mimeType": get_mime_type(img_path),
                        "data": load_image_base64(img_path)
                    }
                })
                print(f"  Ref: {Path(img_path).name}")

    parts.append({"text": prompt})

    print(f"\nGerando {num_variations} variações com {MODEL}...")

    # Gera variações em paralelo
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_single, api_key, parts, i+1, output_prefix): i+1
            for i in range(num_variations)
        }

        for future in as_completed(futures):
            path, error = future.result()
            if path:
                results.append(path)
                print(f"  Variação {futures[future]}: OK")
            if error:
                errors.append(error)
                print(f"  {error}")

    return results, errors

def main():
    parser = argparse.ArgumentParser(description='Gera thumbnails com Nano Banana Pro')
    parser.add_argument('--prompt', help='Prompt direto')
    parser.add_argument('--prompt-file', help='Arquivo com o prompt')
    parser.add_argument('--refs', nargs='+', help='Imagens de referência')
    parser.add_argument('--live', type=int, help='Número da live (auto-detecta convidado e refs)')
    parser.add_argument('--channel', default='fleet', choices=['fleet', 'teams'], help='Canal (fleet ou teams)')
    parser.add_argument('--variations', type=int, default=3, help='Número de variações (padrão: 3)')
    parser.add_argument('--prefix', help='Prefixo para arquivos de saída')
    parser.add_argument('--open', action='store_true', help='Abrir imagens após gerar')
    parser.add_argument('--check-guest', type=int, help='Apenas verifica se existe convidado para a live')

    args = parser.parse_args()

    # Modo de verificação de convidado
    if args.check_guest:
        guest = find_guest_for_live(args.check_guest)
        if guest:
            print(json.dumps(guest, ensure_ascii=False))
        else:
            print(json.dumps({"found": False}))
        sys.exit(0)

    # Carrega prompt
    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        print("Erro: Forneça --prompt ou --prompt-file")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("THUMBNAIL AI CREATOR - NANO BANANA PRO")
    print(f"{'='*60}")

    # Monta referências
    refs = []

    # Se --live foi passado, auto-detecta refs e convidado
    if args.live:
        # Refs do apresentador principal
        host_refs = get_host_refs(args.channel)
        refs.extend(host_refs)

        # Verifica se tem convidado
        guest = find_guest_for_live(args.live)
        if guest:
            refs.append(guest['path'])
            print(f"  Convidado detectado: {guest['display']}")

        # Prefix automático se não especificado
        if not args.prefix:
            args.prefix = f"live{args.live}"

    # Refs manuais (adiciona às automáticas se houver)
    if args.refs:
        for ref in args.refs:
            if '*' in ref:
                import glob
                refs.extend(glob.glob(ref))
            else:
                refs.append(ref)

    results, errors = generate_thumbnails(
        prompt=prompt,
        reference_images=refs,
        num_variations=args.variations,
        output_prefix=args.prefix
    )

    print(f"\n{'='*60}")
    print(f"RESULTADO: {len(results)} imagens geradas")
    for path in results:
        print(f"  {path}")
    print(f"{'='*60}")

    if args.open and results:
        for path in results:
            os.system(f'open "{path}"')

if __name__ == "__main__":
    main()
