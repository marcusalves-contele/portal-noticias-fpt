# Thumbnail AI Creator

Sistema inteligente de geração de thumbnails para YouTube usando Gemini Nano Banana Pro.

## Como Funciona

Quando o usuário pedir para criar uma thumbnail, siga este fluxo:

### 1. Detectar Convidado Automaticamente

**ANTES de perguntar ao usuário**, verifique se existe convidado para a live:

```bash
python3 generate.py --check-guest {NUMERO_LIVE}
```

Retorna JSON com informações do convidado se encontrado:
```json
{"path": "...", "title": "Convidado", "name": "Nelson Margarido", "display": "Convidado Nelson Margarido"}
```

**Padrão de arquivo de convidado:** `{titulo}_live-{numero}-{Nome-Completo}.{ext}`
- Exemplos: `convidado_live-317-Nelson-Margarido.jpg`, `especialista_live-320-Maria-Silva.png`
- Títulos suportados: convidado, especialista, gestor, parceiro, etc.

### 2. Briefing Obrigatório (BLOCKER — não pular)

**ANTES de criar qualquer prompt**, as 3 respostas abaixo devem estar completas e específicas:

1. **Quem assiste esse vídeo?** (público — ex: "gestor de equipe externa", NÃO "usuários em geral")
2. **O que queremos que essa pessoa entenda ou decida?** (objetivo — ex: "que existe um pré-lançamento e ele deve experimentar")
3. **O que vai acontecer no conteúdo?** (o que tem no vídeo — ex: "demo das funcionalidades do novo app do gestor")

**Regras:**
- Se qualquer uma estiver vaga ou ausente → perguntar, não prosseguir
- O título/tema é **derivado** dessas respostas, não substituto delas
- Resposta genérica entra → criativo genérico sai (caso Live 186 v1)

**Contexto coletado** antes de prosseguir para o próximo passo:
- Canal: Fleet (Julio) ou Teams (Leonardo)?
- Número da live
- Respostas das 3 perguntas acima
- Se NÃO detectou convidado automaticamente: Tem convidado?

### 3. Definir 2 Ângulos Criativos (A/B)

A partir do briefing, **VOCÊ define 2 conceitos distintos** — não variações do mesmo, mas abordagens diferentes.

Cada ângulo deve ter:
- **Título diferente** (não apenas reformulado — apelo emocional diferente)
- **Composição diferente** (pose, posição no frame, elementos visuais)
- **Hook diferente** (o que vai fazer o gestor clicar no ângulo A vs ângulo B)

**Pares de ângulos comuns:**

| Par | Ângulo A | Ângulo B |
|-----|----------|----------|
| Desejo vs FOMO | "Olha o que chegou" — empolgação, novidade | "Seja o primeiro" — urgência, pré-lançamento exclusivo |
| Dor vs Solução | Problema que o gestor enfrenta hoje | O que muda com o novo recurso |
| Produto vs Resultado | Mostra o app/feature em detalhe | Mostra o gestor no controle, equipe funcionando |
| Surpresa vs Autoridade | Reação de "uau", algo inesperado | Tom seguro, "isso já chegou" |

Documente os 2 ângulos antes de criar qualquer prompt:
```
Ângulo A: [título] — [hook em 1 frase]
Ângulo B: [título] — [hook em 1 frase]
```

### 4. Criar 2 Prompts e Gerar

Crie 2 arquivos de prompt separados e gere 2 variações de cada.

Salve os prompts como `prompts/live{NUMBER}_a.txt` e `prompts/live{NUMBER}_b.txt`.

**Geração (rodar os 2 em sequência):**
```bash
cd /Users/marcofassa/Documents/growth-contele/thumbnail-ai-creator

# Ângulo A
python3 generate.py \
  --prompt-file prompts/live{NUMBER}_a.txt \
  --live {NUMBER} \
  --channel teams \
  --variations 2 \
  --prefix live{NUMBER}_a

# Ângulo B
python3 generate.py \
  --prompt-file prompts/live{NUMBER}_b.txt \
  --live {NUMBER} \
  --channel teams \
  --variations 2 \
  --prefix live{NUMBER}_b
```

**Fleet (Julio)** — remover `--channel teams` (fleet é o padrão).

**Modo manual** (refs específicas):
```bash
python3 generate.py \
  --prompt-file prompts/live{NUMBER}_a.txt \
  --refs referencias/julio/*.JPEG referencias/convidados/nome.jpg \
  --variations 2 \
  --prefix live{NUMBER}_a
```

