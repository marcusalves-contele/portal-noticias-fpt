# Changelog: conteleteams.com.br

Registro de mudancas no server / landings Teams servidos via Express.

---

## 15/05/2026: Fixes pos-review (4 agentes isções: Growth, Copy, QA, Tech Lead)

Pos-review antes do PR ir pra producao, com base em achados convergentes:

- **24 botoes sem `type`**: adicionados `type="button"` em todos (Tech Lead apontou risco de submit acidental dentro do form sidebar). Script Python regex-based, validado em 0 botoes sem type apos
- **3 citações fracas removidas** dos cases (CMA, Cartão TODOS, Hart's) - mantido apenas o card+resultado, sem blockquote. Schema Review sincronizado: 8 → 4 reviews (Beach Park, Tahto, Prisma, Master). Buffalo também saiu do schema porque não tinha quote verbal no HTML
- **Cookie banner compactado em mobile**: media query @580px reduz padding/font pra não cobrir secao #logos no iPhone

## 15/05/2026: SEO para LLMs - cases textuais + FAQ visivel + Schema Review

**Issue**: contele/growth#138

Auditoria SEO-para-LLM identificou que homepage tinha schema solido mas conteudo dependia muito de imagens (thumbs YouTube) e nao tinha FAQ visivel no DOM. LLMs (ChatGPT, Gemini, Perplexity) recomendam com mais peso quando ha narrativa textual concreta de problema/solucao/resultado.

**JSON-LD adicionados**:
- Schema `Review` (array com 8 cases reais extraidos da pasta canonica do Drive "Casos de sucesso - Teams e Fleet"): CMA Elevadores, Cartao de TODOS, Hart's Alimentos Naturais, Beach Park, Tahto/Getnet, Laboratorio Prisma, Buffalo Corretora, Master Solucoes. Cada Review com `itemReviewed` SoftwareApplication, `reviewBody` (citacao real do cliente), `author` Organization e `reviewRating` 5/5

**Novas secoes visiveis no HTML**:
- `#cases-clientes` antes de `#depoimentos`: 8 cards textuais (1 paragrafo de 50-80 palavras por case) com header (empresa + setor), narrativa, blockquote com citacao e bloco de resultado destacado. Substitui dependencia de thumbs YT como unica fonte de contexto pra LLM
- `#faq-visible` antes de `</main>`: accordion CSS-only (`<details>/<summary>`) espelhando as 6 Q&A do JSON-LD FAQPage existente, com respostas expandidas (50-80 palavras cada). Antes, FAQ existia so no schema; agora tambem renderizado no DOM

**CSS**: classes `.case-card`, `.cases-grid`, `.case-quote`, `.case-result`, `.faq-list` com responsividade mobile-first (grid colapsa pra 1 coluna em <580px). Paleta `--blue-primary` mantida

**Out of scope (decisao pendente)**:
- Unificacao do blog (hoje `blog.contelege.com.br`) em `conteleteams.com.br/blog`. Issue #138 lista como nao-bloqueante

---

## 11/05/2026: Atualizacao de precos prateleira Teams (mai/26)

**Issue**: contele/demandas_para_desenvolvimento#6281

Reajuste oficial dos precos de prateleira do Contele Teams a partir de mai/26:
- 4 a 40 usuarios: R$59,90 -> **R$62,50** / usuario / mes
- 41+ usuarios: R$49,90 -> **R$52,00** / usuario / mes
- Minimo de 4 licencas: R$239,60 -> **R$250,00** / mes (4 x R$62,50)

**Alteracoes em `index.html`**:
- JSON-LD `Offer.price` 59.90 -> 62.50
- FAQPage "Qual o preco" atualizado pro novo minimo
- Cards de plano: trocados os `<img>` SVG (`preco-4-40-usuarios-contele-teams.svg`, `preco-mais-de-41-usuarios-contele-teams.svg`) por markup HTML usando classes ja existentes (`.plan-price .currency/.value/.cents/.period`). Evita regerar SVG e fica consistente com o card Enterprise.
- Mensagem do sidebar pra equipe < 4 e validacao real-time de qtd: R$239,60 -> R$250,00.

**Tambem atualizado**: `llms.txt` e `llms-full.txt` substituindo nomenclatura legada (Essencial/Profissional) pela faixa real exibida na LP (4-40 / 41+).

**Out of scope** (issue trata so de LP): atualizacao no fluxo de contratacao e integracao Vindi vive na issue irma #6251 (ja fechada).

---

## 29/04/2026: Dedup Pipedrive-aware no /api/lead + race guard no submit

**Sintoma**: planilha de leads tinha 2 linhas com mesmo `nome | email | telefone | empresa` e timestamp identico (caso Lucas / MP do Brasil 26/04 09:01:26). Casos similares com janela maior (Rogerio Siqueira 23/04 + 29/04) viravam deals duplicados na pipeline 12 que Daniel fechava como DUPLICADO toda semana.

**Fix em 2 camadas**:

1. **Frontend (index.html)**: flag sincrona `window._formSubmitting` no inicio de `handleInsideForm` e do click handler `btn-accept-small-team`. Antes, `submitBtn.disabled = true` so era setado depois das validacoes, e double-click no mesmo tick passava 2x. Agora bloqueia re-entry no primeiro byte da funcao.

2. **Backend (server.js)**: `findExistingTeamsDeal(email, phone)` busca pessoa no Pipedrive por email exato + phone, recupera deals abertos de cada match, retorna o mais recente em pipeline 12 com idade < 30d. Se achar, `/api/lead` posta `sales-tracking` no contele-os com o `pipedrive_deal_id` existente (atualiza UTMs/gclid/GA4 do retorno), loga sheet com status `6_duplicado_pipedrive`, posta Discord avisando, e sai sem criar pessoa/deal duplicado.

**Por que dois lados**: client cobre 99% (double-click humano), Pipedrive cobre o resto (multi-device, retorno em outro dia, browser limpou localStorage).

**Nao cobre** (out of scope, decisao consciente):
- Lead com email e telefone *diferentes* mas mesmo CNPJ/empresa: cria deal novo. Vira housekeeping cron separado.
- Re-engagement do Leo SDR pra leads em stage avancado: contele-os#376 trata.

---

## 29/04/2026: Forward de delete do Pipedrive pro contele-os

**PR**: contele/growth#113

Handler `/api/pipedrive-webhook` agora detecta delete de deal (Pipedrive v1 `event=deleted.deal`, v2 `meta.action=delete`, header `x-event-action=deleted`) **antes** do fluxo normal de `change.deal` e dispara fire-and-forget `POST /api/webhooks/sales-lead-delete` no contele-os com `{ pipedrive_deal_id, deleted_at }`.

**Por que**:
- Cutover SDR v2 (28/04) so capturava `change.deal`. Quando vendedor deletava deal no Pipedrive, lead virava fantasma na visao `/vendas` ate o cron horario `pipedrive-reconcile` reconciliar.
- Real-time corta latencia de ate 1h pra <30s.

**Tecnicamente**:
- Filtro `pipelineId === 12` (Teams). Outros pipelines: ignora (Fleet trata no proprio server).
- Fallback de extracao de `deal_id`: `previous.id || meta.id || data.id` (cobre v1 + v2).
- Notifica Discord (`DISCORD_WEBHOOK_URL`) com payload de delete pra observabilidade.
- Cron `/api/cron/pipedrive-reconcile` no contele-os continua como rede de protecao (caso webhook caia).

**Pre-deploy**:
- Criar subscription Pipedrive Teams: `event_action=deleted`, `event_object=deal` -> `https://conteleteams.com.br/api/pipedrive-webhook`.
- Endpoint `sales-lead-delete` no contele-os precisa estar no ar antes (issue separada).
