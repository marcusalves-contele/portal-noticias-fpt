# CLAUDE.md - Growth (Contele Referral Pages)

## Project Overview

Repositório de landing pages de growth hacking para Contele. Projeto principal: **Indique e Ganhe** - sistema de referência com recompensa PIX (R$ 300,00).

**Produtos suportados**:
- **Contele Fleet** - Gestão de frotas
- **Contele Teams** - Gestão de equipes externas

**Fluxo de conversão**:
1. Visitante preenche dados do indicado (lead)
2. Preenche seus dados (nome, WhatsApp, chave PIX)
3. Seleciona produto de interesse
4. Submit envia para webhook n8n
5. n8n integra com Pipedrive CRM
6. Pagamento automático após fechamento

## Stack Técnica

| Tech | Version | Uso |
|------|---------|-----|
| React | 19.2.1 | Framework UI |
| TypeScript | 5.8 | Type safety |
| Vite | 6.2 | Build + dev server |
| Tailwind CSS | CDN | Styling |
| lucide-react | 0.557 | Icons |

## Project Structure

```
growth/
├── CLAUDE.md                    # Este arquivo
├── contele-referral-page/       # Landing page "Indique e Ganhe"
│   ├── railway.json             # Config Railway (NIXPACKS)
│   ├── package.json             # Dependencies
│   ├── vite.config.ts           # Vite build config
│   ├── index.html               # HTML template
│   ├── App.tsx                  # Root component
│   ├── types.ts                 # TypeScript interfaces
│   ├── components/
│   │   ├── Header.tsx           # Nav com logo
│   │   ├── Benefits.tsx         # Value props + hero
│   │   └── ReferralForm.tsx     # Form principal (257 LOC)
│   └── services/
│       └── webhookService.ts    # Integração n8n
```

## Key Components

### ReferralForm.tsx (Principal)
- State management para form multi-step
- Validação de telefone com máscara BR: (XX) XXXXX-XXXX
- Radio buttons para seleção de produto
- Loading states + success/error screens
- Mantém dados do referidor para múltiplas indicações

### webhookService.ts
- POST JSON para webhook n8n
- Adiciona timestamp e source tracking
- URL configurável via env var `VITE_N8N_WEBHOOK_URL`

## Development

```bash
cd contele-referral-page
npm install
cp .env.local.example .env.local   # Configurar webhook URL
npm run dev                         # http://localhost:5173
```

## Environment Variables

Criar `.env.local` baseado no `.env.local.example`:

```bash
VITE_N8N_WEBHOOK_URL=https://primary-production-2349.up.railway.app/webhook/referral-submission
```

**Importante**: Prefixo `VITE_` é obrigatório para Vite expor a variável no client-side.

## Deployment (Railway)

### URLs
| Ambiente | URL |
|----------|-----|
| **Produção** | https://growth-production-8ca9.up.railway.app |
| **Domínio futuro** | https://indique.contele.io (pendente config Cloudflare) |

### Configuração no Dashboard
1. New Project → Deploy from GitHub repo
2. **Root Directory**: `contele-referral-page`
3. **Builder**: NIXPACKS (automático)
4. Adicionar env vars no painel

### railway.json
Já configurado com:
- Builder: NIXPACKS
- Start: `npm run preview` (serve dist/ em produção)
- Health check: `/`

### Deploy Commands
```bash
npm run build    # Gera dist/
npm run preview  # Serve SPA com fallback
```

## n8n Integration

**Webhook atual**: `https://primary-production-2349.up.railway.app/webhook/referral-submission`

**Payload enviado**:
```json
{
  "leadName": "Nome do Indicado",
  "leadPhone": "(11) 99999-9999",
  "leadCompany": "Empresa do Lead",
  "referrerName": "Nome de Quem Indica",
  "referrerPhone": "(11) 88888-8888",
  "referrerPixKey": "email@exemplo.com",
  "selectedProduct": "Contele Fleet",
  "timestamp": "2025-12-10T15:30:00.000Z",
  "source": "lp-indique-ganhe-v2"
}
```

