# youtube-principles-2026.md
## Algoritmo YouTube 2026 : Princípios Operacionais para Planejamento de Conteúdo

> **Como usar este documento**
> Carregar ANTES de qualquer planejamento de live, vídeo gravado, thumb ou título de qualquer canal Frota Para Todos / Contele Teams.
> Este doc complementa `soul-canal-fpt.md` (que tem o dado específico do canal FPT). Aqui é o **algoritmo genérico 2026** : vale pra qualquer canal, qualquer nicho, qualquer estágio.
>
> Última atualização: 2026-04-29
> Base: 13 fontes 2024-2026 (Google/The Keyword, SearchEngineJournal, Retention Rabbit, ytshark, vidIQ, Tubebuddy, team5pm, Thumbify, Music Ally, OutlierKit, Miraflow, Shortimize, Creator Insider) + curadoria de vídeos selecionados pelo Marco.
> Refresh: trimestral, ou quando mudança grande de algoritmo for anunciada.

---

## 0. Como o agente Prism deve aplicar

Antes de gerar plano de live / vídeo / thumb / título / SEO, agente DEVE:

1. Validar que a recomendação está alinhada com os **9 pilares** abaixo.
2. Cruzar com `soul-canal-fpt.md` (dado factual do canal específico).
3. Se algum pilar contradiz dado do canal: **dado do canal vence**, mas explicitar a tensão pro humano decidir.

Princípio operacional: este doc descreve o que o algoritmo **prefere em média**. O canal específico tem padrões próprios que podem dobrar a força (live 130-170min do FPT, por exemplo) ou anular a recomendação genérica.

---

## 1. Os 9 pilares (síntese 2024-2026)

### Pilar 1 : APV > Watch Time bruto como sinal de ranking
- **Antes (até 2023)**: minutos assistidos puros pesavam.
- **Agora (2025-2026)**: APV (Average Percentage Viewed = % do vídeo assistida em média) é o dominante. Sinal de "vídeo entrega o que promete".
- Implicação: vídeo de 5min com 70% APV vence vídeo de 40min com 12% APV em ranking, mesmo com watch time bruto menor do primeiro.
- Corolário: **duração ideal = APV alto, não minutos**. Não otimizar pra duração; otimizar pra retenção.

### Pilar 2 : Browse vs Suggested são caixas separadas
- **Browse** (homepage do usuário, "watch next" da home): pesa CTR + video velocity (views/hora nas primeiras 24-48h) + subscribers.
- **Suggested** (sidebar de outro vídeo): pesa co-watch (quem viu o vídeo X também viu Y) + contexto temático. Subscribers NÃO contam aqui.
- Implicação: vídeo com CTR baixo mas APV alto pode vencer em Suggested mesmo perdendo em Browse.

### Pilar 3 : Live durante stream ≠ Live arquivado (VOD)
- Durante o stream: ranqueia por concurrent viewers + chat engagement + tempo médio de assistir-ao-vivo.
- Depois do stream (VOD arquivado): compete como upload normal contra outros vídeos do nicho. APV durante a live importa pro VOD herdar bons sinais.
- Implicação: live de 3h com 30 concurrents que assistem 80% do tempo > live de 1h com 200 concurrents que entram-e-saem.

### Pilar 4 : Shorts Decoupling (separação Shorts × Long-form)
- Desde fim 2025, Shorts e long-form são **sistemas de descoberta e ranking separados**. Subscribers ganhos via Short não convertem em audiência long-form na mesma proporção.
- Implicação: Short serve pra alcance/descoberta; **canal não se sustenta em Short**. Long-form continua sendo o cavalo de batalha pra subs qualificados + watch time + monetização.

### Pilar 5 : Paid (Ads) e Organic são caixas separadas oficialmente (Google 2024)
- Boost pago a um vídeo NÃO transfere score orgânico ao canal.
- Vídeo ad-boosted que parece grande nas métricas pode ser **orgânico fraco mascarado por budget**.
- Implicação: ao analisar performance, sempre **separar traffic_class organic_puro vs misto vs ad_boosted**. Compare maçãs com maçãs.

### Pilar 6 : A/B nativo (Test & Compare) — winner por watch time share
- Feature 2026: até **5 thumbnails variantes** simultâneas. YouTube serve em rodízio por 7-14 dias.
- Winner é escolhido por **watch time share**, NÃO por CTR isolado. Thumb que clicka muito mas retém pouco perde.
- Implicação: testar variantes de thumb diferentes em vez de chutar a "boa". Não confiar em CTR cego.