### 5. Apresentar ao Usuário — 2 Finalistas

1. Mostrar as 4 imagens geradas (2 do ângulo A + 2 do ângulo B) com `Read`
2. Perguntar qual variação de A preferem e qual de B preferem
3. **Resultado final**: 1 imagem do ângulo A + 1 imagem do ângulo B = par A/B para teste

Se quiser ajustes em algum ângulo, ajustar o prompt do ângulo específico e regerar só ele.

---

## Estrutura do Projeto

```
thumbnail-ai-creator/
├── .env                    # GEMINI_NANO_BANANA_KEY
├── generate.py             # Script de geração
├── prompts/
│   ├── template_fleet.md   # Template Julio/Fleet
│   ├── template_teams.md   # Template Leonardo/Teams
│   ├── live{N}_a.txt       # Ângulo A (conceito 1)
│   └── live{N}_b.txt       # Ângulo B (conceito 2)
├── referencias/
│   ├── julio/              # Fotos ref Julio (2 JPEGs)
│   ├── leonardo/           # Fotos ref Leonardo
│   └── convidados/         # Fotos de convidados (ver padrão abaixo)
└── output/                 # Thumbnails geradas
    ├── live{N}_a_v1.png    # Variação 1 do ângulo A
    ├── live{N}_a_v2.png    # Variação 2 do ângulo A
    ├── live{N}_b_v1.png    # Variação 1 do ângulo B
    └── live{N}_b_v2.png    # Variação 2 do ângulo B
```

### Padrão de Nomenclatura de Convidados

Arquivos em `referencias/convidados/` devem seguir o padrão:
```
{titulo}_live-{numero}-{Nome-Completo}.{ext}
```

**Exemplos:**
- `convidado_live-317-Nelson-Margarido.jpg`
- `especialista_live-320-Maria-Silva.png`
- `gestor_live-325-Joao-Santos.jpeg`
- `parceiro_live-330-Pedro-Almeida.jpg`

O script extrai automaticamente:
- **Título**: "Convidado", "Especialista", "Gestor", etc.
- **Nome**: "Nelson Margarido" (hífens viram espaços)
- **Display**: "Convidado Nelson Margarido" (usado no prompt/thumbnail)

## Referências Disponíveis

### Julio César (Fleet) — Referências Oficiais (Mar/2026)
- `referencias/julio/julio-ref-primary-1.jpg` — Foto real ensaio (polo preta, frontal neutro, fundo branco)

**Usar `--channel fleet`** — `generate.py` carrega automaticamente `*-primary-*.jpg`.
Refs antigas IA (`julio_gray_blazzer.png`, `julio_polo_navy.png`, `julio_polo_white.png`) disponíveis na pasta principal para uso manual com `--refs`.
10 fotos de poses disponíveis em `referencias/julio/julio-polo-preta-*.jpg` para uso manual.

### Leonardo Gazolli (Teams) — Referências Oficiais (Mar/2026)
- `referencias/leonardo/leo-ref-primary.png` — Estúdio Gemini refinado (sorrindo, camiseta preta Contele, fundo branco)
  - Gerado por Gemini Nano Banana 2, refinamento de curva (pele + dentes). Cópia de `leonardo_studio_v1.png`.

**Usar `--channel teams`** — `generate.py` carrega automaticamente `leo-ref-primary.png`.
10 fotos de poses disponíveis em `referencias/leonardo/leo-camiseta-preta-contele-*.jpg` para uso manual.

---

## Elementos Persuasivos 2026

### Gatilhos Visuais
- **Urgência**: Vermelho, "ALERTA", "AGORA", relógios
- **Curiosidade**: "O que ninguém te conta", "Segredo", "?"
- **Autoridade**: Logos, certificados, números grandes
- **Social proof**: Fotos de pessoas, depoimentos visuais
- **Novidade**: "NOVO", "2026", estrelas, brilhos

### Expressões que Convertem
- **Surpresa**: Boca aberta, olhos arregalados
- **Preocupação**: Sobrancelhas franzidas, olhar sério
- **Empolgação**: Sorriso grande, energia
- **Dúvida**: Cabeça inclinada, mão no queixo

