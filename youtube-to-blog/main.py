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
from fastapi.responses import JSONResponse, HTMLResponse
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
WP_FLEET_URL = "https://blog.contelefleet.com.br"
WP_FLEET_USER = "Admin"
WP_FLEET_PASSWORD = os.environ.get("WP_FLEET_APP_PASSWORD")

# WordPress Teams
WP_TEAMS_URL = "https://blog.conteleteams.com.br"
WP_TEAMS_USER = "lgazolli"
WP_TEAMS_PASSWORD = os.environ.get("WP_TEAMS_APP_PASSWORD")

# Evolution API (WhatsApp)
EVOLUTION_API_ENDPOINT = os.environ.get("EVOLUTION_API_ENDPOINT")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "Vendas%20n2")

# Grupos WhatsApp por produto (IDs da instancia Vendas n2)
WHATSAPP_GROUPS = {
    "fleet": [
        "120363040705704064@g.us",   # VIP | Frota Para Todos
        "120363298313504328@g.us",   # Fleet | CS | Produto
        "120363305098835612@g.us",   # Fleet Vendas CEO
    ],
    "teams": [
        "120363304219016321@g.us",   # Teams Vendas CEO
        "120363298722268756@g.us",   # Teams | CS | Produto
    ]
}

# Gemini
GEMINI_TEXT_MODEL = "gemini-3-pro-preview"
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
    transcript: Optional[str] = Field(None, description="Transcricao opcional (usar se auto-fetch falhar)")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube to Blog</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 600px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 5px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        input, select, textarea { width: 100%; padding: 12px; border: 1px solid #ddd;
                                   border-radius: 6px; font-size: 16px; }
        textarea { min-height: 100px; resize: vertical; }
        button { width: 100%; padding: 14px; background: #2563eb; color: white;
                 border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        button:disabled { background: #94a3b8; cursor: not-allowed; }
        .result { margin-top: 20px; padding: 20px; background: white; border-radius: 6px;
                  border: 1px solid #ddd; display: none; }
        .result.success { border-color: #22c55e; }
        .result.error { border-color: #ef4444; }
        .result h3 { margin-top: 0; }
        .result a { color: #2563eb; }
        .spinner { display: none; }
        .loading .spinner { display: inline-block; margin-left: 10px; }
        .loading button span { display: none; }
        .note { font-size: 13px; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>YouTube to Blog</h1>
    <p class="subtitle">Transforma videos em posts de blog</p>

    <form id="form">
        <div class="form-group">
            <label for="video_id">URL ou ID do Video</label>
            <input type="text" id="video_id" placeholder="https://youtube.com/watch?v=... ou ID" required>
        </div>

        <div class="form-group">
            <label for="blog">Blog Destino</label>
            <select id="blog" required>
                <option value="fleet">Fleet (blog.contelefleet.com.br)</option>
                <option value="teams">Teams (blog.conteleteams.com.br)</option>
            </select>
        </div>

        <div class="form-group">
            <label for="transcript">Transcricao (opcional)</label>
            <textarea id="transcript" placeholder="Deixe vazio para buscar automaticamente..."></textarea>
            <p class="note">A transcricao sera buscada automaticamente do YouTube.</p>
        </div>

        <button type="submit" id="btn">
            <span>Gerar Post</span>
            <span class="spinner">Gerando...</span>
        </button>
    </form>

    <div id="result" class="result"></div>

    <script>
        const form = document.getElementById('form');
        const btn = document.getElementById('btn');
        const result = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            btn.disabled = true;
            btn.classList.add('loading');
            result.style.display = 'none';

            const data = {
                video_id: document.getElementById('video_id').value,
                blog: document.getElementById('blog').value
            };
            const transcript = document.getElementById('transcript').value.trim();
            if (transcript) data.transcript = transcript;

            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const json = await res.json();

                result.style.display = 'block';
                if (json.status === 'success') {
                    result.className = 'result success';
                    result.innerHTML = `
                        <h3>Post Criado!</h3>
                        <p><strong>Titulo:</strong> ${json.title}</p>
                        <p><strong>URL:</strong> <a href="${json.post_url}" target="_blank">${json.post_url}</a></p>
                        <p><strong>Editar:</strong> <a href="${json.edit_url}" target="_blank">WordPress Admin</a></p>
                        <hr style="margin: 15px 0; border: none; border-top: 1px solid #eee;">
                        <p><strong>Texto WhatsApp:</strong></p>
                        <pre style="background:#f5f5f5;padding:10px;border-radius:4px;white-space:pre-wrap;font-size:14px;">${json.whatsapp_text || ''}</pre>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `<h3>Erro</h3><p>${json.error}</p>`;
                }
            } catch (err) {
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = `<h3>Erro</h3><p>${err.message}</p>`;
            }

            btn.disabled = false;
            btn.classList.remove('loading');
        });
    </script>
</body>
</html>"""

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
    """Busca transcricao do video (PT preferido, EN fallback)"""
    try:
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id, languages=['pt', 'pt-BR', 'en'])
        segments = list(result)
        return " ".join([s.text for s in segments])
    except Exception as e:
        error_msg = str(e)
        if "blocking" in error_msg.lower() or "ip" in error_msg.lower():
            raise Exception(
                "YouTube bloqueou o IP do servidor. "
                "Use o parametro 'transcript' com a transcricao do video. "
                "Obtenha a transcricao em: https://www.youtube.com/watch?v=" + video_id
            )
        raise


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
    """Aplica watermark na imagem com margem segura para thumbnails"""
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")

    # Baixa logo
    logo_response = requests.get(logo_url)
    logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")

    # Redimensiona logo (10% da largura - um pouco menor para caber melhor)
    scale = 0.10
    new_width = int(img.size[0] * scale)
    ratio = logo.size[1] / logo.size[0]
    new_height = int(new_width * ratio)
    logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Ajusta opacidade
    alpha = logo.split()[3].point(lambda p: int(p * 0.85))
    logo.putalpha(alpha)

    # Posiciona com margem segura (10% da dimensao para evitar corte em thumbnails)
    # WordPress faz crop para thumbnails, entao o logo precisa estar na "safe zone"
    margin_x = int(img.size[0] * 0.08)  # 8% da largura
    margin_y = int(img.size[1] * 0.10)  # 10% da altura
    pos = (img.size[0] - new_width - margin_x, img.size[1] - new_height - margin_y)
    img.paste(logo, pos, logo)

    # Converte para bytes
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def send_whatsapp_message(group_id: str, message: str) -> bool:
    """Envia mensagem para grupo WhatsApp via Evolution API"""
    if not EVOLUTION_API_ENDPOINT or not EVOLUTION_API_KEY:
        print(f"[WhatsApp] Credenciais nao configuradas, pulando envio para {group_id}")
        return False

    try:
        url = f"{EVOLUTION_API_ENDPOINT}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": group_id,
            "text": message
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 201:
            print(f"[WhatsApp] Mensagem enviada para {group_id}")
            return True
        else:
            print(f"[WhatsApp] Erro ao enviar para {group_id}: {response.status_code}")
            return False
    except Exception as e:
        print(f"[WhatsApp] Excecao ao enviar para {group_id}: {e}")
        return False


def send_whatsapp_to_groups(blog: str, message: str) -> int:
    """Envia mensagem para todos os grupos do produto"""
    groups = WHATSAPP_GROUPS.get(blog, [])
    sent_count = 0

    for group_id in groups:
        if send_whatsapp_message(group_id, message):
            sent_count += 1

    return sent_count


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


def detect_content_type(title: str, description: str = "") -> dict:
    """Usa IA para detectar o tipo de conteudo do video"""
    prompt = f"""Analise o titulo e descricao deste video do YouTube e identifique o tipo de conteudo.

TITULO: {title}
DESCRICAO: {description[:500] if description else "N/A"}

TIPOS POSSIVEIS:
- live: Transmissao ao vivo, live stream
- podcast: Episodio de podcast, bate-papo, conversa
- entrevista: Entrevista com convidado, case de cliente
- webinar: Webinar, aula, workshop
- tutorial: Tutorial, como fazer, passo a passo
- video: Video comum (quando nao se encaixa nos outros)

RESPONDA APENAS em JSON:
{{"tipo": "live|podcast|entrevista|webinar|tutorial|video", "titulo_secao": "Assista ao Video Completo", "descricao": "Este artigo foi baseado no video..."}}

EXEMPLOS:
- "LIVE #45: Gestao de Frotas" -> {{"tipo": "live", "titulo_secao": "Assista a Live Completa", "descricao": "Este artigo foi baseado na live"}}
- "Podcast EP12: Entrevista com Joao" -> {{"tipo": "podcast", "titulo_secao": "Ouca o Episodio Completo", "descricao": "Este artigo foi baseado no episodio do podcast"}}
- "Case: Como a Empresa X reduziu custos" -> {{"tipo": "entrevista", "titulo_secao": "Assista a Entrevista Completa", "descricao": "Este artigo foi baseado na entrevista"}}
"""
    try:
        result = call_gemini(prompt, model="gemini-3-flash-preview")
        # Extrai JSON da resposta
        json_match = re.search(r'\{[^}]+\}', result)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[ContentType] Erro na deteccao, usando padrao: {e}")

    # Fallback padrao
    return {
        "tipo": "video",
        "titulo_secao": "Assista ao Video Completo",
        "descricao": "Este artigo foi baseado no video"
    }


def create_wordpress_post(content: dict, media_id: int, wp_url: str, wp_user: str, wp_password: str, categories: list, video_id: str, blog: str, content_type: dict = None) -> dict:
    """Cria post no WordPress"""
    html_content = content["content_html"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    # Define canal baseado no blog
    canal = "Eng. Leonardo Gazolli - Equipes Externas" if blog == "teams" else "Julio Cesar | Frota Para Todos"

    # Usa tipo de conteudo detectado ou padrao
    if content_type is None:
        content_type = {"titulo_secao": "Assista ao Video Completo", "descricao": "Este artigo foi baseado no video"}

    titulo_secao = content_type.get("titulo_secao", "Assista ao Video Completo")
    descricao_video = content_type.get("descricao", "Este artigo foi baseado no video")

    # Adiciona thumbnail clicavel do YouTube ao final
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
        cta_base = "https://conteleteams.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live&utm_term="
    else:
        autor = "Julio Cesar, especialista em gestao de frotas"
        contexto = "gestao de frotas (rastreamento, combustivel, manutencao, motoristas)"
        canal = "Julio Cesar | Frota Para Todos"
        cta_base = "https://contelefleet.com.br/?utm_source=blog&utm_medium=post&utm_campaign=youtube-live&utm_term="

    return f"""Voce e o {autor}, escrevendo para o blog em primeira pessoa.

Transforme esta transcricao em artigo de blog otimizado para SEO.

## VIDEO
- Titulo: {titulo}
- Canal: {canal}
- Duracao: {duracao}

## TRANSCRICAO
{transcricao[:25000]}

## TOM E ESTILO (MUITO IMPORTANTE)
- Escreva como ESPECIALISTA compartilhando experiencia pratica, NAO como vendedor
- EVITE palavras: "garantir", "revolucionar", "transformar", "infalivel", "segredo", "definitivo"
- EVITE promessas de resultados ou beneficios exagerados
- Reconheca desafios, limitacoes e nuances quando relevante
- Baseie-se nos exemplos CONCRETOS e dados mencionados na transcricao
- Tom: profissional e educativo, como conversa entre colegas de profissao
- Prefira "pode ajudar" em vez de "vai garantir"
- Prefira "na minha experiencia" em vez de "sempre funciona"
- NAO pareca texto gerado por IA - seja natural e realista

## REQUISITOS
1. Titulo descritivo com keyword principal (EVITE clickbait e promessas)
2. Introducao que contextualize o assunto de forma natural (SEM promessas exageradas)
3. 1.500-2.000 palavras
4. H2/H3 para estrutura
5. FAQ section com duvidas reais do publico
6. CTA final com link: {cta_base}[SLUG] (substitua [SLUG] pelo slug que voce gerar)
7. Tom conversacional, primeira pessoa
8. Contexto: {contexto}
9. IMPORTANTE: Estamos em 2026. Use "2026" para referencias ao ano atual (NAO use 2024 ou 2025)
10. TODOS os links devem ter target="_blank" rel="noopener" para abrir em nova aba
11. NUNCA escreva "Contele Rastreador". O nome correto do produto e "Contele Fleet". Use sempre "Contele Fleet" quando referenciar a empresa/produto

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


def generate_image_prompt_with_ai(blog: str, theme: str) -> str:
    """Usa IA para analisar o tema e criar prompt de imagem contextualizado"""

    if blog == "teams":
        context = "gestao de equipes externas (vendedores, tecnicos, promotores)"
        style_guide = """
ESTILO TEAMS:
- Foto estilo smartphone (iPhone 15 Pro) - natural, autentica
- Profissional brasileiro (30-45 anos) verificando dados da equipe em tablet/celular
- Ambiente: escritorio real, luz natural
- Tela mostra: dashboard teal/azul com graficos ou mapa
- NOT looking at camera, sem poses de stock photo"""
    else:
        context = "gestao de frotas (rastreamento, combustivel, manutencao, motoristas)"
        style_guide = """
ESTILO FLEET:
- Foto documental/editorial profissional (Canon 5D Mark IV, 35mm f/1.8)
- Gestor de frotas brasileiro (35-50 anos) em ambiente de trabalho REAL relacionado ao tema
- Luz natural, profundidade de campo rasa
- NOT looking at camera, momento capturado naturalmente
- O CENARIO deve mostrar elementos ESPECIFICOS do tema (ex: se fala de caldeira movel, mostrar caldeira movel; se fala de manutencao, mostrar oficina)"""

    meta_prompt = f"""Voce e um especialista em criar prompts para geracao de imagens.

TAREFA: Analisar o titulo do artigo e criar um prompt de imagem que represente VISUALMENTE o tema especifico.

TITULO DO ARTIGO: {theme}
CONTEXTO: {context}

{style_guide}

INSTRUCOES:
1. Identifique o ELEMENTO PRINCIPAL do titulo (ex: "caldeira movel", "abastecimento", "manutencao preventiva")
2. Crie uma cena que MOSTRE esse elemento de forma realista
3. Inclua um profissional brasileiro interagindo com o cenario
4. A cena deve ser especifica, NAO generica

FORMATO DE RESPOSTA (retorne APENAS o prompt, sem explicacoes):
Professional documentary-style photograph for fleet management blog.

ARTICLE TOPIC: [tema]

SCENE: [descricao detalhada da cena com elementos especificos do tema]
SETTING: [ambiente especifico relacionado ao tema]

SUBJECT: Brazilian fleet professional (35-50yo), business casual.
POSE: Actively engaged, NOT looking at camera.

TECHNICAL:
- Natural lighting, shallow depth of field
- Warm professional color grading

STRICT REQUIREMENTS:
- NO text, watermarks, logos
- NO stock photo poses
- Background must show specific elements related to: [tema]

OUTPUT: 16:9 landscape, photorealistic."""

    try:
        # Usa modelo de texto rapido para gerar o prompt
        generated_prompt = call_gemini(meta_prompt, model="gemini-3-flash-preview")
        # Limpa o prompt (remove markdown se houver)
        generated_prompt = generated_prompt.strip()
        if generated_prompt.startswith("```"):
            generated_prompt = "\n".join(generated_prompt.split("\n")[1:-1])
        print(f"[ImagePrompt] Prompt gerado por IA para: {theme[:50]}...")
        return generated_prompt
    except Exception as e:
        print(f"[ImagePrompt] Fallback para prompt estatico: {e}")
        return get_image_prompt_fallback(blog, theme)


def get_image_prompt_fallback(blog: str, theme: str) -> str:
    """Fallback: prompt estatico caso a geracao por IA falhe"""

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
        return f"""Professional documentary-style photograph for fleet management blog article.

ARTICLE TOPIC: {theme}

SCENE: Brazilian fleet manager (35-50yo) actively working in environment related to: {theme}
SETTING: Professional fleet operations environment with relevant equipment visible

SUBJECT: Brazilian male fleet professional (35-50 years old), wearing business casual.
POSE: Actively engaged with work, natural posture, NOT looking at camera.

TECHNICAL:
- Natural lighting, shallow depth of field
- Warm professional color grading

STRICT REQUIREMENTS:
- NO text, watermarks, logos or overlays
- NO stock photo staging
- Background must relate to the topic: {theme}

OUTPUT: 16:9 landscape, photorealistic, editorial quality."""


def get_image_prompt(blog: str, theme: str) -> str:
    """Retorna prompt para geracao de imagem - usa IA para contextualizar"""
    return generate_image_prompt_with_ai(blog, theme)


def get_whatsapp_prompt(title: str, url: str) -> str:
    """Retorna prompt para texto WhatsApp com copywriting persuasivo"""
    return f"""Voce e um copywriter expert. Crie uma mensagem WhatsApp IMPOSSIVEL de ignorar.

POST: "{title}"
URL: {url}

MODELO MENTAL (Simon Sinek):
Comece pelo PORQUE. Por que o gestor deveria se importar com isso AGORA?

FORMULA:
[Afirmacao provocativa sobre o problema] + [Gancho de curiosidade incompleto] + [Link]

BONS EXEMPLOS:
"Caldeira movel e um buraco negro de combustivel. A menos que voce faca isso aqui.
{url}"

"Gestores experientes erram nisso o tempo todo. E so percebem quando olham o fechamento do mes.
{url}"

"Se voce acha que controla o combustivel da sua frota, esse artigo vai te surpreender.
{url}"

PALAVRAS PROIBIDAS:
- descubra, confira, acesse, clique, saiba mais, nao perca
- voce sabia, e importante, precisamos falar
- qualquer saudacao (oi, pessoal, galera)
- emojis no inicio

FORMATO:
- 2 frases curtas + link
- Maximo 200 caracteres antes do link
- Tom: insider revelando segredo, nao vendedor

RETORNE APENAS A MENSAGEM, NADA MAIS."""


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

        # 1. Transcricao (usa fornecida ou busca automaticamente)
        if request.transcript:
            transcript = request.transcript
        else:
            transcript = get_transcript(video_id)

        # 2. Metadados
        metadata = get_video_metadata(video_id)

        # 3. Gerar conteudo
        blog_prompt = get_blog_prompt(blog, metadata["title"], metadata["duration"], transcript)
        content_raw = call_gemini(blog_prompt)

        # Parse JSON (com limpeza de caracteres problematicos)
        json_match = re.search(r'\{[\s\S]*\}', content_raw)
        if not json_match:
            raise Exception("Falha ao gerar conteudo JSON")

        json_str = json_match.group()
        # Remove newlines dentro de strings JSON (causa erro de parse)
        json_str = re.sub(r'(?<!\\)\n(?=(?:[^"]*"[^"]*")*[^"]*$)', ' ', json_str)
        # Tenta parse, se falhar tenta limpar mais
        try:
            content = json.loads(json_str)
        except json.JSONDecodeError:
            # Tenta extrair apenas o primeiro objeto JSON valido
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)  # Remove control chars
            content = json.loads(json_str)

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

        # 6. Detectar tipo de conteudo (apenas Teams - tem podcasts, entrevistas, etc)
        content_type = None
        if blog == "teams":
            content_type = detect_content_type(metadata["title"], metadata.get("description", ""))
            print(f"[ContentType] Detectado: {content_type.get('tipo', 'video')}")

        # 7. Criar post
        post_result = create_wordpress_post(content, media_id, wp_url, wp_user, wp_password, categories, video_id, blog, content_type)

        # 8. Gerar texto WhatsApp
        whatsapp_prompt = get_whatsapp_prompt(content["title"], post_result["post_url"])
        whatsapp_text = call_gemini(whatsapp_prompt).strip()

        # 9. Enviar WhatsApp para grupos do produto
        sent_count = send_whatsapp_to_groups(blog, whatsapp_text)
        print(f"[WhatsApp] Enviado para {sent_count} grupos de {blog}")

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
