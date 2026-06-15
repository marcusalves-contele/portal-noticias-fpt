---
title: "Brand fpt agent"
tags: [marca, fpt]
source: human
updated: 2026-04-18
---

## TL;DR

**O que e**: Biblia da marca Frota Para Todos (FPT) para agentes de IA. Carregar antes de criar qualquer material FPT (thumbnail, copy, imagem, roteiro, post).
**Canal**: YouTube `@JulioCesarFrotaParaTodos` (33,4K subs). Julio Cesar e a marca. FPT = topo de funil, Contele Fleet = conversao.
**Paleta exata**: Roxo Principal `#8B23E5` (nunca aproximacoes), Roxo Profundo `#4E0091`, Background Dark `#080010`, Branco Suave `#F7F7F7`. Proibido: `#7C3AED`, `#6D28D9`.
**Tipografia**: Montserrat exclusivamente. H1 48px Bold, H2 36px Semi-bold, Body 18px Regular.
**Arquetipo**: Sage Pragmatico (primario) + Hero (secundario). Vilao: Conteudo de Vitrine e Gestor que Apaga Fogo.
**Assets**: Drive master `1VMLHN8V9Pf9MCVSkxhdn-nLVtipq5575`. Logos: `1345X5PBzS3rGdQ_VKV0Fvr31WeKA4JZW`. Identidade sonora (Opcao A escolhida por Julio): `fpt-option-a.wav`.
**Regras criticas**: Sempre Montserrat, sempre paleta exata, nunca fundo claro como principal, nunca tom corporativo, polo navy lisa no Julio (sem logos em geracoes IA).
**Ultima atualizacao**: 2026-03-10

---

# brand-fpt-agent.md
## Bíblia da Marca FPT — Versão para Agentes de IA

> **Como usar este documento**
> Carregue este arquivo antes de qualquer operação que envolva a marca Frota Para Todos: criar thumbnail, escrever copy, gerar imagem, montar roteiro, criar post, definir tom de resposta, construir persona, editar qualquer material do canal.
> Este documento é a fonte da verdade operacional para agentes. A versão humana está em: https://marcofassa-cto.web.app/brand-fpt/
>
> Última atualização: 2026-03-10

---

## 0. PROTOCOLO DE SINCRONIZAÇÃO

> Este bloco define como manter os dois documentos de marca em sincronia.

### Dois documentos, uma fonte da verdade

| Documento | Tipo | Para quem | Onde |
|---|---|---|---|
| `brand-fpt-agent.md` | Fonte da verdade | Agentes de IA, sistemas, Prism OS | Vault Obsidian |
| `brand-fpt/index.html` | Representação visual | Humanos (time, parceiros) | Firebase: marcofassa-cto.web.app/brand-fpt/ |

**Regra de ouro:** sempre atualizar `brand-fpt-agent.md` primeiro. O HTML é reflexo do agent md — nunca o contrário.

### O que sincronizar (agent md → HTML)

| Bloco agent md | Seção HTML | Seção brand-fpt.md |
|---|---|---|
| 1. Identidade Central | 01 Posicionamento | 1. Posicionamento |
| 2. Arquétipo | 02 Arquétipo | 2. Arquetipo da Marca |
| 3. Design Tokens (paleta) | 03 Identidade Visual | 3. Identidade Visual |
| 3. Design Tokens (tipografia) | 04 Tipografia | 3. Identidade Visual |
| 3. Design Tokens (logo) | 05 Logo | 3. Identidade Visual |
| 4. Identidade Sonora + 5. Motion | 06 Motion | 6. Identidade Sonora |
| 6. Tom de Voz | 07 Tom de Voz | 4. Tom de Voz |
| 6.5. Pilares de Conteúdo | (em Tom de Voz) | 5. Pilares de Conteudo |
| 7. Personas | 09 Personas | 11. Personas de Audiencia |
| 8+9. Thumbnails + Nutellas | 08 Conteúdo | 9. Thumbnails / 10. Nutellas |
| 14. Pendentes | 10 Roadmap | 12. Backlog |

### O que NÃO vai para o HTML (agent-only)
- Prompts de geração de imagem
- Caminhos de arquivo (paths locais e Drive IDs)
- Contatos do time com telefone/email
- Detalhes técnicos do motion logo (frames, springs)
- Instruções operacionais para agentes

### Fluxo de atualização

