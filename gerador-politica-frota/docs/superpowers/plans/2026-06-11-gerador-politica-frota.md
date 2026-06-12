# Gerador de Política de Frota — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um arquivo `index.html` completo com landing page moderna (paleta roxa escura), formulário multi-step e geração instantânea de política de frota personalizda com download em TXT.

**Architecture:** Arquivo único `index.html`. Tailwind CSS via CDN para layout e utilidades. CSS customizado inline para efeitos visuais (grid de fundo, glassmorphism, animações). JavaScript vanilla para controle multi-step, validação, geração do documento e ações de clipboard/download.

**Tech Stack:** HTML5 semântico, Tailwind CSS CDN, Font Awesome 6 CDN, Google Fonts (Montserrat), JavaScript Vanilla ES6+.

---

## Arquivo de Saída

`/home/contele/claude code/projetos/fleet/melhoria gerador de politica de frota/index.html`

---

### Task 1: Estrutura base do HTML, CDNs e estilos globais

**Files:**
- Create: `index.html`

- [ ] **Step 1: Criar o arquivo com `<head>` completo**

Crie `index.html` com o seguinte conteúdo:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Gerador de Política de Frota Gratuito — Contele Fleet</title>
  <meta name="description" content="Crie sua Política de Frota personalizada em minutos. Gratuito, rápido e pronto para baixar. Proteja sua empresa e reduza multas." />

  <!-- Google Fonts: Montserrat -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet" />

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Font Awesome 6 CDN -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />

  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            'purple-deep':   '#080010',
            'purple-900':    '#4E0091',
            'purple-700':    '#6C12B9',
            'purple-500':    '#8B23E5',
            'purple-light':  '#b56fff',
          },
          fontFamily: {
            sans: ['Montserrat', 'sans-serif'],
          },
        }
      }
    }
  </script>

  <style>
    * { font-family: 'Montserrat', sans-serif; }

    /* Grid de fundo roxo sutil */
    .bg-grid {
      background-color: #080010;
      background-image:
        linear-gradient(rgba(139,35,229,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(139,35,229,0.08) 1px, transparent 1px);
      background-size: 60px 60px;
    }

    /* Gradiente principal */
    .gradient-purple {
      background: linear-gradient(135deg, #4E0091, #8B23E5);
    }

    /* Glow roxo em botões */
    .btn-glow:hover {
      box-shadow: 0 0 24px rgba(139,35,229,0.6);
    }

    /* Barra de progresso animada */
    .progress-bar {
      transition: width 0.4s ease;
    }

    /* Card borda roxa */
    .card-purple {
      border: 1px solid rgba(139,35,229,0.2);
      box-shadow: 0 4px 24px rgba(139,35,229,0.08);
    }

    /* Campo inválido */
    .field-error {
      border-color: #ef4444 !important;
    }

    /* Scrollbar roxa */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #080010; }
    ::-webkit-scrollbar-thumb { background: #6C12B9; border-radius: 3px; }

    /* Transição suave entre seções */
    .section-fade {
      animation: fadeIn 0.5s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* Iframe responsivo */
    .video-wrapper {
      position: relative;
      padding-bottom: 56.25%;
      height: 0;
      overflow: hidden;
    }
    .video-wrapper iframe {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      border-radius: 12px;
    }
  </style>
</head>
<body class="bg-gray-50 text-gray-900">
  <!-- Seções serão inseridas nos próximos tasks -->
</body>
</html>
```

- [ ] **Step 2: Verificar abertura no navegador**

Abra `index.html` no navegador. Esperado: página em branco sem erros no console. Confirme que o Tailwind e Font Awesome carregaram na aba Network.

- [ ] **Step 3: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/melhoria gerador de politica de frota"
git init
git add index.html
git commit -m "feat: estrutura base HTML com CDNs e estilos globais"
```

---

### Task 2: Hero Section

**Files:**
- Modify: `index.html` — substituir `<body>` pelo conteúdo com Hero completo

- [ ] **Step 1: Adicionar Hero Section dentro do `<body>`**

Substitua o comentário dentro do `<body>` por:

```html
  <!-- ===== HERO ===== -->
  <section class="bg-grid min-h-screen flex flex-col justify-center items-center text-center px-4 py-20 relative overflow-hidden">

    <!-- Glow decorativo de fundo -->
    <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full opacity-20 blur-3xl pointer-events-none"
         style="background: radial-gradient(circle, #8B23E5, transparent 70%);"></div>

    <!-- Badge -->
    <span class="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/30 text-green-400 text-sm font-600 px-4 py-1.5 rounded-full mb-6">
      <i class="fa-solid fa-check-circle"></i> 100% Gratuito
    </span>

    <!-- Headline -->
    <h1 class="text-3xl md:text-5xl lg:text-6xl font-extrabold text-white leading-tight max-w-4xl mb-6">
      Crie uma <span style="background: linear-gradient(135deg, #b56fff, #8B23E5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Política de Frota</span><br />
      Personalizada em 5 Minutos
    </h1>

    <!-- Subheadline -->
    <p class="text-gray-400 text-lg md:text-xl max-w-2xl mb-10 leading-relaxed">
      Proteja seu patrimônio, reduza multas em até <strong class="text-white">40%</strong> e garanta a conformidade com a LGPD.
      Gratuito, rápido e pronto para baixar.
    </p>

    <!-- CTA -->
    <a href="#form"
       class="gradient-purple btn-glow text-white font-bold text-lg px-10 py-4 rounded-xl transition-all duration-300 hover:scale-105 inline-flex items-center gap-3 mb-16">
      <i class="fa-solid fa-bolt"></i>
      Gerar Minha Política Agora
    </a>

    <!-- 3 ícones flutuantes -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full">
      <div class="card-purple bg-white/5 backdrop-blur-sm rounded-xl p-4 flex flex-col items-center gap-2">
        <div class="w-12 h-12 gradient-purple rounded-lg flex items-center justify-center">
          <i class="fa-solid fa-shield-halved text-white text-xl"></i>
        </div>
        <span class="text-white text-sm font-semibold">Segurança Jurídica</span>
      </div>
      <div class="card-purple bg-white/5 backdrop-blur-sm rounded-xl p-4 flex flex-col items-center gap-2">
        <div class="w-12 h-12 gradient-purple rounded-lg flex items-center justify-center">
          <i class="fa-solid fa-gauge-high text-white text-xl"></i>
        </div>
        <span class="text-white text-sm font-semibold">Controle de Velocidade</span>
      </div>
      <div class="card-purple bg-white/5 backdrop-blur-sm rounded-xl p-4 flex flex-col items-center gap-2">
        <div class="w-12 h-12 gradient-purple rounded-lg flex items-center justify-center">
          <i class="fa-solid fa-file-contract text-white text-xl"></i>
        </div>
        <span class="text-white text-sm font-semibold">Documento Pronto</span>
      </div>
    </div>

  </section>
```

- [ ] **Step 2: Verificar Hero no navegador**

Abra `index.html`. Esperado: seção hero com fundo escuro, grid roxo, headline em branco com degradê roxo, badge verde, botão roxo e 3 cards de ícones. Verificar responsividade redimensionando a janela.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar hero section com headline, CTA e cards de ícones"
```

---

### Task 3: Seção de Benefícios

**Files:**
- Modify: `index.html` — adicionar seção após o Hero

- [ ] **Step 1: Adicionar seção de benefícios após a tag `</section>` do Hero**

```html
  <!-- ===== BENEFÍCIOS ===== -->
  <section class="bg-gray-50 py-20 px-4">
    <div class="max-w-5xl mx-auto">

      <div class="text-center mb-12">
        <span class="text-purple-500 font-semibold text-sm uppercase tracking-widest">Por que você precisa disso</span>
        <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900 mt-2">
          O que uma Política de Frota resolve
        </h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

        <!-- Card 1 -->
        <div class="card-purple bg-white rounded-2xl p-8 flex flex-col gap-4 hover:shadow-lg transition-shadow duration-300">
          <div class="w-14 h-14 gradient-purple rounded-xl flex items-center justify-center mb-2">
            <i class="fa-solid fa-circle-dollar-to-slot text-white text-2xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-900">Redução de Custos e Multas</h3>
          <p class="text-gray-500 leading-relaxed">
            Regras claras de velocidade máxima e condutores autorizados eliminam infrações e reduzem o desgaste prematuro dos veículos.
          </p>
        </div>

        <!-- Card 2 -->
        <div class="card-purple bg-white rounded-2xl p-8 flex flex-col gap-4 hover:shadow-lg transition-shadow duration-300">
          <div class="w-14 h-14 gradient-purple rounded-xl flex items-center justify-center mb-2">
            <i class="fa-solid fa-scale-balanced text-white text-2xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-900">Segurança Jurídica</h3>
          <p class="text-gray-500 leading-relaxed">
            Documente responsabilidades e proteja a empresa contra passivos trabalhistas. Com assinatura do colaborador, a empresa fica blindada.
          </p>
        </div>

        <!-- Card 3 -->
        <div class="card-purple bg-white rounded-2xl p-8 flex flex-col gap-4 hover:shadow-lg transition-shadow duration-300">
          <div class="w-14 h-14 gradient-purple rounded-xl flex items-center justify-center mb-2">
            <i class="fa-solid fa-lock text-white text-2xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-900">Conformidade com LGPD</h3>
          <p class="text-gray-500 leading-relaxed">
            Inclua cláusulas de telemetria e rastreamento veicular com consentimento documentado, evitando sanções da ANPD.
          </p>
        </div>

      </div>
    </div>
  </section>
```

- [ ] **Step 2: Verificar benefícios no navegador**

Esperado: 3 cards brancos com ícone roxo, título e descrição. Em mobile, empilhados. Em desktop, lado a lado.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar seção de benefícios com 3 cards"
```

---

### Task 4: Seção de Vídeo

**Files:**
- Modify: `index.html` — adicionar seção de vídeo após Benefícios

- [ ] **Step 1: Adicionar seção de vídeo após a seção de benefícios**

```html
  <!-- ===== VÍDEO ===== -->
  <section class="bg-grid py-20 px-4">
    <div class="max-w-4xl mx-auto text-center">

      <span class="text-purple-light font-semibold text-sm uppercase tracking-widest">Veja na prática</span>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mt-2 mb-10">
        Como funciona o Gerador de Política de Frota
      </h2>

      <div class="video-wrapper card-purple rounded-xl overflow-hidden">
        <iframe
          src="https://www.youtube.com/embed/7jbr0301cE4"
          title="Gerador de Política de Frota — Contele Fleet"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen>
        </iframe>
      </div>

    </div>
  </section>
```

- [ ] **Step 2: Verificar vídeo no navegador**

Esperado: vídeo do YouTube embutido, responsivo (proporção 16:9 mantida), fundo escuro com grid roxo ao redor.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar seção de vídeo com embed YouTube responsivo"
```

---

### Task 5: Formulário Multi-step (HTML)

**Files:**
- Modify: `index.html` — adicionar formulário multi-step após Vídeo

- [ ] **Step 1: Adicionar seção do formulário após a seção de vídeo**

```html
  <!-- ===== FORMULÁRIO ===== -->
  <section id="form" class="bg-gray-50 py-20 px-4">
    <div class="max-w-2xl mx-auto">

      <div class="text-center mb-10">
        <span class="text-purple-500 font-semibold text-sm uppercase tracking-widest">É grátis e leva 2 minutos</span>
        <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900 mt-2">
          Gere sua Política Agora
        </h2>
        <p class="text-gray-500 mt-3">Preencha os campos abaixo e receba o documento pronto na tela.</p>
      </div>

      <!-- Card do formulário -->
      <div class="card-purple bg-white rounded-2xl p-8 md:p-10">

        <!-- Barra de progresso -->
        <div class="mb-8">
          <div class="flex justify-between text-sm font-semibold mb-2">
            <span id="step-label" class="text-purple-500">Passo 1 de 2 — Dados da Empresa</span>
            <span id="step-percent" class="text-gray-400">50%</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div id="progress-bar" class="gradient-purple h-2 rounded-full progress-bar" style="width: 50%"></div>
          </div>
        </div>

        <!-- STEP 1: Dados da Empresa -->
        <div id="step-1" class="section-fade">
          <div class="grid grid-cols-1 gap-5">

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Razão Social da Empresa <span class="text-red-500">*</span></label>
              <input id="razao-social" type="text" placeholder="Ex: Transportes Silva Ltda"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">E-mail Corporativo <span class="text-red-500">*</span></label>
              <input id="email" type="email" placeholder="contato@suaempresa.com.br"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Nome do Gestor Responsável <span class="text-red-500">*</span></label>
              <input id="gestor" type="text" placeholder="Ex: João da Silva"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Quantidade de Veículos na Frota <span class="text-red-500">*</span></label>
              <select id="qtd-veiculos"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors bg-white">
                <option value="">Selecione...</option>
                <option value="1 a 10 veículos">1 a 10 veículos</option>
                <option value="11 a 30 veículos">11 a 30 veículos</option>
                <option value="31 a 50 veículos">31 a 50 veículos</option>
                <option value="Mais de 50 veículos">Mais de 50 veículos</option>
              </select>
            </div>

          </div>

          <button onclick="nextStep()"
            class="mt-8 w-full gradient-purple btn-glow text-white font-bold py-4 rounded-xl transition-all duration-300 hover:scale-105 flex items-center justify-center gap-2">
            Próximo <i class="fa-solid fa-arrow-right"></i>
          </button>
        </div>

        <!-- STEP 2: Regras Operacionais -->
        <div id="step-2" class="section-fade hidden">
          <div class="grid grid-cols-1 gap-5">

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Velocidade Máxima Permitida (km/h) <span class="text-red-500">*</span></label>
              <input id="velocidade" type="number" value="110" min="40" max="200"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Horários Permitidos de Uso <span class="text-red-500">*</span></label>
              <input id="horario" type="text" value="07h às 19h"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Nível do Tanque na Devolução <span class="text-red-500">*</span></label>
              <select id="tanque"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors bg-white">
                <option value="">Selecione...</option>
                <option value="100% cheio (tanque completo)">100% cheio (tanque completo)</option>
                <option value="no mesmo nível em que foi retirado">No mesmo nível em que foi retirado</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1">Restrição Geográfica</label>
              <input id="restricao" type="text" placeholder="Ex: Apenas na região metropolitana de São Paulo"
                class="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-purple-500 transition-colors" />
              <p class="text-xs text-gray-400 mt-1">Opcional. Deixe em branco se não houver restrição.</p>
            </div>

          </div>

          <div class="flex gap-3 mt-8">
            <button onclick="prevStep()"
              class="flex-1 border-2 border-purple-500 text-purple-500 font-bold py-4 rounded-xl transition-all duration-300 hover:bg-purple-50 flex items-center justify-center gap-2">
              <i class="fa-solid fa-arrow-left"></i> Voltar
            </button>
            <button onclick="generatePolicy()"
              class="flex-2 gradient-purple btn-glow text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 hover:scale-105 flex items-center justify-center gap-2 flex-grow">
              <i class="fa-solid fa-file-circle-check"></i> Gerar Minha Política
            </button>
          </div>
        </div>

      </div>
    </div>
  </section>
```

- [ ] **Step 2: Verificar formulário no navegador**

Esperado: card branco centralizado, barra de progresso a 50%, Step 1 visível com 4 campos. Clicar em "Próximo" sem preencher não deve avançar (JS ainda não implementado — ok por ora).

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar formulário multi-step com campos step 1 e step 2"
```

---

### Task 6: Seção do Documento Gerado (HTML)

**Files:**
- Modify: `index.html` — adicionar seção de output após o formulário

- [ ] **Step 1: Adicionar seção do documento após a seção `#form`**

```html
  <!-- ===== DOCUMENTO GERADO ===== -->
  <section id="policy-section" class="bg-gray-50 py-10 px-4 hidden">
    <div class="max-w-3xl mx-auto">

      <!-- Botões de ação -->
      <div class="flex flex-wrap gap-3 mb-6 justify-center">
        <button onclick="copyText()"
          id="btn-copy"
          class="inline-flex items-center gap-2 border-2 border-purple-500 text-purple-500 font-bold px-6 py-3 rounded-xl transition-all duration-300 hover:bg-purple-50">
          <i class="fa-solid fa-copy"></i> Copiar Texto
        </button>
        <button onclick="downloadTXT()"
          class="inline-flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white font-bold px-6 py-3 rounded-xl transition-all duration-300 hover:scale-105">
          <i class="fa-solid fa-download"></i> Baixar TXT
        </button>
        <button onclick="resetForm()"
          class="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 font-semibold px-6 py-3 rounded-xl border border-gray-200 hover:border-gray-300 transition-all duration-300">
          <i class="fa-solid fa-rotate-left"></i> Gerar Nova Política
        </button>
      </div>

      <!-- Card do documento -->
      <div class="bg-white rounded-2xl card-purple overflow-hidden section-fade">

        <!-- Cabeçalho do documento -->
        <div class="gradient-purple px-8 py-6 text-center">
          <p class="text-purple-200 text-xs font-semibold uppercase tracking-widest mb-1">Contele Fleet</p>
          <h2 class="text-white text-2xl font-extrabold">Política de Uso de Frota</h2>
          <p id="doc-empresa-header" class="text-purple-200 text-sm mt-1"></p>
        </div>

        <!-- Corpo do documento -->
        <div id="policy-output" class="px-8 py-10 text-gray-800 leading-relaxed text-sm space-y-6 whitespace-pre-wrap">
          <!-- Texto gerado via JS -->
        </div>

      </div>

    </div>
  </section>
```

- [ ] **Step 2: Verificar estrutura no navegador**

A seção deve estar invisível (`hidden`). Inspecionar o DOM e confirmar que o elemento existe com id `policy-section`.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar seção de documento gerado (oculta até geração)"
```

---

### Task 7: Footer

**Files:**
- Modify: `index.html` — adicionar footer antes do `</body>`

- [ ] **Step 1: Adicionar footer**

```html
  <!-- ===== FOOTER ===== -->
  <footer class="bg-grid py-10 px-4">
    <div class="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">

      <div class="text-center md:text-left">
        <p class="text-white font-bold text-lg">Contele Fleet</p>
        <p class="text-gray-500 text-sm mt-1">© 2003–2026 Contele Soluções Tecnológicas LTDA — Santos/SP</p>
      </div>

      <div class="flex gap-6 text-sm text-gray-500">
        <a href="#" class="hover:text-purple-light transition-colors">Política de Privacidade</a>
        <a href="#" class="hover:text-purple-light transition-colors">Termos de Uso</a>
        <a href="https://contelerotas.com.br" target="_blank" rel="noopener" class="hover:text-purple-light transition-colors">Contele Fleet</a>
      </div>

    </div>
  </footer>
```

- [ ] **Step 2: Verificar footer no navegador**

Esperado: fundo escuro com grid roxo, texto de copyright e links alinhados.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar footer com copyright e links"
```

---

### Task 8: JavaScript — Multi-step e Validação

**Files:**
- Modify: `index.html` — adicionar `<script>` antes de `</body>`

- [ ] **Step 1: Adicionar bloco `<script>` com controle de steps e validação**

Adicione antes de `</body>`:

```html
<script>
  // ============================================
  // CONTROLE MULTI-STEP
  // ============================================

  function showStep(stepNumber) {
    document.getElementById('step-1').classList.toggle('hidden', stepNumber !== 1);
    document.getElementById('step-2').classList.toggle('hidden', stepNumber !== 2);

    const labels = {
      1: { label: 'Passo 1 de 2 — Dados da Empresa',       percent: '50%',  width: '50%' },
      2: { label: 'Passo 2 de 2 — Regras Operacionais',    percent: '100%', width: '100%' },
    };

    document.getElementById('step-label').textContent   = labels[stepNumber].label;
    document.getElementById('step-percent').textContent = labels[stepNumber].percent;
    document.getElementById('progress-bar').style.width = labels[stepNumber].width;
  }

  function nextStep() {
    if (validateStep(1)) showStep(2);
  }

  function prevStep() {
    showStep(1);
  }

  // ============================================
  // VALIDAÇÃO
  // ============================================

  function validateStep(step) {
    const fields = step === 1
      ? ['razao-social', 'email', 'gestor', 'qtd-veiculos']
      : ['velocidade', 'horario', 'tanque'];

    let valid = true;

    fields.forEach(id => {
      const el = document.getElementById(id);
      const empty = !el.value.trim();
      el.classList.toggle('field-error', empty);
      if (empty) {
        valid = false;
        el.addEventListener('input', () => el.classList.remove('field-error'), { once: true });
      }
    });

    // Validação extra: e-mail
    if (step === 1) {
      const emailEl = document.getElementById('email');
      const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailEl.value.trim());
      if (!emailOk) {
        emailEl.classList.add('field-error');
        valid = false;
      }
    }

    return valid;
  }
</script>
```

- [ ] **Step 2: Testar validação no navegador**

- Clicar "Próximo" com campos vazios: todos os campos devem ganhar borda vermelha.
- Preencher um campo: a borda vermelha deve sumir imediatamente nesse campo.
- Preencher todos os campos do Step 1 com e-mail válido: deve avançar para Step 2.
- No Step 2, clicar "Voltar": deve retornar ao Step 1 com dados preservados.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar controle multi-step e validação de campos"
```

---

### Task 9: JavaScript — Geração do Documento

**Files:**
- Modify: `index.html` — adicionar funções de geração dentro do `<script>` existente

- [ ] **Step 1: Adicionar funções de geração dentro do bloco `<script>`, após as funções de validação**

```javascript
  // ============================================
  // GERAÇÃO DO DOCUMENTO
  // ============================================

  function generatePolicy() {
    if (!validateStep(2)) return;

    // Coletar dados
    const empresa    = document.getElementById('razao-social').value.trim();
    const email      = document.getElementById('email').value.trim();
    const gestor     = document.getElementById('gestor').value.trim();
    const qtd        = document.getElementById('qtd-veiculos').value;
    const velocidade = document.getElementById('velocidade').value;
    const horario    = document.getElementById('horario').value.trim();
    const tanque     = document.getElementById('tanque').value;
    const restricao  = document.getElementById('restricao').value.trim();

    const hoje = new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
    const restricaoTexto = restricao
      ? `Os veículos somente poderão circular na seguinte área geográfica: ${restricao}. Deslocamentos fora dessa região devem ser previamente autorizados pelo gestor de frota.`
      : 'Não há restrição geográfica específica definida nesta versão da política. O gestor poderá estabelecer restrições pontuais por comunicado interno.';

    const policyText = `
POLÍTICA DE USO DE FROTA CORPORATIVA
${empresa.toUpperCase()}

Data de emissão: ${hoje}
Gestor responsável: ${gestor}
E-mail de contato: ${email}
Quantidade de veículos: ${qtd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. APRESENTAÇÃO E OBJETIVO

A presente Política de Uso de Frota Corporativa estabelece as normas, responsabilidades e diretrizes para a utilização dos veículos pertencentes ou locados por ${empresa} (doravante denominada "Empresa").

O objetivo é garantir o uso responsável, seguro e econômico dos veículos, proteger o patrimônio da Empresa, assegurar a conformidade legal e preservar a integridade física dos colaboradores e de terceiros.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. ABRANGÊNCIA E CONDUTORES AUTORIZADOS

2.1. Esta política aplica-se a todos os colaboradores, prestadores de serviço e terceiros que, por qualquer razão, utilizem os veículos da frota de ${empresa}.

2.2. Somente estão autorizados a conduzir os veículos da frota colaboradores devidamente cadastrados no sistema de gestão de frota, com Carteira Nacional de Habilitação (CNH) válida e compatível com a categoria do veículo.

2.3. É expressamente proibido ceder, emprestar ou permitir que terceiros não autorizados conduzam veículos da frota, sob pena das sanções previstas nesta política.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. REGRAS DE USO DOS VEÍCULOS

3.1. VELOCIDADE MÁXIMA
A velocidade máxima permitida para todos os veículos da frota é de ${velocidade} km/h, respeitando sempre os limites legais de cada via, que prevalecerão quando inferiores a esse limite. O monitoramento é realizado por sistema de telemetria e eventuais excessos serão registrados e comunicados ao colaborador e ao RH.

3.2. HORÁRIOS DE UTILIZAÇÃO
Os veículos somente poderão ser utilizados no horário de ${horario}. Deslocamentos fora desse período devem ser previamente solicitados e aprovados pelo gestor responsável (${gestor}), com registro formal.

3.3. COMBUSTÍVEL E DEVOLUÇÃO DO VEÍCULO
Ao devolver o veículo, o colaborador deverá entregar o tanque ${tanque}. O não cumprimento desta regra implicará em desconto correspondente ao combustível faltante no próximo demonstrativo de pagamento.

3.4. RESTRIÇÃO GEOGRÁFICA
${restricaoTexto}

3.5. USO EXCLUSIVAMENTE CORPORATIVO
Os veículos da frota destinam-se exclusivamente ao uso corporativo. É vedada a utilização para fins pessoais, transporte remunerado de passageiros (aplicativos de mobilidade), transporte de cargas não autorizadas ou qualquer outra finalidade não relacionada às atividades da Empresa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. RESPONSABILIDADES DO CONDUTOR

4.1. O condutor é responsável pela vistoria do veículo antes de cada uso, devendo registrar quaisquer avarias preexistentes no sistema de frota.

4.2. Em caso de acidente, o condutor deve: (a) preservar a cena; (b) acionar as autoridades competentes; (c) notificar imediatamente o gestor de frota (${gestor}); (d) registrar boletim de ocorrência.

4.3. Multas de trânsito geradas por infrações cometidas pelo condutor são de responsabilidade exclusiva do mesmo, incluindo o pagamento e eventuais pontos na CNH.

4.4. É proibido conduzir veículos da frota sob influência de álcool, drogas ou qualquer substância que altere a capacidade de direção, nos termos do Código de Trânsito Brasileiro.

4.5. O uso de celular ao volante sem dispositivo viva-voz é expressamente proibido.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. INFRAÇÕES, MULTAS E PENALIDADES

5.1. O descumprimento das normas desta política sujeitará o colaborador às seguintes penalidades, aplicadas de forma gradual e proporcional:
   • 1ª ocorrência: Advertência verbal registrada em prontuário.
   • 2ª ocorrência: Advertência escrita.
   • 3ª ocorrência: Suspensão do direito de uso dos veículos da frota por período determinado.
   • Ocorrências graves (embriaguez ao volante, acidente por negligência, uso indevido): Medidas disciplinares imediatas, podendo resultar em demissão por justa causa nos termos da CLT.

5.2. Danos causados ao veículo por imprudência, negligência ou imperícia do condutor poderão ser ressarcidos pela empresa e cobrados do colaborador, conforme avaliação do gestor e do setor de RH.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. TERMO DE CONSENTIMENTO — LEI GERAL DE PROTEÇÃO DE DADOS (LGPD)

Em conformidade com a Lei nº 13.709/2018 (LGPD), ${empresa} informa que os veículos de sua frota são equipados com dispositivos de rastreamento e telemetria veicular.

Os dados coletados incluem: localização em tempo real, velocidade, frenagens bruscas, acelerações, tempo de condução e outros comportamentos de direção.

Finalidade do tratamento: gestão da frota, segurança operacional, prevenção de acidentes, controle de custos e conformidade com apólices de seguro.

Os dados serão armazenados pelo período necessário à gestão da frota e poderão ser compartilhados com seguradoras, autoridades competentes e prestadores de serviços de manutenção, quando necessário.

O colaborador tem o direito de: acessar seus dados, solicitar correções, portabilidade e, quando aplicável, a exclusão dos registros, mediante solicitação ao DPO da empresa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. VIGÊNCIA E REVISÃO

Esta política entra em vigor na data de sua assinatura e tem validade por 12 (doze) meses, podendo ser revista a qualquer momento por iniciativa da Empresa, com comunicação prévia de 15 dias aos colaboradores.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. ASSINATURAS

Ao assinar este documento, o colaborador declara ter lido, compreendido e concordado integralmente com os termos desta Política de Uso de Frota Corporativa, bem como com o Termo de Consentimento LGPD acima.


Local e data: _________________________, ${hoje}


PELA EMPRESA:

Nome: ${gestor}
Cargo: Gestor de Frota
Assinatura: _____________________________________________


PELO COLABORADOR:

Nome completo: _________________________________________
CPF: ___________________________________________________
Cargo: _________________________________________________
Assinatura: _____________________________________________
Data: __________________________________________________


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documento gerado pela plataforma Contele Fleet — contelerotas.com.br
${hoje}
    `.trim();

    // Armazenar texto globalmente para uso nas funções de ação
    window._policyText = policyText;

    // Atualizar cabeçalho do documento
    document.getElementById('doc-empresa-header').textContent = empresa;

    // Renderizar no DOM
    document.getElementById('policy-output').textContent = policyText;

    // Ocultar formulário e exibir documento
    document.getElementById('form').classList.add('hidden');
    const policySection = document.getElementById('policy-section');
    policySection.classList.remove('hidden');

    // Scroll suave até o documento
    setTimeout(() => {
      policySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
```

- [ ] **Step 2: Testar geração no navegador**

- Preencher todos os campos do Step 1 e Step 2.
- Clicar em "Gerar Minha Política".
- Esperado: formulário some, documento aparece com todas as variáveis preenchidas corretamente (razão social, gestor, velocidade, horário, tanque, restrição geográfica).
- Verificar que a data está no formato correto (ex: "11 de junho de 2026").
- Verificar que a restrição geográfica, se deixada em branco, exibe o texto alternativo correto.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar geração do documento de política com variáveis personalizadas"
```

---

### Task 10: JavaScript — Copiar, Baixar e Reset

**Files:**
- Modify: `index.html` — adicionar funções de ação dentro do `<script>` existente

- [ ] **Step 1: Adicionar funções copyText, downloadTXT e resetForm dentro do `<script>`, após generatePolicy**

```javascript
  // ============================================
  // AÇÕES DO DOCUMENTO
  // ============================================

  function copyText() {
    if (!window._policyText) return;

    navigator.clipboard.writeText(window._policyText).then(() => {
      const btn = document.getElementById('btn-copy');
      const original = btn.innerHTML;
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
      btn.classList.add('bg-purple-50');
      setTimeout(() => {
        btn.innerHTML = original;
        btn.classList.remove('bg-purple-50');
      }, 2500);
    });
  }

  function downloadTXT() {
    if (!window._policyText) return;

    const empresa = document.getElementById('razao-social').value.trim().replace(/\s+/g, '-').toLowerCase();
    const blob = new Blob([window._policyText], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `politica-de-frota-${empresa}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function resetForm() {
    // Limpar campos
    ['razao-social','email','gestor','qtd-veiculos','velocidade','horario','tanque','restricao'].forEach(id => {
      const el = document.getElementById(id);
      if (el.tagName === 'SELECT') el.selectedIndex = 0;
      else if (id === 'velocidade') el.value = '110';
      else if (id === 'horario') el.value = '07h às 19h';
      else el.value = '';
      el.classList.remove('field-error');
    });

    // Limpar texto gerado
    window._policyText = null;
    document.getElementById('policy-output').textContent = '';

    // Voltar ao Step 1
    showStep(1);

    // Ocultar documento, exibir formulário
    document.getElementById('policy-section').classList.add('hidden');
    document.getElementById('form').classList.remove('hidden');

    // Scroll até o formulário
    setTimeout(() => {
      document.getElementById('form').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
```

- [ ] **Step 2: Testar todas as ações no navegador**

- Gerar uma política.
- Clicar "Copiar Texto": botão muda para "Copiado!" por 2.5s. Colar em qualquer editor e confirmar o texto.
- Clicar "Baixar TXT": arquivo `politica-de-frota-[empresa].txt` deve baixar com o conteúdo correto.
- Clicar "Gerar Nova Política": formulário deve aparecer no Step 1 com todos os campos em branco (exceto velocidade = 110 e horário = "07h às 19h").

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: adicionar ações de copiar, baixar TXT e reset do formulário"
```

---

### Task 11: Verificação final de responsividade e polimento

**Files:**
- Modify: `index.html` — ajustes finais se necessário

- [ ] **Step 1: Testar em viewports mobile (375px), tablet (768px) e desktop (1280px)**

Usar DevTools (F12 → Toggle device toolbar). Verificar em cada tamanho:
- [ ] Hero: headline legível, botão não cortado, 3 cards empilhados em mobile
- [ ] Benefícios: 1 coluna em mobile, 3 colunas em desktop
- [ ] Vídeo: proporção 16:9 mantida, sem overflow horizontal
- [ ] Formulário: campos ocupam 100% da largura, botões legíveis
- [ ] Documento: texto não transborda, botões de ação enrolam corretamente em mobile
- [ ] Footer: links empilhados em mobile

- [ ] **Step 2: Verificar console do navegador**

Abrir DevTools → Console. A página completa (Hero → Footer → Geração → Download) não deve apresentar nenhum erro ou warning.

- [ ] **Step 3: Commit final**

```bash
git add index.html
git commit -m "feat: landing page gerador de política de frota - versão completa"
```

---

## Resumo de Tasks

| # | Task | Entrega |
|---|------|---------|
| 1 | Estrutura base + CDNs + estilos | `index.html` com `<head>` completo |
| 2 | Hero Section | Fundo escuro, headline, CTA, ícones |
| 3 | Benefícios | 3 cards com ícones |
| 4 | Vídeo | Embed YouTube responsivo |
| 5 | Formulário HTML | Multi-step com barra de progresso |
| 6 | Documento HTML | Seção oculta de output |
| 7 | Footer | Copyright e links |
| 8 | JS: Multi-step + validação | Navegação entre steps, campos obrigatórios |
| 9 | JS: Geração do documento | Política completa com variáveis |
| 10 | JS: Copiar, Baixar, Reset | Ações pós-geração |
| 11 | Responsividade + polimento | Verificação final |