## Design System

### Cores Contele
```css
--blue-primary: #002F6C    /* Azul escuro principal */
--accent-green: #00D084    /* Verde PIX/destaque */
--blue-gradient: from-blue-900 to-blue-800
```

### Responsividade
- Mobile-first (1 coluna)
- Desktop lg: (2 colunas - benefits + form)

## Git Workflow

- **Branch principal**: `master`
- **Remote**: `https://github.com/contele/growth.git`
- **Nunca commitar**: `.env.local`, `node_modules/`, `dist/`

## Checklist Pre-Deploy

- [ ] `npm install` rodou sem erros
- [ ] `.env.local` criado com webhook URL
- [ ] `npm run dev` funciona localmente
- [ ] `npm run build` gera `dist/` sem erros
- [ ] Railway Root Directory = `contele-referral-page`
- [ ] Env vars configuradas no Railway
- [ ] Health check passando após deploy

## Troubleshooting

### Build falha no Railway
- Verificar se `railway.json` está em `contele-referral-page/`
- Confirmar Root Directory no dashboard
- Usar NIXPACKS, não Dockerfile

### Webhook não funciona
- Verificar se `VITE_N8N_WEBHOOK_URL` está setada
- Testar webhook URL diretamente com curl
- Checar logs do n8n

### Formulário não valida telefone
- Formato esperado: (XX) XXXXX-XXXX
- Regex: `/^\(\d{2}\) \d{5}-\d{4}$/`

---

## Thumbnail AI Creator

Sistema de geração de thumbnails YouTube com Gemini (`gemini-3-pro-image-preview`).
Doc completo: `thumbnail-ai-creator/CLAUDE.md`

### Planilhas de Conteúdo (fonte de dados)
| Canal | Spreadsheet ID | Sheet |
|-------|---------------|-------|
| **Fleet** (Julio) | `1lluvZ8SKQNThV4o4OzWqmsttP-BgRC1FU3AqwvfJbqI` | `Fleet` (gid=25167001) |
| **Teams** (Leonardo) | `1RjMazaU0fV5npXIJFcZTrrGVbJVeWxv8VV8y1uMEJVU` | `Teams` (gid=1789816867) |

**Colunas**: Tarefa no Asana | tema | Tipo | title | Texto da thumb | Convidado | url | summary | type

Linhas com "Tarefa no Asana" preenchido = thumbs pendentes de criação.

### Grupo WhatsApp de Entrega
- **Grupo**: IA - Growth Contele
- **JID**: `120363424539843742@g.us`
- Enviar thumbs aprovadas via zap agent (suporta imagens via `/send-image`)

### Referências Disponíveis
- **Julio** (Fleet): `referencias/julio/` — 3 fotos (2 sérias + 1 sorrindo)
- **Leonardo** (Teams): `referencias/leonardo/` — 2 fotos (cyberpunk-styled)
- **Convidados**: `referencias/convidados/` — padrão: `convidado_live-{NUM}-{Nome}.{ext}`

### Pendências para Liberar o Sistema pro Time

1. **Fotos profissionais 4K do Julio e Leonardo**
   - Expressões variadas: sério, empolgado, surpreso, preocupado
   - Hoje as refs são limitadas e impactam fidelidade facial
   - Julio: 3 fotos atuais (aceitáveis mas não ideais)
   - Leonardo: 2 fotos cyberpunk (ruim pra referência, neon/efeitos atrapalham)

2. **Fotos dos convidados**
   - Hoje depende de buscar manualmente (site, Asana, etc)
   - Ideal: time sobe foto na planilha/Asana ANTES de pedir thumb
   - Fotos reais simples (selfie, foto corporativa) > fotos estilizadas

3. **Planilha unificada**
   - Hoje: 2 planilhas separadas (Fleet + Teams) como base de conteúdo
   - Objetivo: base de dados ÚNICA com todos os vídeos + ações
   - Precisa alinhar formato com Marco (conversa pendente)
   - Proposta: vídeos + status thumb + link thumb + responsável + prioridade
