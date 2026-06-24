# Editorial Dark Redesign — Portal FPT

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o portal de "funcional" para "editorial profissional" com direção visual Editorial Dark — Playfair Display nos títulos, hero com post destaque full-bleed, grid assimétrico, post page com hero overlay e mobile nav.

**Architecture:** Todas as mudanças são em arquivos estáticos (`public/style.css`, `public/index.html`, `public/post.html`). Zero backend. O servidor Express serve os arquivos como estão — rodar `node server.js` na pasta `fpt-portal/` e abrir `http://localhost:3000` para validar cada tarefa visualmente.

**Tech Stack:** HTML/CSS/JS vanilla, Montserrat (existente), Playfair Display (nova via Google Fonts), sem build step.

---

## Arquivos Modificados

| Arquivo | O que muda |
|---|---|
| `public/style.css` | Tipografia, hero, grid, cards, post hero, mobile nav, glows |
| `public/index.html` | Hero dinâmico com post destaque, grid novo, hamburger menu |
| `public/post.html` | Hero full-bleed com overlay, hamburger menu |

---

## Task 1: Tipografia Editorial (Playfair Display)

**Files:**
- Modify: `public/style.css` — adicionar font import e variáveis de tipografia

- [ ] **Step 1: Adicionar Playfair Display ao import de fontes**

Em `public/style.css`, linha 1, substituir o `@import` atual por:

```css
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap');
```

- [ ] **Step 2: Adicionar variável CSS para a font serif**

Logo após `:root { ... }` (após linha 13), adicionar dentro do bloco `:root`:

```css
  --fpt-font-display: 'Playfair Display', Georgia, serif;
  --fpt-font-body: 'Montserrat', sans-serif;
```

- [ ] **Step 3: Aplicar Playfair Display nos títulos principais**

No `style.css`, encontrar `.hero h1` e atualizar:

```css
.hero h1 {
  font-family: var(--fpt-font-display);
  font-size: 48px;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}
```

Encontrar `.article-title` e atualizar:

```css
.article-title {
  font-family: var(--fpt-font-display);
  font-size: 40px;
  font-weight: 800;
  line-height: 1.25;
  margin: 16px 0 12px;
  letter-spacing: -0.5px;
}
```

Encontrar `.card-title` e atualizar:

```css
.card-title {
  font-family: var(--fpt-font-display);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 10px;
  color: var(--fpt-text-light);
}
```

Encontrar `.card.featured .card-title` e atualizar:

```css
.card.featured .card-title { font-size: 26px; }
```

- [ ] **Step 4: Validar no browser**

Abrir `http://localhost:3000`. Os títulos dos cards e o hero devem usar serif. Se a fonte não carregou (sem internet), vai cair em Georgia — aceitável para validação local.

- [ ] **Step 5: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css
git commit -m "feat(fpt-portal): tipografia editorial — Playfair Display nos títulos"
```

---

## Task 2: Hero Dinâmico com Post Destaque

**Files:**
- Modify: `public/index.html` — hero passa a exibir o primeiro post publicado com imagem de fundo
- Modify: `public/style.css` — estilos do hero editorial

- [ ] **Step 1: Atualizar CSS do hero para suportar imagem de fundo**

No `style.css`, substituir o bloco `.hero` atual por:

```css
/* Hero Editorial */
.hero {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 48px;
  min-height: 420px;
  display: flex;
  align-items: flex-end;
  cursor: pointer;
  background: linear-gradient(135deg, var(--fpt-purple-deep), #1a0040);
}

.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.45;
  transition: opacity 0.4s ease-out;
}

.hero:hover .hero-bg { opacity: 0.55; }

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(8, 0, 16, 0.95) 0%,
    rgba(8, 0, 16, 0.5) 50%,
    rgba(8, 0, 16, 0.1) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 40px;
  width: 100%;
  max-width: 760px;
}

.hero-content .badge { margin-bottom: 16px; }

