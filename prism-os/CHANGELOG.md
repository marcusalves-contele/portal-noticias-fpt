# Changelog

Registro de mudancas no Prism OS.

---

## 23/04/2026: Estrategia de Live nativa no Prism (mata workaround Gem externo)

**Issue**: #83

- Feature: ao subir audio de briefing no fluxo Thumbnails de Live, o Prism agora gera estrategia completa num shot (antes so extraia q1/q2/q3). Saida:
  - Palavra-chave SEO principal + posicionamento
  - 6 titulos SEO (otimizados pra busca, keyword-first)
  - 6 titulos criativos (emocional/curiosidade, viram texto da thumb)
  - Tags SEO (8+)
  - Objetivo resumido da live
  - 3 opcoes de enquete (pergunta + alternativas)
- Backend: nova funcao `thumb_live.generate_live_strategy()` usando Gemini Pro 3 com thinking adaptive + injecao de knowledge base (`playbook-conteudo-contele-2026.md` + `brand-manual-2024.md`). Novo endpoint `/api/thumb-live-strategy`
- Frontend: painel "Estrategia de Live" aparece apos upload do audio, cards editaveis, radio-select pro titulo criativo escolhido (vai como `thumb_text` no Step 3)
- Motivacao: aposentar workaround do mkt que usava Gem externo no Google Gemini pra gerar a mesma coisa por fora do Prism

---

## 23/04/2026: Tier 4 transcricao (audio + Gemini Flash) + anti-silent-failure

**Issues**: #73, #84

- **Tier 4 novo**: quando tiers 1-3 (transcript-api, yt-dlp subtitles, YouTube Data API) falham, o sistema agora baixa o audio via yt-dlp em m4a 64k mono, divide em chunks de 15min via ffmpeg e transcreve cada chunk em paralelo com Gemini Flash (gemini-3-flash-preview). Segmentos com timestamps globais reajustados por offset. Funciona mesmo em videos sem captions (raiz de #73 e #84)
- **Observabilidade**: `suggest.py` agora usa logger estruturado (antes era `print`) com nivel e modulo. Mensagens de erro consolidadas com detalhe por tier (`Tier1: ... | Tier2: ... | Tier3: ... | Tier4: ...`)
- **Anti-silent-failure em thumb_live.transcribe_audio**: antes retornava `{"q1":"","q2":"","q3":"","raw_text":...}` silenciosamente quando o JSON falhava, corrompendo o pipeline de Thumb de Live (UI mostrava sucesso com briefing vazio). Agora lanca `RuntimeError` explicito com raw text pra debug
- Teste E2E local: video `Qqohke8fsYw` (falha 404 em captions.list, Tier 3 morre) agora transcrito com sucesso via Tier 4

---

## 23/04/2026: v0.3.0 shipped — fix credencial Julio, premissas de corte, badge topo, stream log

**Issues**: #5, #6, #7, #8 | **Commits**: 95db7c0, da28328

- **#5 P0 Fix credencial YouTube**: upload.py agora valida `channel_id` fail-closed antes de subir. Bloqueia upload se o canal autenticado nao bater com o canal alvo (prevencao pro bug de videos irem pro canal do Marco em vez do Julio)
- **#6 P1 Premissas de corte**: prompt em suggest.py ajustado pra 2-3 clips por live (max 3), minimo 5min, conteudo educativo/promocional, corte limpo
- **#7 P1 Badge topo**: tarja de identidade movida do rodape pro topo do video (build.py `badge_y = 0`). Badge dinamico (via `badge_path`) continua suportado
- **#8 P2 Stream log + timer**: painel de log em tempo real e timer estilo Claude Code nas telas de progresso do dashboard (static/index.html)
- **Fix doc** (da28328): corrigir mencao "90s" para "3min" no CLAUDE.md

---

## 20/04/2026: Token OAuth canal Teams (Leonardo) em producao

- **Fix definitivo**: blog Teams agora extrai transcricao via Tier 3 (YouTube Data API) com token OAuth proprio do canal Leonardo Gazolli
- Marco virou gerente do canal Teams, fez OAuth via brand account e gerou token_youtube_teams.pickle
- Base64 setado em `YOUTUBE_TEAMS_TOKEN_B64` no Railway, isolado do token Fleet
- Teste E2E em producao: video `OptcPLCSDRM` transcrito com 1009 segmentos, post publicado em blog.conteleteams.com.br/roteirizacao-equipe-externa-passo-a-passo/
- Tier 1 (cookies) continua falhando em cloud IP: esperado, Tier 3 e o path feliz pra Teams
- Novo script: `prism-os/nutella-creator/reauth_youtube_teams.py` (valida captions.list/download e imprime base64)
- `*.pickle` e `token_*.json` no gitignore pra nao vazar token OAuth
- Issue #74 atualizada com status
- Commit: ddea208

---

## 13/04/2026: Features + bug fixes batch

### Thumb Roteiro: Ajustar A/B (closes #66)
- Botoes "Ajustar A" e "Ajustar B" funcionam na tela de Roteiro
- Mesmo padrao da tela de Lives (feedback + regeneracao via Gemini)
- Commit: f733081

### Studio: multiplas imagens (closes #68)
- Studio aceita ate 5 imagens por mensagem (antes: 1)
- Drag-and-drop, selecao multipla, preview com remocao individual
- Backend retrocompativel (image_b64 e images_b64)
- Commit: 33dc26e

### Fix blog Teams + cookies bypass

- **Bug**: blog Teams dava erro 403 na extracao de legendas (Cris reportou 10/04)
- **Causa raiz**: OAuth token era do Julio (Fleet), YouTube API so libera captions pro owner. Tiers 1-2 bloqueados por IP no Railway
- **Fix definitivo**: cookies do YouTube exportados, filtrados e injetados via `COOKIES_B64` env var no Railway
- Tier 1 (youtube-transcript-api) agora funciona com cookies pra qualquer canal
- Textarea de transcricao manual na UI como fallback
- Suporte multi-token OAuth preparado (YOUTUBE_TEAMS_TOKEN_B64)
- boot.py decodifica COOKIES_B64 para /tmp/cookies.txt no startup
- Issues fechadas: #58, #69, #72
- Issue #59 parcialmente resolvida (legendas OK, download video pendente)
- Commits: 85e0605, 1041822, bb6363f, fc2f207

---

## Historico semver (pre-data changelog)

### v0.2.0 (11/mar/2026)

**Commit**: `01b0cb5` | **Issues**: #1, #2, #3, #4

- Separacao briefing x script no fluxo de thumbnail (#1)
- Selecao inteligente de fotos de referencia (#2)
- Botoes de publicacao Drive + YouTube na review (#3)
- Campo observacao criativa (prompt humano) (#4)
- Auto-briefing: botao "Auto-preencher do video" via Gemini Flash
- Divergencia A/B (slider 1-10) pra thumbnails
- Dashboard v2: SSE progress, state server-side, review completo

### v0.1.0 (mar/2026)

**Commit**: `b2ae1b3`

- Dashboard local (http://127.0.0.1:8765)
- Pipeline: URL > Analise IA > Build (ffmpeg) > Review > Upload
- Nutella Creator: suggest.py + build.py + upload.py
- Thumbnail AI Creator: Gemini Nano Banana 2 com face-lock
- Agendamento inteligente baseado em 2.873 videos analisados
- Cortes 16:9 + 9:16 (shorts) com deteccao facial
- Intro + CTA automaticos
- Upload YouTube com scheduling
