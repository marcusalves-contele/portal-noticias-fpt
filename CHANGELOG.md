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

### 29/04/2026
- **prism-os**: Cortes Nutella + Studio thumb sem leak (3 PRs). PRs #109 + #110 + #111 mergeados em master, deploy Railway prism-os automatico. PR #111 (closes #95): Definition of Done dos cortes Nutella, prompt do `suggest.py` agora orienta o LLM a NAO cortar raciocinios incompletos, NAO cortar intros vazias e exigir entrega da promessa do titulo. PR #109 (closes #96): cortes manuais nao perdem mais historico entre etapas, fluxo agora tem CTA "proxima etapa" com persistencia server-side. PR #110 (closes #89 + #101): "Ajustar Thumb" no Studio agora preserva composicao + referencia da imagem original. Causa raiz era config (`imageConfig` ausente, `temperature 0.8`, `responseModalities` permitindo leak de prompt template), nao o modelo. Mantido `gemini-3.1-flash-image-preview` (Nano Banana 2) com `imageConfig.aspectRatio: "16:9"`, `imageSize: "2K"`, `temperature: 0.4`. Gate fisico no cliente filtra `inlineData` only e sanitiza `summary`. **Versionamento abandonado:** footer do dashboard nao mostra mais "PRISM OS v1.0.0", link "Changelog" agora aponta pra `prism-os/CHANGELOG.md` no repo com data dinamica via `/api/version`. Detalhe em [`prism-os/CHANGELOG.md`](prism-os/CHANGELOG.md).
- **prism-os**: Planejador Senior v2 — plano + roteiro + redesign editorial. PRs #107 + #108 mergeados em master, deploy Railway prism-os automatico. Step 0 "Planejar Proximo Video" na home, 2 campos (Tema + Direcao opcional pra orientar agente), Gemini 3 Pro com `responseSchema` PLAN_SCHEMA 14 campos, knowledge layer novo (soul-canal-fpt + youtube-principles-2026 + template-roteiro-live-julio), runtime cruzando calendario FPT (Sheets) + dataset 2.786 videos, roteiro narrado Julio bloco a bloco, historico server-side versionado, refinar plano com feedback acumulado. Closes #97 (asset cta-final-pronto-v2.mp4 trocado 33MB->1.2MB). Detalhe em [`prism-os/CHANGELOG.md`](prism-os/CHANGELOG.md).

### 28/04/2026
- **contele/contelefleet + conteleteams**: Enhanced Conversions for Leads via Google Ads API (PR #99 mergeado, closes #93). Patch additive nos 2 servers gemeos: payload `uploadClickConversions` agora inclui `userIdentifiers` (hashedEmail + hashedPhoneNumber) quando disponiveis. Hashes ja vinham do Contele OS (`getCustomField` + `hashEmail/hashPhoneBR`), antes so iam pro GA4 MP. Pre-condicoes validadas em 26/04: customers Fleet `3984015785` e Teams `5532904101` com `acceptedCustomerDataTerms=true` + `enhancedConversionsForLeadsEnabled=true`. Esperado: alerta "Nenhuma tentativa de importacao com dados fornecidos pelo usuario" some em 24h; match rate visivel em 14d (B2B SaaS BR esperado 30-60%). Risco zero (additive). Deploy automatico Railway pos-merge.
- **contele/conteleteams**: cleanup pos deep research Senior Google Ads (14 refs externas + docs oficiais). Customer `5532904101`: buckets `PAGE_VIEW` e `OUTBOUND_CLICK` no Customer Conversion Goal mudados pra `biddable=false` via Google Ads API mutate (alinha com Fleet `3984015785` ja limpo desde mar/2026). GTM Teams `GTM-TQNBWXFK` v22 publicada: Tag 11 "ADS - Form Submit" (awct, conversionId legacy `16687281900` label `dHeKCIzixNEZEOztjpU-`) PAUSED apos auditoria confirmar 0 conversion actions ENABLED com esse id (todas as 6 estavam removed; tag silently rejected ha 19 meses, padrao do incidente Teams mar/2026). Tag 12 "ADS - Remarketing" (sp) com `conversionLabel` removido (anti-pattern em remarketing tag, preserva `conversionId` pra audiencia "All visitors" 6.4k search/3.7k display via Tag 7 googtag). Tag 13 "ADS - User-Provided Data" (awud) MANTIDA como redundancia client-side ate Enhanced Conversions server-side validar 14d. Hipotese inicial de R$3k/mes economia nao se sustenta (buckets vazios) - fix vale como prevencao.

### 27/04/2026
- **contele/contelefleet**: exit intent popup com round-robin Marcia/Thiago ferias-aware (PR #94). Detalhe em [`contelefleet.com.br/CHANGELOG.md`](contelefleet.com.br/CHANGELOG.md).
- **contele/contelefleet**: cleanup GTM pos-cutover via Tag Manager API v2 (issue #98). Container heritage `GTM-52PR2JW` (RM Digital abandonou ha 14 meses) tinha Tag 23 (Meta Pixel - Contact), Tag 25 (GA4 Event - Fazer_Orcamento) e Tag 36 (GA4 Event - Microsoft UET) ainda apontando pro Trigger 7 (URL antiga `/obrigado` contelerastreador) - silenciadas desde cutover 20/04. GTM v37 publicada com Tag 23 + 25 trocando `firingTriggerId` de `[7]` pra `[27]` (Form Submission custom event no dataLayer); GTM v38 publicada com Tag 36 mesmo fix (Bing/Microsoft Ads volta a receber Lead). Conversion action `formSubmission` (ID 7582250342) deletada via Google Ads API mutate: 0 conversoes lifetime, 0 tag snippets, redundante com `fez-orcamento-fleet` (350788965, 377 primary lifetime via Tag 28). Validado em prod: deal 75078 (ntec) com SUCCESS no upload `lead_qualificado_fleet`.
- **contele/contelefleet**: CHANGELOG.md criado cobrindo 4 marcos retroativos da landing nova (cutover 20/04, Gate 1 22/04, Gate 2 25/04, exit intent 27/04).
- **contele/growth root**: este `CHANGELOG.md` criado como indice consolidado.

### 23/04/2026
- **prism-os**: deprecacao do CLI `thumbnail-ai-creator/` (fluxo migrou pro `nutella-creator/dashboard.py`).
- **prism-os**: anti-silent-failure em PIL preview e Drive upload, com classificacao de erro (401, 403, 404, 429, 502, 503).
- **prism-os**: estrategia de Live nativa (palavra-chave SEO + 6 titulos SEO + 6 titulos criativos + tags + 3 enquetes) usando Gemini Pro 3 com knowledge base injetada.

Para mudancas anteriores, consulte o CHANGELOG.md de cada subprojeto.
