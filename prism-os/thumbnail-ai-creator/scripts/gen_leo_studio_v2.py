#!/usr/bin/env python3
"""Gera studio portrait 4K do Leo usando novas fotos de referência (sem óculos)."""

import os
import base64
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ["GEMINI_API_KEY"]
REF1 = Path("/Users/marcofassa/Downloads/IMG_2007_small.png")
REF2 = Path("/Users/marcofassa/Downloads/IMG_2024_small.png")
OUTPUT_DIR = Path("/Users/marcofassa/Documents/growth-contele/thumbnail-ai-creator/output")
OUT_PATH = OUTPUT_DIR / "teams_leo_face_v2_studio.png"

client = genai.Client(api_key=API_KEY)

PROMPT = """Using these two photos as strict face references, generate a high-quality 4K professional studio portrait of the same man.

CRITICAL — MUST MATCH THE REFERENCE FACES EXACTLY:
- Round/oval face shape with fuller cheeks — MATCH THE REFERENCE
- Short dark brown hair with natural gray streaks on the sides — MATCH THE REFERENCE
- NO glasses — clean face, no eyewear (as shown in reference photos)
- Dark brown eyes — MATCH THE REFERENCE
- Clean shaven — no beard, no stubble
- Age: 43-48 years old, natural mature appearance — do NOT make him younger
- Same skin tone, same facial proportions — COPY FROM REFERENCES

SHOT:
- Close-up portrait, face and upper shoulders only
- Direct frontal gaze, confident and warm expression — slight natural smile
- Slight forward lean toward camera

LIGHTING & BACKGROUND:
- Professional studio lighting: soft key light from the right, subtle fill from left
- Clean dark charcoal/near-black backdrop, very slight gradient
- Cinematic depth — background slightly defocused

QUALITY:
- 4K resolution, ultra-sharp facial detail
- Photorealistic skin texture — pores, natural imperfections, no over-smoothing
- Professional headshot / editorial photography quality

NO text overlays. Output: portrait only."""

print(f"Gerando studio portrait 4K do Leonardo com 2 novas refs...")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        types.Content(parts=[
            types.Part(inline_data=types.Blob(mime_type="image/png", data=REF1.read_bytes())),
            types.Part(inline_data=types.Blob(mime_type="image/png", data=REF2.read_bytes())),
            types.Part(text=PROMPT),
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    ),
)

saved = False
for part in response.candidates[0].content.parts:
    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
        OUT_PATH.write_bytes(part.inline_data.data)
        print(f"Salvo: {OUT_PATH}")
        saved = True
        break

if not saved:
    print("Resposta texto:", response.text)
    raise RuntimeError("Nenhuma imagem retornada.")

subprocess.run(["open", "-R", str(OUT_PATH)])
print("Aberto no Finder.")