```
1. Decidir algo sobre a marca
2. Atualizar brand-fpt-agent.md (bloco correspondente)
3. Atualizar data "Última atualização"
4. Refletir mudança no HTML (seção correspondente)
5. firebase deploy --only hosting
6. Se impactar Prism OS ou outros agentes → atualizar contexto dos agentes afetados
```

### Checklist de deploy
- [ ] `brand-fpt-agent.md` atualizado
- [ ] Data de atualização corrigida
- [ ] HTML reflete a mudança
- [ ] Bloco 14 (pendentes) atualizado se item foi concluído
- [ ] `firebase deploy` executado

---

## 1. IDENTIDADE CENTRAL

### O que é o FPT
**Nome completo:** Frota Para Todos
**Canal YouTube:** https://www.youtube.com/@JulioCesarFrotaParaTodos
**Site:** https://frotaparatodos.com.br/
**Categoria:** Educação em gestão de frotas — maior canal do Brasil no segmento

### Quem é o Julio César
- Engenheiro Eletrônico
- CEO da Contele Fleet
- 20+ anos de experiência em campo (gestão de frotas real, não teórica)
- Face e voz do canal — ele É a marca

### Relação FPT / Contele Fleet
- FPT = marca de conteúdo (topo de funil)
- Contele Fleet = produto (conversão)
- Fluxo: YouTube → frotaparatodos.com.br → Cartão Fleet 2026 → Contele Fleet

### Frase de posicionamento
> "Gestão de frotas não precisa ser complicada. Precisa ser prática, acessível e feita por quem vive isso todo dia."

### Tagline comercial
> "Toda empresa de frotas vende rastreador. A Contele vende resultado."

---

## 2. ARQUÉTIPO DA MARCA

> Definido em 2026-03-05 — entrevista com Julio César realizada.
> Processamento completo: `DOCS/entrevista-arquetipo-julio-PROCESSADO.md`

**Arquétipo primário:** Sage Pragmático
**Arquétipo secundário:** Hero

### Sage Pragmático — o que significa
Não é o professor acadêmico. É o mestre que aprendeu no campo — visão estratégica acumulada em anos de conversa diária com gestores reais. Destila a prática de milhares de operações em conteúdo aplicável amanhã.

Loop central: **ensinar → coletar feedback → aprender → ensinar de novo.**

Inspirações declaradas: "Cerveja Fácil" (Leandro) e "Primo Rico" (Tiago Negro) — canais que explicam coisas complexas de forma que qualquer pessoa entende e aplica.

### Hero — traços secundários
Luta contra comportamentos concretos (veja Vilão abaixo). A escolha estratégica de ser o MAIOR canal — não apenas o mais impactante — é postura de Herói: credibilidade como arma para ter autoridade de orientar.

### Vilão da Marca (dois comportamentos, não pessoas)

**Vilão 1 — O Conteúdo de Vitrine:**
Blogs de agências de marketing, conteúdo formal e filosófico cheio de termos difíceis que não entregam nenhuma ação concreta. É o que o gestor consumiria se o FPT não existisse.
> Antiexemplos reais citados pelo Julio: Prolog App, Coble.

**Vilão 2 — O Gestor Que Apaga Fogo:**
O gestor que não sai do operacional, impõe regras sem envolver o motorista, não tem metas nem premiações — e vai "cortar unhas" eternas sem mudar comportamento da equipe.
> Frase do Julio: "O problema do gestor é passar os dias apagando fogo, sem conseguir se organizar, planejar ou obter apoio da diretoria."

### Propósito além do posicionamento
O canal é um instrumento de transformação de carreira: motorista que vira gestor, gestor que monta empresa, empresa que não fecha porque aprendeu a controlar a frota.
> "Que o canal mudou a vida ou a carreira das pessoas." — Julio César

---

## 3. DESIGN TOKENS

### Paleta de Cores — EXATA

| Nome | Hex | Uso |
|---|---|---|
| Roxo Profundo | `#4E0091` | Fundos densos, pesos visuais |
| Roxo Médio | `#6C12B9` | Transições, gradientes |
| Roxo Principal | `#8B23E5` | Cor primária da marca, CTAs, destaques |
| Branco Suave | `#F7F7F7` | Texto sobre fundo escuro, backgrounds claros |
| Background Dark | `#080010` | Fundo padrão motion/digital |

**Regra crítica:** Nunca usar roxo fora da paleta acima. Proibido: `#7C3AED`, `#6D28D9`, qualquer roxo que não seja `#8B23E5` como principal.