.hero-content h1 {
  font-family: var(--fpt-font-display);
  font-size: 40px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.hero-content .hero-excerpt {
  font-size: 15px;
  color: rgba(247, 247, 247, 0.8);
  line-height: 1.6;
  margin-bottom: 20px;
  max-width: 560px;
}

.hero-meta {
  font-size: 13px;
  color: rgba(247, 247, 247, 0.6);
}

/* Hero fallback (sem posts) */
.hero-static {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 40px;
  border-bottom: 1px solid rgba(139,35,229,0.2);
  margin-bottom: 40px;
  background: linear-gradient(135deg, rgba(139,35,229,0.06), transparent);
  border-radius: 16px;
}

.hero-static h1 {
  font-family: var(--fpt-font-display);
  font-size: 48px;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.hero-static p { color: var(--fpt-text-muted); font-size: 16px; }
```

- [ ] **Step 2: Atualizar o HTML do hero em `public/index.html`**

Substituir o bloco `<section class="hero">` atual (linhas 28–31):

```html
<!-- Hero: preenchido via JS com o primeiro post, ou estático se vazio -->
<section id="hero-section"></section>
```

- [ ] **Step 3: Adicionar função `renderHero` no JS de `public/index.html`**

Logo antes da função `renderCard` (linha ~79), adicionar:

```js
function renderHero(post) {
  const heroSection = document.getElementById('hero-section');
  if (!post) {
    heroSection.innerHTML = `
      <div class="hero-static">
        <h1>Referência em Gestão de Frotas</h1>
        <p>Notícias, análises e conteúdo prático para gestores de frota do Brasil.</p>
      </div>`;
    return;
  }
  heroSection.innerHTML = `
    <div class="hero" onclick="location.href='/post/${post.slug}'">
      ${post.image_url ? `<img class="hero-bg" src="${post.image_url}" alt="${post.title}">` : ''}
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <span class="badge">${CATEGORY_LABELS[post.category] || post.category}</span>
        <h1>${post.title}</h1>
        <p class="hero-excerpt">${post.excerpt || ''}</p>
        <span class="hero-meta">${formatDate(post.published_at)} · Julio César</span>
      </div>
    </div>`;
}
```

- [ ] **Step 4: Chamar `renderHero` dentro de `loadPosts`**

Na função `loadPosts`, após `const posts = await fetch(url).then(r => r.json())`, adicionar:

```js
// Renderiza hero com primeiro post (só na view "Todos", sem filtro de categoria)
if (!category) {
  renderHero(posts[0] || null);
} else if (!document.querySelector('.hero')) {
  renderHero(null);
}
```

E no bloco `if (!posts.length)`, antes do return, adicionar:

```js
if (!category) renderHero(null);
```

- [ ] **Step 5: Remover o primeiro post do grid quando vira hero**

Na linha onde monta o grid, substituir:

```js
grid.innerHTML = posts.map((post, i) => renderCard(post, i)).join('');
```

por:

```js
const gridPosts = (!category && posts.length > 0) ? posts.slice(1) : posts;
grid.innerHTML = gridPosts.map((post, i) => renderCard(post, i)).join('');
```

- [ ] **Step 6: Validar no browser**

Abrir `http://localhost:3000`. Se houver posts publicados, o hero deve mostrar o primeiro com imagem de fundo e título grande. Se não houver posts, deve mostrar o hero estático.

Para testar com posts: acesse `/admin`, insira a API key (`dev-key` em dev), force o sync YouTube via botão, então aprove um post.

- [ ] **Step 7: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css fpt-portal/public/index.html
git commit -m "feat(fpt-portal): hero dinâmico com post destaque e overlay"
```

---

## Task 3: Grid Editorial Assimétrico

**Files:**
- Modify: `public/style.css` — grid com 3 colunas, cards variados
- Modify: `public/index.html` — segundo post recebe destaque lateral

- [ ] **Step 1: Atualizar grid no CSS**

Substituir `.posts-grid` e `.card.featured` por:

```css
/* Grid editorial */
.posts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 48px;
}

/* Segundo post (índice 0 no grid, pois o 1º virou hero): ocupa 2 colunas */
.card.featured {
  grid-column: span 2;
}

.card.featured .card-image { height: 280px; }
.card.featured .card-title { font-size: 22px; }
.card.featured .card-excerpt { -webkit-line-clamp: 4; }
```

- [ ] **Step 2: Atualizar mobile — grid 1 coluna**

No bloco `@media (max-width: 640px)`, substituir:

```css
.posts-grid { grid-template-columns: 1fr; }
.card.featured { grid-column: span 1; }
.card.featured .card-image { height: 200px; }
.card.featured .card-title { font-size: 18px; }
```

- [ ] **Step 3: Adicionar breakpoint para tablet (641–1024px) — 2 colunas**

Após o bloco `@media (max-width: 640px)`, adicionar:

```css
@media (min-width: 641px) and (max-width: 1024px) {
  .posts-grid { grid-template-columns: repeat(2, 1fr); }
  .card.featured { grid-column: span 2; }
  .hero-content h1 { font-size: 32px; }
}
```

- [ ] **Step 4: Melhorar visual dos cards**

Substituir o bloco `.card` e `.card:hover` por:

```css
.card {
  background: var(--fpt-card);
  border: 1px solid rgba(139,35,229,0.12);
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.25s ease-out, box-shadow 0.25s ease-out, border-color 0.25s ease-out;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.card:hover {
  transform: translateY(-5px);
  border-color: rgba(139,35,229,0.45);
  box-shadow: 0 12px 40px rgba(139,35,229,0.15), 0 4px 12px rgba(0,0,0,0.3);
}

.card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-excerpt {
  font-size: 14px;
  color: var(--fpt-text-muted);
  line-height: 1.6;
  margin-bottom: 16px;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-date {
  font-size: 12px;
  color: var(--fpt-text-muted);
  margin-top: auto;
}
```

- [ ] **Step 5: Validar no browser**

Abrir `http://localhost:3000`. Grid deve ter 3 colunas, primeiro card ocupando 2. Em mobile deve cair para 1 coluna. Redimensionar o browser para validar o breakpoint de tablet.

- [ ] **Step 6: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css
git commit -m "feat(fpt-portal): grid editorial 3 colunas com card destaque assimétrico"
```

---

## Task 4: Post Page com Hero Full-Bleed

**Files:**
- Modify: `public/style.css` — estilos do hero do artigo
- Modify: `public/post.html` — estrutura do artigo com hero overlay

- [ ] **Step 1: Adicionar CSS do hero do artigo**

No `style.css`, substituir `.article-cover` por:

```css
/* Hero do artigo */
.article-hero {
  position: relative;
  width: 100%;
  height: 480px;
  overflow: hidden;
  margin-bottom: 0;
}

.article-hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.6;
}

.article-hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(8,0,16,1) 0%,
    rgba(8,0,16,0.6) 45%,
    rgba(8,0,16,0.1) 100%
  );
}

