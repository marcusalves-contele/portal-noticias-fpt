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

### Julio César (Fleet)
- `referencias/julio/julio-ref-01.JPEG` - Perfil com camisa Contele (expressão séria)
- `referencias/julio/julio-ref-02.JPEG` - Frontal sério
- `referencias/julio/julio_ref-sorrindo.jpg` - **SORRINDO** (usar para temas empolgantes)

**IMPORTANTE:** Escolher referência baseado no tema:
- Tema SÉRIO/ALERTA (multas, golpes, prejuízo): usar refs 01 e 02
- Tema EMPOLGANTE/NOVIDADE (IA grátis, lançamento, dica): usar ref-sorrindo PRIMEIRO

### Leonardo (Teams)
- Aguardando 4 fotos profissionais

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

### A/B Testing de Thumbs

Estratégia validada: gerar 2 conceitos diferentes pro mesmo vídeo e deixar o time escolher.
- **Ângulo "dor"**: curiosity gap focado no problema ("Ninguém lê as regras?")
- **Ângulo "choque de valor"**: contraste financeiro ("R$10.000 → R$0 GRÁTIS")
- Cada ângulo atrai perfil diferente de espectador — ambos são válidos para CTR
