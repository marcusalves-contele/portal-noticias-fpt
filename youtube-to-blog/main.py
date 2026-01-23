"""
YouTube to Blog API - Transforma videos do YouTube em posts de blog

Endpoints:
- GET /health - Health check
- POST /generate - Gera post a partir de video YouTube
"""

import os
import re
import json
import base64
import requests
from io import BytesIO
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi

# =============================================================================
# CONFIG
# =============================================================================

app = FastAPI(
    title="YouTube to Blog API",
    description="Transforma videos do YouTube em posts de blog otimizados para SEO",
    version="1.0.0"
)

# APIs
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# WordPress Fleet
WP_FLEET_URL = "https://blog.contelerastreador.com.br"
WP_FLEET_USER = "Admin"
WP_FLEET_PASSWORD = os.environ.get("WP_FLEET_APP_PASSWORD")

# WordPress Teams
WP_TEAMS_URL = "https://blog.conteleteams.com.br"
WP_TEAMS_USER = "lgazolli"
WP_TEAMS_PASSWORD = os.environ.get("WP_TEAMS_APP_PASSWORD")

# Gemini
GEMINI_TEXT_MODEL = "gemini-2.0-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Logos
LOGO_FLEET_URL = "https://images.contelege.com.br/Conteudos/FPT/frota-para-todos-2025.png"
LOGO_TEAMS_URL = "https://images.contelege.com.br/logo-contele-teams-branco-250x150px.png"

# =============================================================================
# MODELS
# =============================================================================

class GenerateRequest(BaseModel):
    video_id: str = Field(..., description="ID do video YouTube (11 caracteres)")
    blog: str = Field(..., description="Blog destino: 'fleet' ou 'teams'")

class GenerateResponse(BaseModel):
    status: str
    post_id: Optional[int] = None
    post_url: Optional[str] = None
    edit_url: Optional[str] = None
    title: Optional[str] = None
    whatsapp_text: Optional[str] = None
    error: Optional[str] = None

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {
        "service": "YouTube to Blog API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Gera post a partir de video YouTube",
            "GET /health": "Health check"
        }
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_video_id(url_or_id: str) -> str:
    """Extrai VIDEO_ID de URL ou retorna ID direto"""
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'v=([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"Nao foi possivel extrair VIDEO_ID de: {url_or_id}")


