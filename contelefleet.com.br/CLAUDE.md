# CLAUDE.md: contelefleet.com.br

## O que e

Landing page do Contele Fleet (gestao de frota). Scaffold backend criado em 20/04/2026 (Fase 1 da issue growth#79). HTML/frontend e outros assets sao responsabilidade de outro agente.

## Stack

- **Frontend**: HTML/CSS/JS puro (mesmo padrao do Teams, inline CSS/SVG)
- **Backend**: Express.js (`server.js`), Railway
- **CDN**: Cloudflare (proxy ligado)
- **Tracking**: GTM-52PR2JW (separado do Teams), GA4 (G-EQD5JNT9PS), Google Ads Fleet (398-401-5785)

## Diferencas vs Teams (contelefleet vs conteleteams)

| Item | Teams | Fleet |
|------|-------|-------|
| Pipeline Pipedrive | 12 | **1** |
| Stage inicial | 94 (EM CONTATO) | **2 (CONTATANDO)** |
| Stages qualificados | 96, 209, 245, 95, 156 | **157, 263, 3, 155** |
| Stages won | 257, 272, 278, 279, 280, 238 | **259, 270, 281, 282, 283, 240** |
| Stage LOST | (nao trackeado) | **241** (logado, nao dispara conversao) |
| Gatekeeping | < 4 lic: aceita pacote min ou sheet only | **< 4 veic: sheet + redirect `/obrigado-2/`, nunca cria deal** |
| Metrica entrada | `tamanho_equipe` (licencas) | `tamanho_frota` (veiculos) - aceita ambos |
| Vendedores | Daniel (Sheila em maternidade) | **Round-robin 50/50 Thiago + Marcia** |
| CEO notify | Leonardo Gazolli (fixo) | **Julio Cesar via flag `NOTIFY_CEO=true` (default on)** |
| Google Ads customer | 5532904101 | **3984015785** |
| GA4 Measurement ID | G-5VY7G6X0DJ | **G-EQD5JNT9PS** |
| GA4 Property | 319908091 | **319948806** |
| GTM Container | GTM-TQNBWXFK | **GTM-52PR2JW** |
| Planilha lead inadequado | 1cM0RpSRWarWNqSYDfjqTkPnrWI1BSP8jicm77n3KiTY | **1LkTpcEbPqVfb-zWviJHxme0saVGGt3anxg10oz1MjLc** (abas dedicadas, NUNCA "Registros de trials") |
| Discord webhook | `DISCORD_WEBHOOK_URL` | **`DISCORD_WEBHOOK_URL_FLEET`** |
| API secret GA4 | `GA4_API_SECRET` | **`GA4_API_SECRET_FLEET`** (a preencher) |
| Conv action qualified | 7542373908 | **7446455655** |
| Conv action won | 7542084401 | **7453621406** |
| Dedup file | fired-conversions.json | fired-conversions-fleet.json |

Custom fields do Pipedrive sao GLOBAIS (mesma conta contelegv), entao GCLID/GA4/UTMs/Origem usam os mesmos hashes do Teams. O hash chamado `licencas` no Teams e reaproveitado como `veiculos` no Fleet.

## Arquitetura de Leads

```
Browser -> POST /api/lead (Express)
    |-- Gatekeeping < 4 veic: sheet "4_lead_inadequado" + response { redirect: '/obrigado-2/' }
    |-- Teste (nome/email/empresa suspeito): sheet "3-temp-can-delete-teste", nao cria deal
    |-- Lead valido (>= 4 veic):
        |-- Pipedrive: Person + Deal (Pipeline 1, stage 2 CONTATANDO)
        |-- Google Sheets: append (via Contele API)
        |-- Slack: incoming webhook
        |-- WhatsApp: vendedor atribuido (round-robin)
        |-- WhatsApp CEO Julio Cesar (se NOTIFY_CEO=true)
        |-- SDR webhook (se SDR_WEBHOOK_URL_FLEET configurado)
        |-- Contele OS: POST /api/webhooks/sales-tracking (fire-and-forget)

Pipedrive deal stage change -> webhook POST /api/pipedrive-webhook
    |-- Pipeline 1 apenas; ignora outras
    |-- Stage qualificado (157/263/3/155) -> GA4 lead_qualificado + Google Ads upload (se GCLID >= 80)
    |-- Deal won (259/270/281/282/283/240) -> GA4 lead_convertido + Google Ads upload
    |-- Stage LOST (241) -> log apenas
    |-- Dedup via Set persistido em `fired-conversions-fleet.json` (Railway volume)
```

## Arquivos

| Arquivo | Funcao |
|---------|--------|
| `server.js` | Backend Express: /api/lead, /api/pipedrive-webhook, /health, redirects |
| `package.json` | Deps: express 4.21, compression 1.7 |
| `railway.json` | Nixpacks, watchPatterns contelefleet.com.br/** |
| `obrigado/` | Thank you page (lead qualificado) - **outro agente preenche** |
| `obrigado-2/` | Pagina pra lead < 4 veiculos - **outro agente preenche** |
| `termos-uso/` | Termos de uso - **outro agente preenche** |
| `img/` | Assets - **outro agente preenche** |
| `original.html` | HTML antigo (ja existia no repo, nao tocar) |

## Variaveis de Ambiente (Railway)

**Compartilhadas com Teams (mesmo projeto Pipedrive/Evolution/OAuth Google):**

| Var | Uso |
|-----|-----|
| `PIPEDRIVE_API_TOKEN` | API Pipedrive (conta contelegv) |
| `EVOLUTION_API_KEY` | Evolution API WhatsApp |
| `EVOLUTION_API_URL` | URL Evolution (default: evolution-api-817d7afc.contele.io) |
| `EVOLUTION_INSTANCE` | Instancia (default: Vendas n2) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook |
| `GOOGLE_ADS_CLIENT_ID` | OAuth client Google Ads |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth secret |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth refresh token |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | HMDVGk1M3N0rotf2zXiZXQ |
| `CONTELE_OS_URL` | https://os.contele.io |
| `CONTELE_OS_WEBHOOK_SECRET` | Secret pra propagacao tracking |
| `RAILWAY_VOLUME_MOUNT_PATH` | Volume pra dedup + vendor round-robin |

**Especificas Fleet:**

| Var | Uso | Default |
|-----|-----|---------|
| `GOOGLE_ADS_CUSTOMER_ID_FLEET` | 3984015785 | 3984015785 |
| `GA4_MEASUREMENT_ID_FLEET` | G-EQD5JNT9PS | G-EQD5JNT9PS |
| `GA4_API_SECRET_FLEET` | Measurement Protocol secret | **vazio (aguardando agente GA4)** |
| `DISCORD_WEBHOOK_URL_FLEET` | Discord webhook Fleet | vazio |
| `DISCORD_LEAD_CRITICAL_WEBHOOK_URL` | Critical alerts (opcional) | fallback DISCORD_WEBHOOK_URL_FLEET |
| `SDR_WEBHOOK_URL_FLEET` | n8n SDR Fleet | vazio (nao envia) |
| `SPREADSHEET_ID_FLEET` | Planilha principal (landing v2) | 1LkTpcEbPqVfb-zWviJHxme0saVGGt3anxg10oz1MjLc |
| `FLEET_SHEET_HISTORICO` | Aba audit log qualificados (dentro da principal) | `Landing v2 Historico` |
| `FLEET_SHEET_INADEQUADOS` | Aba audit log < 4 veic (dentro da principal) | `Leads Inadequados` |
| `FLEET_SHEET_HISTORICO_ID` | **Plano B:** planilha dedicada qualificados | vazio (usa a principal + aba) |
| `FLEET_SHEET_INADEQUADOS_ID` | **Plano B:** planilha dedicada inadequados | vazio (usa a principal + aba) |
| `NOTIFY_CEO` | Liga notify Julio Cesar | `true` |
| `CEO_FLEET_PHONE` | WhatsApp CEO | 5513997000902 (Julio) |
| `GADS_CONV_QUALIFIED_FLEET` | Conversion action qualified | customers/3984015785/conversionActions/7446455655 |
| `GADS_CONV_WON_FLEET` | Conversion action won | customers/3984015785/conversionActions/7453621406 |

## Endpoints

| Endpoint | Metodo | Funcao |
|----------|--------|--------|
| `/api/lead` | POST | Recebe lead do form, gatekeeping, Pipedrive, notify, SDR |
| `/api/pipedrive-webhook` | POST | Webhook Pipedrive deal change, conversoes offline |
| `/health` | GET | Health check |

## Distribuicao de Vendedores (round-robin)

| Vendedor | Pipedrive user_id | WhatsApp |
|----------|-------------------|----------|
| Thiago Andrade | 4447438 | 5511937083424 |
| Marcia Gabriele | 13168743 | 5513997143896 |

Round-robin 50/50 persistido em `vendor-round-robin-fleet.json` no Railway volume pra nao enviesar em restarts. Alterna a cada deal com >= 4 veiculos. CEO Julio Cesar (5513997000902) recebe copia de toda notificacao quando `NOTIFY_CEO=true`.

## Pipeline 1 Stages (Fleet)

| ID | Tipo | Acao no webhook |
|----|------|-----------------|
| 2 | CONTATANDO (inicial) | Nenhuma |
| 157 | Qualificado | GA4 `lead_qualificado` + Google Ads upload |
| 263 | Qualificado | GA4 + Google Ads |
| 3 | Qualificado | GA4 + Google Ads |
| 155 | Qualificado | GA4 + Google Ads |
| 259 | Won | GA4 `lead_convertido` + Google Ads |
| 270 | Won | GA4 + Google Ads |
| 281 | Won | GA4 + Google Ads |
| 282 | Won | GA4 + Google Ads |
| 283 | Won | GA4 + Google Ads |
| 240 | Won | GA4 + Google Ads |
| 241 | LOST | Log apenas |

## REGRA CRITICA: planilha Fleet tem Apps Script ligado

A planilha `1LkTpcEbPqVfb...` tem (ou teve) Apps Script `onChange` na aba **"Registros de trials"** que ja cria deal no Pipedrive + dispara fluxo n8n/WhatsApp. Se o server.js escrever nessa aba, vai DUPLICAR tudo.

**Regras hard no codigo (`appendSheet`):**

1. Nunca escreve na aba "Registros de trials" (blocklist explicita).
2. Lead qualificado (>= 4 veic) -> target `historico` -> aba `Landing v2 Historico` (audit log).
3. Lead inadequado (< 4 veic) -> target `inadequados` -> aba `Leads Inadequados`.
4. Test/fake -> target `historico` (fica no audit log).
5. Payload da API Contele inclui `sheet` + `sheetName` no body pra API escolher a aba. Se a API ignorar os params e sempre gravar na primeira aba, rodar **plano B**.

**Plano B (se API Contele `/spreadsheet/{id}` ignora o param `sheet`):**

Marco cria duas planilhas novas (sem Apps Script ligado) e preenche as envs:

1. Criar planilha nova "Fleet Landing v2 Historico" no Drive.
2. Criar planilha nova "Fleet Leads Inadequados" no Drive.
3. **Compartilhar ambas com a service account** (procurar qual SA o endpoint `ge-prd-web-api.contele.com.br/api/v1/spreadsheet/{id}` usa internamente - provavelmente a conta do projeto Contele que fala com Google Sheets; Marco pode confirmar no time de infra ou via suporte).
4. Preencher no Railway: `FLEET_SHEET_HISTORICO_ID=<id_planilha_historico>` e `FLEET_SHEET_INADEQUADOS_ID=<id_planilha_inadequados>`.
5. Com as envs preenchidas, `appendSheet` ignora `SPREADSHEET_ID_FLEET` pra essas operacoes e manda direto pra planilha dedicada (zero risco de cair numa aba errada).

**Como saber se precisa do plano B:** depois do deploy, um lead inadequado deve aparecer na aba "Leads Inadequados" (criar se nao existir). Se cair na Pagina1 ou em qualquer outra aba existente, a API nao suporta o param `sheet` e vale executar o plano B.

## Protecoes

- **Gatekeeping < 4 veiculos**: retorna `{ redirect: '/obrigado-2/' }`, grava sheet, NAO cria deal
- **Filtro teste**: nome/email com teste/test/fake/@contele.com -> sheet "3-temp-can-delete-teste"
- **Dedup conversao**: Set persistente em Railway volume (`fired-conversions-fleet.json`)
- **Stage filter**: webhook so processa se stage_id mudou E previous.stage_id existe
- **Won filter**: so dispara se previous.status existe E era diferente de 'won'
- **GCLID length check**: Google Ads upload so se GCLID >= 80 chars
- **Wrapper global**: qualquer throw em processLead dispara alerta critico, frontend ja recebeu 200

## Testar local

```bash
cd /Users/marcofassa/Documents/growth-contele/contelefleet.com.br
npm install
node server.js

# health
curl http://localhost:3000/health

# lead inadequado (< 4 veiculos) -> retorna redirect
curl -X POST http://localhost:3000/api/lead \
  -H "Content-Type: application/json" \
  -d '{"nome":"Teste Inadequado","email":"fake@fake.com","telefone":"5511999999999","empresa":"Empresa X","tamanho_frota":2}'

# lead teste (filtrado) -> sheet only
curl -X POST http://localhost:3000/api/lead \
  -H "Content-Type: application/json" \
  -d '{"nome":"Teste Fulano","email":"teste@teste.com","telefone":"5511999999999","empresa":"Contele","tamanho_frota":10}'
```

## NAO feito nesta fase

- `index.html` (frontend) - outro agente
- imagens em `img/` - outro agente
- conteudo de `obrigado/index.html`, `obrigado-2/index.html`, `termos-uso/index.html` - outro agente
- `sitemap.xml`, `robots.txt`, `llms.txt` - outro agente
- config Railway env vars (deploy) - Fase 4
- webhook Pipedrive cadastrado apontando pra `https://contelefleet.com.br/api/pipedrive-webhook` - Fase 4
- Cloudflare DNS apontando pra Railway - Fase 4

## Doc completa no Vault

Issue origem: `contele/growth#79`
Procedimento vendas: `obsidian-marco/DOCS/procedimento-vendas-fleet.md`