### Composições Eficazes
- Rosto ocupa 40-60% do frame
- Texto à esquerda, pessoa à direita (ou vice-versa)
- Contraste figura-fundo forte
- Máximo 5-7 palavras no título

---

## Modelo de IA

**Modelo**: `gemini-3-pro-image-preview` (Nano Banana Pro)
**API Key**: `GEMINI_NANO_BANANA_KEY` no `.env`
**Aspect Ratio**: 16:9 (padrão YouTube)
**Output**: PNG ~800KB-1MB

### Dicas para Prompts

1. Faces primeiro, composição depois
2. Sempre incluir hard negatives para idade/pele
3. Descrever características faciais específicas
4. Especificar poses e expressões claramente
5. Texto legível: pedir "large bold white text with shadow"

---

## Exemplo de Prompt Completo (Fleet)

```
Create a YouTube thumbnail in 16:9 aspect ratio for a fleet management channel.

REFERENCE IMAGES PROVIDED:
- Image 1 and 2: JULIO (main host) face references - may be rotated 90 degrees
- Image 3: GUEST face reference (if applicable)
- Image 4: COMPOSITION/STYLE REFERENCE (if applicable)

JULIO (MAIN HOST) - FACE CONSISTENCY:
- Gray/white stubble beard (salt and pepper, short)
- Short brown hair, slightly wavy
- Brown/hazel eyes, NO glasses
- Age: 40-42 years old, YOUTHFUL appearance
- Wearing dark blue Contele polo shirt

SKIN TEXTURE - CRITICAL:
- Keep skin SMOOTH like a fit 40 year old
- Do NOT add wrinkles or age marks
- Forehead SMOOTH, cheeks FIRM

COMPOSITION:
- Julio in CENTER, medium shot (waist up)
- POSE: [DEFINIR POSE BASEADO NO TEMA]
- Background: [DEFINIR BACKGROUND]

TEXT ELEMENTS:
- TOP: Red badge "LIVE [NUMBER]"
- TITLE: "[TÍTULO]" large white bold text with shadow

EXPRESSION: [DEFINIR EXPRESSÃO]

LOGOS:
- Purple Contele logo (stylized "9")
- [OUTROS LOGOS SE APLICÁVEL]

STYLE: Professional YouTube thumbnail, photorealistic, purple/magenta cinematic lighting, high contrast.
```

---

## Checklist Antes de Gerar

- [ ] Canal definido (Fleet/Teams)
- [ ] Número da live extraído
- [ ] Verificar convidado: `python3 generate.py --check-guest {NUM}`
- [ ] Título impactante (máx 7 palavras)
- [ ] Pose escolhida para o tema
- [ ] Expressão definida
- [ ] Se tem convidado: incluir "{Título} {Nome}" no prompt de texto
- [ ] Background/elementos definidos

## Workflow Resumido

1. Usuário fornece info da live (número, tema)
2. Verificar convidado: `--check-guest {NUM}`
3. **Briefing obrigatório**: 3 perguntas respondidas (público, objetivo, conteúdo)
4. **Definir 2 ângulos criativos** (A e B) com títulos e hooks diferentes
5. **EU (Claude Code) crio os 2 prompts** — NÃO delegar para subagentes
6. Salvar como `prompts/live{NUM}_a.txt` e `prompts/live{NUM}_b.txt`
7. Gerar 2 variações de cada ângulo (`--variations 2 --prefix live{NUM}_a/b`)
8. Mostrar as 4 imagens → usuário escolhe 1 de cada ângulo → par A/B final

## IMPORTANTE: Geração de Prompts

**NÃO delegar criação de prompts para subagentes.** A consistência do rosto do Julio depende do prompt ter EXATAMENTE esta estrutura no início:

```
CRITICAL - FACE REFERENCE IMAGES:
- Images 1-2 are JULIO's actual face photos - YOU MUST COPY THIS EXACT FACE
- Do NOT create a different person - use the reference photos as the PRIMARY SOURCE
- The man in the thumbnail MUST look like the man in reference images 1-2

JULIO - COPY THE FACE FROM REFERENCE PHOTOS EXACTLY:
- WIDER face shape, slightly square jaw - MATCH THE REFERENCE
- DENSE gray/white stubble beard covering jaw and chin (salt and pepper, NOT sparse)
- Receding hairline with short brown/gray hair - MATCH THE REFERENCE
- Deep-set brown/hazel eyes, NO glasses
- Age: 45+, mature appearance
- Dark navy blue polo shirt (plain, no logos)
- The face MUST be recognizable as the same person from the reference photos
```