def format_duration(duration_iso: str) -> str:
    """Converte duracao ISO 8601 para formato legivel"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    if not match:
        return duration_iso

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)

    if hours > 0:
        return f"{hours}h{minutes:02d}min"
    return f"{minutes}min"


def get_transcript(video_id: str) -> str:
    """Busca transcricao do video"""
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'pt-BR'])
    return " ".join([segment['text'] for segment in transcript])


def get_video_metadata(video_id: str) -> dict:
    """Busca metadados do video via YouTube API"""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"YouTube API error: {response.status_code}")

    data = response.json()
    if not data.get("items"):
        raise Exception(f"Video nao encontrado: {video_id}")

    video = data["items"][0]
    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "duration": format_duration(video["contentDetails"]["duration"]),
        "channel": video["snippet"]["channelTitle"]
    }


def call_gemini(prompt: str, model: str = None) -> str:
    """Chama Gemini API para texto"""
    if model is None:
        model = GEMINI_TEXT_MODEL

    url = f"{GEMINI_API_URL}/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192}
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code}")

    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


def generate_image(prompt: str) -> bytes:
    """Gera imagem via Gemini"""
    url = f"{GEMINI_API_URL}/{GEMINI_IMAGE_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["image", "text"],
            "imageConfig": {"aspectRatio": "16:9"}
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Gemini Image API error: {response.status_code}")

    result = response.json()
    for part in result["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])

    raise Exception("Nenhuma imagem gerada")


def apply_watermark(image_bytes: bytes, logo_url: str) -> bytes:
    """Aplica watermark na imagem"""
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")

    # Baixa logo
    logo_response = requests.get(logo_url)
    logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")

    # Redimensiona logo (12% da largura)
    scale = 0.12
    new_width = int(img.size[0] * scale)
    ratio = logo.size[1] / logo.size[0]
    new_height = int(new_width * ratio)
    logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Ajusta opacidade
    alpha = logo.split()[3].point(lambda p: int(p * 0.85))
    logo.putalpha(alpha)

    # Posiciona
    margin = 30
    pos = (img.size[0] - new_width - margin, img.size[1] - new_height - margin)
    img.paste(logo, pos, logo)

    # Converte para bytes
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def upload_image_wordpress(image_bytes: bytes, filename: str, wp_url: str, wp_user: str, wp_password: str) -> int:
    """Upload imagem para WordPress e retorna media_id"""
    response = requests.post(
        f"{wp_url}/wp-json/wp/v2/media",
        auth=(wp_user, wp_password),
        files={"file": (filename, image_bytes, "image/png")}
    )

    if response.status_code != 201:
        raise Exception(f"WordPress upload error: {response.status_code} - {response.text[:200]}")

    return response.json()["id"]


def create_wordpress_post(content: dict, media_id: int, wp_url: str, wp_user: str, wp_password: str, categories: list) -> dict:
    """Cria post no WordPress"""
    post_data = {
        "title": content["title"],
        "content": content["content_html"],
        "excerpt": content.get("excerpt", ""),
        "slug": content["slug"],
        "status": "publish",
        "categories": categories,
        "featured_media": media_id
    }

    response = requests.post(
        f"{wp_url}/wp-json/wp/v2/posts",
        auth=(wp_user, wp_password),
        json=post_data
    )

    if response.status_code not in [200, 201]:
        raise Exception(f"WordPress post error: {response.status_code} - {response.text[:200]}")

    post = response.json()
    return {
        "post_id": post["id"],
        "post_url": f"{wp_url}/{content['slug']}/",
        "edit_url": f"{wp_url}/wp-admin/post.php?post={post['id']}&action=edit"
    }


# =============================================================================
# PROMPTS (importados dos scripts originais - simplificados para API)
# =============================================================================

def get_blog_prompt(blog: str, titulo: str, duracao: str, transcricao: str) -> str:
    """Retorna prompt para geracao do post"""

    if blog == "teams":
        autor = "Leonardo Gazolli, Engenheiro de Producao especialista em gestao de equipes externas"
        contexto = "gestao de equipes externas (vendedores, tecnicos, promotores)"
        canal = "Eng. Leonardo Gazolli - Equipes Externas"
        cta_url = "https://conteleteams.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live"
    else:
        autor = "Julio Cesar, especialista em gestao de frotas"
        contexto = "gestao de frotas (rastreamento, combustivel, manutencao, motoristas)"
        canal = "Julio Cesar | Frota Para Todos"
        cta_url = "https://contelerastreador.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live"

    return f"""Voce e o {autor}, escrevendo para o blog em primeira pessoa.

Transforme esta transcricao em artigo de blog otimizado para SEO.

## VIDEO
- Titulo: {titulo}
- Canal: {canal}
- Duracao: {duracao}

## TRANSCRICAO
{transcricao[:25000]}

## REQUISITOS
1. Titulo com numero + beneficio + keyword
2. Hook forte nos primeiros paragrafos (SEM H2 "Introducao")
3. 1.500-2.000 palavras
4. H2/H3 para estrutura
5. FAQ section
6. CTA final com link: {cta_url}
7. Tom conversacional, primeira pessoa
8. Contexto: {contexto}

## FORMATO JSON
{{
    "title": "Titulo H1",
    "slug": "url-amigavel",
    "meta_description": "150-160 chars",
    "excerpt": "Resumo curto",
    "content_html": "<p>Hook...</p><h2>...</h2>...",
    "primary_keyword": "keyword principal"
}}
"""


def get_image_prompt(blog: str, theme: str) -> str:
    """Retorna prompt para geracao de imagem"""

    if blog == "teams":
        return f"""Candid smartphone photograph of a real person at work managing their field team.

