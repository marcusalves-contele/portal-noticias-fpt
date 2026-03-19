# Template PodVisitar (Podcast Contele Teams)

## Formato
Podcast com convidados reais (clientes/parceiros). Case de transformacao digital.
Leonardo entrevista empreendedores que implantaram tecnologia na gestao de equipes externas.

## Diferenças vs Template Teams (Lives)
- Badge: "PODVISITAR #XX" (nao "LIVE XXX")
- Background: estudio de podcast (microfones, paineis acusticos) — nao escritorio corporativo
- Tom: storytelling de case real, nao aula/tutorial
- Angulo A sempre foca no RESULTADO do case
- Angulo B sempre foca no PROBLEMA/TENSAO que o convidado enfrentou
- Sem "CONTELE TEAMS" branding na thumb (marca aparece na camiseta do Leo)

## Variáveis
- {EPISODE}: Numero do episodio (01, 02...)
- {TITLE_A}: Titulo angulo A (resultado)
- {SUBTITLE_A}: Subtitulo angulo A
- {TITLE_B}: Titulo angulo B (tensao)
- {SUBTITLE_B}: Subtitulo angulo B
- {EXPRESSION_A}: Expressao Leo angulo A (assertivo, confiante, sorrindo, empolgado)
- {EXPRESSION_B}: Expressao Leo angulo B (surpreso, serio, negativo)
- {ELEMENTS_3D_A}: Elementos 3D angulo A
- {ELEMENTS_3D_B}: Elementos 3D angulo B
- {GUEST_NAME}: Nome do convidado (se tiver foto)

## Prompt Base — Angulo A (Resultado)

```
Create a YouTube thumbnail in 16:9 aspect ratio for a B2B team management podcast channel.

CRITICAL - FACE REFERENCE IMAGES:
- Image 1: LEONARDO POSE/EXPRESSION reference — COPY THIS EXACT POSE AND EXPRESSION ({EXPRESSION_A}). The body language, hand position, and facial expression in Image 1 is what you MUST reproduce.
- Image 2: LEONARDO FACE IDENTITY reference — use this to confirm facial features (face shape, hair, skin). But the EXPRESSION and POSE must come from Image 1, NOT Image 2.

LEONARDO (HOST) - COPY THE FACE FROM REFERENCE PHOTOS EXACTLY:
- Oval face, clear smooth skin
- Medium brown hair, well-groomed
- Expressive brown eyes, NO glasses
- Age: 35-38, youthful friendly appearance
- Wearing BLACK Contele branded t-shirt (plain black tee)
- RIGHT SIDE of frame, medium shot (chest up)
- Expression: {EXPRESSION_A}
- The face MUST be recognizable as the same person from the reference photos

SKIN TEXTURE - CRITICAL:
- Keep skin SMOOTH and NATURAL
- Do NOT add wrinkles
- Youthful, healthy appearance

COMPOSITION:
- Leonardo on RIGHT SIDE
- LEFT SIDE: large bold text
- Background: modern podcast studio with professional microphones, acoustic panels, warm purple/magenta ambient lighting. Premium feel.
- Subtle depth of field blur on background

3D ELEMENTS (subtle, max 2 items, small, not competing with face):
- {ELEMENTS_3D_A}

TEXT ELEMENTS:
- TOP LEFT: Small badge "PODVISITAR #{EPISODE}" in purple pill/rounded rectangle
- MAIN TITLE: "{TITLE_A}" very large white bold text with strong drop shadow, positioned left side
- SUBTITLE: "{SUBTITLE_A}" medium golden/amber text below title, with subtle glow
- Do NOT add "LIVE" badge

COLOR PALETTE:
- Dominant: deep purple (#4E0091) and magenta (#8B23E5) ambient lighting
- Accent: golden/amber for subtitle (achievement, result)
- Text: crisp white with strong shadow for readability
- Background: dark purple gradient with warm studio lighting

LIGHTING:
- Warm purple/magenta side lighting from left
- Soft golden accent light from right on Leonardo's face
- Premium podcast studio atmosphere

STYLE: Professional YouTube thumbnail, photorealistic, purple/magenta premium lighting, high contrast. PODCAST thumbnail, not a live stream.
```

## Prompt Base — Angulo B (Tensao/Problema)