**Gradiente padrão:** `linear-gradient(135deg, #8B23E5, #b56fff)`
**Glow padrão (motion):** `rgba(139,35,229,0.70)` + `rgba(37,99,235,0.45)`

### Tipografia

**Fonte única:** Montserrat (Google Fonts — gratuita)
**Pesos em uso:** 300 · 400 · 500 · 600 · 700 · 800 · 900

**Hierarquia oficial (manual de marca Figma, mar/2026):**

| Nível | Tamanho | Peso | Uso |
|---|---|---|---|
| H1 | 48px | Bold | Títulos principais, headlines |
| H2 | 36px | Semi-bold | Subtítulos, seções |
| H3 | 28px | Medium | Subseções, destaques |
| Body | 18px | Regular | Texto corrido, parágrafos |
| Legenda | 14px | Regular Itálico | Notas, créditos, fontes |

Para thumbnails e social: escalar proporcionalmente acima. Manter progressão Bold > Semi-bold > Medium > Regular.

**Razão da escolha:** Força institucional + clareza técnica + autoridade. Transmite organização e domínio técnico, adequado para engenheiro falando de frotas.

### Logo

**6 variações oficiais (Drive Contele — pasta Logos):**
- `logo-fpt-horizontal-branco.png` — uso preferencial em fundos escuros
- `logo-fpt-vertical-branco.png`
- `logo-fpt-isotipo-branco.png` — ícone isolado
- `logo-fpt-horizontal-preto.png` — fundos claros
- `logo-fpt-vertical-preto.png`
- `logo-fpt-isotipo-preto.png`

**Drive Contele Logos:** `1345X5PBzS3rGdQ_VKV0Fvr31WeKA4JZW`

**Nota:** Logo foi geometrizado vetorialmente (grid construtivo aplicado). Versões acima são a fonte da verdade. Não usar versões antigas.

**Área de proteção (clear space)**
Unidade de medida: **"O"** (derivada do pneu no ícone do volante).
Distanciamento mínimo ao redor do logotipo deve corresponder à proporção da unidade "O", em qualquer escala (digital ou impressa).

**Uso incorreto (exemplos do manual Figma)**
- Logo em roxo sobre fundo branco (apenas branco ou preto)
- Isotipo sozinho cortado (sem wordmark completo)
- Logo sobre fundo roxo sem contraste suficiente
- Logo sem "Julio César" (descaracteriza)
- Logo sem isotipo (texto sem ícone do volante)

**Aplicações da marca**
- Thumbnails YouTube (lives, badge "LIVE", logo no canto)
- Boné roxo com logo vertical branco
- Garrafa térmica roxa com logo vertical branco
- Camisetas (branca e roxa) com logo e ilustração de veículos

**Elemento gráfico auxiliar**
Ilustração line art de veículos (caminhão, van, carro) em roxo #4E0091. Uso decorativo.

**Manual de marca (Figma)**
- Original (Rarissa): https://www.figma.com/design/DZ8Aq7DBEP2L2pFujVgPax/IDV---Julio-C%C3%A9sar-%7C-Frota-Para-Todos?node-id=0-1
- Cópia workspace Contele: https://www.figma.com/design/TGpySsgfBiG8LyjI8Q2u2Q/IDV---Julio-C%C3%A9sar-%7C-Frota-Para-Todos--Copy-?node-id=0-1

---

## 4. IDENTIDADE SONORA

**Assinatura escolhida:** Opção A — "Diesel Épico"
**Decisão:** Julio César (04/03/2026)
**Arquivo master:** `fpt-option-a.wav` (Drive Contele — pasta Identidade Sonora)

**Conceito Opção A:** Diesel potente desde a abertura. Transmite autoridade, tradição e força. A voz sonora do canal.

**Conceito Opção K (Marco — segunda opção):** Motor elétrico suave na entrada, diesel acorda no impacto, ressonância cresce. Representa a frota real do Brasil: 90% combustão, olhos no elétrico.

**Uso:** Motion logo (`FPTLogoImpact.tsx`). Decisão tomada em 04/03/2026 — usar `fpt-option-a.wav`. Código já atualizado para option-a.wav.

**Drive Contele Identidade Sonora:** `1nChc6T_j2sPBzINt0rEmWrsAnwhLXxOu`

---

## 5. MOTION LOGO

