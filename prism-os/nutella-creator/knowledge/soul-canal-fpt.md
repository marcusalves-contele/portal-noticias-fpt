# soul-canal-fpt.md
## Alma do canal Frota Para Todos — Diretivas Operacionais Baseadas em Dado

> **Como usar este documento**
> Carregue ANTES de qualquer geracao de roteiro, thumb, titulo ou copy do canal FPT.
> Este e o complemento factual ao `brand-fpt-agent.md`: brand book diz QUEM o canal e (qualitativo). Soul diz COMO ele se comporta na pratica (quantitativo). Os dois juntos formam a fonte da verdade.
>
> Ultima atualizacao: 2026-04-28
> Base: dataset_classified_with_leads.json (2.786 videos, lifetime + janela 180d)
> Refresh: rodar `/canal-julio refresh` no repo `assistant-sexta-feira` trimestralmente

---

## 0. Protocolo de uso pelo agente

Antes de gerar qualquer artefato pro canal (roteiro, thumb, titulo, descricao, post de divulgacao):

1. Ler `brand-fpt-agent.md` (identidade, voz, vocabulario, vilao, persona)
2. Ler este `soul-canal-fpt.md` (dado factual, anatomia de hit/flop, gates)
3. Aplicar checklist da secao 8 antes de propor o artefato
4. Se algum gate falhar, retornar pro humano com motivo, nao "gerar mesmo assim"

---

## 1. O canal hoje em numero organico (lifetime + 180d)

### Distribuicao de trafego

| Classe | N videos | Subs ganhos | % subs |
|---|---|---|---|
| organico_puro | 2.440 | 16.352 | 53% |
| misto (organico + boost posterior) | 49 | 12.770 | 41% |
| ad_boosted (criado pra ad) | 180 | 2.003 | 6% |

**Insight critico**: 49 videos "misto" geram 41% dos inscritos. **Misto = melhor uso de budget de patrocinio** porque amplifica conteudo que ja provou tracao organica. Ad_boosted puro (180 videos criados pra ad) gera 6% — orcamento mal investido.

### Volume por formato (organico, exclui ad_boosted)

| Formato | N | Subs/video | Subs/1k_views | APV organico medio |
|---|---|---|---|---|
| live | 336 | **28,3** | **25,45** | 17,5% |
| gravado | 907 | 19,2 | 18,91 | 39,1% |
| short | 1.246 | 0,6 | 1,71 | 67,0% |

**Interpretacao**: live converte 15x mais inscrito por view que short. Gravado e o cavalo de batalha (volume + retencao). Short serve descoberta, NAO sustenta canal.

---

## 2. Anatomia de hit organico

Padroes que aparecem repetidos nos top 30 organicos lifetime (61% dos subs do canal):

### Hit do tipo "Aulao formativo (live longa)" — padrao vencedor identificado

**Os 8 melhores lives organicas em subs/1k sao TODAS "Aulao do Zero ao Profissional"** (8 versoes ao longo dos anos). 138, 132, 101, 95, 83, 80 subs/1k_org. Confirma que NAO e tema generico, e formato especifico:

- **Duracao**: 130-170 minutos (2h-2h45)
- **Naming pattern**: "Aulao Gestao de Frotas do Zero ao Profissional" + edicao/data. Tambem: "Semana da Gestao de Frotas", "Aula N - tema"
- **Estrutura**: aulao didatico em N modulos, framework completo, nivel iniciante->profissional
- **APV organico**: 16-20% (baixo por duracao, alto em subs/1k)
- **Subs/video**: 196-802

**Outros formatos de live que tambem funcionam (segundo nivel)**:
- Live tematica focada de 60-90min (Indicadores 6 Melhores 646 subs, Live 01 basico 453)
- Aula N de serie (CPK, Frota Lucrativa, Gestao Pneus)
- Live com convidado especialista (Direcao Extraeconomica 116 subs)

**Exemplo TOP**: Aulao 802 subs (2h28), versao 28/07. Pode replicar formato 1-2x/ano.

### Hit do tipo "Gravado tema-produto 10-20min"

