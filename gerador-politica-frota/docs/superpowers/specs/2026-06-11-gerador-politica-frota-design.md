# Design Spec — Landing Page: Gerador de Política de Frota

**Data:** 2026-06-11  
**Projeto:** Melhoria Gerador de Política de Frota  
**Arquivo de saída:** `index.html` (arquivo único)

---

## 1. Objetivo

Criar uma landing page moderna e sofisticada para o Gerador de Política de Frota da Contele Fleet. O usuário preenche um formulário multi-step e recebe sua política de frota personalizada **gerada instantaneamente na tela**, podendo copiar ou baixar em TXT. O e-mail é coletado como lead.

---

## 2. Stack Tecnológica

- **HTML5** — estrutura semântica
- **Tailwind CSS** — via CDN
- **Font Awesome 6** — via CDN
- **Google Fonts (Montserrat)** — via CDN
- **JavaScript Vanilla** — lógica do formulário, validação e geração do documento

---

## 3. Paleta de Cores

| Elemento | Valor |
|---|---|
| Fundo Hero / Footer | `#080010` |
| Roxo profundo | `#4E0091` |
| Roxo médio | `#6C12B9` |
| Roxo vibrante (CTAs, destaques) | `#8B23E5` |
| Gradiente principal | `135deg, #4E0091 → #8B23E5` |
| Texto em fundo escuro | `#F7F7F7` |
| Texto em fundo claro | `#1E1035` |
| Texto secundário | `#94A3B8` |
| Sucesso / botão download | `#22C55E` |
| Fundo seções claras | `#F7F7F7` |
| Cards | Branco com borda `rgba(139,35,229,0.2)` |
| Grid de fundo | `rgba(139,35,229,0.08)` 60×60px |

**Fonte:** Montserrat — pesos 400, 600, 700, 800

---

## 4. Estrutura da Página

### 4.1 — Hero Section
- Fundo `#080010` com grid roxo sutil
- Badge "100% Gratuito" em verde
- **Headline:** "Crie uma Política de Frota Personalizada para sua Empresa em 5 Minutos"
- **Subheadline:** "Proteja seu patrimônio, reduza multas em até 40% e garanta a conformidade com a LGPD. Gratuito, rápido e pronto para baixar."
- **CTA:** Botão gradiente roxo "Gerar Minha Política Agora" → ancora no formulário (`#form`)
- 3 ícones flutuantes (escudo, velocímetro, documento) em cards com borda roxa

### 4.2 — Benefícios
- Fundo `#F7F7F7`
- 3 cards brancos com borda roxa suave, ícone FA, título e descrição:
  1. **Redução de Custos e Multas** — Regras claras de velocidade e condutores
  2. **Segurança Jurídica** — Proteção contra passivos trabalhistas
  3. **Conformidade LGPD** — Cláusulas de telemetria e rastreamento

### 4.3 — Vídeo
- Fundo escuro `#080010`
- Título contextual acima: "Veja como funciona na prática"
- Embed YouTube: `https://www.youtube.com/watch?v=7jbr0301cE4`
- Player responsivo (aspect-ratio 16/9), centralizado

### 4.4 — Formulário Multi-step
- Fundo `#F7F7F7`
- Card branco centralizado, borda roxa suave, sombra suave
- **Barra de progresso visual** (Step 1/2 → Step 2/2) com roxo vibrante
- **Step 1 — Dados da Empresa:**
  - Razão Social (text, obrigatório)
  - E-mail Corporativo (email, obrigatório — captura de lead)
  - Nome do Gestor (text, obrigatório)
  - Quantidade de Veículos (select: "1 a 10", "11 a 30", "31 a 50", "Mais de 50")
- **Step 2 — Regras Operacionais:**
  - Velocidade Máxima Permitida (number, default: 110)
  - Horários Permitidos (text, default: "07h às 19h")
  - Nível do Tanque na Entrega (select: "100% Cheio", "Mesmo nível da retirada")
  - Restrição Geográfica (text, placeholder: "Ex: Apenas na região metropolitana")
- Botão "Próximo →" no Step 1 (com validação)
- Botão "← Voltar" + "Gerar Minha Política" no Step 2 (com validação)

### 4.5 — Documento Gerado
- Oculto até o clique em "Gerar Minha Política"
- Formulário oculto, documento exibido com transição suave
- Card branco premium com cabeçalho roxo
- Política profissional em português, com variáveis preenchidas:
  - Razão Social, Nome do Gestor, Qtd. de Veículos
  - Velocidade máxima, horário, nível do tanque, restrição geográfica
- Seções do documento:
  1. Apresentação e Objetivo
  2. Abrangência e Condutores Autorizados
  3. Regras de Uso dos Veículos (velocidade, horário, combustível, área geográfica)
  4. Responsabilidades do Condutor
  5. Infrações, Multas e Penalidades
  6. Termo de Consentimento LGPD
  7. Espaço para Assinaturas (Empresa + Colaborador)
- **Botões de ação:**
  - "Copiar Texto" (copia para clipboard, muda ícone para ✓)
  - "Baixar TXT" (gera download direto do arquivo .txt)
  - "Gerar Nova Política" (volta ao formulário)

### 4.6 — Footer
- Fundo `#080010`
- Copyright: "© 2003–2026 Contele Soluções Tecnológicas LTDA — Santos/SP"
- Links: Política de Privacidade (simulada) e Termos de Uso (simulados)

---

## 5. Lógica JavaScript

### Formulário Multi-step
- `showStep(n)` — exibe o step correto, atualiza barra de progresso
- `validateStep(n)` — valida campos do step atual, marca borda vermelha se inválido
- Botão "Próximo" chama `validateStep(1)` antes de avançar
- Botão "Gerar" chama `validateStep(2)` antes de gerar

### Geração do Documento
- `generatePolicy()` — lê todos os campos, monta string do documento
- Renderiza HTML do documento no elemento `#policy-output`
- Faz scroll suave até o documento

### Ações do Documento
- `copyText()` — `navigator.clipboard.writeText()`, feedback visual no botão
- `downloadTXT()` — cria `Blob` com o texto, gera link temporário e clica
- `resetForm()` — limpa campos, volta ao Step 1, oculta documento

---

## 6. Responsividade

- Mobile-first: grid 1 coluna em mobile, 3 colunas em desktop
- Formulário ocupa 100% em mobile, max-w-2xl em desktop
- Vídeo com wrapper `aspect-video` para proporção correta em qualquer tela
- Hero com padding generoso em mobile

---

## 7. Fluxo do Usuário

```
Acessa a página
    → Lê Hero + benefícios + assiste vídeo (opcional)
    → Clica em "Gerar Minha Política Agora"
    → Preenche Step 1 (dados da empresa)
    → Clica "Próximo"
    → Preenche Step 2 (regras operacionais)
    → Clica "Gerar Minha Política"
    → Política renderiza na tela instantaneamente
    → Clica "Baixar TXT" → arquivo baixa direto no computador
```

---

## 8. Arquivo de Saída

`/home/contele/claude code/projetos/fleet/melhoria gerador de politica de frota/index.html`
