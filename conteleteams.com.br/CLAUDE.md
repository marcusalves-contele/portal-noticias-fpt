# CLAUDE.md: conteleteams.com.br

## O que é

Landing page do Contele Teams (gestão de equipes externas).
Hospedada no Railway, CDN Cloudflare, backend Express nativo.

## Stack

- **Frontend**: HTML/CSS/JS puro (zero framework), inline CSS, inline SVGs
- **Backend**: Express.js (`server.js`), Railway
- **CDN**: Cloudflare (proxy ligado, SSL Full via Configuration Rule)
- **Tracking**: GTM (GTM-TQNBWXFK), GA4 (G-5VY7G6X0DJ), Bing UET, RD Station (lazy)

## Arquitetura de Leads

```
Browser → POST /api/lead (Express)
    ├── Pipedrive: Person + Deal (com GCLID, GA4, UTMs)
    ├── Google Sheets: append (via Contele API)
    ├── Slack: incoming webhook
    ├── WhatsApp: Evolution API (vendedor + Leonardo)
    └── n8n Cloud: SDR primeira mensagem (único n8n que resta)

Pipedrive deal stage change → webhook POST /api/pipedrive-webhook
    ├── Stage qualificado → GA4 Measurement Protocol (lead_qualificado)
    ├── Deal won → GA4 Measurement Protocol (lead_convertido)
    ├── Discord: notificação
    └── Slack: notificação
```

## Arquivos principais

| Arquivo | Função |
|---------|--------|
| `index.html` | Página principal (toda inline) |
| `server.js` | Backend Express: /api/lead, /api/pipedrive-webhook, health, redirects |
| `obrigado/index.html` | Thank you page (vídeo Leonardo, pilares) |
| `sitemap.xml` | Sitemap pra Google |
| `robots.txt` | Robots pra crawlers |
| `llms.txt` | Resumo pra crawlers de IA (Gemini, ChatGPT, etc.) |
| `llms-full.txt` | Documentação completa pra LLMs |
| `railway.json` | Config Railway (Nixpacks, start command) |
| `legacy-appscript-send-to-n8n.js` | Apps Script antigo (referência, desativar) |

## Variáveis de Ambiente (Railway)

| Var | Uso |
|-----|-----|
| `PIPEDRIVE_API_TOKEN` | API Pipedrive |
| `EVOLUTION_API_KEY` | Evolution API WhatsApp |
| `EVOLUTION_API_URL` | URL da Evolution API |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook |
| `GA4_API_SECRET` | Measurement Protocol secret |
| `GA4_MEASUREMENT_ID` | G-5VY7G6X0DJ |
| `DISCORD_WEBHOOK_URL` | Discord webhook (conversões) |
| `RAILWAY_VOLUME_MOUNT_PATH` | Volume pra persistir dedup |

## Pipedrive Custom Fields (Teams Pipeline 12)

| Campo | Key (hash) |
|-------|-----------|
| GCLID | `51bccf176e39e275ee09ace59bc724e0eb0157ab` |
| GA4 Client ID | `e98e94a65dcb60d96401853899c2126819991a43` |
| Dados UTM | `f0fbb1341f09d81ca594898bab753004fb28b6ec` |
| Origem (URL) | `ded37a6dfbe7c85aacde82a228ac17011b97cca0` |
| Licenças | `3c8d91b14db8b39066af6d9ccac83bba77382582` |
| Info | `d32b1afb76380fd11b2979947d42701ca0ab1884` |
| Chatwoot | `1fe8780223d0b482b4de80f742f6d5c261858fe8` |

## Pipeline 12 Stages

| ID | Nome | Tipo |
|----|------|------|
| 94 | EM CONTATO | Inicial |
| 265 | SDR FINALIZADO | - |
| 211 | AGENDAR APRES. | - |
| 158 | APRES. AGENDADA | - |
| 96 | APRES. REALIZADA | Qualificado |
| 209 | ACOMP. TESTE | Qualificado |
| 245 | AGUARDANDO APROVAÇÃO | Qualificado |
| 95 | FECHAMENTO SEMANA | Qualificado |
| 156 | COMPRA ATÉ 90d | Qualificado |
| 257-280 | ETAPA 1-5 | Won/Onboarding |
| 238 | BASE GE | Won/Ativo |

## Distribuição de Vendedores

| Faixa | Vendedor | Pipedrive user_id |
|-------|----------|-------------------|
| >= 21 licenças | Sheila | 6186902 |
| 10-20 licenças | Round-robin Sheila/Daniel | - |
| 4-9 licenças | Daniel | 13133598 |
| < 4 licenças | Nenhum (lead inadequado) | - |

## Proteções

- **Anti-spam**: localStorage 60s no frontend
- **Filtro teste**: nome/email com teste/test/fake ou @contele.com → planilha only
- **Dedup conversão**: Set persistente em volume Railway (1 conversão por deal)
- **Stage filter**: webhook só processa se stage_id mudou de verdade
- **Won filter**: só dispara lead_convertido se previous.status !== 'won'

## GTM (GTM-TQNBWXFK)

- Versão publicada: v13
- Trigger de conversão: Custom Event "formSubmission" (ID 24)
- Tags antigas (URL /obrigado): pausadas
- Enhanced Conversions: PENDENTE (habilitar na tag 11, publicar v14)

## GA4 (property 319908091)

- Stream: 9677066728 (Contele Teams nova Landing page)
- Conversões marcadas: formSubmission, lead_qualificado, lead_convertido
- Measurement Protocol Secret: conteleteams-backend
- 4 contas Google Ads vinculadas

## Cloudflare (zone 1a8b17b1b6164d973ab4720cc99cdf97)

- Root + www: CNAME → Railway, proxy ON
- SSL: Flexible (global) + Configuration Rule "Full" só pro root/www
- APIs (app, prd-api, etc.): proxy ON, SSL Flexible (não mudar!)

## Doc completa no Vault

`obsidian-marco/02-DOING/nova-landing-page-contele-teams.md`
