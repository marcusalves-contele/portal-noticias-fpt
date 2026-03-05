# Thumbnail AI Creator

Gerador de thumbnails para YouTube usando IA (Gemini Nano Banana Pro).

## Setup

1. Criar `.env` com a credencial:
```
GEMINI_NANO_BANANA_KEY=sua_chave_aqui
```

2. Colocar fotos de referência em `referencias/`:
   - `julio/` - Fotos do Julio (Fleet)
   - `leonardo/` - Fotos do Leonardo (Teams)
   - `convidados/` - Fotos de convidados

## Uso com Claude Code

Abra o projeto e peça para criar uma thumbnail. O Claude Code vai:
1. Perguntar detalhes (título, tema, convidado)
2. Criar o prompt criativo
3. Gerar 3 variações
4. Mostrar para você escolher

## Uso Manual

```bash
python3 generate.py \
  --prompt "seu prompt aqui" \
  --refs referencias/julio/*.JPEG \
  --variations 3 \
  --open
```

Ou com arquivo de prompt:
```bash
python3 generate.py \
  --prompt-file prompts/live316.txt \
  --refs referencias/julio/*.JPEG \
  --variations 3
```

## Estrutura

```
├── generate.py          # Script principal
├── CLAUDE.md            # Instruções para Claude Code
├── prompts/
│   ├── template_fleet.md   # Template Julio
│   └── template_teams.md   # Template Leonardo
├── referencias/         # Fotos de referência
└── output/              # Thumbnails geradas
```

## Modelo

- **Gemini 3 Pro Image Preview** (Nano Banana Pro)
- Aspect ratio: 16:9
- Output: PNG ~1MB
