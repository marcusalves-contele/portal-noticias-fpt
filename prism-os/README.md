# PRISM OS: Content Production OS

Sistema operacional de producao de conteudo do canal Frota Para Todos (Julio Cesar).

URL de uma live entra -> clips, shorts, thumbnails A/B, SEO e agendamento saem.

## Setup Local

### Pre-requisitos

- **Python 3.10+**
- **ffmpeg** no PATH (`brew install ffmpeg` no macOS)
- **Gemini API Key** (para thumbnails e analise)

### Instalacao

```bash
cd prism-os/nutella-creator
pip install -r requirements.txt
```

### Configuracao (.env)

Criar `nutella-creator/.env` com:

```env
GEMINI_NANO_BANANA_KEY=sua-chave-gemini
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret
SECRET_KEY=qualquer-string-aleatoria
```

| Variavel | Uso | Obrigatoria |
|----------|-----|-------------|
| `GEMINI_NANO_BANANA_KEY` | API Gemini (thumbnails, analise) | Sim |
| `GOOGLE_CLIENT_ID` | OAuth login no dashboard | Sim (se auth ativo) |
| `GOOGLE_CLIENT_SECRET` | OAuth login no dashboard | Sim (se auth ativo) |
| `SECRET_KEY` | Sessoes HTTP persistentes | Nao (gera random se ausente) |

### Assets obrigatorios

A pasta `assets/` contem arquivos de video e imagem usados na composicao dos cortes. Ja estao commitados no repo:

| Arquivo | Uso |
|---------|-----|
| `intro-julio-cortes-nutela-v2.mp4` | Vinheta de abertura (intro) |
| `cta-final-pronto-v2.mp4` | Call-to-action final |
| `badge-overlay.png` | Badge 1920x90 do rodape |
| `moldura-cortes-video.png` | Moldura dos cortes |

Sem esses arquivos o `build.py` nao consegue gerar os cortes.

### Rodar

```bash
cd prism-os/nutella-creator
python3 dashboard.py
# Abre http://127.0.0.1:8765
```

Porta custom: `python3 dashboard.py --port 8800`

### Fluxo no Dashboard

1. Cole URL do YouTube -> Analisar (transcricao + Gemini -> lista de nutellas)
2. Selecione quais construir -> Build (download + ffmpeg -> 16:9 + 9:16)
3. Review: players, metadados, aprovar
4. Gerar thumbnail A/B (Gemini, face-lock, slider de divergencia 1-10)
5. Aprovar angulo(s) -> Upload Drive por angulo

### Dependencias

| Pacote | Uso |
|--------|-----|
| Flask + Werkzeug + Authlib | Servidor web, sessoes, OAuth |
| google-api-python-client + google-auth-* | YouTube Data API, Sheets, Drive |
| opencv-python-headless + mediapipe | Deteccao facial (fallback: letterbox) |
| youtube-transcript-api + yt-dlp | Transcricao e download de video |
| Pillow | Manipulacao de imagens |

### Limpeza

Apos processar videos, limpar arquivos temporarios:

```bash
rm -rf nutella-creator/downloads nutella-creator/output
```

Pastas sao recriadas automaticamente no proximo uso.

## Modulos

| Modulo | Path | Funcao |
|--------|------|--------|
| Nutella Creator | `nutella-creator/` | Pipeline completo: URL -> cortes + thumbnails via dashboard |
| Thumbnail AI Creator | `thumbnail-ai-creator/` | Geracao standalone de thumbnails via CLI |

## Deploy (Railway)

Servico `prism-os` no projeto `growth`. Auto-deploy via push para `master`.

Ver `CLAUDE.md` para armadilhas de deploy e env vars de producao.
