#!/usr/bin/env python3
"""
blog.py — YouTube to Blog: transforma videos em posts WordPress.

Pipeline: URL > transcript > Gemini blog > imagem IA > WordPress > WhatsApp

Integrado ao PRISM OS. Usa suggest.py para transcript (3-tier fallback).
"""

import os
import re
import json
import base64
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

PROJECT_DIR = Path(__file__).parent

def _load_key(name: str) -> str:
    """Carrega key de env var ou .env local."""
    val = os.environ.get(name)
    if val:
        return val
    env_path = PROJECT_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith(name):
                    return line.split("=", 1)[1].strip().strip('"')
    return ""


GEMINI_API_KEY = _load_key("GEMINI_NANO_BANANA_KEY") or _load_key("GEMINI_API_KEY")
YOUTUBE_API_KEY = _load_key("YOUTUBE_API_KEY")

# WordPress
WP_CONFIG = {
    "fleet": {
        "url": "https://blog.contelerastreador.com.br",
        "user": "Admin",
        "password": _load_key("WP_FLEET_APP_PASSWORD"),
        "logo_url": "https://images.contelege.com.br/Conteudos/FPT/frota-para-todos-2025.png",
        "categories": [839],
    },
    "teams": {
        "url": "https://blog.conteleteams.com.br",
        "user": "lgazolli",
        "password": _load_key("WP_TEAMS_APP_PASSWORD"),
        "logo_url": "https://images.contelege.com.br/logo-contele-teams-branco-250x150px.png",
        "categories": [175],
    },
    "fpt_portal": {
        "url": "https://noticias.frotaparatodos.com.br",
        "user": "admin",
        "password": _load_key("WP_FPT_APP_PASSWORD"),
        "logo_url": "https://images.contelege.com.br/Conteudos/FPT/frota-para-todos-2025.png",
        "categories": [],  # preencher com IDs reais após criar categorias no WP admin
        "status": "pending",  # curadoria humana obrigatória antes de publicar
    },
}

# Evolution API (WhatsApp)
EVOLUTION_API_ENDPOINT = _load_key("EVOLUTION_API_ENDPOINT")
EVOLUTION_API_KEY_VAL = _load_key("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "Vendas%20n2")

WHATSAPP_GROUPS = {
    "fleet": [
        "120363040705704064@g.us",   # VIP | Frota Para Todos
        "120363298313504328@g.us",   # Fleet | CS | Produto
        "120363305098835612@g.us",   # Fleet Vendas CEO
    ],
    "teams": [
        "120363304219016321@g.us",   # Teams Vendas CEO
        "120363298722268756@g.us",   # Teams | CS | Produto
    ],
    "fpt_portal": [
        "120363040705704064@g.us",   # VIP | Frota Para Todos
    ],
}

# Gemini
GEMINI_TEXT_MODEL = "gemini-3.1-pro-preview"
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


# -------------------------------------------------------------------
# Gemini helpers
# -------------------------------------------------------------------

def call_gemini(prompt: str, model: str = None) -> str:
    if model is None:
        model = GEMINI_TEXT_MODEL
    url = f"{GEMINI_API_URL}/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Gemini error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def generate_image(prompt: str) -> bytes:
    url = f"{GEMINI_API_URL}/{GEMINI_IMAGE_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["image", "text"],
            "imageConfig": {"aspectRatio": "16:9"},
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Gemini Image error {resp.status_code}")
    for part in resp.json()["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise Exception("Nenhuma imagem gerada")


# -------------------------------------------------------------------
# YouTube metadata
# -------------------------------------------------------------------

def get_video_metadata(video_id: str) -> dict:
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part": "snippet,contentDetails,statistics", "id": video_id, "key": YOUTUBE_API_KEY}
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"YouTube API error: {resp.status_code}")
    data = resp.json()
    if not data.get("items"):
        raise Exception(f"Video nao encontrado: {video_id}")
    video = data["items"][0]
    duration_iso = video["contentDetails"]["duration"]
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    hours = int(match.group(1) or 0) if match else 0
    minutes = int(match.group(2) or 0) if match else 0
    duration = f"{hours}h{minutes:02d}min" if hours > 0 else f"{minutes}min"
    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "duration": duration,
        "channel": video["snippet"]["channelTitle"],
    }


# -------------------------------------------------------------------
# WordPress
# -------------------------------------------------------------------