**Arquivo:** `remotion-video/src/fpt/FPTLogoImpact.tsx`
**Duração:** 3.5s (105 frames @ 30fps)
**Resolução:** 1920x1080

**Sequência de animação:**
1. **Frames 5-35:** Logo vem de longe com spring overshoot (scale 0.02 → 1), blur 20px → 0
2. **Frames 28-35:** Flash branco (blend overlay — não vira branco sólido)
3. **Frames 32-65:** 8 partículas em direções cardeais (azul `#2563eb` + verde `#4CAF50`)
4. **Frames 28-58:** Onda de choque radial roxo+azul expande no fundo
5. **Frames 38-90:** Wobble de assento em 3 camadas (stiffness 420/380/360, damping 5)
6. **Frame 50+:** Tagline spring: "MAIOR CANAL DE GESTÃO / DE FROTAS DO YOUTUBE"

**Fundo:** `#080010` + grid roxo sutil `rgba(139,35,229,0.08)` 60x60px
**Vignette:** radial roxa profunda nos cantos
**Glow residual:** roxo + azul cyberpunk pós-impacto

---

## 6. TOM DE VOZ

### Identidade
**Persona:** Mentor acessível e "mão na massa" que descomplica a gestão de frotas.

### Três eixos de equilíbrio

| Eixo | O que significa na prática |
|---|---|
| **Autoridade pragmática** | Fala como quem viveu o problema. Dado concreto > opinião |
| **Didático** | Entrega ferramenta real. Nunca teoria sem aplicação |
| **Comunitário** | Próximo, entende a rotina estressante do gestor |

### Foco principal
- Redução de custos com frota
- Fim de desperdícios operacionais
- Resultado financeiro mensurável

### O que o Julio É
- Prático
- Direto
- Técnico mas acessível
- Focado em resultado
- Próximo do gestor

### O que o Julio NÃO É
- Corporativo
- Formal em excesso
- Vendedor de produto
- Teórico sem aplicação
- Inflado de promessas

### Frases Reais do Julio (voz autêntica — extraídas da entrevista 2026-03-05)

1. **"Quem quer faz, quem não quer uma desculpa."**
2. **"Tem que envolver o motorista na frota."**
3. **"Km por litro é a taxa Selic da gestão de frota."**
4. **"Premiação não é custo. É valor pago com a economia gerada."**
5. **"Gestor de frotas é gestor de pessoas."**
6. **"O motorista precisa ser o dono do veículo."**

### Bordões do canal (uso frequente em vídeos)
1. **"Dica de ouro"**
2. **"O que você falaria para quem está assistindo esse conteúdo fazer amanhã?"**
3. **"Feito é melhor do que perfeito."**
4. **"Pareto 80/20"**
5. **"Gestão é compartilhada (Motorista + Gestor)"**
6. **"Conhecimento vale muito!"**
7. **"Esse conteúdo poderia ser pago mas a gente está disponibilizando de graça pra ajudar você a ter mais conhecimento."**
8. **"Fala meus amigos gestores"**

### Vocabulário: palavras PARA USAR

| Termo | Por quê |
|---|---|
| Gestão de frotas | Termo do mercado, claro |
| Resultado | Foco da marca: financeiro, mensurável |
| Prático / Na prática | Marca registrada do tom FPT |
| Economia | Benefício tangível que o gestor busca |
| Custo por quilômetro (CPK) | Métrica central |
| Km por litro | "A taxa Selic da gestão de frota" |
| Ferramenta | Concreto, tangível, aplicável |
| Gestor | Respeita quem assiste |
| Motorista | Parte da solução, não o problema |
| Premiação | Não é custo, é investimento |
| Mão na massa | Tom acessível e prático |
| Na ponta do lápis | Linguagem financeira acessível |
| Vamos resolver | Convite à ação conjunta |
| Direto ao ponto | Promessa de objetividade |

### Vocabulário: palavras para EVITAR

| Termo | Alternativa |
|---|---|
| Solução inovadora | "Ferramenta que funciona" |
| Líder de mercado | "20+ anos no campo" |
| Disruptivo | "Prático" |
| Ecossistema | "Conjunto de ferramentas" |
| Sinergia | Remover |
| Stakeholder | "Gestor", "diretor", "dono" |
| Case de sucesso | "Resultado real", "exemplo prático" |
| Agregamos valor | Dizer o valor concreto |
| Tecnologia de ponta | Nome da tecnologia específica |
| Exclusivo / Premium | "Completo", "detalhado" |
| Otimizar | "Reduzir custo", "cortar desperdício" |
| Venha conhecer | "Assista", "teste", "aplique amanhã" |