.article-hero-content {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 40px;
  max-width: 860px;
  margin: 0 auto;
}

.article-hero-content .badge { margin-bottom: 16px; }

.article-hero-content h1 {
  font-family: var(--fpt-font-display);
  font-size: 44px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.5px;
  color: #fff;
  text-shadow: 0 2px 12px rgba(0,0,0,0.5);
  margin-bottom: 16px;
}

.article-hero-content .article-meta {
  color: rgba(247,247,247,0.7);
  font-size: 14px;
  margin-bottom: 0;
}

/* Artigo sem imagem (mantém layout atual) */
.article {
  max-width: 760px;
  margin: 0 auto;
  padding: 48px 24px;
}

.article-header { margin-bottom: 32px; }

@media (max-width: 640px) {
  .article-hero { height: 320px; }
  .article-hero-content { padding: 24px; }
  .article-hero-content h1 { font-size: 28px; }
  .article-title { font-size: 26px; }
}
```

- [ ] **Step 2: Atualizar `renderArticle` em `public/post.html` para usar hero quando há imagem**

No arquivo `post.html`, dentro da função `loadPost`, substituir o bloco que monta o `article.innerHTML` por:

```js
document.title = `${post.title} — Frota Para Todos`;

const videoEmbed = post.video_id
  ? `<div class="video-embed">
       <iframe src="https://www.youtube.com/embed/${post.video_id}"
         allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
         allowfullscreen></iframe>
     </div>`
  : '';

