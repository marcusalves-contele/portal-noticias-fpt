#!/usr/bin/env python3
"""Gera versão 4K studio portrait do Leo usando Gemini image generation."""

import os
import base64
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]
REF_PATH = Path(__file__).parent.parent / "output" / "teams_leo_face_v1.png"
OUT_PATH = Path(__file__).parent.parent / "output" / "teams_leo_face_4k_v1.png"

client = genai.Client(api_key=API_KEY)

# Carrega imagem de referência
img_bytes = REF_PATH.read_bytes()
img_b64 = base64.b64encode(img_bytes).decode()

PROMPT = """Using this image as a strict face reference, generate a high-quality 4K studio portrait photo of the same man.

CRITICAL — MUST MATCH THE REFERENCE FACE EXACTLY:
- Same round/oval face shape with fuller cheeks
- Same dark wavy/curly hair with natural texture and gray streaks
- Same black rectangular frame glasses — keep the glasses
- Same dark brown eyes behind the glasses
- Clean shaven — no beard, no stubble
- Age 43-48, natural mature appearance — do NOT make him younger
- Same facial features, proportions, skin tone

SHOT:
- Close-up portrait, face and upper shoulders only
- Direct frontal gaze, confident and serious expression
- Slight forward lean toward camera

LIGHTING & BACKGROUND:
- Professional studio lighting: soft key light slightly to the right, subtle fill
- Clean dark charcoal/near-black backdrop, very slight gradient
- Cinematic depth — background slightly defocused

QUALITY:
- 4K resolution, ultra-sharp facial detail
- Photorealistic skin texture — pores, natural imperfections, no over-smoothing
- Professional headshot / editorial photography quality

NO text overlays. Output: portrait only."""

print(f"Gerando 4K studio portrait do Leo com referência: {REF_PATH.name}")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        types.Content(parts=[
            types.Part(inline_data=types.Blob(mime_type="image/png", data=img_bytes)),
            types.Part(text=PROMPT),
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    ),
)

# Salva imagem gerada
saved = False
for part in response.candidates[0].content.parts:
    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
        OUT_PATH.write_bytes(part.inline_data.data)
        print(f"Salvo: {OUT_PATH}")
        saved = True
        break

if not saved:
    # Tenta via texto (se modelo retornou só texto)
    print("Resposta texto:", response.text)
    raise RuntimeError("Nenhuma imagem retornada pelo modelo.")

# Abre no Finder
subprocess.run(["open", "-R", str(OUT_PATH)])
print("Aberto no Finder.")
