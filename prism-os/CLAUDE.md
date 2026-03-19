# PRISM OS — Content Production OS

Sistema operacional de produção de conteúdo do canal Frota Para Todos (Julio César).

**Visão**: URL de uma live entra → clips, shorts, thumbnails A/B, SEO e agendamento saem. Zero trabalho manual no meio.

Hoje o sistema cobre Plan → Shoot → Multiply. Quando crescer o suficiente, vira repositório independente.

---

## Submodules

| Módulo | Path | O que faz |
|--------|------|-----------|
| **Nutella Creator** | `nutella-creator/` | Pipeline completo: URL → cortes 16:9 + 9:16 + thumbnail via dashboard local |
| **Thumbnail AI Creator** | `thumbnail-ai-creator/` | Geração standalone de thumbnails via CLI (Fleet e Teams) |

---

## Nutella Creator

Dashboard local que transforma uma live do YouTube em conteúdo distribuível.

**Rodar:**
```bash
cd prism-os/nutella-creator
python3 dashboard.py
# abre http://127.0.0.1:8765
```

**Fluxo no dashboard:**
1. Cole URL YouTube → Analisar (transcrição + Gemini → lista de nutellas)
2. Selecione quais construir → Build (download + ffmpeg → 16:9 + 9:16)
3. Review: players, metadados, aprovar
4. Gerar thumbnail A/B (Gemini Nano Banana 2, face-lock, slider de divergência 1-10)
5. Aprovar ângulo(s) → Upload Drive por ângulo

**Auto-briefing**: botão "Auto-preencher do vídeo" — transcreve e extrai q1/q2/q3 automaticamente via Gemini Flash. Nutellas não precisam preencher briefing manual (usam `thumb_text` da planilha).

**Divergência A/B:**
- 1-3: Sutil (variação de cor/pose)
- 4-6: Moderado (ângulo emocional diferente)
- 7-8: Alto (conceitos distintos)
- 9-10: Máximo (abordagens opostas)

**Doc completo**: `nutella-creator/CLAUDE.md`

---

## Thumbnail AI Creator

Geração de thumbnails via CLI. Usado quando não há dashboard (batch, testes, Lives que não são nutellas).

**Canais:**
- Fleet (Julio César): `--channel fleet`
- Teams (Leonardo Gazolli): `--channel teams`

**Fluxo A/B:**
1. Definir briefing (3 perguntas: público, objetivo, conteúdo)
2. Criar 2 ângulos criativos distintos (não variações do mesmo)
3. Gerar com `--variations 2` para cada ângulo
4. Par A/B final = 1 variação escolhida de cada ângulo

**Doc completo**: `thumbnail-ai-creator/CLAUDE.md`

---

## Agendamento Inteligente

Baseado em análise de 2.873 vídeos do canal (2024-2026).

| Tipo | Dias ideais | Horário |
|------|------------|---------|
| Nutellas (16:9) | Qui + Sex | 15h / 17h |
| Shorts (9:16) | Ter + Seg | 18h / 17h |
| Quarta | NUNCA | dia da live |

---

## Planilhas de Conteúdo

| Canal | Spreadsheet ID | Sheet |
|-------|---------------|-------|
| Fleet (Julio) | `1lluvZ8SKQNThV4o4OzWqmsttP-BgRC1FU3AqwvfJbqI` | `Fleet` |
| Teams (Leonardo) | `1RjMazaU0fV5npXIJFcZTrrGVbJVeWxv8VV8y1uMEJVU` | `Teams` |

Colunas relevantes: `tema` · `Tipo` · `title` · `Texto da thumb` · `Convidado` · `url`

Linhas com "Tarefa no Asana" preenchido = pendentes.

---

## Referências Faciais

| Apresentador | Ref primária | Onde |
|---|---|---|
| Julio César (Fleet) | `julio-ref-primary-1.jpg` | `thumbnail-ai-creator/referencias/julio/` |
| Leonardo Gazolli (Teams) | `leo-ref-primary.png` | `thumbnail-ai-creator/referencias/leonardo/` |
| Convidados | `convidado_live-{NUM}-{Nome-Completo}.{ext}` | `thumbnail-ai-creator/referencias/convidados/` |

