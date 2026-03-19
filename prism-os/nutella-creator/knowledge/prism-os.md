---
title: "PRISM OS — Product Vision"
created: 2026-03-05
tags: [prism-os, produto, content-os, thumbnails, nutellas, youtube, ia]
---

# PRISM OS

## Tagline

**EN:** From brief to viral, by design.
**PT:** Do briefing ao viral, por design.

---

## O que é

**EN:**
PRISM OS is a content production operating system. It enters before the camera rolls and stays until the video is live — covering pre-planning, production, and post-production in a single pipeline.

One video in. Clips, shorts, thumbnails, SEO, and a smart publishing schedule out.

**PT:**
PRISM OS é um sistema operacional de produção de conteúdo. Ele entra antes da câmera ligar e permanece até o vídeo ir ao ar — cobrindo pré-planejamento, produção e pós-produção em um único pipeline.

Um vídeo entra. Clips, shorts, thumbnails, SEO e agendamento inteligente saem.

---

## Os Três Atos

| Fase | EN | PT |
|------|----|----|
| Pre | Plan: SEO, title, thumbnail concept, description | Planejar: SEO, título, conceito de thumbnail, descrição |
| Production | Shoot: live or scripted video | Produzir: live ou vídeo com roteiro |
| Post | Multiply: AI-powered cutting, face-locked thumbnails, smart scheduling | Multiplicar: corte por IA, thumbnails com face-lock, agendamento inteligente |

---

## Capabilities

- Análise de transcrição por IA para identificar os melhores momentos de viralização
- Corte automático em 16:9 (clip) e 9:16 (short) com detecção facial
- Geração de thumbnails realistas com face-lock via Gemini + referências fotográficas reais
- Upload no YouTube com título SEO, tags, descrição e agendamento inteligente

**Input:** URL de um vídeo do YouTube (live ou com roteiro)
**Output:** Clips, shorts, thumbnails, metadados e agendamento — prontos para publicar

---

## Positioning

> "The full-cycle content OS for serious creators."

Diferencial: não é só um cortador de vídeo. É um sistema que entra no pré, acompanha a produção e fecha no pós — com IA em cada etapa.

---

## Status

- Versão: v2 (Dashboard web)
- Canal piloto: Frota Para Todos (Julio César)
- Stack: Python + Gemini + ffmpeg + YouTube API

---

## Módulos (docs técnicas)

| Módulo | Doc |
|--------|-----|
| Thumbnail AI Creator | [[thumbnail-ai-creator]] |
| Sistema de Thumbnails | [[sistema-thumbnails-ai]] |
| Nutella Creator (clips virais) | [[nutella-plano-producao-master]] |
| Nutella Backlog de Lives | [[nutella-backlog-lives]] |
| Agendamento Inteligente | [[nutella-agendamento-inteligente]] |
| Prompt Agent Thumb | [[prompt---agent-thumb-creator]] |
| Template PodVisitar | `thumbnail-ai-creator/prompts/template_podvisitar.md` |

**Repo local:** `growth-contele/prism-os/`
- `nutella-creator/`
- `thumbnail-ai-creator/`

---

## Plano de Publicação V2 — Canal Frota Para Todos

> Atualizado: 05/mar/2026 | Status: validando com Isa + Julio

### Contexto

- Lives semanais (quarta, 8h BRT) → fonte de conteúdo
- Backlog: 24 lives represadas → 48+ vídeos potenciais
- Último vídeo da fila antiga: **09/03** → novo plano começa **12/03**

### Fórmula V2

```
4 vídeos/semana
├── 2 clips da live mais recente (Clip A + Clip B)
└── 2 clips de live do backlog priorizado (Clip A + Clip B)

Regras:
- NUNCA publicar na quarta (dia da live ao vivo)
- Máx 1 vídeo/dia
- Clip A e B da mesma live: mínimo 2 dias de distância
```

**Slots confirmados por analytics:**

| Slot | Dia | Hora |
|------|-----|------|
| C1 | Quinta | 15h |
| C2 | Sexta | 17h |
| C3 | Sábado | 07h |
| C4 | Segunda | 17h |

---

### Backlog Priorizado V2

> Critério duplo: engajamento orgânico (base atual) + volume de busca externo (descoberta)

| # | Live | Tema | Score Eng | Demanda Externa | Evidência |
|---|------|------|-----------|-----------------|-----------|
| 1 | **317** | Veículo Elétrico: O Que Saber Antes | 36 | ALTA | Sardinha: 193K views no tema |
| 2 | **298** | Manutenção: Da Planilha ao Sistema | 44 | ALTA | Hashtag Treinamentos: 85K em "planilha frota" |
| 3 | **305** | Fraude de Combustível: Guia Definitivo | 38 | ALTA | Dor real, FPT domina o tema |
| 4 | **318** | Condução Econômica: Elimine o Jeitinho | 36 | MÉDIA | INFLEET: 10K, concorrente fraco |
| 5 | **313** | Dashboards com IA para Frota | 54 | BAIXA | FPT domina, ótimo pra base atual |
| 6 | **304** | Plano de Manutenção do Zero com IA | 40 | BAIXA | Nicho FPT |
| 7 | **303** | Manutenção Preventiva e Redução de Custos | 38 | BAIXA | Concorrentes fracos (<1.5K views) |
| 8 | **302** | TIN: Do Conceito ao Controle | 38 | BAIXA | Jargão do nicho, FPT owns 100% |