Se esse bloco não estiver no início do prompt, o modelo gera pessoas aleatórias.

---

## Aprendizados — Fev/2026

### Refs Cyberpunk = Fidelidade Facial Baixa (~60-70%)

Fotos com efeitos pesados (neon, hologramas, headsets cyberpunk) prejudicam a capacidade do Gemini de copiar rostos. O modelo confunde efeitos visuais com características faciais reais.

**Solução validada: Face-lock com thumb aprovada**

Quando a primeira geração acertar os rostos mas o conceito mudar:
1. Gerar primeiro com conceito simples (menos elementos visuais = mais atenção nos rostos)
2. Usar a thumb aprovada como **3a referência** nas próximas gerações
3. No prompt, instruir: "Image 3 is a PREVIOUSLY APPROVED THUMBNAIL — use as PRIMARY face reference"

Exemplo real:
```bash
python3 generate.py \
  --prompt-file prompts/treinamento_choque_v3_facelock.txt \
  --refs \
    referencias/convidados/convidado_live-319-Leonardo-Teixeira.jpg \
    referencias/convidados/convidado_live-319-Lucca-Silva.jpg \
    output/treinamento_politica_ia_v1.png \
  --variations 3 \
  --prefix treinamento_choque_facelock
```

Resultado: rostos melhoraram significativamente na segunda composição (choque) usando a thumb da primeira (dor) como âncora facial.

**Recomendação**: Sempre pedir fotos naturais (selfie, corporativa) dos apresentadores. Fotos estilizadas/cyberpunk servem como fallback mas nunca vão dar 90%+ de fidelidade.

### Vídeos de Treinamento (não-live)

Para vídeos que não são lives numeradas:
- Sem badge "LIVE XXX" — usar badge "TREINAMENTO" no topo
- Usar `--refs` manual em vez de `--live` (que puxa Julio automaticamente)
- Prefix descritivo: `--prefix treinamento_politica_ia`
- Apresentadores podem ser diferentes do host do canal (ex: Leonardo + Lucca no canal Fleet)

### Texto Overlay via Pillow = Ruim

Adicionar texto por cima de thumb gerada com Pillow fica amador — fonte não combina com o estilo da imagem. Melhor pedir o texto direto no prompt do Gemini na primeira geração. Se precisar adicionar contexto depois, é melhor regerar do zero.

### Pipeline Face-Lock — Método Avançado para Múltiplos Rostos

**Quando acionar**: thumbnails com 3+ pessoas (host + 2 convidados) onde a geração direta falha — rostos saem genéricos, sem semelhança com as referências.

**Por que acontece**: o modelo tem limite de atenção. Com 4+ imagens de referência simultâneas (2 do host + 2 convidados), ele distribui a atenção e nenhum rosto sai fiel.

**O método — 2 etapas:**

1. **Etapa 1 — Acertar o rosto do host**
   - Gerar com apenas 2 refs (as fotos do host)
   - Sem convidados no prompt ainda
   - Gerar 2-3 variações e aprovar a melhor

2. **Etapa 2 — Face-lock + convidados**
   - Usar a thumb aprovada na Etapa 1 como `Image 3` nas refs
   - Adicionar refs dos convidados como `Image 4`, `Image 5`
   - No prompt: "Image 3 is a PREVIOUSLY APPROVED THUMBNAIL — use as PRIMARY face reference"
   - O host fica consistente; convidados entram no espaço livre da composição

**Exemplo real — Live 320 (26/02/2026):**
```bash
# Etapa 1 — host sozinho
python3 generate.py \
  --prompt-file prompts/live320_b_julio.txt \
  --refs referencias/julio/julio-ref-01.JPEG referencias/julio/julio-ref-02.JPEG \
  --variations 2 --prefix live320_b_julio

# Etapa 2 — face-lock + 2 convidados
python3 generate.py \
  --prompt-file prompts/live320_b_facelock.txt \
  --refs referencias/julio/julio-ref-01.JPEG referencias/julio/julio-ref-02.JPEG \
    output/live320_b_julio_v1.png \
    referencias/convidados/convidado_live-320-Carla-da-Luz.png \
    referencias/convidados/convidado_live-320-Hiago-Daros.png \
  --variations 3 --prefix live320_b_facelock
```