- **Duracao**: 10-20 minutos (bucket vencedor: 79 subs/video, 37,56 subs/1k)
- **Tema**: produto/ferramenta concreta (rastreador, sistema, app, dashboard, planilha, cartao combustivel)
- **Estrutura de titulo (validada em 30 top, n=38 com >=200 views_org)**:
  - **57% usam separador `:`, ` - ` ou ` | `** ("Sistema de Rastreamento Veicular: O que e e como funciona?")
  - **30% sao perguntas** (acabam com `?`)
  - **30% tem numero** (mas NAO R$/%): "6 Melhores", "5 Dicas", "Live 41"
  - 0% tem cifrao ou %
  - Palavra "frota" aparece em 53% dos titulos top (16 de 30)
- **Thumb**: rosto Julio em closeup + produto/ativo visivel + texto curto + cor de destaque
- **APV organico**: 17-46% (mediana 30%)
- **Subs/video**: 80-1200
- **Leads/1k_org**: 0,4-2,6

**Exemplos** (todos top 5 do bucket): Sistema Rastreamento Veicular 805 subs, Checklist Rapido Download Gratis 259, Relatorios Gestao Efetivos 191, Controle Abastecimento Gratis Online 132, Politica de Frota processo criminal 71.

**Anti-padrao**: titulo sem separador, sem promessa concreta no subtitulo, sem nome especifico do produto/ferramenta. Bottom do bucket tem titulos genericos ("Adeus Borracharia", "Tirando duvidas sobre ARLA 32").

### Hit do tipo "Implementacao live (live curta tematica)"

- **Duracao**: 60-90 minutos
- **Tema**: "da X para Y" (planilha pro sistema, manual pra automatico, iniciante pra metodo)
- **Formato**: live tematica focada com convidado eventual
- **APV organico**: 15-25% (baixo, mas converte lead)
- **Leads/1k_org**: **7,71** (Live 298 Planilha->Sistema, melhor taxa do canal)

---

## 3. Anatomia de flop organico (NAO replicar)

Padroes que aparecem nos bottom 100 organicos:

### Flop do tipo "anuncio de evento/curso"

- **Sintoma**: APV organico <22%, sem lead
- **Exemplos**: "Aulao vem ai" (36% APV mas 0 lead), "Curso FPT inscricoes abertas" (14% APV)
- **Por que**: anuncio nao e conteudo de canal. Audiencia foge. Separar: lancamento e ad pago, canal e autoridade.

### Flop do tipo "review generico de veiculo"

- **Sintoma**: cluster "review veiculo novo" tem APV 21-26%, baixa atribuicao a leads
- **Por que**: sai do arquetipo (Julio nao e revisor automotivo). Publico errado.

### Flop do tipo "como X generico longo"

- **Sintoma**: titulo abre com "Como" sem especificar o "X". APV cai pra 22-28%.
- **Exemplo**: "Como organizar a frota" vs "Como reduzir CPK em 30% com 3 indicadores" (este converte)

### Flop do tipo "short isolado sem cluster"

- **Sintoma**: 1246 shorts geraram 754 subs (0,6 subs/video, 1,71 subs/1k)
- **Por que**: short serve descoberta, nao retencao. Canal nao se sustenta em short.

### Flop do tipo "video curto 1-5min isolado"

- **Sintoma**: bucket 1-5min em gravado tem 3,8 subs/video (vs 79 do bucket 10-20m)
- **Por que**: nao da tempo de gerar inscricao. Se for short, e short. Se for gravado, ir pra 10+ minutos.

---

## 4. Diretivas operacionais pro Prism (geracao de thumb)

> Aplica ao `thumbnail-ai-creator/` e a qualquer thumb gerada pelo time.

### Regras-base

1. **Rosto do Julio sempre** (100% das thumbs organicas dos ultimos 180d tem rosto)
2. **Polo navy lisa** (sem logos), barba sal e pimenta, sem oculos, expressao de autoridade calma (nao sorriso largo, nao surpresa exagerada)
3. **Fundo cinematografico** com bokeh e gradiente — nao roxo puro dominante (cor da marca FPT vira ruido em thumb)
4. **Texto curto** (3-6 palavras maximo), bold, contraste alto
5. **Numero ou simbolo de R$/% sempre que possivel** (R$, %, +, ↓, →)
6. **Brightness baixa-media** (testes mostram bottom 75% das thumbs flop tem brightness alto)

### Foto real do Julio vs Prism AI