> Regra de título: lives com demanda ALTA precisam ter a palavra-chave da busca no título do clip.
> Exemplo: Live 298 → título precisa conter "planilha" explicitamente.

---

### Calendário V2 — Semana a Semana

#### Semana 2 (12–17 mar) — Live 321 + Backlog #1: Live 317

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 12/03 | Qui | 15h | 321 | Clip A |
| 13/03 | Sex | 17h | 317 | Clip A |
| 14/03 | Sáb | 07h | 321 | Clip B |
| 16/03 | Seg | 17h | 317 | Clip B |

Produzir essa semana: Live 321 + Live 317

#### Semana 3 (19–24 mar) — Welcome Video + Live 322 + Backlog #2: Live 298

| Data | Dia | Hora | Conteúdo |
|------|-----|------|----------|
| 19/03 | Qui | 15h | Primeiros Passos para o Gestor de Frota (vídeo novo) |
| 20/03 | Sex | 17h | Live 298 — Clip A |
| 21/03 | Sáb | 07h | Live 322 — Clip A |
| 23/03 | Seg | 17h | Live 322 — Clip B |

Produzir: Live 322 (nova 11/03) + gravar Welcome Video semana de 09/03

#### Semana 4 (26–31 mar) — Live 323 + Live 298 B + Backlog #3: Live 305

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 26/03 | Qui | 15h | 298 | Clip B |
| 27/03 | Sex | 17h | 305 | Clip A |
| 28/03 | Sáb | 07h | 323 | Clip A |
| 30/03 | Seg | 17h | 323 | Clip B |

#### Semana 5 (02–07 abr) — Live 324 + Live 305 B + Backlog #4: Live 318

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 02/04 | Qui | 15h | 305 | Clip B |
| 03/04 | Sex | 17h | 318 | Clip A |
| 04/04 | Sáb | 07h | 324 | Clip A |
| 06/04 | Seg | 17h | 324 | Clip B |

#### Semana 6 (09–14 abr) — Live 325 + Live 318 B + Backlog #5: Live 313

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 09/04 | Qui | 15h | 318 | Clip B |
| 10/04 | Sex | 17h | 313 | Clip A |
| 11/04 | Sáb | 07h | 325 | Clip A |
| 13/04 | Seg | 17h | 325 | Clip B |

#### Semana 7 (16–21 abr) — Live 326 + Live 313 B + Backlog #6: Live 304

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 16/04 | Qui | 15h | 313 | Clip B |
| 17/04 | Sex | 17h | 304 | Clip A |
| 18/04 | Sáb | 07h | 326 | Clip A |
| 20/04 | Seg | 17h | 326 | Clip B |

#### Semana 8 (23–28 abr) — Live 327 + Live 304 B + Backlog #7: Live 303

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 23/04 | Qui | 15h | 304 | Clip B |
| 24/04 | Sex | 17h | 303 | Clip A |
| 25/04 | Sáb | 07h | 327 | Clip A |
| 27/04 | Seg | 17h | 327 | Clip B |

#### Semana 9 (30 abr – 05 mai) — Live 328 + Live 303 B + Backlog #8: Live 302

| Data | Dia | Hora | Live | Tipo |
|------|-----|------|------|------|
| 30/04 | Qui | 15h | 303 | Clip B |
| 01/05 | Sex | 17h | 302 | Clip A |
| 02/05 | Sáb | 07h | 328 | Clip A |
| 04/05 | Seg | 17h | 328 | Clip B |

Revisão de slots: mai/2026 — comparar performance por slot com dados reais.

---

### Status de Validação

| Pessoa | Status |
|--------|--------|
| Isabela Brigido (MKT) | Mensagem enviada 05/03, aguardando resposta |
| Julio César (canal) | Pendente contato |

---

## TODO — Produto

- [ ] **Favicon / ícone na aba do Chrome** — criar ícone representando o PRISM OS (prisma refrataando luz?) e adicionar no `<head>` do dashboard
- [ ] **Motion na tela inicial** — criar animação de entrada que remeta a IA e ao conceito de prisma (luz se decompondo, partículas, efeito de refração) — deve ser impactante e premium
- [ ] **Mover youtube-to-blog para dentro do PRISM OS** — `growth-contele/youtube-to-blog/` já existe e é parte do pipeline de distribuição (vídeo → post de blog). Integrar como módulo do OS junto com nutella-creator e thumbnail-ai-creator.
