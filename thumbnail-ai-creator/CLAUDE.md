# Thumbnail AI Creator

Sistema inteligente de geração de thumbnails para YouTube usando Gemini Nano Banana Pro.

## Como Funciona

Quando o usuário pedir para criar uma thumbnail, siga este fluxo:

### 1. Coletar Informações (perguntas ao usuário)

Use `AskUserQuestion` para perguntar:

```
1. Canal: Fleet (Julio) ou Teams (Leonardo)?
2. Número da live (ex: 316)
3. Título/tema da live
4. Sobre o que será falado (1-2 frases)
5. Tem convidado? Se sim:
   - Nome completo
   - Fornecer foto de referência
6. Tem material específico? (tela do sistema, documento, CTA)
```

### 2. Criar Prompt Criativo (IA decide)

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

```bash
cd /Users/marcofassa/Documents/growth-contele/thumbnail-ai-creator

python3 generate.py \
  --prompt-file prompts/live{NUMBER}.txt \
  --refs referencias/julio/*.JPEG \
  --variations 3 \
  --prefix live{NUMBER} \
  --open
```

Se tiver convidado, adicione a foto:
```bash
--refs referencias/julio/*.JPEG referencias/convidados/nome.jpg
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
│   └── convidados/         # Fotos de convidados
└── output/                 # Thumbnails geradas
```

## Referências Disponíveis

### Julio César (Fleet)
- `referencias/julio/julio-ref-01.JPEG` - Perfil com camisa Contele
- `referencias/julio/julio-ref-02.JPEG` - Frontal sério

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