### Pilar 7 : Lives são automaticamente recortadas em Shorts/Clips (2025-2026)
- YouTube identifica trechos virais de lives e gera Shorts automaticamente.
- Implicação: estruturar live em **blocos auto-contidos de 5-10min** pra facilitar o corte automático funcionar bem. Cada bloco é um Short potencial.
- Bônus: agente Prism pode sugerir esses recortes no `plan` do planejador.

### Pilar 8 : Mobile-first thumbnail (70%+ das views são mobile)
- Thumb é vista em ~150x84px no feed mobile, não em 1280x720 do laptop.
- Texto pequeno = ilegível. 3 elementos visuais é o teto.
- Brightness baixa-média + contraste alto vencem brightness alta.
- Rosto humano sempre que possível (ativa córtex visual mais rápido que objeto).

### Pilar 9 : Carga cognitiva reduzida vence
- Thumb com 1 ideia clara > thumb com 3 ideias competindo.
- Título com 5-8 palavras > título com 12+ palavras.
- Hook nos primeiros 15s do vídeo: 1 promessa concreta, 1 número/dado, 1 frase. Não 3 promessas misturadas.
- Implicação: cortar tudo que não for indispensável. "Menos é mais" virou regra dura, não estética.

---

## 2. Diretivas de thumbnail (algoritmo genérico)

> Estas são diretrizes 2026 baseadas em literatura. **Cruzar com `soul-canal-fpt.md` § 4** pra dado específico do canal — quando dado do canal contradiz, dado vence.

### Cores que tendem a funcionar
- **Vermelho + preto + branco**: combinação dominante no top organic de canais com persona de autoridade/educação. Vermelho NÃO derruba APV (mito comum) e tende a aumentar views/dia.
- **Azul escuro como accent forte**: aparece muito mais no top que no bottom em análises de canais B2B.
- Verde, amarelo, laranja: usar como destaque pontual, não dominante.

### Cores e elementos a EVITAR
- **Moldura vermelha redonda + seta vermelha clichê**: virou ruído em todo YouTube. Não é específico do canal — é fadiga visual generalizada.
- **Roxo dominante**: cor de marca pode ser ruim em thumb. Aparece em top e bottom igual = não diferencia.
- **Brightness alta**: top organic tende fortemente a brightness baixa. Bottom tem brightness alta.
- **Texto longo (8+ palavras)**: ilegível no mobile feed. Cortar.

### Curadoria Marco (vídeos selecionados que alimentam este doc)

**TR Peter (`Hxd8PN0l9ug`) — https://youtu.be/Hxd8PN0l9ug**
12 insights sintetizados:
- Duração ideal: 15-25min
- Título: 5-8 palavras
- Múltiplos rostos na thumb tende a vencer rosto único
- Texto na thumb reduz views ~19% em média
- Cores que vencem em thumb: ciano/verde/amarelo/laranja como destaque
- Números no título: -11% performance (contraintuitivo, contradiz Pilar 9 quando o número não tem promessa concreta atrás)
- Humor > controvérsia em retenção longa
- Negativos > positivos em CTR ("não", "pare", "evite")
- Brilho > escuro em mobile feed (contradiz nosso dado de canal — **dado do canal vence**, mas vale registrar tensão)
- Carga cognitiva reduzida sempre vence

**Tensão registrada com canal FPT**: o dado de "brilho > escuro" do TR Peter contradiz nossa análise de 91 thumbs do FPT (top 13/20 brightness baixa). Hipótese: nicho de educação técnica B2B (frotas) tem audiência com tolerância maior a thumb mais cinematográfica/séria. Em outros nichos pode ser diferente.

> **Marco: adicionar mais vídeos aqui conforme curar.** Padrão: link YouTube + 5-12 insights destilados + tensão registrada vs dado do canal.

---

## 3. Diretivas de título (algoritmo genérico)

### Estruturas que tendem a vencer
- **Pergunta direta** ("Sistema de Rastreamento Veicular: O que é e como funciona?")
- **Separador `:`, ` - `, ` | `** ("Tema principal: subtítulo descritivo concreto")
- **Número com promessa concreta** ("6 Indicadores que Reduzem CPK em 30%")
- **Negativo + curiosidade** ("NÃO Faça Isso Quando Assumir Uma Frota")
- **5-8 palavras** total. Tudo acima de 12 corta no mobile.

### Padrões a EVITAR
- "Como [verbo] [substantivo genérico]" sem promessa concreta ("Como Organizar a Frota")
- Cifrão (R$) ou % no título (TR Peter aponta -11%, FPT confirma 0% nos top 30)
- Adjetivos vazios ("Incrível", "Surreal", "Inacreditável")
- ALL CAPS COMPLETO (vira spam visual)

---

## 4. Diretivas de SEO/descrição

