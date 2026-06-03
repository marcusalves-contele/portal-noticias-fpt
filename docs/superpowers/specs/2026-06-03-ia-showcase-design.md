# Design Spec: Página de Showcase de IA & Automações

**Data:** 2026-06-03  
**Status:** Aprovado  
**Repositório:** `growth/contele-ia-projetos/`

---

## Objetivo

Página de marketing pública para demonstrar a capacidade da Contele em criar projetos personalizados de IA e automação para clientes parceiros. Público-alvo: potenciais clientes querendo entender o que é possível construir com Contele.

---

## Arquitetura

**Stack:** HTML puro + CSS inline + JS vanilla, servido por Express.js  
**Padrão:** Idêntico ao `conteleteams.com.br/benchmark/vitamedic/`  
**Deploy:** Railway (Nixpacks), novo serviço no projeto Railway da Contele

```
growth/contele-ia-projetos/
├── index.html      # Página completa
├── server.js       # Express estático (porta 3000)
├── package.json    # express, compression
└── railway.json    # Nixpacks, start: node server.js
```

---

## Design Visual

Seguir exatamente o sistema de design do `benchmark/vitamedic`:

- **Fundo:** `#0A0E1A` (dark base)
- **Fontes:** Fraunces (títulos serif), DM Sans (corpo), JetBrains Mono (labels/badges)
- **Cores de acento:** `#4A58FF` (azul), `#29BDFF` (cyan), `#4ADE80` (verde/sucesso)
- **Efeitos:** noise texture overlay, glassmorphism no nav, gradientes radiais no hero
- **Animações:** fade-in on scroll via IntersectionObserver (igual ao benchmark)

---

## Seções da Página

### 1. Nav (sticky)
- Logo Contele (quadrado azul + "Contele")
- Label "IA & Automações" em JetBrains Mono
- Glassmorphism + blur

### 2. Hero
- Eyebrow: `[ PROJETOS PERSONALIZADOS ]` em mono uppercase
- Título: "Automações inteligentes para operações de campo" (Fraunces, `--fs-hero`)
- Subtítulo: descrição de 2 linhas sobre customização com IA + n8n
- Stat inline: "4 projetos com IA desenvolvidos" e "258+ automações ativas"
- Gradiente radial azul/cyan no fundo

### 3. Projetos em Destaque (4 cards grandes)
Grid 2×2 no desktop, 1 coluna no mobile. Cada card tem:
- **Badge de tecnologia** (ex: `Google Gemini Vision`) — JetBrains Mono, cor ciano
- **Tag de categoria** (ex: `Visão Computacional`) — pill colorido
- **Nome do case** — Fraunces bold
- **Descrição** — DM Sans, 2-3 linhas
- **Integrações** — ícones/tags das ferramentas usadas (Google Sheets, PostgreSQL, etc.)
- Borda sutil (`--line-2`), hover com lift e glow azul

**Os 4 cases de IA:**

| # | Nome do Case | Tecnologia | Categoria |
|---|---|---|---|
| 1 | Validação de Fotos por IA | Google Gemini Vision | Visão Computacional |
| 2 | Reagendamento Inteligente de Visitas | Google Gemini Vision + LangChain | Agendamento Inteligente |
| 3 | Análise de Química de Piscina por Foto | Google Gemini Vision | Visão Computacional |
| 4 | Analisador Automático de Workflows | Google Gemini Flash 2.5 | Análise & Documentação |

Clientes apresentados de forma genérica (ex: "Cliente do setor automotivo") para não expor parceiros sem permissão.

### 4. Outras Automações (grid secundário)
Grid 3 colunas no desktop, 2 no tablet, 1 no mobile. Cards menores com:
- Ícone representativo (SVG inline simples)
- Título do caso
- Descrição curta (1 linha)
- Tag de integração principal

**6 exemplos secundários (de workflows ativos reais):**

1. Checklist → Relatório em Planilha (JMV Manutenção / Fleet)
2. Integração Contele × Bling (Ouro Verde / Teams)
3. Visita Concluída → Planilha de Gestão (Teclift / Teams)
4. Notificações para Cliente Final (PVClean / Teams)
5. Agenda Visita via Notion (Vértis Elevadores / Teams)
6. Relatório de Abastecimento e Cerca Eletrônica (Disfer / Fleet)

### 5. CTA Final
- Título: "Quer uma automação personalizada para seu negócio?"
- Subtítulo: 1 linha de valor
- Botão primário: "Falar com especialista" → link WhatsApp da Contele (mesmo padrão das outras landing pages do repo)
- Fundo com gradiente azul diferenciado da seção anterior

---

## Componentes JS (vanilla)

- **Reading progress bar** — barra de 2px no topo, linear-gradient azul/cyan
- **Fade-in on scroll** — IntersectionObserver com `threshold: 0.1`, classe `.visible` adiciona `opacity: 1; transform: translateY(0)`
- **Nav chapter update** — ao scrollar, atualiza label da seção atual

---

## O que está fora do escopo

- Formulário de contato na própria página (redireciona para canal existente)
- Filtros/tabs por categoria
- Modais com detalhes expandidos
- Analytics/GTM (pode ser adicionado depois)
- Autenticação ou área privada