### Padrão de construção de raciocínio
- **Começa pela história**: não apresenta a solução primeiro — constrói contexto até a ideia fazer sentido
- **Define antes de usar**: qualquer sigla ou termo técnico é explicado antes de aparecer no argumento (ex: "CPK — Custo por Quilômetro")
- **Fecha com ação**: toda comunicação termina com algo implementável no dia seguinte
- **Inclui o motorista**: não fala só para o gestor — o motorista sempre entra no raciocínio

---

## 6.5. PILARES DE CONTEÚDO

### Temas principais
1. Gestão de Frotas
2. Direção Segura e Econômica
3. Dicas de Gestão de Frotas

### Temas de apoio
- Manutenção
- Sistema para Gestão de Frotas
- I.A na Gestão de Frotas
- Gestão de Combustível
- Gestão de Pneus
- Gestão de Multas
- Rastreamento Veicular
- Gestão de Motoristas

> Fonte: mapeamento Rarissa (mar/2026) baseado em performance dos vídeos.

---

## 7. PERSONAS DO PÚBLICO

> Construídas a partir de dados reais do YouTube Analytics, análise de comentários e padrões de comportamento. Jan 2023 - Mar 2025. Levantamento Rarissa (mar/2026).

### Persona 1: O Iniciante Involuntário (principal, maior volume de comentários)

**Marcos**, 32 anos, gestor de frota designado, interior ou cidade média, frota de 30 veículos.

> "Acabei caindo de paraquedas nessa área, e agora preciso estudar e aprender pra dar o meu melhor."

- Acessa pelo celular (intervalo, pátio, noite em casa)
- Urgência de aprendizado muito alta: assumiu o cargo há pouco tempo, cada erro aumenta risco de perder a função
- Chega ao canal por busca ativa: "gestão de frotas iniciantes", "como controlar multas frota"
- Ação mais desejada: baixar material (planilhas, checklists, modelos prontos)
- Maratona vídeos em sequência, clica em "passo a passo", "do zero", "iniciantes"
- Motivação emocional: não ser visto como incompetente pelo chefe. Assiste pra sobreviver no cargo.

**Dores:** multas sem processo, veículo parado sem histórico, não sabe quais indicadores acompanhar, combustível sem controle, medo de ser visto como incompetente.

**Objetivos:** rotina de gestão básica desde a primeira semana, planilhas prontas, vocabulário técnico, manutenção preventiva, provar ao chefe que está evoluindo.

### Persona 2: O Profissional em Evolução (alto engajamento técnico)

**Ricardo**, 30 anos, gestor de frota, Sul/Sudeste, frota de 80 veículos, 2 anos na área.

> "Trabalho com gestão de frota há 2 anos. Estou buscando novas fontes de conhecimento para tentar colocar em prática na empresa que estou."

- Celular e PC (celular no dia a dia, PC para planilhas)
- Urgência moderada: não está apagando incêndio, quer método
- Chega por indicação e algoritmo (WhatsApp do setor, vídeos sugeridos)
- Ação mais desejada: trocar experiência, validar o que já faz, benchmarks
- Valoriza profundidade técnica acessível: "não quer MBA, quer aplicar na segunda-feira"

**Dores:** construindo na intuição sem saber se está certo, falta dado pra justificar gastos, custo de manutenção imprevisível, combustível sem controle real, sente que outros gestores estão mais avançados.

**Objetivos:** substituir intuição por método, benchmarks (CPK, km/l), impressionar a diretoria com dados, networking no setor, virar referência interna.

### Persona 3: O Estudante Estratégico (alta intenção de carreira)

**Lucas**, 22 anos, estudante de logística (3o ano), todo o Brasil, 0 veículos sob gestão.

> "Sou estudante de logística e estava procurando justamente vídeos que me ajudassem a melhorar o conhecimento na área."

- Celular (entre aulas, transporte, noite)
- Urgência alta mas intencional: quer vantagem sobre colegas formandos
- Chega por busca no YouTube (termos técnicos, complementar a faculdade)
- Ação mais desejada: encontrar curso com certificado pro currículo
- Assiste vídeos antigos sem problema: não liga pra data de publicação
- Em 2 anos se torna o Marcos (persona 1): renova o ciclo do canal