// Se tem imagem e não é vídeo: hero full-bleed fora do .article
// Se não tem imagem: header simples dentro do .article
if (post.image_url && !post.video_id) {
  document.getElementById('article-hero').innerHTML = `
    <div class="article-hero">
      <img src="${post.image_url}" alt="${post.title}">
      <div class="article-hero-overlay"></div>
      <div class="article-hero-content">
        <span class="badge">${CATEGORY_LABELS[post.category] || post.category}</span>
        <h1>${post.title}</h1>
        <div class="article-meta">
          <time>${formatDate(post.published_at)}</time> · ${readingTime(post.content_html)} min de leitura · Julio César | Frota Para Todos
        </div>
      </div>
    </div>`;

  article.innerHTML = `
    <a href="/" class="back-link">← Voltar para o portal</a>
    ${videoEmbed}
    <div class="article-content">${post.content_html}</div>`;
} else {
  document.getElementById('article-hero').innerHTML = '';
  article.innerHTML = `
    <a href="/" class="back-link">← Voltar para o portal</a>
    <div class="article-header">
      <span class="badge">${CATEGORY_LABELS[post.category] || post.category}</span>
      <h1 class="article-title">${post.title}</h1>
      <div class="article-meta">
        <time>${formatDate(post.published_at)}</time> · ${readingTime(post.content_html)} min de leitura · Julio César | Frota Para Todos
      </div>
    </div>
    ${videoEmbed}
    <div class="article-content">${post.content_html}</div>`;
}
```

- [ ] **Step 3: Adicionar `div#article-hero` no HTML de `post.html`**

No `post.html`, antes do `<main>`, adicionar:

```html
<div id="article-hero"></div>
```

O `<main>` existente continua com `<article id="article" class="article">`.

- [ ] **Step 4: Validar no browser**

Abrir um post que tenha `image_url`. O título e categoria devem aparecer sobrepostos sobre a imagem no topo da página. Posts de vídeo (sem imagem) devem usar o layout simples atual.

- [ ] **Step 5: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css fpt-portal/public/post.html
git commit -m "feat(fpt-portal): post page com hero full-bleed e título overlay"
```

---

## Task 5: Mobile Nav — Menu Hamburger

**Files:**
- Modify: `public/style.css` — hamburger e menu mobile
- Modify: `public/index.html` — botão hamburger + lógica de toggle
- Modify: `public/post.html` — mesma estrutura de nav

- [ ] **Step 1: Adicionar CSS do hamburger e menu mobile**

No `style.css`, após o bloco `.header-nav a:hover`, adicionar:

```css
/* Hamburger mobile */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 4px;
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--fpt-text-light);
  border-radius: 2px;
  transition: all 0.25s ease-out;
}

.hamburger.open span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }

.mobile-nav {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(8, 0, 16, 0.97);
  z-index: 99;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 32px;
}

.mobile-nav.open { display: flex; }

.mobile-nav a {
  font-family: var(--fpt-font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--fpt-text-light);
  transition: color 0.2s;
}

.mobile-nav a:hover { color: var(--fpt-purple); }

