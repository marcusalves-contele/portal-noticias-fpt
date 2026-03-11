# Agent: PRISM Smart Reference Photo Selection

Resolve GitHub Issue #2: IA escolher melhores fotos de referencia por contexto (nao apenas primary).

## Contexto

O sistema SEMPRE usa `ref-primary` (foto neutra/frontal) como ancora facial. O `EXPR_MAP` em `get_host_refs()` tenta selecionar pose por keyword, mas:

1. A primary SEMPRE vai como Image 2, dominando a expressao final
2. Roupas nao sao consideradas (blazer vs polo vs navy)
3. So 2 fotos sao usadas, mesmo tendo 16 disponíveis

### Fotos Julio (Fleet) disponiveis

```
julio-polo-preta-bracos-cruzados.jpg      # pose: bracos cruzados, roupa: polo preta
julio-polo-preta-com-celular.jpg           # pose: segurando celular, roupa: polo preta
julio-polo-preta-dedo-para-cima.jpg        # pose: dedo pra cima, roupa: polo preta
julio-polo-preta-frontal-neutro.jpg        # pose: frontal neutro, roupa: polo preta
julio-polo-preta-gesto-explicando.jpg      # pose: explicando, roupa: polo preta
julio-polo-preta-mao-aberta-atencao.jpg    # pose: mao aberta, roupa: polo preta
julio-polo-preta-pensativo-mao-queixo.jpg  # pose: pensativo, roupa: polo preta
julio-polo-preta-perfil-3-4.jpg            # pose: perfil 3/4, roupa: polo preta
julio-polo-preta-sorrindo-maos-cintura.jpg # pose: sorrindo, roupa: polo preta
julio-polo-preta-surpreso.jpg              # pose: surpreso, roupa: polo preta
julio-ref-primary-1.jpg                    # ancora facial principal
julio_gray_blazzer.png                     # roupa: blazer cinza (autoridade)
julio_polo_navy.png                        # roupa: polo azul marinho
julio_polo_white.png                       # roupa: polo branca
```

E equivalente para Leonardo (Teams) em `referencias/leonardo/`.

## Arquivos

- `prism-os/nutella-creator/thumb_live.py`: `get_host_refs()`, `generate_angles()`, `generate_one_thumb()`
- `prism-os/thumbnail-ai-creator/referencias/julio/`: fotos Julio
- `prism-os/thumbnail-ai-creator/referencias/leonardo/`: fotos Leonardo
- Novo: `prism-os/thumbnail-ai-creator/referencias/catalogo.json`

## O que fazer

### 1. Criar catalogo de fotos (catalogo.json)

```json
{
  "julio": [
    {
      "file": "julio-polo-preta-bracos-cruzados.jpg",
      "pose": "bracos cruzados",
      "expressao": "confiante, assertivo, serio",
      "roupa": "polo preta",
      "angulo": "frontal",
      "contexto_ideal": "autoridade, confronto, desafio"
    },
    {
      "file": "julio_gray_blazzer.png",
      "pose": "frontal",
      "expressao": "neutro, profissional",
      "roupa": "blazer cinza",
      "angulo": "frontal",
      "contexto_ideal": "autoridade, institucional, evento, palestra"
    }
    // ... todas as 16
  ],
  "leonardo": [ ... ]
}
```

### 2. Nova funcao: `select_best_refs()`

Adicionar em `thumb_live.py` uma funcao que:

1. Recebe: `channel`, `angle_data` (titulo, expressao, background, cor_dominante), `briefing` (q1/q2/q3 + script)
2. Carrega catalogo.json
3. Chama Gemini Flash com prompt:

```
Voce e diretor de fotografia escolhendo fotos de referencia para uma thumbnail YouTube.

CONTEXTO DO VIDEO:
{briefing resumido}

ANGULO CRIATIVO:
- Titulo: {titulo}
- Expressao pedida: {expressao_host}
- Background: {background}
- Iluminacao: {iluminacao}
- Tom: {cor_dominante}

CATALOGO DE FOTOS DISPONÍVEIS:
{catalogo formatado}

Escolha EXATAMENTE 2 fotos, em ordem de prioridade:
1. FOTO PRINCIPAL (Image 1): a que melhor representa a pose, expressao e roupa para este angulo
2. FOTO ANCORA (Image 2): a que garante reconhecimento facial (pode ser a primary OU outra frontal)

REGRAS:
- Se a expressao pedida tem foto perfeita, use-a como Image 1
- Considere a ROUPA: blazer para autoridade, polo preta para dia-a-dia, branca para leveza
- A primary so e necessaria como Image 2 se a Image 1 for muito diferente (perfil, angulo lateral)
- Se Image 1 ja e frontal e bem iluminada, pode repetir a mesma como Image 2

Retorne JSON: {"image_1": "filename.jpg", "image_2": "filename.jpg", "reasoning": "1 frase"}
```

4. Retorna lista de Paths

### 3. Integrar no fluxo existente

Em `generate_angles()` e `regenerate_single()`:
- Apos obter `angle_a` e `angle_b` do Gemini, chamar `select_best_refs()` para cada angulo
- Substituir chamada atual de `get_host_refs(channel, expressao=expr)` por resultado da selecao inteligente
- Manter `get_host_refs()` como FALLBACK caso `select_best_refs()` falhe

### 4. NAO alterar

- Frontend (HTML/JS): nao precisa mudar, selecao e transparente
- Endpoints da API: nao mudam
- Estrutura de pastas de referencias: nao muda

## Validacao

1. Criar `catalogo.json` com TODAS as fotos de julio/ e leonardo/
2. Rodar dashboard, gerar thumb para video com tom "alarmista" (ex: diesel)
   - Verificar nos logs quais fotos foram selecionadas
   - Esperar: foto com expressao "surpreso" ou "preocupado", NAO a primary neutra
3. Gerar thumb para video com tom "autoridade" (ex: palestra, politica de frota)
   - Esperar: blazer cinza ou bracos cruzados
4. Gerar com divergencia alta (8+)
   - Angulo A e B devem usar fotos DIFERENTES entre si
5. Testar fallback: renomear catalogo.json temporariamente
   - Sistema deve usar `get_host_refs()` antigo sem quebrar

## Criterios de aceite

- [ ] catalogo.json criado com metadados de todas as fotos (julio + leonardo)
- [ ] `select_best_refs()` funciona e retorna fotos coerentes com o tom do angulo
- [ ] Angulos A e B podem usar fotos diferentes entre si
- [ ] Roupa e considerada (blazer para autoridade, polo para casual)
- [ ] Primary NAO e obrigatoria em todos os casos
- [ ] Fallback para `get_host_refs()` funciona se catalogo falhar
- [ ] Logs mostram qual foto foi selecionada e por que