**Dores:** faculdade ensina teoria desconectada, sem experiência prática, medo de chegar ao primeiro emprego sem saber o básico.

**Objetivos:** dominar vocabulário técnico antes do mercado, exemplos práticos pra entrevistas, certificação reconhecida, contatos no setor.

### Persona 4: O Motorista Profissional (parte da solução)

**Sergio**, 38 anos, motorista de frota há 10+ anos, ensino médio, todo o Brasil.

> "O rastreador é pra me vigiar ou pra me ajudar?"

- Celular é sua única tela. Assiste no intervalo, no pernoite, esperando carga
- Não é audiência direta do canal, mas é central no discurso: "o motorista é parte da solução"
- Chega por recomendação do gestor ou por acidente (algoritmo)
- Quer: premiação por desempenho, reconhecimento, ser tratado como profissional
- O Julio sempre inclui o motorista no raciocínio: "gestão é compartilhada"

**Dores:** se sente vigiado pelo rastreador, não entende os indicadores, acha que tecnologia é pra punir, não recebe feedback positivo.

**Objetivos:** premiação por km/l, reconhecimento, entender como a tecnologia ajuda (não fiscaliza), ser parte da solução.

> Persona adicionada após auditoria de marca (mar/2026): o documento insistia que o motorista é central, mas não o definia como persona.

### Persona 5: O Visitante Pontual (ruído, baixíssimo potencial de conversão)

**José**, 40 anos, motorista ou pessoa física com problema específico, todo o Brasil.

> "Tenho categoria A, mas tem um carro em meu nome e ele tem multa de radar. Isso prejudica minha CNH?"

- Pesquisa no momento exato do problema (parado no trânsito, na oficina, recebendo multa)
- Urgência pontual e imediata: resolveu, some, não volta
- Chega por palavra-chave acidental ("multa radar CNH", "rastreador barato")
- NÃO é audiência-alvo. É o perfil que inflou o dado de 70,1% de não inscritos no Analytics.
- Única ação possível: card para conteúdo de gestão durante o vídeo

---

## 8. SISTEMA DE THUMBNAILS

### Modelo de geração
- **IA:** Gemini Pro Image Preview (`gemini-3-pro-image-preview`)
- **Técnica:** Face-lock em 2 etapas para consistência facial
- **Sistema:** `growth-contele/prism-os/thumbnail-ai-creator/`

### Identidade visual do Julio nas thumbs
```
- Polo navy lisa escura (SEM logos, SEM texto na camisa)
- Barba sal e pimenta (curta, bem cuidada)
- Cabelo castanho curto, levemente ondulado
- Olhos castanhos/avelã, SEM óculos
- Idade aparente: 40-42 anos, pele firme e natural
- Expressão: autêntica, não forçada
- Posição: médio-plano (peito para cima)
```

### Paleta das thumbs
- Fundo: roxo/magenta cinematográfico com bokeh
- Overlay: gradiente purple/magenta
- Texto: branco bold com sombra preta forte
- Badge LIVE: vermelho (canto superior esquerdo)

### Estratégia A/B
Cada live gera 2 conceitos distintos:
- **Ângulo "dor":** problema do gestor, urgência, o que ele está perdendo
- **Ângulo "solução":** resultado, transformação, o que ele vai ganhar

### Face-lock multi-convidado
```
Etapa 1: Gerar Julio solo (2 refs: ref1 + ref2) → 2-3 variações → aprovar melhor
Etapa 2: Usar aprovado como Image 3 + refs convidado como Image 4+ → 2-3 variações
```

### Referências Julio (polo preta)
`thumbnail-ai-creator/referencias/julio/` — 10 poses validadas (fev/2026)
Primary ref: `julio-ref-primary-1.jpg`

### Prompt base
```
Identidade Julio: gray/white stubble beard, short brown hair slightly wavy, brown/hazel eyes NO glasses, age 40-42 YOUTHFUL, PLAIN dark navy blue polo shirt NO logos, natural relaxed posture.
Skin: SMOOTH like a fit 40 year old, NO wrinkles, NO age spots, natural skin tone.
Background: purple/magenta color grade, bokeh blur, dramatic lighting.
Style: professional YouTube thumbnail, photorealistic, slightly stylized background, high contrast for mobile viewing.
```

---

## 9. NUTELLAS — SISTEMA DE CLIPES VIRAIS