.mobile-nav-close {
  position: absolute;
  top: 20px;
  right: 24px;
  background: none;
  border: none;
  color: var(--fpt-text-muted);
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
}
```

- [ ] **Step 2: Atualizar `@media (max-width: 640px)` — mostrar hamburger, esconder nav**

No bloco `@media (max-width: 640px)` existente, substituir `.header-nav { display: none; }` por:

```css
.header-nav { display: none; }
.hamburger { display: flex; }
```

- [ ] **Step 3: Adicionar hamburger e mobile-nav no `<header>` de `public/index.html`**

Substituir o `<header>` de `index.html` por:

```html
<header class="header">
  <a href="/" class="header-logo">Frota Para <span>Todos</span></a>
  <nav class="header-nav">
    <a href="/">Início</a>
    <a href="/?category=noticias">Notícias</a>
    <a href="/?category=analises">Análises</a>
    <a href="/?category=entrevistas">Entrevistas</a>
    <a href="/?category=videos">Vídeos</a>
  </nav>
  <button class="hamburger" id="hamburger" aria-label="Menu" onclick="toggleMobileNav()">
    <span></span><span></span><span></span>
  </button>
</header>

<div class="mobile-nav" id="mobile-nav">
  <button class="mobile-nav-close" onclick="toggleMobileNav()">✕</button>
  <a href="/" onclick="toggleMobileNav()">Início</a>
  <a href="/?category=noticias" onclick="toggleMobileNav()">Notícias</a>
  <a href="/?category=analises" onclick="toggleMobileNav()">Análises</a>
  <a href="/?category=entrevistas" onclick="toggleMobileNav()">Entrevistas</a>
  <a href="/?category=videos" onclick="toggleMobileNav()">Vídeos</a>
</div>
```

- [ ] **Step 4: Adicionar função `toggleMobileNav` no JS de `index.html`**

No `<script>` de `index.html`, antes de `loadSponsors()`, adicionar:

```js
function toggleMobileNav() {
  const nav = document.getElementById('mobile-nav');
  const btn = document.getElementById('hamburger');
  nav.classList.toggle('open');
  btn.classList.toggle('open');
  document.body.style.overflow = nav.classList.contains('open') ? 'hidden' : '';
}
```

- [ ] **Step 5: Repetir no `public/post.html`**

No `post.html`, substituir o `<header>` por:

```html
<header class="header">
  <a href="/" class="header-logo">Frota Para <span>Todos</span></a>
  <nav class="header-nav">
    <a href="/">Início</a>
    <a href="/?category=noticias">Notícias</a>
    <a href="/?category=videos">Vídeos</a>
  </nav>
  <button class="hamburger" id="hamburger" aria-label="Menu" onclick="toggleMobileNav()">
    <span></span><span></span><span></span>
  </button>
</header>

<div class="mobile-nav" id="mobile-nav">
  <button class="mobile-nav-close" onclick="toggleMobileNav()">✕</button>
  <a href="/">Início</a>
  <a href="/?category=noticias">Notícias</a>
  <a href="/?category=videos">Vídeos</a>
</div>
```

E no `<script>` de `post.html`, antes de `loadPost()`, adicionar:

```js
function toggleMobileNav() {
  const nav = document.getElementById('mobile-nav');
  const btn = document.getElementById('hamburger');
  nav.classList.toggle('open');
  btn.classList.toggle('open');
  document.body.style.overflow = nav.classList.contains('open') ? 'hidden' : '';
}
```

- [ ] **Step 6: Validar no browser**

Redimensionar o browser para largura < 640px (DevTools → mobile). O hambúrguer deve aparecer no header. Clicar: menu fullscreen deve abrir com links grandes em Playfair Display. Clicar em ✕ ou num link deve fechar.

- [ ] **Step 7: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css fpt-portal/public/index.html fpt-portal/public/post.html
git commit -m "feat(fpt-portal): mobile nav hamburger fullscreen"
```

---

## Task 6: Profundidade Visual — Glows, Seções, Detalhes

**Files:**
- Modify: `public/style.css` — glow no hero, seção newsletter, footer, badge

- [ ] **Step 1: Glow sutil no hero ao hover**

No `.hero:hover .hero-bg` já adicionado na Task 2, confirmar que existe. Adicionar também:

```css
.hero::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 80px;
  background: linear-gradient(to top, var(--fpt-dark), transparent);
  z-index: 1;
  pointer-events: none;
}
```

