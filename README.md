# Growth

Projetos de growth hacking e automacao de marketing da Contele.

## Projetos

### youtube-to-blog/

API FastAPI que transforma videos do YouTube em posts de blog otimizados para SEO.

**URL Producao:** https://youtube-to-blog-production-6f85.up.railway.app

**Funcionalidades:**
- Extrai transcricao automatica do video
- Gera conteudo otimizado via Gemini AI
- Cria imagem de capa com watermark
- Publica direto no WordPress (Fleet ou Teams)
- Gera texto pronto para WhatsApp

**Stack:** Python, FastAPI, Gemini API, YouTube API, WordPress REST API

**Deploy:** Railway (auto-deploy via GitHub)

---

### contele-referral-page/

Landing page para programa de indicacao de clientes.

**Stack:** React, TypeScript, Vite

**Funcionalidades:**
- Formulario de indicacao
- Integracao com CRM

---

## Estrutura

```
growth/
├── youtube-to-blog/     # API de conversao YouTube -> Blog
│   ├── main.py          # FastAPI app
│   ├── requirements.txt
│   └── railway.json     # Config Railway
│
└── contele-referral-page/   # Landing page indicacoes
    ├── App.tsx
    ├── components/
    └── package.json
```

## Deploy

Cada pasta e um servico independente no Railway, com seu proprio Root Directory configurado.