### Descrição YouTube (sempre)
- **Primeiras 2 linhas**: gancho + keyword principal. Aparece no resultado de busca.
- **Capítulos (timestamps)**: sempre que vídeo for >5min. YouTube usa pra navegação e também pra Suggested temático.
- **Tags**: 5-10 tags. Específicas > genéricas. "gestao de frota" > "frota".
- **End screen + cards**: 1 card pro próximo vídeo do cluster, 1 card pra vídeo evergreen do canal.

### Hashtags
- 3 hashtags max. Aparecem acima do título. Use o tema principal + 2 secundários.

---

## 5. Diretivas de hook (primeiros 30s do vídeo)

### Estrutura validada
1. **0-3s**: pergunta retórica ou afirmação chocante. ("E se eu te dissesse que 80% dos gestores...")
2. **3-10s**: promessa concreta com número. ("Vou te mostrar 3 indicadores que reduzem 30% do CPK")
3. **10-15s**: credibilidade ("20+ anos no campo, milhares de gestores")
4. **15-30s**: roteiro do vídeo ("Vamos cobrir: 1) X, 2) Y, 3) Z. Fica até o final que tem um bônus")

### O que NÃO fazer no hook
- **NÃO se apresentar antes da promessa.** "Olá pessoal, meu nome é Julio e hoje vou falar sobre..." = drop em 5s. Promessa vem primeiro.
- **NÃO pedir like/inscrição nos primeiros 30s.** Mata APV.
- **NÃO recapitular o que você fez no vídeo passado.** Audiência nova não viu.
- **NÃO usar intro de 10s+** com logo/animação. Corta direto pro hook.

---

## 6. Pilares de retenção ao longo do vídeo

### Pattern interrupts a cada 60-90s
- Mudar plano, ângulo, cenário, ou formato (b-roll, animação, dado na tela).
- Pergunta retórica: "Mas e se você tem 50 veículos?"
- Antecipação: "Em 2 minutos eu te mostro o número que muda tudo".

### Estrutura "loop aberto"
- Anunciar bônus ou caso real no início. Entregar no final.
- "No final, eu mostro o caso da empresa X que economizou R$200k em 6 meses".

### Q&A ou bônus no final
- Aprofundar uma dica que só quem assistiu até o fim ganha. Cria APV alto na ponta.
- Esses últimos 10% do vídeo viram clip Short/Nutella forte.

---

## 7. Métricas-norte (genéricas pra qualquer canal)

| Métrica | Meta benchmark 2026 |
|---|---|
| APV organic médio (excluir ad-boosted) | >=35% |
| CTR médio (Browse) | >=4% |
| Subs / 1k views organic | >=10 (>15 = ótimo) |
| Watch time share em A/B test | winner deve ter >=51% |

> Para o canal FPT específico, ver `soul-canal-fpt.md` § 7. Metas do canal podem ser mais agressivas que o benchmark genérico.

---

## 8. O que NÃO acreditar (mitos comuns 2026)

1. **"Vermelho na thumb é ruim"** — falso. Vermelho aumenta views/dia em vários nichos. O ruim é a moldura vermelha redonda + seta clichê.
2. **"Vídeo curto vence sempre"** — falso. Em educação B2B, gravado 10-20min vence em subs. Live de 130-170min vence em subs/1k em formato formativo.
3. **"Shorts crescem o canal"** — falso desde 2025. Shorts servem descoberta. Long-form sustenta.
4. **"Mais palavras no título = mais SEO"** — falso. 5-8 palavras é o sweet spot.
5. **"Postar todo dia vence"** — falso em B2B. Qualidade + cluster temático > frequência.
6. **"YouTube prioriza canal grande"** — meio falso. Vídeo bom de canal pequeno consegue Browse + Suggested se APV for alto. Subs ajudam Browse, não Suggested.

---

## 9. Refresh cycle

- **Trimestral**: revisar literatura nova. Adicionar vídeos curados pelo Marco. Atualizar pilares se mudança de algoritmo for anunciada.
- **Quando alterar pilar central**: avisar Marco + Julio + Cris antes de aplicar.

---

## Conexões (wikilinks)

- `soul-canal-fpt.md` — dado específico do canal FPT (cruzar)
- `brand-fpt-agent.md` — voz, persona, vilão (canal-específico)
- `template-roteiro-live-julio.md` — estrutura de live concreta usando esses pilares
- `playbook-conteudo-contele-2026.md` — estratégia de conteúdo Contele OS

---

## Fonte técnica

- Curadoria de vídeos: Marco indica via tag `[CURADORIA-MARCO]` neste doc
- Análise de canal: ver `assistant-sexta-feira/output/fpt-canal-julio/`
- Literatura externa: 13 fontes consultadas 2024-2026 (lista no início do doc)