| Tipo | APV organico | Views/dia | Quando usar |
|---|---|---|---|
| Foto real | 37,3% | 0,91 | Gravado tema-produto, live, conteudo de profundidade |
| Prism AI | 31,7% | 1,65 | Topo de funil, descoberta, short, conteudo conceitual |

**Regra**: Prism vence em views/dia (+81%) mas perde APV (-15%). Usar Prism em conteudo onde objetivo e DESCOBERTA, nao retencao. Pra video de produto/conversao, usar foto real.

### Cores PROIBIDAS na thumb

- `#7C3AED` (Tailwind 600): muito frio, nao e nosso roxo
- Roxo dominante na thumb (sim, parece marca, mas em thumb prejudica clique)
- Laranja, amarelo, rosa: fora do territorio
- Gradientes multicoloridos: descaracterizam

### Composicao validada (templates)

- Closeup rosto Julio (35-50% da area) lateral esquerda + texto destaque direita
- Rosto centralizado + produto/ativo visivel atras (rastreador, dashboard, planilha)
- Live: mesma logica + badge "AO VIVO" vermelho canto superior direito

---

## 5. Diretivas pro agente de roteiro

> Aplica a `roteiro-video` skill e a qualquer geracao de pauta.

### Estrutura de gravado tema-produto (formato vencedor 10-20m)

1. **Hook 0-15s**: numero forte + promessa concreta (R$, %, tempo)
2. **Quem fala 15-30s**: Julio se apresenta com 1 frase de credibilidade ("20+ anos no campo", "milhares de gestores"). Nao mais que 30s.
3. **Problema 30s-2min**: descrever vilao em historia real ("o gestor X que apaga fogo", "a empresa Y que perde R$1.200 por veiculo")
4. **Solucao 2-12min**: passo a passo aplicavel **amanha**. Numerar (1, 2, 3). Mostrar tela/produto sempre que possivel.
5. **CTA 12-15min**: "se quiser ferramenta pra fazer isso, [link/curso/cartao]". Direto.
6. **Q&A ou bonus 15-20min**: dica final aprofundada que so quem ficou ate o final ganha (gera APV alto na ponta)

### Estrutura de live tematica (60-90min, formato 7,71 leads/1k)

1. **Abertura 0-3min**: cumprimentar, perguntar de onde tao vendo, alinhar expectativa
2. **Tema do dia 3-15min**: contexto + por que esse tema agora
3. **Bloco 1: dor 15-30min**: detalhar o problema com exemplo real
4. **Bloco 2: framework 30-50min**: passo a passo. Lista numerada. Tela/planilha/produto.
5. **Bloco 3: aplicacao 50-70min**: caso real. Como o gestor X resolveu.
6. **Q&A 70-80min**: chat. Aqui sai os melhores leads.
7. **CTA 80-90min**: oferta gratuita (planilha, checklist) + caminho pro produto Contele

### Frases reais do Julio que SEMPRE devem aparecer

- "Dica de ouro" (uma vez no inicio, uma no fim)
- "O que voce falaria pra alguem fazer amanha?"
- "Feito e melhor do que perfeito"
- "Pareto 80/20"
- "Gestao e compartilhada (motorista + gestor)"
- "Conhecimento vale muito"
- "Fala meus amigos gestores" (abertura padrao)

### Vocabulario obrigatorio (USAR)

CPK, km/l, pratico, na pratica, na ponta do lapis, mao na massa, gestor, motorista (parte da solucao), premiacao, ferramenta, resultado, economia, vamos resolver.

### Vocabulario PROIBIDO (substituir antes de gerar)

solucao inovadora, disruptivo, ecossistema, sinergia, stakeholder, case de sucesso, agregamos valor, tecnologia de ponta, exclusivo/premium, otimizar, venha conhecer.

---

## 6. Tabus de tema (NAO produzir)

Cada um tem dado por tras:

1. **Anuncio de evento/curso isolado** ("Aulao vem ai", "Curso 3.0 inscricoes"). APV <22%, gasta posicao na grade. Se for lancamento, ad pago.
2. **Review generico de veiculo novo**. Fora do arquetipo. Cluster review tem APV 21-26%.
3. **"Como" generico longo sem promessa numerica** ("Como organizar a frota"). Clique mas nao retem.
4. **Conteudo "para iniciantes" como aposta de lead**. Audiencia consome, nao converte. Manter pra topo de funil, esperar conversao em outro lugar.
5. **Short isolado sem cluster tematico**. Curtissimo retorno em subs.