### O que é uma Nutella
Clipe viral educativo extraído de live longa. Envolto com intro + CTA. Publicado como conteúdo autônomo.

**Formatos:**
- 16:9 — mínimo 90s (+ ~2min de wrapper)
- 9:16 Shorts — mínimo 30-60s

**Sistema:** `growth-contele/nutella-creator/`

### Tipos de Nutella (rankeados por potencial)

| Tipo | Objetivo | Quando usar |
|---|---|---|
| **Autoridade** | Julio como referência de mercado | Momentos de expertise única |
| **Viralização** | Alto compartilhamento | Dado surpreendente, insight contra-intuitivo |
| **Inscrição** | Motivo para seguir | Prova de comunidade, resultados da audiência |
| **Educacional** | Resolve 1 dúvida específica | "Como fazer X em frotas" |
| **Wow Factor** | Demo ao vivo, ferramenta, resultado visível | Demonstrações práticas |

### Scheduling validado
- **Quinta 15h** — maior CTR (validado 6+ meses)
- **Sexta 17h** — segundo melhor
- Shorts: performance consistente qualquer dia (baixa variância)

### Pipeline
```
URL da live → Gemini analisa transcript → sugere N Nutellas rankeadas →
selecionar → download → face detection → compose 16:9 + 9:16 →
review no player → aprovar/rejeitar → gerar thumbnail → upload YouTube
```

---

## 10. CARTÃO FLEET 2026

**URL:** https://marcofassa-cto.web.app/cartao-fleet-2026/
**Formato:** A5 landscape (210×148mm), offset print

**Frente (carta do CEO):**
- Foto grande do Julio (~40% da frente)
- Credenciais: 23 anos campo, 33K+ inscritos, 1.500+ empresas, R$3.367 em cursos
- QR WhatsApp direto

**Verso (método + manifesto):**
- Metodologia "Frota Para Todos" — 5 passos estruturados
- Manifesto: resultado > produto

**Posicionamento:**
> "Não vendemos rastreadores, câmeras ou sistemas. Entregamos resultado em gestão de frotas com metodologia e solução."

**Uso:** Onboarding de clientes Contele Fleet. Conecta autoridade do Julio com o produto.

---

## 11. JORNADA DO LEAD

```
YouTube (conteúdo gratuito, autoridade)
        ↓
frotaparatodos.com.br (hub: curso, planilhas, lives)
        ↓
Cartão Fleet 2026 (conversão: lead vira cliente)
        ↓
Contele Fleet (produto)
```

---

## 12. ATIVOS E REFERÊNCIAS

### Drive Contele — Pasta Master Brand FPT
`1VMLHN8V9Pf9MCVSkxhdn-nLVtipq5575`

| Subpasta | ID | Conteúdo |
|---|---|---|
| Logos | `1345X5PBzS3rGdQ_VKV0Fvr31WeKA4JZW` | 6 PNGs (horizontal, vertical, isotipo) |
| Identidade Sonora | `1nChc6T_j2sPBzINt0rEmWrsAnwhLXxOu` | fpt-option-a.mp4, fpt-impact-final.mp4, WAVs |
| Headers e Banners | `1pNtpQ7v1hGuI-PJWHzPSpkTv6gO2E6aL` | Capas YouTube/LinkedIn/Facebook + foto perfil |

### Código e Sistemas
| Item | Caminho |
|---|---|
| Motion logo | `remotion-video/src/fpt/FPTLogoImpact.tsx` |
| Audio K (Marco) | `remotion-video/public/fpt/audio/fpt-option-k.wav` |
| Audio A (Julio) | `remotion-video/public/fpt/audio/fpt-option-a.wav` |
| Sistema thumbnails | `growth-contele/prism-os/thumbnail-ai-creator/` |
| Sistema Nutellas | `growth-contele/nutella-creator/` |
| Site FPT | `/Users/marcofassa/Documents/frotaparatodos` |

### Contatos do Time FPT
| Pessoa | Papel | Contato |
|---|---|---|
| Julio César | Dono da marca, host | `juliocesar@contele.com.br` / `5513997000902` |
| Eng. Marco Antonio | Brand design, Figma manual | Marketing Fleet grupo |
| Rarissa | Marketing FPT, ponto focal | `5513996542205` |
| Cris (Christopher Ronaldo) | Marketing Contele | `5513996544450` |
| Marco | CTO, estratégia, sistemas | `5513997818442` |