- [ ] **Step 2: Melhorar o badge com variação por categoria**

Substituir `.badge` por:

```css
.badge {
  display: inline-block;
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 12px;
  background: var(--fpt-purple);
  color: #fff;
}

.badge[data-cat="videos"]      { background: #1d4ed8; }
.badge[data-cat="noticias"]    { background: #b91c1c; }
.badge[data-cat="analises"]    { background: #047857; }
.badge[data-cat="entrevistas"] { background: #b45309; }
.badge[data-cat="casos"]       { background: #6d28d9; }
```

- [ ] **Step 3: Atualizar renderCard e renderHero para passar `data-cat` no badge**

Em `index.html`, na função `renderCard`, substituir:

```js
<span class="badge">${CATEGORY_LABELS[post.category] || post.category}</span>
```

por:

```js
<span class="badge" data-cat="${post.category}">${CATEGORY_LABELS[post.category] || post.category}</span>
```

Fazer o mesmo na função `renderHero` (hero content) e no `post.html` onde o badge é inserido via JS.

- [ ] **Step 4: Melhorar newsletter section**

Substituir `.newsletter-section` no CSS por:

```css
.newsletter-section {
  position: relative;
  background: linear-gradient(135deg, rgba(139,35,229,0.12), rgba(139,35,229,0.04));
  border: 1px solid rgba(139,35,229,0.3);
  border-radius: 20px;
  padding: 56px 40px;
  margin: 56px 0;
  overflow: hidden;
}

.newsletter-section::before {
  content: '';
  position: absolute;
  top: -80px;
  right: -80px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(139,35,229,0.15), transparent 70%);
  pointer-events: none;
}

.newsletter-text h2 {
  font-family: var(--fpt-font-display);
  font-size: 28px;
  font-weight: 800;
  margin-bottom: 8px;
}
```

- [ ] **Step 5: Linha separadora com glow entre hero e grid**

Após `.filters` no CSS, adicionar:

```css
.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}
```

(sem mudança, apenas confirmar que existe)

Adicionar separador visual nos filtros — atualizar `.filter-btn.active`:

```css
.filter-btn:hover, .filter-btn.active {
  background: var(--fpt-purple);
  border-color: var(--fpt-purple);
  color: #fff;
  box-shadow: 0 0 12px rgba(139,35,229,0.4);
}
```

- [ ] **Step 6: Validar no browser**

Abrir `http://localhost:3000`. Verificar:
- Badges com cores por categoria
- Newsletter com glow no canto
- Filter buttons com glow ao ativar

- [ ] **Step 7: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/public/style.css fpt-portal/public/index.html fpt-portal/public/post.html
git commit -m "feat(fpt-portal): profundidade visual — glows, badges por categoria, newsletter"
```

---

## Task 7: Merge no Master e Deploy

**Files:**
- Branch atual: `feat/portal-noticias-fpt`

- [ ] **Step 1: Confirmar que tudo está commitado**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git status
```

Esperado: `nothing to commit, working tree clean`

- [ ] **Step 2: Commitar arquivos não monitorados pendentes (sponsors.js, favicon.svg, unsubscribe.html, docs/)**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git add fpt-portal/sponsors.js fpt-portal/public/favicon.svg fpt-portal/public/unsubscribe.html fpt-portal/docs/
git commit -m "feat(fpt-portal): sponsors, favicon, unsubscribe page e docs"
```

- [ ] **Step 3: Merge no master**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt"
git checkout master
git merge feat/portal-noticias-fpt --no-ff -m "feat(fpt-portal): redesign editorial dark — tipografia, hero, grid, post hero, mobile nav"
```

- [ ] **Step 4: Push pro remote**

```bash
git push origin master
```

- [ ] **Step 5: Confirmar deploy Railway**

Aguardar ~60s e checar se o Railway disparou o deploy (verificar logs no dashboard ou via health check):

```bash
curl -s https://growth-production-8ca9.up.railway.app/api/health
```

Esperado: `{"ok":true}`