Topic: {theme}

Style: iPhone 15 Pro photograph - natural, authentic, not staged.
Scene: Brazilian professional (30-45yo) casually checking team data on tablet/phone.
Setting: Real office, natural daylight, some desk details.
Device shows: Teal/blue dashboard with charts or map.

Requirements:
- NO text or watermarks
- NOT looking at camera
- NO stock photo poses
- Authentic corporate photography feel

Output: 16:9 landscape, photorealistic."""
    else:
        return f"""Professional photograph for fleet management blog.

Topic: {theme}

Scene: Brazilian fleet manager reviewing vehicle data on tablet/laptop.
Setting: Modern office or operations center.
Screen shows: Dashboard with routes, vehicles, metrics.

Style: Corporate photography, natural lighting, shallow depth of field.

Requirements:
- NO text or watermarks
- Authentic, not staged
- Professional but approachable

Output: 16:9 landscape, photorealistic."""


def get_whatsapp_prompt(title: str, url: str) -> str:
    """Retorna prompt para texto WhatsApp"""
    return f"""Crie mensagem CURTA (3-4 linhas) para WhatsApp divulgando este post:

POST: "{title}"
URL: {url}

REGRAS:
- Hook forte na primeira linha
- Max 1 emoji
- SEM "confira", "nao perca"
- Tom de colega indicando conteudo util

RETORNE APENAS O TEXTO."""


# =============================================================================
# MAIN ENDPOINT
# =============================================================================

@app.post("/generate", response_model=GenerateResponse)
async def generate_post(request: GenerateRequest):
    """Gera post de blog a partir de video YouTube"""

    try:
        # Validacao
        video_id = extract_video_id(request.video_id)
        blog = request.blog.lower()

        if blog not in ["fleet", "teams"]:
            raise HTTPException(status_code=400, detail="blog deve ser 'fleet' ou 'teams'")

        # Config baseada no blog
        if blog == "teams":
            wp_url = WP_TEAMS_URL
            wp_user = WP_TEAMS_USER
            wp_password = WP_TEAMS_PASSWORD
            logo_url = LOGO_TEAMS_URL
            categories = [175]  # Produtividade
        else:
            wp_url = WP_FLEET_URL
            wp_user = WP_FLEET_USER
            wp_password = WP_FLEET_PASSWORD
            logo_url = LOGO_FLEET_URL
            categories = [839]  # Gestao de frotas

        # 1. Transcricao
        transcript = get_transcript(video_id)

        # 2. Metadados
        metadata = get_video_metadata(video_id)

        # 3. Gerar conteudo
        blog_prompt = get_blog_prompt(blog, metadata["title"], metadata["duration"], transcript)
        content_raw = call_gemini(blog_prompt)

        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', content_raw)
        if not json_match:
            raise Exception("Falha ao gerar conteudo JSON")
        content = json.loads(json_match.group())

        # 4. Gerar imagem
        image_prompt = get_image_prompt(blog, metadata["title"])
        image_bytes = generate_image(image_prompt)
        image_with_watermark = apply_watermark(image_bytes, logo_url)

        # 5. Upload imagem
        media_id = upload_image_wordpress(
            image_with_watermark,
            f"{content['slug']}-featured.png",
            wp_url, wp_user, wp_password
        )

        # 6. Criar post
        post_result = create_wordpress_post(content, media_id, wp_url, wp_user, wp_password, categories)

        # 7. Gerar texto WhatsApp
        whatsapp_prompt = get_whatsapp_prompt(content["title"], post_result["post_url"])
        whatsapp_text = call_gemini(whatsapp_prompt).strip()

        return GenerateResponse(
            status="success",
            post_id=post_result["post_id"],
            post_url=post_result["post_url"],
            edit_url=post_result["edit_url"],
            title=content["title"],
            whatsapp_text=whatsapp_text
        )

    except Exception as e:
        return GenerateResponse(
            status="error",
            error=str(e)
        )


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
