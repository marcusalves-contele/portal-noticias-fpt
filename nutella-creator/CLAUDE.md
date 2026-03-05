# Nutella Creator — Pipeline de Clips Virais

Sistema completo para transformar lives do YouTube em clips otimizados: análise IA, corte automático, thumbnails, e upload.

Canal principal: Frota Para Todos (Julio César | `UCz31CtOANqSFuLEdFTi1iCQ`)

---

## O Que É Uma Nutella

Um clip educacional autônomo de **90s a 4min** extraído de uma live longa. Funciona sozinho.

### Regras de duração
- **Clip 16:9**: MÍNIMO 90 segundos (intro+CTA adicionam ~2min de wrapper)
- **Short 9:16**: MÍNIMO 30 segundos, ideal 45-60s
- Clip < 90s com wrapper > conteúdo → rejeitado

### Tipos de nutella

| Tipo | Característica |
|------|---------------|
| `autoridade` | Julio como referência do nicho |
| `viralização` | Verdade incômoda compartilhável |
| `inscricao` | Prova que o canal entrega mais que consultor |
| `educacional` | Resolve UMA dúvida com clareza cirúrgica |
| `wow_factor` | Demo ao vivo que parece impossível |

---

## Fluxo — Dashboard v2

```
python3 dashboard.py → http://127.0.0.1:8765

Tela 1: Cole URL → Analisar
         │
         ▼
Tela 2: Análise IA (SSE progress)
        Transcrição → Gemini → N nutellas
        Selecionar quais construir
         │
         ▼
Tela 3: Build (SSE progress)
        Download → Face detection → Composição 16:9 + 9:16
         │
         ▼
Tela 4: Review
        Players + metadados + aprovar/rejeitar
        Gerar thumbnail (Gemini) ao aprovar
        Feedback → regerar com IA
         │
         ▼
Tela 5: Upload YouTube
        Vídeo + thumb + título + descrição + tags
        Unlisted ou agendamento inteligente
```

### CLI (alternativo)

```bash
cd growth-contele/nutella-creator

# Pipeline completo via dashboard
python3 dashboard.py

# Scripts individuais
python3 suggest.py https://youtube.com/live/VIDEO_ID
python3 build.py output/VIDEO_ID_nutellas.json --ranks 1,2,3
python3 gen_thumb.py output/VIDEO_ID_cuts/ --rank 1
python3 upload.py output/VIDEO_ID_cuts/ --rank 1 --schedule
```

---

## Arquitetura

```
nutella-creator/
├── dashboard.py       # Servidor HTTP + API REST + SSE (entry point)
├── suggest.py         # Análise: transcrição → Gemini → JSON de nutellas
├── build.py           # Corte: download → face detect → ffmpeg 16:9 + 9:16
├── gen_thumb.py       # Thumbnails: Gemini Nano Banana 2 + feedback loop
├── upload.py          # Upload YouTube: OAuth + scheduling + SEO
├── preview.py         # Preview HTML estático (legado)
├── render_cards.py    # Brief cards Remotion (legado)
├── static/            # Frontend profissional (SPA)
│   └── index.html
├── assets/            # Intro, CTA, badge overlay
├── downloads/         # Cache de vídeos baixados
├── output/            # JSONs + cuts + thumbs
│   ├── {video_id}_nutellas.json
│   └── {video_id}_cuts/
│       ├── live{N}_{rank}_*.mp4
│       ├── live{N}_{rank}_short_*.mp4
│       ├── live{N}_{rank}_meta.json
│       ├── live{N}_{rank}_thumb.png
│       └── state.json
└── .env               # GEMINI_NANO_BANANA_KEY
```

---

## API Endpoints (dashboard.py)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/videos` | Lista vídeos processados |
| POST | `/api/analyze` | `{url}` → `{job_id}` |
| POST | `/api/build` | `{video_id, ranks}` → `{job_id}` |
| GET | `/api/progress/{job_id}` | SSE stream: progress/complete/error |
| GET | `/api/metas/{video_id}` | Metas + state + thumbs |
| POST | `/api/approve` | `{video_id, rank, status}` |
| POST | `/api/generate-thumb` | `{video_id, rank}` → `{thumb}` |
| POST | `/api/regenerate-thumb` | `{video_id, rank, feedback}` → `{thumb}` |
| POST | `/api/upload-youtube` | `{video_id, ranks, privacy, schedule}` |

Estado de aprovação: `{cuts_dir}/state.json` (server-side, não localStorage).

