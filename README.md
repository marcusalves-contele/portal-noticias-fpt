# Growth - Monorepo Contele

Projetos de growth hacking e automacao de marketing da Contele.

## Arquitetura

Este repositorio e um **monorepo** com multiplos micro-servicos independentes, todos deployados no Railway.

### Railway Project

- **Projeto:** growth (Railway)
- **Repo GitHub:** contele/growth
- **Branch:** master (auto-deploy)

### Watch Paths (Deploy Seletivo)

Cada servico tem `watchPatterns` configurado no seu `railway.json` para evitar deploys desnecessarios:

```json
{
  "build": {
    "watchPatterns": ["nome-do-servico/**"]
  }
}
```

Isso garante que alteracoes em um servico **nao trigam deploy** dos outros.

---

## Servicos

### calculadora-reembolso-km/

Calculadora de reembolso por km rodado para equipes externas. Ativo de marketing para captacao de leads.

| Item | Valor |
|------|-------|
| **URL Producao** | https://calculadora-reembolso-km-production.up.railway.app |
| **Stack** | Node.js, Express, HTML/CSS/JS vanilla |
| **Database** | Supabase (PostgreSQL) |
| **Tabelas** | `growth_calculadora_usuarios`, `growth_calculadora_resultados` |

**Funcionalidades:**
- Calculo de reembolso por categoria de veiculo (moto, popular, medio, SUV)
- Considera: combustivel, depreciacao, seguro, manutencao, pneus, IPVA
- Captura de leads (WhatsApp + empresa)
- Historico de calculos por usuario
- Modal de metodologia transparente

---

### youtube-to-blog/

API que transforma videos do YouTube em posts de blog otimizados para SEO.

| Item | Valor |
|------|-------|
| **URL Producao** | https://youtube-to-blog-production-6f85.up.railway.app |
| **Stack** | Python, FastAPI, Gemini API |

**Funcionalidades:**
- Extrai transcricao automatica do video
- Gera conteudo otimizado via Gemini AI
- Cria imagem de capa com watermark
- Publica direto no WordPress (Fleet ou Teams)
- Gera texto pronto para WhatsApp

---

### contele-referral-page/

Landing page para programa de indicacao de clientes.

| Item | Valor |
|------|-------|
| **URL Producao** | https://indique.contele.io |
| **Stack** | React, TypeScript, Vite |

**Funcionalidades:**
- Formulario de indicacao
- Integracao com CRM (Pipedrive)

---

## Estrutura do Monorepo

```
growth/
├── calculadora-reembolso-km/   # Calculadora KM (Node.js)
│   ├── public/                 # Frontend (HTML/CSS/JS)
│   ├── src/                    # Backend (Express)
│   │   ├── server.js
│   │   ├── routes/api.js
│   │   └── services/supabase.js
│   ├── railway.json            # Config Railway + watchPatterns
│   └── package.json
│
├── youtube-to-blog/            # API YouTube->Blog (Python)
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   └── railway.json
│
├── contele-referral-page/      # Landing page (React)
│   ├── src/
│   ├── package.json
│   └── railway.json
│
└── README.md
```

## Deploy

### Configuracao no Railway

Cada servico no Railway tem:

1. **Source Repo:** `contele/growth`
2. **Root Directory:** `/nome-do-servico` (ex: `/calculadora-reembolso-km`)
3. **Watch Paths:** `nome-do-servico/**` (via railway.json)
4. **Branch:** `master`

### Adicionar Novo Servico

1. Criar pasta na raiz do repo
2. Adicionar `railway.json` com watchPatterns:
   ```json
   {
     "$schema": "https://railway.com/railway.schema.json",
     "build": {
       "builder": "NIXPACKS",
       "watchPatterns": ["nome-do-servico/**"]
     },
     "deploy": {
       "startCommand": "...",
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```
3. No Railway Dashboard:
   - New Service > GitHub Repo > contele/growth
   - Settings > Root Directory: `/nome-do-servico`
   - O watchPatterns sera lido automaticamente do railway.json

### Variaveis de Ambiente

Configuradas no Railway Dashboard para cada servico. Nunca commitar `.env` no repo.

---

## Para Agentes de IA

- Cada pasta e um servico independente
- Alteracoes em um servico nao afetam os outros (watch paths)
- Supabase project ID: `ziddmmazfgydnvcrjjtq`
- Prefixo de tabelas growth: `growth_`
- Deploy automatico via push no branch master
