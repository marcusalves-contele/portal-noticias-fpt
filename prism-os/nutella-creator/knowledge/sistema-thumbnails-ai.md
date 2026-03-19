# Sistema de Thumbnails AI (Nano Banana Pro)

## Visão Geral

Sistema de geração automatizada de thumbnails para os canais da Contele no YouTube usando IA. Desenvolvido em janeiro/2026 após extensa fase de testes.

**Nome interno**: Nano Banana Pro
**Repositório**: `growth-contele/thumbnail-ai-creator`

---

## Modelo e API

### Especificações Técnicas

- **API**: Google Gemini 3 Pro Image Preview
- **Model ID**: `gemini-3-pro-image-preview`
- **Capability**: Text-to-Image + Reference Images
- **Output**: 16:9 aspect ratio (YouTube standard)

### Configuração Crítica

```python
"generationConfig": {
    "responseModalities": ["IMAGE"],
    "imageConfig": {"aspectRatio": "16:9"},
    "temperature": 0  # OBRIGATÓRIO para consistência facial
}
```

**⚠️ IMPORTANTE**: `temperature=0` é essencial para reduzir variação facial e manter consistência com as referências.

---

## Aprendizados de Testes (Jan/2026)

### ✅ O que FUNCIONA

1. **Temperature = 0**
   - Reduz drasticamente a variação facial entre gerações
   - Mantém características mais próximas às referências
   - Essencial para reconhecimento dos apresentadores

2. **Prompts Detalhados**
   - Descrições minuciosas funcionam melhor que instruções curtas
   - Incluir: pose, expressão, roupa, background, cores, tipografia
   - Template estruturado aumenta consistência

3. **Refs na Orientação Original**
   - Usar imagens de referência sem rotação/edição prévia
   - Modelo interpreta melhor poses e ângulos originais
   - Não tentar "corrigir" orientação das fotos

4. **Gerar 3+ Variações**
   - Sempre gerar múltiplas opções (mínimo 3)
   - Escolher a melhor semelhança facial manualmente
   - Determinismo não é 100% garantido

5. **Camisa LISA no Prompt**
   - Especificar "camisa social lisa azul escuro" ou cor específica
   - Evitar mencionar logos/marcas (modelo inventa detalhes)
   - Simplicidade é melhor

### ❌ O que NÃO Funciona

1. **Rotacionar Imagens de Referência**
   - Piora a interpretação facial pelo modelo
   - Usar sempre orientação original da foto

2. **Prompts Curtos**
   - "Copy face exactly" não funciona bem
   - Falta de contexto gera resultados inconsistentes

3. **Pedir "Variações de Design"**
   - Gera collages ou múltiplas versões na mesma imagem
   - Manter prompt focado em UMA composição

4. **Seed Parameter**
   - Não garante determinismo total
   - Mesmo seed pode gerar rostos diferentes
   - Depender de múltiplas gerações + seleção manual

---

## Apresentadores e Referências

### Fleet (Frota)

**Apresentador**: Julio César
**Pasta de Refs**: `referencias/julio/`

Arquivos:
- `julio-ref-01.JPEG`
- `julio-ref-02.JPEG`
- `julio-ref-1.png`
- `julio-ref-2.png`

**Estilo**: `referencias/estilo_thumb_julio_fleet.jpg`

### Teams (Equipes)

**Apresentador**: Leonardo
**Pasta de Refs**: `referencias/leonardo/`

Arquivos:
- `leonardo.jpg`

**Estilo**: `referencias/estilo_thumb_leonardo_teams.jpg`

---

## Resultados de Testes

### Exemplos Bem-Sucedidos (Jan/2026)

Pasta: `referencias/resultados/`

1. **julio_v2_solo.png**
   - Julio solo, fundo amarelo vibrante
   - Boa semelhança facial

2. **julio_v4_convidado_cnh.png**
   - Julio + convidado (advogado)
   - Tema: CNH suspensa
   - Composição lado a lado

3. **leonardo_v5_final.png**
   - Leonardo solo, fundo azul tecnológico
   - Melhor resultado após 5 iterações

---

## Workflow de Produção

### 1. Briefing Inicial

Marketing/Produto solicita thumbnail com:
- **Canal**: Fleet ou Teams
- **Número do episódio**: Ex: #47
- **Título do vídeo**: Texto exato
- **Tema principal**: Resumo em 1-2 linhas
- **Convidado**: Nome + contexto (se aplicável)

### 2. Preparação

- Identificar apresentador e carregar referências
- Carregar estilo de referência do canal
- Escolher template de prompt apropriado

### 3. Geração

```python
# Gerar 3 variações mínimo
for i in range(3):
    response = generate_thumbnail(
        prompt=final_prompt,
        references=[ref1, ref2, style_ref],
        temperature=0
    )
    save_image(f"output/thumb_v{i+1}.png")
```

### 4. Seleção

- Avaliar manualmente as 3+ opções
- Critérios:
  - Semelhança facial (prioridade 1)
  - Composição e legibilidade
  - Aderência ao tema
- Escolher melhor e enviar para aprovação

### 5. Iteração (se necessário)

- Ajustar prompt baseado em feedback
- Regerar com modificações específicas
- Repetir até aprovação

---

## Templates de Prompts

### Localização

Pasta: `prompts/`

Arquivos:
- `template_fleet.md` - Template para Fleet
- `template_teams.md` - Template para Teams
- `julio_fleet_final.md` - Exemplo final validado

### Estrutura Padrão

```markdown
Create a YouTube thumbnail in 16:9 aspect ratio for [CANAL] channel.

SUBJECT:
- Main presenter: [NOME] (use reference images)
- [Descrição física: pose, expressão, roupa]
- [Convidado: se aplicável]

DESIGN:
- Background: [cor, gradiente, elementos]
- Typography: [título, posicionamento, estilo]
- Style: [energético/profissional/tecnológico]

REFERENCES:
[Descrição das imagens de referência anexadas]
```

---

## Repositório GitHub

**Repo**: `growth-contele/thumbnail-ai-creator`

### Estrutura

```
thumbnail-ai-creator/
├── prompts/              # Templates de prompt
├── referencias/          # Fotos dos apresentadores
│   ├── julio/
│   ├── leonardo/
│   └── resultados/       # Melhores outputs
├── output/               # Gerações (gitignored)
├── generate.py           # Script principal
└── README.md
```

### Dependências

- Google Generative AI SDK
- Python 3.8+
- API Key do Gemini (env var)

---

## Próximos Passos

### Melhorias Planejadas

1. **Script de Automação**
   - CLI interativo para coletar briefing
   - Geração automática de 3 variações
   - Preview lado a lado

2. **Fine-tuning de Prompts**
   - Testar variações de descrição física
   - Otimizar para diferentes temas (técnico vs. comercial)

3. **Banco de Estilos**
   - Categorizar temas recorrentes
   - Criar prompts especializados por categoria

4. **Integração com Workflow**
   - Notificação automática quando vídeo entra em edição
   - Upload direto para YouTube (draft)

---

## Contatos

**Owner**: Marco Fassa (CTO)
**Stakeholders**: Marketing, Produto
**Repo**: github.com/growth-contele/thumbnail-ai-creator

---

**Última atualização**: 2026-01-30
**Status**: ✅ Operacional (testado e validado)