### Canais
| Canal | Views (90d) | Seguidores | Melhor formato | Status |
|---|---|---|---|---|
| YouTube | 2,6M total | 33,4K | Lives + Nutellas | Ativo (restrição pendente) |
| Instagram | 163K | 7.718 | Reels | Ativo |
| TikTok | 54K | 1.986 | Cortes curtos | Ativo (25,3% tráfego de buscas) |
| LinkedIn | 54K | 5.855 | Comunidade | Ativo |
| Podcast | 210 views (3m) | - | - | Praticamente parado |
| Site | - | - | Hub central | frotaparatodos.com.br |

Perfil demográfico: Homens (83%), 25-54 anos. Público maduro com poder de compra.
> Fonte métricas: levantamento Rarissa (mar/2026)

---

## 13. REGRAS ABSOLUTAS PARA AGENTES

### SEMPRE
- Usar paleta exata (`#8B23E5` como principal — nunca aproximações)
- Usar Montserrat como fonte em qualquer material FPT
- Referenciar o Julio como autoridade técnica, nunca como celebridade
- Focar em resultado financeiro concreto (redução de custo, número, percentual)
- Linguagem: direta, prática, acessível — sem jargão desnecessário
- Polo navy lisa nas gerações de imagem do Julio (sem logos)

### NUNCA
- Usar fundo claro como principal em materiais digitais
- Tom corporativo, formal, inflado
- Prometer produto — o FPT vende conhecimento, não rastreador
- Criar thumbnail sem face-lock (resultado inconsistente)
- Usar roxo fora da paleta definida
- Adicionar logos em camisas do Julio nas gerações IA
- Criar conteúdo que promova concorrentes da Contele Fleet
- Enviar link de `drive.google.com` ou `docs.google.com` como material publico (planilha, ebook, checklist). Material SEMPRE via LP `https://exclusivo.contelerastreador.com.br/{slug}/` — a LP captura o email do lead e alimenta o funil. Se nao houver LP confirmada, NAO usar Drive como fallback: responder "link na descricao do video" ou pedir slug correto. (regra 06/05/2026, [[brand-fpt]])

### ANTES DE CRIAR QUALQUER COISA
1. Aplicar arquétipo (bloco 2) — Sage Pragmático + Hero. Vilão = Conteúdo de Vitrine e Gestor que Apaga Fogo
2. Verificar paleta e tipografia (bloco 3)
3. Verificar tom de voz e frases reais (bloco 6)
4. Verificar persona do público que o conteúdo atinge (bloco 7)
5. Checar se há pendências no bloco 14 que afetam o que está sendo criado

---

## 14. O QUE ESTÁ PENDENTE (a expandir neste doc)

| Item | Status | Impacto |
|---|---|---|
| Arquétipo do Julio | ✅ Concluído (2026-03-05) | Blocos 2 e 6 atualizados |
| Frases reais do Julio (voz) | ✅ Concluído (2026-03-05) | 6 frases extraídas da entrevista |
| Pilares de conteúdo do canal | ✅ Concluído (mar/2026: Rarissa) | Estratégia de conteúdo |
| Personas validadas com analytics | ✅ Concluído (mar/2026: Rarissa, 5 personas incluindo Sergio motorista) | Precisão do público |
| Imagens realistas das personas | ✅ Concluído (10/03/2026: 5 imagens Gemini em output/) | Brand book completo |
| Benchmark de canais similares | Pesquisar | Diferenciação |
| Regras de uso do logo (clear space) | ✅ Concluído (10/03/2026: extraído do Figma) | Manual completo |
| Photography style guide | Eng. Marco Antonio | Consistência visual |
| Canais ativos confirmados | ✅ Concluído (mar/2026: Rarissa) | Estratégia multicanal |
| Migrar arquivo Figma pro workspace CONTELE | Rarissa notificada 10/03 | Centralização |
| Sincronizar página web brand board | ✅ Concluído (10/03/2026) | HTML refletir agent md |

---

*Este documento é vivo. Sempre que uma decisão de marca for tomada, atualizar aqui.*
*Versão humana: https://marcofassa-cto.web.app/brand-fpt/*
*Vault doc de referência: obsidian-marco/DOCS/brand-fpt.md*

## Conexoes

- [[integracao-youtube]]
- [[projeto-frotaparatodos-site]]
- [[funil-marketing-growth-2026]]
