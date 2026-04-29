# Changelog: contelefleet.com.br

Registro de mudancas na landing Fleet em codigo proprio.

---

## 29/04/2026: Dedup Pipedrive-aware no /api/lead + race guard no submit

Mesmo padrao aplicado no Teams (conteleteams.com.br#115). Sintoma identico: `submitBtn.disabled` so era setado depois das validacoes async, double-click no mesmo tick passava 2x na pipeline 1 (Fleet) gerando deals duplicados que vendedor fechava como DUPLICADO depois.

**Frontend (index.html)**: flag `window._formSubmitting` no inicio de `handleFleetForm` antes de qualquer validacao. Lock sincrono.

**Backend (server.js)**: `findExistingFleetDeal(email, phone)` (analogo ao `findExistingTeamsDeal`, pipeline 1 ao inves de 12). Se achar deal aberto < 30d na pipeline Fleet, atualiza tracking via contele-os/sales-tracking, marca sheet `6_duplicado_pipedrive`, posta Discord com link, retorna sem criar pessoa/deal duplicado.

---

## 29/04/2026: Forward de delete do Pipedrive pro contele-os

**PR**: contele/growth#113

Handler `/api/pipedrive-webhook` agora detecta delete de deal (Pipedrive v1 `event=deleted.deal`, v2 `meta.action=delete`, header `x-event-action=deleted`) **antes** do fluxo normal de `change.deal` e dispara fire-and-forget `POST /api/webhooks/sales-lead-delete` no contele-os com `{ pipedrive_deal_id, deleted_at }`.

**Por que**:
- Cutover SDR v2 (28/04) so capturava `change.deal`. Quando vendedor deletava deal no Pipedrive, lead virava fantasma na visao `/vendas` ate o cron horario `pipedrive-reconcile` reconciliar.
- Real-time corta latencia de ate 1h pra <30s.

**Tecnicamente**:
- Filtro `pipelineId === 1` (Fleet). Outros pipelines: ignora.
- Fallback de extracao de `deal_id`: `previous.id || meta.id || data.id` (cobre v1 + v2).
- Notifica Discord (`DISCORD_LEAD_CRITICAL_WEBHOOK_URL` -> fallback `DISCORD_WEBHOOK_URL_FLEET`) com payload de delete.
- Cron `/api/cron/pipedrive-reconcile` no contele-os continua como rede de protecao.

**Pre-deploy**:
- Criar subscription Pipedrive Fleet: `event_action=deleted`, `event_object=deal` -> `https://contelefleet.com.br/api/pipedrive-webhook`.
- Endpoint `sales-lead-delete` no contele-os precisa estar no ar antes.

---

## 27/04/2026: Exit intent popup com round-robin Marcia/Thiago ferias-aware

**PR**: contele/growth#94 (commits 7938a94 + 093e00e, squash 0585bd2)

Modal de saida espelhando padrao ja em producao no Teams, adaptado pro Fleet (paleta roxa, copy Fleet, mensagem WhatsApp dedicada).

**Triggers**:
- Desktop: `mouseout` + `clientY < 10` (mouse sai pela borda de cima)
- Mobile: 45s sem scroll/touch apos delay de armar
- Delay de 15s antes de armar pra nao molestar quem fechou cedo

**Bloqueios pra nao mostrar duas vezes**:
- Sessao atual ja viu (`sessionStorage.fleet_exit_shown`)
- Lead ja submeteu pelo WhatsApp (`localStorage.fleet_lead_submitted`)
- `#lead-form` ja esta visivel no viewport (usuario chegou onde queria)

**Round-robin client-side ferias-aware**:
- Config `SALES_REPS` no JS: `name`, `phone`, `active`, `vacation: { from, to }` em ISO
- Pra colocar alguem em ferias basta editar o objeto `vacation` no JS, sem deploy do servidor
- Filtra elegiveis em runtime, alterna via counter `localStorage`
- Fallback pro primeiro da lista se zero ativos (lead nunca fica sem rep)
- Numeros conferidos contra `server.js:167-170` (Thiago `5511937083424` id 4447438, Marcia `5513997143896` id 13168743)

**Fix paralelo**: `.exit-overlay` z-index passou de 950 pra 1100 pra cobrir o cookie banner que estava z-index 1000.

**Tracking GTM**: `dataLayer.push` de `exit_intent_shown` (com `exit_intent_rep`) e `exit_intent_cta` (com `exit_intent_action: lead_form | whatsapp`). Disponivel pro GA4 Fleet (property 319948806) sem mudanca no container GTM-52PR2JW.

---

## 25/04/2026: Cutover Gate 2 + ajustes finais pre-producao

Round de ajustes na preview Railway antes de virar a chave publica. Tudo aplicado direto em prod via deploy automatico Railway.

**P1 Integracoes e fluxo de vendas**:
- **Evolution config corrigido** (commit `34d8ccc`): env apontava pro Evolution pessoal Easypanel onde a instancia "Vendas n2" nao existe, ai o lead notify saia pelo numero do Marco. Trocado pra Evolution Contele (`evolution-api-817d7afc.contele.io`) + token Vendas n2. Numero remetente agora: `5511973576141`.
- **Anti-silent-failure aplicado**: `sendWhatsApp()` agora checa `response.ok`, loga corpo do erro com instancia + numero, e tambem loga sucesso. Nao falha mais silencioso quando Evolution responde 4xx/5xx.
- **Pipedrive Lead Qualificado** validado E2E: Deal 75071 criado, tracking gravado em `sales_leads` com ga4_client_id, hashed_email/phone, landing_page = contelefleet-production. Stage 157 disparou `[PIPE-FLEET] QUALIFIED` + `GA4 lead_qualificado sent (HTTP 204)`.

**P2 Correcoes LP**:
- 4 botoes "Fale com um Consultor" em recursos (rastreamento, telemetria, camera) e final de beneficios, todos acionando `#lead-form` (commit `084cf21`).
- Footer atualizado: Recursos/Beneficios/Depoimentos pra contelerastreador.com.br, Politica e Termos pra contele.io/privacy, redes pros canais Julio Cesar (`@JulioCesarFrotaParaTodos`, `@juliofassa`, `juliocesargestaodefrotas`), Central Instalador `exclusivo.contelerastreador.com.br/central-do-instalador/`, Indique pra `indique.contele.io`.
- og:image e twitter:image com URL absoluta (PR #92).
- CTA default trocado de "Teste Gratis" pra "consultor" (PR #91, mais alinhado com Fleet).

**P3 Conteudo / FAQ**:
- Pergunta nova "Como funciona a instalacao?" inserida no FAQ depois de "Equipamentos homologados". Resposta sobre autoinstalacao Plug e Use OBD + tecnicos parceiros regionais.

---

## 22/04/2026: Gate 1 concluido (deploy preview Railway + E2E validado)

Deploy Railway preview no `contelefleet-production.up.railway.app`, webhook Pipedrive temporario id 1863327, deal teste 75009 validou fluxo completo:

- Form submit com GCLID+UTMs capturados via querystring
- Pipedrive deal criado Pipeline 1 com custom fields raw_gclid + ga4_cid + ga4_sid + utms populados
- Sheets append, n8n SDR, Contele OS sales-tracking OK
- Pipedrive webhook chegou no server Fleet sem filtro derrubar
- Stage QUALIFIED (157): GA4 MP `lead_qualificado` HTTP 204 + Discord embed
- Stage WON (259): GA4 MP `lead_convertido` HTTP 204 + Discord embed
- Google Ads `uploadClickConversions`: codigo atingiu a Ads API, retornou UNPARSEABLE_GCLID (esperado pelo GCLID sintetico de teste)

Calculadora removida de `/obrigado/` (escopo gate baseline).

---

## 20/04/2026: Nova landing em codigo proprio (fora do bloglite WP)

**Issue**: contele/growth#79 / **PR**: contele/growth#80 / **Branch**: `feature/landing-fleet-v1`

Cutover da landing Fleet de WordPress (bloglite.contelerastreador) pra codigo proprio em Express + HTML/CSS/JS puro. Objetivo #0: avisar Google via API quando lead vira oportunidade (lead_qualificado) e quando vira cliente (lead_convertido). Performance e objetivo #2.

Escolha: **Opcao B** (migracao completa, server.js assume tudo que `ge-prd-web-api` faz hoje).

**Infra + integracoes** (deploy automatico Railway service `contelefleet`):
- GTM container Fleet `GTM-52PR2JW` snapshot (14 tags, 3 triggers, 6 vars)
- Google Ads Fleet customer `3984015785` mapeado + `formSubmission` conversion criado (7582250342). lead_qualificado_fleet (7446455655) e lead_convertido_fleet (7453621406) ja existiam
- GA4 Fleet property 319948806 + MP Secret `contelefleet-backend` (`q4ftMZCMRCmrkwqOgRcdYg`) + 3 key events (formSubmission, lead_qualificado, lead_convertido)
- Discord webhook Fleet proprio: `DISCORD_WEBHOOK_URL_FLEET`
- Pipedrive Pipeline 1 stages mapeados (14 stages: CONTATANDO, qualificados 157/263/3/155, won 259/270/281/282/283/240, lost 241)
- Custom fields Pipedrive globais herdados de Teams (GCLID, GA4 Client ID, UTMs, Origem)

**Codigo server.js v1**:
- Express `/api/lead` + `/api/pipedrive-webhook` + `/health`
- Gate <4 veiculos: retorna `{redirect: '/obrigado-2/', reason: 'below_min_vehicles'}`, NUNCA cria deal, NUNCA dispara GTM/conversao
- Gate teste (nome/email com teste/test/fake/@contele): sheet only
- Round-robin 50/50 Thiago/Marcia persistido em `vendor-round-robin-fleet.json`
- Dedup `fired-conversions-fleet.json` no volume Railway
- CEO Julio Cesar notify via flag `NOTIFY_CEO`
- Blocklist defensiva planilha "Registros de trials"
- GA4 MP endpoint no webhook Pipedrive stage change
- Google Ads Upload API no webhook Pipedrive (se GCLID >=80 chars)

**Conteudo + visual**:
- index.html com 23 secoes HTML/CSS/JS puro
- Hero com ConverteAI smartplayer Julio (id 681353525fa484f00d837d53), lazy via IntersectionObserver, poster click-to-play
- Paleta real Fleet: `--purple-primary #8B23E5`, `--purple-deep #6C12B9`, `--dark-slate #20252E`
- 30 imagens baixadas pra `/img/` local + 23 WebP gerados (~80% economia)
- Carrosseis em 8 de 9 secoes de feature, `initCarousel` reusable via querySelectorAll + IntersectionObserver pra economizar CPU
- /obrigado/ scrape fiel da WP original, /obrigado-2/ pra gate <4 veiculos, /termos-uso/ stub

**SEO + AI crawlers**:
- llms.txt 54 linhas (bilingue PT-BR + EN), llms-full.txt 178 linhas (10 features + FAQ 8Q + EN)
- robots.txt 7 AI bots autorizados (GPTBot, ChatGPT-User, ClaudeBot, Claude-Web, PerplexityBot, Bytespider, GoogleOther)
- sitemap.xml 4 URLs validado xmllint
- Schema.org Organization + SoftwareApplication + FAQPage inline
- OG tags + Twitter Cards + canonical
