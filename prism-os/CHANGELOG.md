# Changelog

Registro de mudancas no Prism OS.

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
