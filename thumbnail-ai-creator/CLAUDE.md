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

### 2. Coletar Informações

Se o usuário já forneceu as informações (título, tema, número), use-as diretamente.

Caso contrário, pergunte apenas o necessário:
- Canal: Fleet (Julio) ou Teams (Leonardo)?
- Número da live
- Título/tema
- Se NÃO detectou convidado automaticamente: Tem convidado?

### 3. Criar Prompt Criativo (IA decide)

Baseado nas respostas, VOCÊ define criativamente:

- **Pose do apresentador**: Escolha a mais impactante para o tema
- **Expressão facial**: Combine com o tom do conteúdo
- **Elementos visuais**: Objetos nas mãos, ícones 3D, logos
- **Composição**: Posição, background, elementos de fundo
- **Texto impactante**: Reescreva o título se necessário para ser mais persuasivo

**Pesquise tendências** de thumbnails 2026:
- Cores vibrantes, alto contraste
- Rostos expressivos em close
- Texto grande e legível
- Elementos 3D/floating
- Sense of urgency ou curiosity gap

### 3. Montar Prompt Final

Use os templates em `prompts/template_fleet.md` ou `prompts/template_teams.md` como base.

Salve o prompt final em `prompts/live{NUMBER}.txt`

### 4. Gerar 3 Variações

**Modo automático (recomendado)** - detecta refs e convidado pelo número da live:
```bash
cd /Users/marcofassa/Documents/growth-contele/thumbnail-ai-creator

# Fleet (Julio) - padrão
python3 generate.py \
  --prompt-file prompts/live{NUMBER}.txt \
  --live {NUMBER} \
  --variations 3

# Teams (Leonardo)
python3 generate.py \
  --prompt-file prompts/live{NUMBER}.txt \
  --live {NUMBER} \
  --channel teams \
  --variations 3
```

**Modo manual** - especifica refs manualmente:
```bash
python3 generate.py \
  --prompt-file prompts/live{NUMBER}.txt \
  --refs referencias/julio/*.JPEG referencias/convidados/nome.jpg \
  --variations 3 \
  --prefix live{NUMBER}
```

### 5. Apresentar ao Usuário

Mostre as 3 variações usando `Read` para exibir as imagens.
Pergunte qual preferem ou se querem ajustes.

---

## Estrutura do Projeto

```
thumbnail-ai-creator/
├── .env                    # GEMINI_NANO_BANANA_KEY
├── generate.py             # Script de geração
├── prompts/
│   ├── template_fleet.md   # Template Julio/Fleet
│   ├── template_teams.md   # Template Leonardo/Teams
│   └── live{N}.txt         # Prompts específicos por live
├── referencias/
│   ├── julio/              # Fotos ref Julio (2 JPEGs)
│   ├── leonardo/           # Fotos ref Leonardo
│   └── convidados/         # Fotos de convidados (ver padrão abaixo)
└── output/                 # Thumbnails geradas
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

1. Usuário fornece info da live (título, número, tema)
2. Verificar se existe convidado: `--check-guest {NUM}`
3. **EU (Claude Code) crio o prompt diretamente** - NÃO delegar para subagentes
4. Usar o template base `_base_fleet.txt` como estrutura
5. Se tem convidado: incluir descrição física + texto "{Título} {Nome}"
6. Gerar: `python3 generate.py --prompt-file prompts/live{NUM}.txt --live {NUM}`
7. Mostrar variações e pedir aprovação

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