def apply_watermark(image_bytes: bytes, logo_url: str) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    logo_resp = requests.get(logo_url, timeout=15)
    logo = Image.open(BytesIO(logo_resp.content)).convert("RGBA")
    scale = 0.10
    new_w = int(img.size[0] * scale)
    ratio = logo.size[1] / logo.size[0]
    new_h = int(new_w * ratio)
    logo = logo.resize((new_w, new_h), Image.Resampling.LANCZOS)
    alpha = logo.split()[3].point(lambda p: int(p * 0.85))
    logo.putalpha(alpha)
    margin_x = int(img.size[0] * 0.08)
    margin_y = int(img.size[1] * 0.10)
    pos = (img.size[0] - new_w - margin_x, img.size[1] - new_h - margin_y)
    img.paste(logo, pos, logo)
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def upload_image_wordpress(image_bytes: bytes, filename: str, wp_url: str, wp_user: str, wp_password: str) -> int:
    resp = requests.post(
        f"{wp_url}/wp-json/wp/v2/media",
        auth=(wp_user, wp_password),
        files={"file": (filename, image_bytes, "image/png")},
        timeout=60,
    )
    if resp.status_code != 201:
        raise Exception(f"WordPress upload error: {resp.status_code} - {resp.text[:200]}")
    return resp.json()["id"]


