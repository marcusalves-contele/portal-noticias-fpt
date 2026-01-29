# Template Fleet (Julio César)

## Variáveis
- {LIVE_NUMBER}: Número da live (ex: 316)
- {TITLE}: Título principal
- {SUBTITLE}: Subtítulo (opcional)
- {GUEST_NAME}: Nome do convidado (se houver)
- {GUEST_DESCRIPTION}: Descrição visual do convidado
- {OBJECT_IN_HANDS}: Objeto nas mãos (CNH, tablet, rastreador, etc)
- {EXPRESSION}: Expressão (serious, excited, questioning, surprised)
- {BACKGROUND_ELEMENTS}: Elementos de fundo (trucks, fleet, maps, etc)

## Prompt Base

```
Create a YouTube thumbnail in 16:9 aspect ratio for a fleet management channel.

MULTI-REFERENCE FACE CONSISTENCY:
- Images 1-2: JULIO (main host) face references - may be rotated 90 degrees
- Image 3+: Additional references (guest, composition style)

JULIO (MAIN HOST):
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
- Julio positioned {POSITION} of frame
- Medium shot (waist up)
- {POSE_DESCRIPTION}
- {OBJECT_IN_HANDS}

EXPRESSION: {EXPRESSION}

BACKGROUND:
- {BACKGROUND_ELEMENTS}
- Purple/magenta color grade overlay
- Bokeh blur, dramatic lighting

TEXT ELEMENTS:
- TOP: Red badge "LIVE {LIVE_NUMBER}"
- TITLE: "{TITLE}" large white bold text
- SUBTITLE: "{SUBTITLE}" (if applicable)

{GUEST_SECTION}

LOGOS:
- Purple Contele logo (stylized "9")
- Additional relevant logos

STYLE: Professional YouTube thumbnail, photorealistic, purple/magenta cinematic lighting, high contrast for mobile viewing.
```

## Poses Sugeridas por Tema

| Tema | Pose | Objeto | Expressão |
|------|------|--------|-----------|
| CNH/Multas | Segurando CNH | CNH brasileira | Serious, concerned |
| Comparação/VS | Mãos abertas pesando | Nenhum | Questioning |
| Novidade/Lançamento | Apontando para frente | Smartphone | Excited, energetic |
| Alerta/Urgente | Mão levantada "pare" | Nenhum | Serious, warning |
| Tecnologia | Segurando tablet | Tablet com dashboard | Confident, professional |
| Economia | Gesto de dinheiro | Nenhum | Happy, satisfied |

## Backgrounds Sugeridos

- **Frota**: Caminhões/vans blurred no fundo
- **Tecnologia**: Escritório moderno com monitores
- **Estrada**: Rodovia com veículos
- **Dashboard**: Telas do sistema Contele