```
Create a YouTube thumbnail in 16:9 aspect ratio for a B2B team management podcast channel.

CRITICAL - FACE REFERENCE IMAGES:
- Image 1: LEONARDO POSE/EXPRESSION reference — COPY THIS EXACT POSE AND EXPRESSION ({EXPRESSION_B}). The body language, hand position, and facial expression in Image 1 is what you MUST reproduce.
- Image 2: LEONARDO FACE IDENTITY reference — use this to confirm facial features (face shape, hair, skin). But the EXPRESSION and POSE must come from Image 1, NOT Image 2.

LEONARDO (HOST) - COPY THE FACE FROM REFERENCE PHOTOS EXACTLY:
- Oval face, clear smooth skin
- Medium brown hair, well-groomed
- Expressive brown eyes, NO glasses
- Age: 35-38, youthful appearance
- Wearing BLACK Contele branded t-shirt (plain black tee)
- CENTER-RIGHT of frame, medium shot (chest up)
- Expression: {EXPRESSION_B}
- The face MUST be recognizable as the same person from the reference photos

SKIN TEXTURE - CRITICAL:
- Keep skin SMOOTH and NATURAL
- Do NOT add wrinkles
- Youthful, healthy appearance

COMPOSITION:
- Leonardo CENTER-RIGHT, expressing shock/concern
- LEFT SIDE: large bold text creating tension
- Background: chaotic environment representing the problem — papers flying, stacked folders, red/orange warning lighting creating urgency and alarm.
- Dramatic depth of field, chaos in background, Leonardo sharp in foreground

3D ELEMENTS (subtle, max 2 items, reinforcing chaos/problem):
- {ELEMENTS_3D_B}

TEXT ELEMENTS:
- TOP LEFT: Small badge "PODVISITAR #{EPISODE}" in red pill/rounded rectangle
- MAIN TITLE: "{TITLE_B}" very large white bold text with strong red drop shadow, positioned left side
- SUBTITLE: "{SUBTITLE_B}" medium red/crimson text below title
- Do NOT add "LIVE" badge

COLOR PALETTE:
- Dominant: dark charcoal (#1a1a2e) with deep red (#8B0000) and orange (#FF4500) alarm lighting
- Accent: crimson red for subtitle (danger, urgency)
- Text: crisp white with red-tinted shadow
- Background: dark with scattered red/orange light beams suggesting chaos

LIGHTING:
- Dramatic red/orange side lighting from left (alarm, warning)
- Cool blue backlight creating tension contrast
- Cinematic urgency atmosphere

STYLE: Professional YouTube thumbnail, photorealistic, red/orange dramatic alarm lighting, very high contrast. PODCAST thumbnail about a near-disaster business story.
```

## Estrategia A/B por Episodio

| Angulo | Foco | Paleta | Expressao Leo | Exemplo |
|--------|------|--------|---------------|---------|
| A | Resultado/conquista do case | Roxo + dourado | assertivo, confiante, empolgado | "400 CLIENTES SALVOS / EM 15 DIAS" |
| B | Problema/tensao do case | Vermelho + alarme | surpreso, serio, chocado | "QUASE PERDEU TUDO / POR CAUSA DO WHATSAPP" |

## Refs Leo por Expressao (selecao automatica)

| Expressao | Image 1 (pose) | Image 2 (face) |
|-----------|----------------|----------------|
| assertivo | leo-camiseta-preta-contele-dedo-para-cima.jpg | leo-ref-primary.png |
| confiante | leo-camiseta-preta-contele-punho-levantado.jpg | leo-ref-primary.png |
| sorrindo | leo-camiseta-preta-contele-sorrindo-frontal.jpg | leo-ref-primary.png |
| empolgado | leo-camiseta-preta-contele-punho-levantado.jpg | leo-ref-primary.png |
| surpreso | leo-camiseta-preta-contele-maos-cabeca-surpreso.jpg | leo-ref-primary.png |
| serio | leo-camiseta-preta-contele-perfil-3-4.jpg | leo-ref-primary.png |
| negativo | leo-camiseta-preta-contele-polegar-baixo.jpg | leo-ref-primary.png |

## Checklist por Episodio

- [ ] Transcrever/extrair transcricao do podcast
- [ ] Responder Q1 (publico), Q2 (objetivo), Q3 (conteudo)
- [ ] Definir titulo A (resultado) e titulo B (tensao) com max 5 palavras
- [ ] Escolher expressao Leo para A e para B (diferentes!)
- [ ] Definir 2 elementos 3D por angulo (relacionados ao case)
- [ ] Gerar A e B em paralelo
- [ ] Apresentar par A/B → escolher finalista

## Historico

| Ep | Convidado | Titulo A | Titulo B | Escolhido |
|----|-----------|----------|----------|-----------|
| 01 | Fabio (Allerta) | 400 CLIENTES SALVOS / EM 15 DIAS | QUASE PERDEU TUDO / POR CAUSA DO WHATSAPP | pendente |
