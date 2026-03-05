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

## Aprendizados Importantes

1. **Camisa LISA**: Sempre especificar "PLAIN dark navy blue polo shirt (NO logos, NO text)"
2. **Face natural**: Pedir "natural-looking face", "authentic expression" para evitar cara artificial
3. **Sem logos**: Explicitamente dizer "Do NOT add any logos anywhere" - a IA tende a adicionar
4. **Texto + Background**: Garantir que texto esteja alinhado com o lado correto do background (ex: "PERSEGUIÇÃO" no lado escuro, "MONITORAMENTO" no lado claro)
5. **Posição do texto**: Especificar "lower third" para não sobrepor o rosto
6. **NÃO rotacionar refs**: Manter imagens de referência na orientação original (rotação PIORA resultado)
7. **Prompt detalhado > curto**: Prompts mais detalhados funcionam melhor que prompts curtos focados em "copiar face"
8. **Variação natural**: O modelo tem variação natural - gerar 3+ e escolher a melhor
9. **NÃO pedir "variações" no prompt**: Se pedir variações de design, o modelo pode criar collages em vez de imagens separadas

## Prompt Base

```
Create a YouTube thumbnail in 16:9 aspect ratio for a fleet management channel.

REFERENCE IMAGES PROVIDED:
- Images 1-2: JULIO (main host) face references - may be rotated 90 degrees
- Image 3+: Additional references (guest, composition style) if applicable

JULIO (MAIN HOST) - FACE CONSISTENCY CRITICAL:
- Gray/white stubble beard (salt and pepper, short, well-groomed)
- Short brown hair, slightly wavy, natural looking
- Brown/hazel eyes, NO glasses
- Age: 40-42 years old, YOUTHFUL appearance, natural skin
- Wearing PLAIN dark navy blue polo shirt (NO logos, NO text on shirt)
- Natural relaxed posture, authentic expression

SKIN TEXTURE - CRITICAL:
- Keep skin SMOOTH like a fit 40 year old
- Do NOT add wrinkles, age spots, or blemishes
- Forehead SMOOTH, cheeks FIRM
- Healthy, natural skin tone
- Natural lighting on face, not overprocessed

COMPOSITION:
- Julio positioned {POSITION} of frame
- Medium shot (chest up)
- {POSE_DESCRIPTION}
- {OBJECT_IN_HANDS}

EXPRESSION: {EXPRESSION}

BACKGROUND:
- {BACKGROUND_ELEMENTS}
- Purple/magenta color grade overlay
- Bokeh blur, dramatic lighting

BRIEFING CONTEXT (informa o tom e posicionamento visual):
- Público: {AUDIENCE} — o criativo deve falar diretamente com essa pessoa
- Objetivo: {OBJECTIVE} — a imagem deve comunicar essa mensagem em 1 segundo
- Conteúdo: {CONTENT_DESCRIPTION} — use isso para definir elementos visuais relevantes

TEXT ELEMENTS:
- TOP LEFT: Red badge "LIVE {LIVE_NUMBER}"
- TITLE: "{TITLE}" large white bold text with strong black shadow
- Position text in lower third, not overlapping face
- {SUBTITLE} (if applicable)

{GUEST_SECTION}

NO LOGOS:
- Do NOT add any logos anywhere in the image
- Do NOT add watermarks or brand marks
- Keep the image clean and focused

STYLE: Professional YouTube thumbnail, photorealistic natural-looking face, slightly stylized background, purple/magenta cinematic lighting, high contrast for mobile viewing.
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