**Resultado**: host consistente em 100% das gerações. Fidelidade dos convidados depende da qualidade das fotos de referência.

**Regra**: só acionar o Pipeline Face-Lock quando a geração direta falhar. Para 1 convidado (3 refs total), a geração direta ainda funciona bem.

---

### A/B Testing de Thumbs

Estratégia validada: gerar 2 conceitos diferentes pro mesmo vídeo e deixar o time escolher.
- **Ângulo "dor"**: curiosity gap focado no problema ("Ninguém lê as regras?")
- **Ângulo "choque de valor"**: contraste financeiro ("R$10.000 → R$0 GRÁTIS")
- Cada ângulo atrai perfil diferente de espectador — ambos são válidos para CTR

---

### Leonardo Gazolli (Teams) — Aprendizados (Fev/2026)

#### Referência Oficial
- **`referencias/leonardo/leo-ref-primary.png`** — única ref válida para o Leo
- Código já atualiza `get_host_refs('teams')` para usar só ela — qualquer `--channel teams` já puxa automaticamente
- As fotos originais (`leo-ia.jpg`, `leo-ia-2.jpg`) ficam como fallback mas **não usar como referência primária**

#### APRENDIZADO CRÍTICO: Referência oficial = `leo-ref-primary.png`
- `leo-ref-primary.png` = cópia de `leonardo_studio_v1.png` (ensaio Mar/2026, Gemini Nano Banana 2 + curva)
- Não substituir sem aprovação explícita do Marco
- Para gerar A (fundo escuro/urgência): usar `b_fl3_v2` como ref única (sem fotos originais) — resolve conflito de iluminação
- Para gerar B (fundo azul/corporativo): usar `--channel teams` normalmente (puxa `leo-ref-primary.png`)

#### Ordem das Referências Importa
- Colocar a âncora aprovada como **Image 1** (primeiro `--refs`) dá resultados mais fiéis do que como Image 3
- O modelo dá mais peso para as primeiras imagens da lista

#### Fundo Escuro (Ângulo A/Urgência) > Fundo Claro (Ângulo B/Corporativo)
- Quando o fundo é escuro/dramático (vermelho, carvão), o modelo mantém melhor a fidelidade facial
- Quando muda para fundo azul/corporativo (ângulo B), o rosto deriva — fica mais jovem e diferente
- **Solução**: gerar ângulo A primeiro (fundo escuro), aprovar o melhor, usar como âncora para ângulo B

#### Pipeline Obrigatório para Teams A/B
```
1. Gerar ângulo A com --channel teams (usa leo-ref-primary.png automaticamente)
2. Aprovar melhor variação do A
3. Gerar ângulo B com âncora = melhor A como Image 1:
   python3 generate.py \
     --prompt-file prompts/..._b.txt \
     --refs output/melhor_A.png \
     --variations 3 --prefix ..._b
4. Após gerar A e B — comparar qual ficou mais fiel ao Leo real
5. Atualizar leo-ref-primary.png com a versão mais fiel (pode ser do B!)
```

#### Prompt: menos elementos = mais fidelidade facial
- Prompts com muitos elementos (smartphone flutuando + ícones + texto + fundo complexo) dispersam atenção do modelo
- Para Teams B (corporativo), manter composição simples: 1 smartphone, fundo limpo, sem muitos elementos flutuantes

---

### Processo Padrão A/B — Válido para Fleet (Julio) e Teams (Leo)

**Regra universal para ambos os canais**: gerar sempre par A/B, 1 variação de cada após refinar a referência.

| Etapa | Fleet (Julio) | Teams (Leo) |
|-------|--------------|-------------|
| Ref primária | `referencias/julio/` (3 fotos, escolher por tema) | `referencias/leonardo/leo-ref-primary.png` |
| Gerar A | `--channel fleet` | `--channel teams` |
| Gerar B | `--refs output/melhor_A.png` | `--refs output/melhor_A.png` |
| Atualizar ref | Comparar A e B → salvar a mais fiel em `julio-ref-approved.png` se necessário | Substituir `leo-ref-primary.png` pela versão mais fiel |

**Quantidade por rodada**: 1 variação de cada ângulo após a ref estar travada (não 2-3 — economiza API e evita confusão de escolha).

**Face-lock para Julio**: aplicar o mesmo pipeline de Teams — se o B derivar do rosto, usar o melhor A como âncora.
