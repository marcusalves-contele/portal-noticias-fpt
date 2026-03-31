# CLAUDE.md: conteleteams.com.br

## O que é

Landing page do Contele Teams (gestão de equipes externas).
Hospedada no Railway, CDN Cloudflare, backend Express nativo.

## Stack

- **Frontend**: HTML/CSS/JS puro (zero framework), inline CSS, inline SVGs
- **Backend**: Express.js (`server.js`), Railway
- **CDN**: Cloudflare (proxy ligado, SSL Full via Configuration Rule)
- **Tracking**: GTM (GTM-TQNBWXFK v14), GA4 (G-5VY7G6X0DJ), Bing UET, RD Station (lazy), Microsoft Clarity

## Arquitetura de Leads

```
Browser → POST /api/lead (Express)
    ├── Pipedrive: Person + Deal (com GCLID, GA4, UTMs)
    ├── Google Sheets: append (via Contele API, 19 colunas)
    ├── Slack: incoming webhook
    ├── WhatsApp: Evolution API (vendedor + Leonardo)
    └── n8n Cloud: SDR primeira mensagem (único n8n que resta)

Pipedrive deal stage change → webhook POST /api/pipedrive-webhook
    ├── Stage qualificado → GA4 Measurement Protocol (lead_qualificado)
    │                      → Google Ads Upload API (se GCLID >= 80 chars)
    ├── Deal won → GA4 Measurement Protocol (lead_convertido)
    │            → Google Ads Upload API (se GCLID >= 80 chars)
    ├── Discord: notificação com detalhes
    └── Slack: notificação
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `index.html` | Página principal (toda inline, ~95KB) |
| `server.js` | Backend Express: /api/lead, /api/pipedrive-webhook, health, redirects |
| `obrigado/index.html` | Thank you page (vídeo Leonardo, pilares, benefícios) |
| `termos-uso/index.html` | Termos de uso (conteúdo jurídico original, recuperado do Wayback Machine) |
| `sitemap.xml` | Sitemap pra Google |
| `robots.txt` | Robots pra crawlers |
| `llms.txt` | Resumo pra crawlers de IA (Gemini, ChatGPT, Perplexity) |
| `llms-full.txt` | Documentação completa pra LLMs |
| `railway.json` | Config Railway (Nixpacks, start command) |
| `legacy-appscript-send-to-n8n.js` | Apps Script antigo (referência, DESATIVADO) |

## Variáveis de Ambiente (Railway)

| Var | Uso |
|-----|-----|
| `PIPEDRIVE_API_TOKEN` | API Pipedrive |
| `EVOLUTION_API_KEY` | Evolution API WhatsApp |
| `EVOLUTION_API_URL` | URL da Evolution API |
| `EVOLUTION_INSTANCE` | Instância Evolution (default: Vendas n2) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook |
| `DISCORD_WEBHOOK_URL` | Discord webhook (conversões realtime) |
| `GA4_API_SECRET` | Measurement Protocol secret (`4vmy2fCVQDuTd7fOEQEasg`) |
| `GA4_MEASUREMENT_ID` | `G-5VY7G6X0DJ` |
| `GOOGLE_ADS_CLIENT_ID` | OAuth client ID Google Ads |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth client secret |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth refresh token |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | `HMDVGk1M3N0rotf2zXiZXQ` (Basic Access) |
| `GOOGLE_ADS_CUSTOMER_ID` | `5532904101` (Teams) |
| `RAILWAY_VOLUME_MOUNT_PATH` | Volume pra persistir dedup |

## Endpoints

| Endpoint | Método | Função |
|----------|--------|--------|
| `/api/lead` | POST | Recebe lead do form, cria Pipedrive, notifica, SDR |
| `/api/pipedrive-webhook` | POST | Webhook Pipedrive deal change, conversões offline |
| `/health` | GET | Health check |

## Pipedrive Custom Fields (Pipeline Teams 12)

| Campo | Key (hash) | Nota |
|-------|-----------|------|
| GCLID | `51bccf176e39e275ee09ace59bc724e0eb0157ab` | Campo dedicado, sem limite 255 chars |
| GA4 Client ID | `e98e94a65dcb60d96401853899c2126819991a43` | |
| Dados UTM | `f0fbb1341f09d81ca594898bab753004fb28b6ec` | String concatenada |
| Origem (URL) | `ded37a6dfbe7c85aacde82a228ac17011b97cca0` | CUIDADO: varchar(255), trunca GCLID! |
| Licenças | `3c8d91b14db8b39066af6d9ccac83bba77382582` | |
| Info | `d32b1afb76380fd11b2979947d42701ca0ab1884` | |
| Chatwoot | `1fe8780223d0b482b4de80f742f6d5c261858fe8` | |

## Pipeline 12 Stages

| ID | Nome | Tipo | Ação no webhook |
|----|------|------|-----------------|
| 94 | EM CONTATO | Inicial | Nenhuma |
| 265 | SDR FINALIZADO | - | Nenhuma |
| 211 | AGENDAR APRES. | - | Nenhuma |
| 158 | APRES. AGENDADA | - | Nenhuma |
| 96 | APRES. REALIZADA | Qualificado | GA4 + Google Ads upload |
| 209 | ACOMP. TESTE | Qualificado | GA4 + Google Ads upload |
| 245 | AGUARDANDO APROVAÇÃO | Qualificado | GA4 + Google Ads upload |
| 95 | FECHAMENTO SEMANA | Qualificado | GA4 + Google Ads upload |
| 156 | COMPRA ATÉ 90d | Qualificado | GA4 + Google Ads upload |
| 257-280 | ETAPA 1-5 | Won/Onboarding | GA4 + Google Ads upload (lead_convertido) |
| 238 | BASE GE | Won/Ativo | GA4 + Google Ads upload (lead_convertido) |

## Distribuição de Vendedores

| Faixa | Vendedor | Pipedrive user_id | WhatsApp |
|-------|----------|-------------------|----------|
| >= 4 licenças | Daniel | 13133598 | 5513997431489 |
| < 4 licenças | Nenhum (lead inadequado) | - | - |

Sheila (6186902) em licenca maternidade desde 31/03/2026. Todos os leads vao para Daniel.
Leonardo Gazolli (CEO) notificado em todos os leads: 5511999796461

## Proteções

- **Anti-spam frontend**: localStorage bloqueia re-submit por 60s
- **Filtro teste**: nome/email com teste/test/fake ou @contele.com → planilha only, sem deal
- **Lead < MIN_TEAM_SIZE (4)**: planilha com "4_lead_inadequado", sem deal, sem conversão
- **Dedup conversão**: Set persistente em Railway volume (`fired-conversions.json`)
- **Stage filter**: webhook só processa se `stage_id` mudou E `previous.stage_id` existe
- **Won filter**: só dispara se `previous.status` existe E era diferente de 'won'
- **GCLID length check**: Google Ads upload só se GCLID >= 80 chars (não truncado)

## GTM (GTM-TQNBWXFK)

- Versão publicada: **v14**
- Trigger de conversão: Custom Event "formSubmission" (ID 24)
- Tags antigas (URL /obrigado): pausadas
- Enhanced Conversions: **habilitado** (email + telefone hasheado via variável "Data phone and email")
- Microsoft Clarity: ativo

## Google Ads (conta Teams 553-290-4101)

| Conversão | Status | Primary | Tipo | Origem |
|-----------|--------|---------|------|--------|
| formSubmission (GA4) | ENABLED | **True** | GA4 Custom | Form submit qualificado |
| lead_qualificado (GA4) | ENABLED | False | GA4 Custom | Deal stage change (observation) |
| lead_convertido (GA4) | ENABLED | False | GA4 Custom | Deal won (observation) |
| se-inscreveu-demo-teams-v2 | ENABLED | False | Webpage | Antiga, rebaixada |

Conversion Actions pra upload offline:
- lead_qualificado: `customers/5532904101/conversionActions/7542373908`
- lead_convertido: `customers/5532904101/conversionActions/7542084401`

## GA4 (property 319908091)

- Stream: 9677066728 (Contele Teams nova Landing page, G-5VY7G6X0DJ)
- Measurement Protocol Secret: `conteleteams-backend` (ID 14123604060)
- Conversões marcadas: formSubmission, lead_qualificado, lead_convertido
- 4 contas Google Ads vinculadas
- Enhanced Measurement: habilitado (scroll, click, form_start, video)

## Cloudflare (zone 1a8b17b1b6164d973ab4720cc99cdf97)

- Root + www: CNAME → `9rzp2oyt.up.railway.app`, proxy ON
- SSL: Flexible (global) + **Configuration Rule** "Full" só pro root/www
- **Transform Rule**: remove X-Frame-Options + set Referrer-Policy (fix YouTube embed)
- APIs (app, prd-api, stg-api, etc.): proxy ON, SSL Flexible (NÃO MUDAR!)
- Token API: `cfut_BL5a...` com permissões: DNS, Zone, Zone Settings, Config Rules, Transform Rules, Cache Purge

## Pipedrive Webhook

- ID: 1850052
- Event: change deal
- URL: `https://conteleteams.com.br/api/pipedrive-webhook`

## Descoberta Crítica: GCLID truncado (varchar 255)

O campo "Origem (MKT)" no Pipedrive é varchar(255). URLs com UTMs + GCLID ultrapassam 255 chars.
O Pipedrive corta o final da URL, que é onde fica o GCLID. Resultado: GCLID truncado (~45 chars em vez de ~90-100).
Isso causava 556 falhas de upload offline. Resolvido com campo GCLID dedicado (sem limite).
Deals antigos: GCLID irrecuperável. Deals novos: GCLID completo via campo dedicado.

## Sistemas Desativados

- Apps Script da planilha: trigger onChange removido (20/mar/2026)
- Workflow n8n Railway (MIfmxdihSCEjS0Jj): desativado (20/mar/2026)
- Conversões offline via planilha (gclid-teams-qualificado): substituídas pelo GA4 + Google Ads API

## SEO e IA

- Schema.org: SoftwareApplication + Organization + FAQPage (6 perguntas)
- Open Graph + Twitter Cards
- Meta robots: max-snippet:-1, max-image-preview:large
- Canonical, sitemap.xml, robots.txt
- llms.txt + llms-full.txt pra crawlers de IA

## Doc completa no Vault

`obsidian-marco/02-DOING/nova-landing-page-contele-teams.md`