**NUNCA usar refs AI-geradas** (`*studio_v1*`, cyberpunk) como referência primária — degradam fidelidade facial.

---

## Modelos de IA

| Uso | Modelo |
|-----|--------|
| Thumbnails (qualidade) | `gemini-3-pro-image-preview` |
| Thumbnails nutella (face-lock) | `gemini-3.1-flash-image-preview` (Nano Banana 2) |
| Análise / briefing | `gemini-3-flash-preview` |

**API Key**: `GEMINI_NANO_BANANA_KEY` (env var no Railway, `.env` local)

---

## Deploy Railway

**Servico**: `prism-os` no projeto `growth` | **Auto-deploy**: push para `master`

### Armadilhas conhecidas (19/mar/2026)

1. **youtube-transcript-api bloqueado**: YouTube bloqueia IPs de cloud (Railway/AWS/GCP).
   `suggest.py` tem fallback automatico via yt-dlp (`--write-auto-sub`).
   Se ambos falharem, configurar `cookies.txt` no container.

2. **libxcb.so.1 / OpenCV / mediapipe**: container precisa de libs X11.
   `nixpacks.toml` tem `nixPkgs` (xorg.libxcb, libGL, glib) + `aptPkgs`.
   Se mediapipe nao carregar, `build.py` usa letterbox (sem face detection).
   NUNCA remover o fallback graceful do import cv2/mediapipe.

3. **.env nao existe em producao**: Railway injeta env vars, nao tem `.env` file.
   Todo `load_api_key()` DEVE preferir `os.environ.get()` antes de ler `.env`.
   Validar qualquer novo script que leia `.env` diretamente.

4. **Dados se perdem no redeploy**: output/, downloads/, state.json resetam.
   Issue #54 aberta para montar Railway Volume.
   Ate resolver: dados sao efemeros, time precisa re-processar apos deploy.

5. **Docker layer cache**: nixpacks cacheia layers agressivamente.
   Mudar apenas `aptPkgs` pode nao invalidar o cache.
   Para forcar rebuild: alterar `nixPkgs` (muda o hash da layer nix).

### Env vars obrigatorias (Railway)

| Var | Uso |
|-----|-----|
| `GEMINI_NANO_BANANA_KEY` | API Gemini (thumbs, analise) |
| `YOUTUBE_TOKEN_B64` | OAuth YouTube (base64 pickle) |
| `SHEETS_TOKEN_B64` | Google Sheets (base64 pickle) |
| `GITHUB_TOKEN` | Criar issues via feedback |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Login OAuth dashboard |

---

## Entrega

- **Grupo WhatsApp**: IA - Growth Contele (`120363424539843742@g.us`)
- **Drive**: upload por ângulo aprovado via dashboard
- **YouTube**: upload via `upload.py` com scheduling inteligente

---

## Issues Abertas (GitHub #1-#4, commit 9e1a917, 11/mar/2026)

Codigo implementado, falta testar no dashboard e fechar:

- [ ] **#1** Separacao briefing x script (3 steps: Source > Briefing > Review)
- [ ] **#2** Selecao inteligente de fotos (catalogo.json + select_best_refs)
- [ ] **#3** Botoes publicacao (Drive + YouTube) na tela de review
- [ ] **#4** Campo observacao criativa (prompt humano, HIGHEST PRIORITY)

Agents de execucao e QA em `.claude/agents/prism-*.md`.
Apos validar, fechar issues no GitHub e marcar checkboxes aqui.

Token YouTube OAuth (`token_youtube_write.pickle`) precisa validar scope `thumbnails.set` pro botao de thumb funcionar.

---

## Roadmap (próximas funções)

- [ ] SEO de títulos integrado ao dashboard
- [ ] Agendamento YouTube direto pelo dashboard
- [ ] Distribuição automática (Drive + grupo + agendamento em 1 clique)
- [ ] Suporte a canais Teams (Leonardo) no dashboard
- [ ] Quando tiver 3+ módulos maduros → extrair para repo `prism-os`
