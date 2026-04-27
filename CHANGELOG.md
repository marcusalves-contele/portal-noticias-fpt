# Changelog: contele/growth

Indice consolidado de mudancas no monorepo growth. Cada subprojeto mantem seu proprio CHANGELOG.md detalhado. Esta pagina serve pra rastrear o que mudou, onde, e quando, sem precisar abrir cada pasta.

## Subprojetos com CHANGELOG dedicado

| Subprojeto | Caminho | Foco |
|---|---|---|
| **Contele Fleet** | [`contelefleet.com.br/CHANGELOG.md`](contelefleet.com.br/CHANGELOG.md) | Landing principal Fleet, tracking GA4/Ads, integracao Pipedrive |
| **PRISM OS** | [`prism-os/CHANGELOG.md`](prism-os/CHANGELOG.md) | Producao de conteudo: Nutella Creator, Thumbnail AI Creator |

## Subprojetos sem CHANGELOG ainda

Quando voce mexer num desses, **crie o CHANGELOG.md da pasta** (mesmo formato dos outros) e adicione um link aqui. Ver regra no [`CLAUDE.md`](CLAUDE.md) deste repo.

- `conteleteams.com.br/`: home Teams + landings dirigidas (benchmark, propostas) servidas via Express
- `contele-referral-page/`: Indique e Ganhe (React + Vite, deploy Railway)
- `calculadora-reembolso-km/`: calculadora de reembolso quilometragem
- `contele-io/`: hub contele.io
- `dashboard-funil/`: dashboard funil comercial
- `youtube-to-blog/`: pipeline YouTube em post de blog

## Mudancas recentes (cross-projeto)

### 27/04/2026
- **contele/contelefleet**: exit intent popup com round-robin Marcia/Thiago ferias-aware (PR #94). Detalhe em [`contelefleet.com.br/CHANGELOG.md`](contelefleet.com.br/CHANGELOG.md).
- **contele/contelefleet**: CHANGELOG.md criado cobrindo 4 marcos retroativos da landing nova (cutover 20/04, Gate 1 22/04, Gate 2 25/04, exit intent 27/04).
- **contele/growth root**: este `CHANGELOG.md` criado como indice consolidado.

### 23/04/2026
- **prism-os**: deprecacao do CLI `thumbnail-ai-creator/` (fluxo migrou pro `nutella-creator/dashboard.py`).
- **prism-os**: anti-silent-failure em PIL preview e Drive upload, com classificacao de erro (401, 403, 404, 429, 502, 503).
- **prism-os**: estrategia de Live nativa (palavra-chave SEO + 6 titulos SEO + 6 titulos criativos + tags + 3 enquetes) usando Gemini Pro 3 com knowledge base injetada.

Para mudancas anteriores, consulte o CHANGELOG.md de cada subprojeto.