---

## Output por nutella (suggest.py)

| Campo | Descrição |
|-------|-----------|
| `clip_entrada` / `clip_saida` | Timestamps 16:9 (mín 90s) |
| `shorts_entrada` / `shorts_saida` | Timestamps 9:16 (mín 30s) |
| `titulo_seo` | Keyword primária nos primeiros 40 chars |
| `titulo_ctr` | Hook emocional na primeira palavra |
| `titulo_shorts` | Título Shorts (≤50 chars) |
| `tags_especificas` | 5-8 tags do tema do clip |
| `descricao_curta` | 2-3 frases para descrição YouTube |
| `thumbnail_texto` | ≤4 palavras, alto contraste |
| `thumbnail_composicao` | SIMPLES: Julio + máx 1 elemento |
| `expressao_julio` | irônico, surpreso, assertivo... |
| `thumbnail_pairing` | A ou B |
| `por_que_viraliza` | Mecanismo psicológico em 1 linha |
| `hook_transcricao` | Primeiras frases do clip |

---

## Thumbnails

- **Modelo**: `gemini-3.1-flash-image-preview` (Nano Banana 2)
- **Refs oficiais Julio**: `thumbnail-ai-creator/referencias/julio/` (3 fotos profissionais)
- **Temperature**: 0 (máxima consistência facial)
- **Composição**: MÁXIMO 2 elementos visuais (Julio + 1 coisa)
- **Feedback loop**: Gemini Flash ajusta prompt baseado em feedback do usuário

---

## Dependências

- Python: `youtube-transcript-api`, `requests`, `google-api-python-client`, `google-auth`
- Sistema: `ffmpeg`, `yt-dlp`
- Python (build): `opencv-python`, `mediapipe`
- API Keys: `GEMINI_NANO_BANANA_KEY` (.env local ou `../thumbnail-ai-creator/.env`)
- YouTube: `token_youtube_write.pickle` em `../../assistant-sexta-feira/`

---

## Agendamento Inteligente

Baseado em análise de **2.873 vídeos** do canal (2024–2026). Doc completo: `obsidian-marco/DOCS/nutella-agendamento-inteligente.md`

### Regras
- **Nutellas (clips 16:9)**: qui 15h e sex 17h — dias mais fortes do canal
- **Shorts (9:16)**: ter 18h e seg 17h — feed separado, não canibaliza
- **Quarta: NUNCA** — dia da live semanal (8h BRT), performa abaixo da média
- **Padrão teaser**: Short 2–3 dias antes do clip correspondente
- **1 vídeo/dia** máximo

### Re-autenticar com Analytics
```bash
python3 reauth_youtube_analytics.py
```
Scope: `yt-analytics.readonly` — habilita views por hora, retenção, origem do tráfego.

---

## Thumbnails

- **Modelo**: `gemini-3.1-flash-image-preview` (Nano Banana 2)
- **Refs Julio**: varredura dinâmica em `thumbnail-ai-creator/referencias/julio/` — exclui `*studio_v1*` (AI-geradas)
- **Seleção por expressão**: `expressao_julio` do meta → keyword matching no nome do arquivo
- **Âncora facial**: sempre inclui `frontal-neutro` como ref primária
- **Temperature**: 0 (máxima consistência facial)
- **Shirt**: black polo (novas fotos mar/2026)

---

## Dependências

- Python: `youtube-transcript-api`, `requests`, `google-api-python-client`, `google-auth`
- Sistema: `ffmpeg`, `yt-dlp`
- Python (build): `opencv-python`, `mediapipe`
- API Keys: `GEMINI_NANO_BANANA_KEY` (.env local ou `../thumbnail-ai-creator/.env`)
- YouTube: `token_youtube_write.pickle` em `../../assistant-sexta-feira/`

---

## Aprendizados

- Gemini precisa timestamps `[MM:SS]` em chunks de 90s para cortes precisos
- Limitar transcrição a 22k chars evita degradação
- Composições simples (Julio + fundo) → melhor fidelidade facial na thumb
- Clips < 90s com intro+CTA de 2m15s → 73% wrapper → rejeitado
- "Verdade Incômoda" viraliza em WhatsApp corporativo
- "WOW Factor" (demo) gera mais inscritos
- Shorts de 45-60s > Shorts de 20-30s em retenção
- Freeze frame 1.5s no início do Short = capa garantida (YouTube usa frame 0)
- Refs AI-geradas (`*studio_v1*`) degradam fidelidade facial — excluir sempre