def create_wordpress_post(content: dict, media_id: int, wp_url: str, wp_user: str,
                          wp_password: str, categories: list, video_id: str,
                          blog: str, content_type: dict = None, status: str = "publish") -> dict:
    html_content = content["content_html"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    canal = "Eng. Leonardo Gazolli - Equipes Externas" if blog == "teams" else "Julio Cesar | Frota Para Todos"
    if content_type is None:
        content_type = {"titulo_secao": "Assista ao Video Completo", "descricao": "Este artigo foi baseado no video"}
    titulo_secao = content_type.get("titulo_secao", "Assista ao Video Completo")
    descricao_video = content_type.get("descricao", "Este artigo foi baseado no video")
    html_content += f"""
<h2>{titulo_secao}</h2>
<p>{descricao_video} do canal <strong>{canal}</strong>. Clique para assistir:</p>
<a href="{video_url}" target="_blank" rel="noopener" style="display: block; position: relative; max-width: 100%;">
<img src="{thumbnail_url}" alt="Assistir no YouTube" style="width: 100%; border-radius: 8px;">
<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 68px; height: 48px; background: #f00; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
<div style="width: 0; height: 0; border-left: 20px solid white; border-top: 12px solid transparent; border-bottom: 12px solid transparent; margin-left: 4px;"></div>
</div>
</a>
"""
    post_data = {
        "title": content["title"],
        "content": html_content,
        "excerpt": content.get("excerpt", ""),
        "slug": content["slug"],
        "status": status,
        "categories": categories,
        "featured_media": media_id,
    }
    resp = requests.post(f"{wp_url}/wp-json/wp/v2/posts", auth=(wp_user, wp_password), json=post_data, timeout=60)
    if resp.status_code not in [200, 201]:
        raise Exception(f"WordPress post error: {resp.status_code} - {resp.text[:200]}")
    post = resp.json()
    return {
        "post_id": post["id"],
        "post_url": f"{wp_url}/{content['slug']}/",
        "edit_url": f"{wp_url}/wp-admin/post.php?post={post['id']}&action=edit",
    }


# -------------------------------------------------------------------
# WhatsApp
# -------------------------------------------------------------------

def send_whatsapp_to_groups(blog: str, message: str) -> int:
    if not EVOLUTION_API_ENDPOINT or not EVOLUTION_API_KEY_VAL:
        print("[WhatsApp] Credenciais nao configuradas")
        return 0
    groups = WHATSAPP_GROUPS.get(blog, [])
    sent = 0
    for gid in groups:
        try:
            resp = requests.post(
                f"{EVOLUTION_API_ENDPOINT}/message/sendText/{EVOLUTION_INSTANCE}",
                headers={"apikey": EVOLUTION_API_KEY_VAL, "Content-Type": "application/json"},
                json={"number": gid, "text": message},
                timeout=30,
            )
            if resp.status_code == 201:
                sent += 1
                print(f"[WhatsApp] Enviado para {gid}")
        except Exception as e:
            print(f"[WhatsApp] Erro {gid}: {e}")
    return sent


# -------------------------------------------------------------------
# Content type detection
# -------------------------------------------------------------------

def detect_content_type(title: str, description: str = "") -> dict:
    prompt = f"""Analise o titulo e descricao deste video e identifique o tipo de conteudo.

TITULO: {title}
DESCRICAO: {description[:500] if description else "N/A"}

TIPOS: live, podcast, entrevista, webinar, tutorial, video

RESPONDA APENAS em JSON:
{{"tipo": "...", "titulo_secao": "Assista ao Video Completo", "descricao": "Este artigo foi baseado no video..."}}"""
    try:
        result = call_gemini(prompt, model="gemini-3-flash-preview")
        match = re.search(r'\{[^}]+\}', result)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[ContentType] Erro: {e}")
    return {"tipo": "video", "titulo_secao": "Assista ao Video Completo", "descricao": "Este artigo foi baseado no video"}


# -------------------------------------------------------------------
# Image prompt generation
# -------------------------------------------------------------------

def get_image_prompt(blog: str, theme: str) -> str:
    if blog == "teams":
        style = "iPhone 15 Pro smartphone photo, Brazilian professional (30-45yo) checking team data on tablet, real office, natural light, teal dashboard on screen"
    else:
        style = "Canon 5D Mark IV 35mm f/1.8, Brazilian fleet manager (35-50yo), documentary editorial, natural light, shallow depth of field"

    meta_prompt = f"""Create an image generation prompt for a blog article.

TITLE: {theme}
STYLE: {style}
CONTEXT: {"field team management" if blog == "teams" else "fleet management (tracking, fuel, maintenance)"}

The scene must VISUALLY represent the specific topic. Include specific elements from the title.
Subject NOT looking at camera, no stock photo poses.
NO text, watermarks, logos. 16:9 landscape, photorealistic.

Return ONLY the prompt, nothing else."""

    try:
        return call_gemini(meta_prompt, model="gemini-3-flash-preview").strip().strip("`")
    except Exception:
        return f"Professional photograph, {style}, topic: {theme}. No text, 16:9, photorealistic."


# -------------------------------------------------------------------
# Blog prompts
# -------------------------------------------------------------------

def get_blog_prompt(blog: str, titulo: str, duracao: str, transcricao: str) -> str:
    if blog == "teams":
        autor = "Leonardo Gazolli, Engenheiro de Producao especialista em gestao de equipes externas"
        contexto = "gestao de equipes externas (vendedores, tecnicos, promotores)"
        canal = "Eng. Leonardo Gazolli - Equipes Externas"
        cta_base = "https://conteleteams.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live&utm_term="
    elif blog == "fpt_portal":
        autor = "Julio Cesar, especialista em gestao de frotas"
        contexto = "gestao de frotas (rastreamento, combustivel, manutencao, motoristas)"
        canal = "Julio Cesar | Frota Para Todos"
        cta_base = "https://frotaparatodos.com.br/?utm_source=portal&utm_medium=post&utm_campaign=youtube&utm_term="
    else:  # fleet (default)
        autor = "Julio Cesar, especialista em gestao de frotas"
        contexto = "gestao de frotas (rastreamento, combustivel, manutencao, motoristas)"
        canal = "Julio Cesar | Frota Para Todos"
        cta_base = "https://contelerastreador.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live&utm_term="

    return f"""Voce e o {autor}, escrevendo para o blog em primeira pessoa.

Transforme esta transcricao em artigo de blog otimizado para SEO.

## VIDEO
- Titulo: {titulo}
- Canal: {canal}
- Duracao: {duracao}

## TRANSCRICAO
{transcricao[:25000]}

## TOM E ESTILO
- Escreva como ESPECIALISTA compartilhando experiencia pratica, NAO como vendedor
- EVITE: "garantir", "revolucionar", "transformar", "infalivel", "segredo", "definitivo"
- Reconheca desafios e limitacoes quando relevante
- Baseie-se nos exemplos CONCRETOS da transcricao
- Tom: profissional e educativo, como conversa entre colegas
- NAO pareca texto gerado por IA

## REQUISITOS
1. Titulo descritivo com keyword principal
2. 1.500-2.000 palavras
3. H2/H3 para estrutura
4. FAQ section
5. CTA final com link: {cta_base}[SLUG]
6. Contexto: {contexto}
7. Estamos em 2026
8. Links com target="_blank" rel="noopener"
9. NUNCA "Contele Rastreador", usar "Contele Fleet"

## FORMATO JSON
{{
    "title": "Titulo H1",
    "slug": "url-amigavel",
    "meta_description": "150-160 chars",
    "excerpt": "Resumo curto",
    "content_html": "<p>Hook...</p><h2>...</h2>...",
    "primary_keyword": "keyword principal"
}}"""


def get_whatsapp_prompt(title: str, url: str) -> str:
    return f"""Crie mensagem WhatsApp impossivel de ignorar.

POST: "{title}"
URL: {url}

FORMULA: [Afirmacao provocativa] + [Gancho de curiosidade] + [Link]

PROIBIDO: descubra, confira, acesse, clique, saiba mais, saudacoes, emojis no inicio

FORMATO: 2 frases curtas + link. Max 200 chars antes do link. Tom: insider revelando segredo.

RETORNE APENAS A MENSAGEM."""


# -------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------

def generate_blog_post(video_id: str, blog: str, transcript: str = None,
                       progress_cb=None) -> dict:
    """Pipeline completo: video -> blog post publicado."""

    def emit(step, msg):
        if progress_cb:
            progress_cb({"step": step, "message": msg})
        print(f"  [blog] {step}: {msg}")

    # 1. Transcript
    if transcript:
        emit("transcript", "Usando transcricao fornecida")
    else:
        emit("transcript", "Buscando transcricao...")
        from suggest import extract_video_id, get_transcript_with_timestamps, build_transcript_text
        vid = extract_video_id(video_id)
        segments = get_transcript_with_timestamps(vid, channel=blog)
        transcript = " ".join(s["text"] for s in segments)
        emit("transcript", f"OK ({len(segments)} segmentos)")

    # 2. Metadata
    emit("metadata", "Buscando metadados do video...")
    metadata = get_video_metadata(video_id)
    emit("metadata", f"OK: {metadata['title']}")

    # 3. Generate blog content
    emit("content", "Gerando artigo com IA...")
    blog_prompt = get_blog_prompt(blog, metadata["title"], metadata["duration"], transcript)
    content_raw = call_gemini(blog_prompt)
    json_match = re.search(r'\{[\s\S]*\}', content_raw)
    if not json_match:
        raise Exception("Falha ao gerar conteudo JSON")
    json_str = json_match.group()
    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
    content = json.loads(json_str)
    emit("content", f"OK: {content['title']}")

    # 4. Generate featured image
    emit("image", "Gerando imagem de capa...")
    image_prompt = get_image_prompt(blog, metadata["title"])
    image_bytes = generate_image(image_prompt)
    wp = WP_CONFIG[blog]
    image_with_watermark = apply_watermark(image_bytes, wp["logo_url"])
    emit("image", "OK")

    # 5. Upload image to WordPress
    emit("upload", "Enviando imagem para WordPress...")
    media_id = upload_image_wordpress(
        image_with_watermark,
        f"{content['slug']}-featured.png",
        wp["url"], wp["user"], wp["password"],
    )
    emit("upload", "OK")

    # 6. Detect content type (Teams only)
    content_type = None
    if blog == "teams":
        content_type = detect_content_type(metadata["title"], metadata.get("description", ""))

    # 7. Create WordPress post
    emit("post", "Publicando no WordPress...")
    post_result = create_wordpress_post(
        content, media_id, wp["url"], wp["user"], wp["password"],
        wp["categories"], video_id, blog, content_type,
        status=wp.get("status", "publish"),
    )
    emit("post", f"OK: {post_result['post_url']}")

    # 8. Generate WhatsApp text
    emit("whatsapp", "Gerando texto WhatsApp...")
    whatsapp_prompt = get_whatsapp_prompt(content["title"], post_result["post_url"])
    whatsapp_text = call_gemini(whatsapp_prompt).strip()

    # 9. Send WhatsApp
    emit("whatsapp", "Enviando para grupos...")
    sent = send_whatsapp_to_groups(blog, whatsapp_text)
    emit("whatsapp", f"OK ({sent} grupos)")

    return {
        "status": "success",
        "post_id": post_result["post_id"],
        "post_url": post_result["post_url"],
        "edit_url": post_result["edit_url"],
        "title": content["title"],
        "whatsapp_text": whatsapp_text,
    }