---

## 7. Metricas-norte mensais (so 5 numeros)

Time olha 1x por mes via `/canal-julio refresh`:

| Metrica | Meta |
|---|---|
| APV organico medio (organico_puro) | >=35% |
| subsGained organico_puro / mes | >=500 |
| Subs organic / 1k views organic | >=15 |
| Leads organic / 1k views organic | >=2,0 |
| % videos com sinal organico (organic_APV>=25% E organic_views>=500) | >=50% |

Se algum cair 2 meses seguidos, alerta: revisar mix.

---

## 8. Checklist pre-producao (gates antes de gerar artefato)

Antes de gerar roteiro/thumb/titulo/descricao, agente DEVE responder:

- [ ] Tema esta dentro de Sage Pragmatico (mestre que aprendeu no campo) + Hero (combate vilao concreto)?
- [ ] Tema combate Vilao 1 (Conteudo de Vitrine) ou Vilao 2 (Gestor que Apaga Fogo)?
- [ ] Persona-alvo identificada: Marcos (iniciante involuntario), Ricardo (profissional em evolucao), Lucas (estudante), Sergio (motorista)? Apenas UMA por video.
- [ ] Promessa do video tem **numero concreto** (R$, %, tempo)? Se nao, reescrever.
- [ ] Formato escolhido coerente com objetivo:
  - Subs/canal: live longa OU gravado 10-20min produto
  - Leads: live tematica de implementacao OU gravado produto direto
  - Descoberta: short com cluster
  - Conversao Contele direta: gravado curto com CTA Cartao Fleet
- [ ] Duracao planejada bate com bucket vencedor:
  - Gravado: 10-20min (vencedor) ou 5-10min (segundo)
  - Live: 60-150min
  - Short: <60s
  - Evitar: 1-5min isolado, 20-60min isolado, >60min nao-live
- [ ] Vocabulario usa termos da lista USAR e nenhum da lista PROIBIDO?
- [ ] Tema NAO esta nos 5 tabus da secao 6?
- [ ] Para video que sera patrocinado: passa nos 3 gates de boost? (organic_views>=500, organic_APV>=25%, tema-produto)

Se ANY check falhar: retorna pro humano com lista do que falhou. Nao gera mesmo assim.

---

## 9. Refresh cycle

- **Trimestral (Q1, Q2, Q3, Q4)**: rodar `/canal-julio refresh` no repo `assistant-sexta-feira`. Atualiza dataset, reclassifica trafego, regenera analises e este soul.md
- **Pos-mudanca de mix**: rodar 30 dias depois de mudar formato pra avaliar impacto (controle: comparar mix novo vs mix antigo nos top 5 videos publicados em cada periodo)
- **Pos-incidente**: se uma metrica-norte cair 30%+ em 1 mes, refresh emergencial + reuniao Marco + Julio + Cris
- **Brand book sync**: numeros de prova social no `brand-fpt-agent.md` se atualizam junto neste refresh (inscritos totais, views totais, etc.)

---

## Conexoes (wikilinks)

- `brand-fpt-agent.md` (qualitativo, identidade, voz)
- `brand-fpt.md` (versao humana)
- `entrevista-arquetipo-julio-PROCESSADO.md` (origem do arquetipo Sage+Hero)
- `playbook-conteudo-contele-2026.md` (estrategia de conteudo Contele OS)
- `sistema-thumbnails-ai.md` (Prism technical)
- `nutella-plano-producao-master.md` (plano de producao Nutellas)
- `prism-os.md` (Prism OS reference)

---

## Fonte tecnica

- **Repo**: `/Users/marcofassa/Documents/assistant-sexta-feira`
- **Skill**: `/canal-julio` (subcomandos: harvest, analyze, ask, report, refresh, status)
- **Dataset bruto**: `output/fpt-canal-julio/dataset_classified_with_leads.json`
- **Analises**: `output/fpt-canal-julio/analises/0X-*.md`
- **Relatorio mais recente**: `output/fpt-canal-julio/relatorios/2026-04-28-decisoes-canal-fpt.md`
