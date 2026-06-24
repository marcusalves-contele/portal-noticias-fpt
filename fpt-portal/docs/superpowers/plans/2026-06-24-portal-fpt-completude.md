# Portal FPT — Completude Editorial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar a experiência editorial do Portal FPT com busca, SEO, artigos relacionados, compartilhamento, página Sobre, links Instagram e suporte a múltiplos patrocinadores.

**Architecture:** Node.js + Express + SQLite backend vanilla. Frontend HTML/CSS/JS puro sem build step. Cada feature toca db.js (queries), server.js (rotas) e/ou public/*.html (UI). Não há framework de testes — verificações feitas com curl e checklist manual no browser.

**Tech Stack:** Node.js 18+, Express 4, sqlite3, HTML/CSS/JS vanilla, Playfair Display + Montserrat, CSS custom properties (`--fpt-*`).

---

## Estrutura de arquivos

| Arquivo | O que muda |
|---------|-----------|
| `db.js` | + `search()`, + `getRelated()` |
| `server.js` | + `/api/search`, + `/api/posts/related/:slug`, + `/sitemap.xml`, + `/about` route |
| `public/robots.txt` | NOVO — permite crawlers, aponta sitemap |
| `public/index.html` | + search bar, + Instagram link no footer/nav |
| `public/post.html` | + OG meta tags, + JSON-LD, + share buttons, + artigos relacionados |
| `public/about.html` | NOVO — página institucional |
| `public/style.css` | + estilos de search overlay, share bar, related grid, about page |

---

## Task 1: Search — API

**Files:**
- Modify: `db.js` (ao final do module.exports, antes do `}`)
- Modify: `server.js` (após rota `GET /api/posts/:slug`, ~linha 57)

- [ ] **Step 1: Adicionar `search()` em db.js**

Abrir `db.js`. Dentro de `module.exports = { ... }`, após a linha `getByVideoId: ...`, adicionar:

```js
search: (q, limit = 10) => {
  const term = `%${q}%`;
  return all(
    "SELECT * FROM posts WHERE status = 'published' AND (title LIKE ? OR excerpt LIKE ?) ORDER BY published_at DESC LIMIT ?",
    [term, term, limit]
  );
},
```

- [ ] **Step 2: Adicionar rota `/api/search` em server.js**

Após a rota `app.get('/api/posts/:slug', ...)` (linha ~57), inserir:

```js
// --- Busca ---
app.get('/api/search', async (req, res) => {
  const { q, limit = 10 } = req.query;
  if (!q || q.trim().length < 2) return res.json([]);
  try {
    const results = await db.search(q.trim(), Number(limit));
    res.json(results);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

- [ ] **Step 3: Testar a API**

```bash
curl "http://localhost:3000/api/search?q=frota"
# Esperado: array JSON com posts que tenham "frota" no título ou excerpt

curl "http://localhost:3000/api/search?q=a"
# Esperado: [] (q muito curto)

curl "http://localhost:3000/api/search"
# Esperado: []
```

- [ ] **Step 4: Commit**

```bash
cd "/home/contele/claude code/projetos/fleet/portal-noticias-fpt/fpt-portal"
git add db.js server.js
git commit -m "feat(fpt-portal): search API — /api/search?q= com LIKE em title+excerpt"
```

---

## Task 2: Search — UI no index.html

**Files:**
- Modify: `public/index.html`
- Modify: `public/style.css`

- [ ] **Step 1: Adicionar barra de busca no header em index.html**

No `<header class="header">`, após `<nav class="header-nav">...</nav>`, antes do `<button class="hamburger"`:

```html
<div class="search-wrap" id="search-wrap">
  <button class="search-toggle" id="search-toggle" aria-label="Buscar" onclick="toggleSearch()">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
  </button>
  <div class="search-box" id="search-box" style="display:none">
    <input type="search" id="search-input" placeholder="Buscar artigos..." autocomplete="off">
    <button class="search-close" onclick="closeSearch()">✕</button>
  </div>
</div>
```

- [ ] **Step 2: Adicionar overlay de resultados em index.html**

Logo após `</header>`, antes de `<div id="sponsor-bar">`:

```html
<div class="search-results-overlay" id="search-results-overlay" style="display:none">
  <div class="container">
    <div id="search-results-grid" class="posts-grid"></div>
    <p id="search-empty" style="display:none;color:#94A3B8;padding:32px;text-align:center;">Nenhum resultado encontrado.</p>
  </div>
</div>
```

- [ ] **Step 3: Adicionar JS de busca em index.html**

Dentro da `<script>` existente, antes de `loadSponsors()`, adicionar:

```js
let searchDebounce = null;

function toggleSearch() {
  const box = document.getElementById('search-box');
  const toggle = document.getElementById('search-toggle');
  const isOpen = box.style.display !== 'none';
  if (isOpen) {
    closeSearch();
  } else {
    box.style.display = 'flex';
    toggle.style.display = 'none';
    document.getElementById('search-input').focus();
  }
}

function closeSearch() {
  document.getElementById('search-box').style.display = 'none';
  document.getElementById('search-toggle').style.display = 'flex';
  document.getElementById('search-input').value = '';
  document.getElementById('search-results-overlay').style.display = 'none';
  document.getElementById('hero-section').parentElement.style.display = '';
  document.getElementById('posts-grid').style.display = '';
  document.getElementById('load-more-wrap').style.display = currentOffset >= PAGE_SIZE ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('search-input');
  if (input) {
    input.addEventListener('input', () => {
      clearTimeout(searchDebounce);
      const q = input.value.trim();
      if (q.length < 2) {
        document.getElementById('search-results-overlay').style.display = 'none';
        document.getElementById('hero-section').parentElement.style.display = '';
        document.getElementById('posts-grid').style.display = '';
        return;
      }
      searchDebounce = setTimeout(() => runSearch(q), 300);
    });
  }
});

async function runSearch(q) {
  const overlay = document.getElementById('search-results-overlay');
  const grid = document.getElementById('search-results-grid');
  const empty = document.getElementById('search-empty');
  document.getElementById('hero-section').parentElement.style.display = 'none';
  document.getElementById('posts-grid').style.display = 'none';
  document.getElementById('load-more-wrap').style.display = 'none';
  overlay.style.display = 'block';
  grid.innerHTML = renderSkeleton(3);
  try {
    const results = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=12`).then(r => r.json());
    if (!results.length) {
      grid.innerHTML = '';
      empty.style.display = 'block';
    } else {
      empty.style.display = 'none';
      grid.innerHTML = results.map((post, i) => renderCard(post, i)).join('');
      setupScrollReveal();
    }
  } catch (e) {
    grid.innerHTML = '<div class="empty-state">Erro ao buscar.</div>';
  }
}
```

- [ ] **Step 4: Adicionar CSS em style.css**

Ao final do arquivo (antes das media queries):

```css
/* Search */
.search-wrap { display: flex; align-items: center; gap: 8px; }

.search-toggle {
  background: transparent;
  border: none;
  color: var(--fpt-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 6px;
  border-radius: 6px;
  transition: color 0.2s ease-out;
}
.search-toggle:hover { color: var(--fpt-text-light); }

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(139,35,229,0.4);
  border-radius: 8px;
  padding: 4px 12px;
}

.search-box input[type="search"] {
  background: transparent;
  border: none;
  color: var(--fpt-text-light);
  font-family: var(--fpt-font-body);
  font-size: 14px;
  width: 200px;
  outline: none;
}
.search-box input[type="search"]::placeholder { color: var(--fpt-text-muted); }

.search-close {
  background: transparent;
  border: none;
  color: var(--fpt-text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}

.search-results-overlay {
  background: var(--fpt-dark);
  border-bottom: 1px solid rgba(139,35,229,0.2);
  padding: 32px 0;
  min-height: 200px;
}
```

- [ ] **Step 5: Verificar no browser**

Abrir `http://localhost:3000`. Clicar no ícone de lupa no header. Digitar 2+ caracteres. Verificar que os resultados aparecem abaixo do header e o grid/hero somem. Clicar em ✕ deve restaurar a homepage.

- [ ] **Step 6: Commit**

```bash
git add public/index.html public/style.css
git commit -m "feat(fpt-portal): search UI — lupa no header, overlay de resultados com debounce 300ms"
```

---

## Task 3: SEO — robots.txt + sitemap.xml + OG/JSON-LD no post

**Files:**
- Create: `public/robots.txt`
- Modify: `server.js`
- Modify: `public/post.html`

- [ ] **Step 1: Criar public/robots.txt**

```
User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: https://noticias.frotaparatodos.com.br/sitemap.xml
```

- [ ] **Step 2: Testar robots.txt**

```bash
curl http://localhost:3000/robots.txt
# Esperado: conteúdo do arquivo acima
```

- [ ] **Step 3: Adicionar rota /sitemap.xml em server.js**

Após as rotas HTML (linha ~331), antes de `app.listen`, adicionar:

```js
app.get('/sitemap.xml', async (req, res) => {
  const base = process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br';
  try {
    const posts = await db.getPublished(1000, 0, null);
    const staticUrls = [
      `<url><loc>${base}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>`,
      `<url><loc>${base}/about</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>`,
    ];
    const postUrls = posts.map(p => {
      const lastmod = p.published_at ? p.published_at.substring(0, 10) : '';
      return `<url><loc>${base}/post/${p.slug}</loc>${lastmod ? `<lastmod>${lastmod}</lastmod>` : ''}<changefreq>monthly</changefreq><priority>0.8</priority></url>`;
    });
    res.setHeader('Content-Type', 'application/xml; charset=utf-8');
    res.send(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${[...staticUrls, ...postUrls].join('\n  ')}
</urlset>`);
  } catch (e) {
    res.status(500).send('Erro ao gerar sitemap');
  }
});
```

- [ ] **Step 4: Testar sitemap**

```bash
curl http://localhost:3000/sitemap.xml
# Esperado: XML válido com <urlset>, entradas para / e /post/<slug> de cada post publicado
```

- [ ] **Step 5: Adicionar OG meta tags dinâmicas + JSON-LD em post.html**

No `<head>` de `post.html`, após `<meta name="viewport" ...>`, adicionar:

```html
<meta property="og:title" content="Frota Para Todos" id="og-title">
<meta property="og:description" content="Referência editorial em gestão de frotas." id="og-description">
<meta property="og:image" content="" id="og-image">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Frota Para Todos">
<meta name="description" content="" id="meta-description">
<script type="application/ld+json" id="article-jsonld"></script>
```

- [ ] **Step 6: Preencher OG + JSON-LD via JS em post.html**

Dentro da função `loadPost()`, logo após `document.title = ...` (linha ~88), adicionar:

```js
const base = location.origin;
const heroImgFull = post.image_url || (post.video_id ? `https://img.youtube.com/vi/${post.video_id}/maxresdefault.jpg` : '');

document.getElementById('og-title').setAttribute('content', post.title + ' — Frota Para Todos');
document.getElementById('og-description').setAttribute('content', post.excerpt || 'Referência editorial em gestão de frotas.');
if (heroImgFull) document.getElementById('og-image').setAttribute('content', heroImgFull);
document.getElementById('meta-description').setAttribute('content', post.excerpt || '');

document.getElementById('article-jsonld').textContent = JSON.stringify({
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": post.title,
  "description": post.excerpt || '',
  "image": heroImgFull || '',
  "datePublished": post.published_at,
  "author": { "@type": "Person", "name": "Julio César" },
  "publisher": {
    "@type": "Organization",
    "name": "Frota Para Todos",
    "url": base
  },
  "mainEntityOfPage": { "@type": "WebPage", "@id": location.href }
});
```

- [ ] **Step 7: Verificar JSON-LD no browser**

Abrir `http://localhost:3000/post/<qualquer-slug>`. Abrir DevTools > Elements > pesquisar por `application/ld+json`. Verificar que o script tem o JSON correto com o título do artigo.

- [ ] **Step 8: Commit**

```bash
git add public/robots.txt server.js public/post.html
git commit -m "feat(fpt-portal): SEO — robots.txt, sitemap.xml dinâmico, OG tags e JSON-LD nos artigos"
```

---

## Task 4: Artigos Relacionados

**Files:**
- Modify: `db.js`
- Modify: `server.js`
- Modify: `public/post.html`
- Modify: `public/style.css`

- [ ] **Step 1: Adicionar `getRelated()` em db.js**

Dentro de `module.exports`, após `search: ...`, adicionar:

```js
getRelated: (slug, category, limit = 3) =>
  all(
    "SELECT * FROM posts WHERE status = 'published' AND category = ? AND slug != ? ORDER BY published_at DESC LIMIT ?",
    [category, slug, limit]
  ),
```

- [ ] **Step 2: Adicionar rota `/api/posts/related/:slug` em server.js**

Após a rota `/api/search`, adicionar:

```js
app.get('/api/posts/related/:slug', async (req, res) => {
  try {
    const post = await db.getBySlug(req.params.slug);
    if (!post) return res.json([]);
    const related = await db.getRelated(post.slug, post.category);
    res.json(related);
  } catch (e) {
    res.json([]);
  }
});
```

- [ ] **Step 3: Testar API**

```bash
# Substitua <slug> por um slug real publicado
curl "http://localhost:3000/api/posts/related/<slug>"
# Esperado: array com até 3 posts da mesma categoria (excluindo o atual)
```

- [ ] **Step 4: Adicionar seção "Continue lendo" em post.html**

Após `<div id="comments-section" ...>`, antes de `</main>`, adicionar:

```html
<div id="related-section" class="article" style="display:none">
  <div class="related-wrap">
    <h3 class="related-title">Continue lendo</h3>
    <div id="related-grid" class="related-grid"></div>
  </div>
</div>
```

- [ ] **Step 5: Adicionar função `loadRelated()` em post.html**

No `<script>`, após `loadComments(slug)`, chamar:

```js
await loadRelated(slug);
```

E definir a função após `loadComments`:

```js
async function loadRelated(slug) {
  try {
    const posts = await fetch(`/api/posts/related/${slug}`).then(r => r.json());
    if (!posts.length) return;
    const grid = document.getElementById('related-grid');
    const CATEGORY_LABELS_R = { noticias: 'Notícias', analises: 'Análises', entrevistas: 'Entrevistas', casos: 'Casos', videos: 'Vídeos' };
    grid.innerHTML = posts.map(p => {
      const img = p.image_url || (p.video_id ? `https://img.youtube.com/vi/${p.video_id}/maxresdefault.jpg` : '');
      const date = new Date(p.published_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
      return `
        <article class="related-card" onclick="location.href='/post/${p.slug}'">
          ${img ? `<img class="related-card-img" src="${esc(img)}" alt="${esc(p.title)}" loading="lazy">` : '<div class="related-card-img related-card-placeholder"></div>'}
          <div class="related-card-body">
            <span class="badge" data-cat="${esc(p.category)}">${CATEGORY_LABELS_R[p.category] || esc(p.category)}</span>
            <h4 class="related-card-title">${esc(p.title)}</h4>
            <time class="card-date">${date}</time>
          </div>
        </article>`;
    }).join('');
    document.getElementById('related-section').style.display = 'block';
  } catch (e) {}
}
```

- [ ] **Step 6: Adicionar CSS em style.css**

Ao final do arquivo (antes das media queries `@media`):

```css
/* Related Articles */
.related-wrap {
  padding: 40px 0;
  border-top: 1px solid rgba(139,35,229,0.2);
  margin-top: 8px;
}

.related-title {
  font-family: var(--fpt-font-display);
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 24px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.related-card {
  background: var(--fpt-card);
  border: 1px solid rgba(139,35,229,0.12);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s ease-out, border-color 0.25s ease-out;
}
.related-card:hover {
  transform: translateY(-4px);
  border-color: rgba(139,35,229,0.4);
}

.related-card-img {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}

.related-card-placeholder {
  background: linear-gradient(135deg, var(--fpt-purple-deep), var(--fpt-purple-mid));
}

.related-card-body {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.related-card-title {
  font-family: var(--fpt-font-display);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--fpt-text-light);
}
```

- [ ] **Step 7: Verificar no browser**

Abrir `http://localhost:3000/post/<slug>`. Rolar até o final do artigo. Verificar que a seção "Continue lendo" aparece com até 3 cards de artigos da mesma categoria (se existirem).

- [ ] **Step 8: Commit**

```bash
git add db.js server.js public/post.html public/style.css
git commit -m "feat(fpt-portal): artigos relacionados — API /related/:slug + seção 'Continue lendo' no post"
```

---

## Task 5: Share Buttons

**Files:**
- Modify: `public/post.html`
- Modify: `public/style.css`

- [ ] **Step 1: Adicionar HTML dos botões de compartilhamento em post.html**

Dentro da função `loadPost()`, após renderizar o conteúdo do artigo (após a linha com `${post.content_html}`), adicionar uma barra de compartilhamento. Localizar onde `article.innerHTML = ...` é definido (existe em dois lugares: com hero e sem hero). Em **ambos** os casos, antes do fechamento da template string, adicionar:

```html
<div class="share-bar">
  <span class="share-label">Compartilhar:</span>
  <a id="share-wa" class="share-btn share-whatsapp" target="_blank" rel="noopener">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.125.557 4.122 1.526 5.855L0 24l6.294-1.503A11.954 11.954 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.374l-.36-.213-3.731.891.934-3.629-.234-.373A9.796 9.796 0 012.182 12C2.182 6.58 6.58 2.182 12 2.182S21.818 6.58 21.818 12 17.42 21.818 12 21.818z"/></svg>
    WhatsApp
  </a>
  <button class="share-btn share-copy" onclick="copyPostLink()">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
    Copiar link
  </button>
</div>
```

Em JavaScript, após definir `post`, definir o href do WhatsApp:

```js
const waText = encodeURIComponent(`${post.title} — ${location.href}`);
const shareWaEl = document.getElementById('share-wa');
if (shareWaEl) shareWaEl.href = `https://api.whatsapp.com/send?text=${waText}`;
```

- [ ] **Step 2: Adicionar função `copyPostLink()` em post.html**

Dentro do `<script>`, adicionar:

```js
function copyPostLink() {
  navigator.clipboard.writeText(location.href).then(() => {
    const btn = document.querySelector('.share-copy');
    const orig = btn.innerHTML;
    btn.innerHTML = '✓ Copiado!';
    btn.style.borderColor = '#22C55E';
    btn.style.color = '#22C55E';
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.style.borderColor = '';
      btn.style.color = '';
    }, 2000);
  });
}
```

- [ ] **Step 3: Adicionar CSS em style.css**

```css
/* Share Bar */
.share-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 32px 0;
  padding: 20px 0;
  border-top: 1px solid rgba(139,35,229,0.15);
  border-bottom: 1px solid rgba(139,35,229,0.15);
}

.share-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--fpt-text-muted);
  margin-right: 4px;
}

.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border-radius: 8px;
  font-family: var(--fpt-font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease-out;
  border: 1px solid transparent;
}

.share-whatsapp {
  background: rgba(37, 211, 102, 0.1);
  border-color: rgba(37, 211, 102, 0.3);
  color: #25D366;
}
.share-whatsapp:hover {
  background: rgba(37, 211, 102, 0.2);
  color: #25D366;
}

.share-copy {
  background: transparent;
  border-color: rgba(139,35,229,0.3);
  color: var(--fpt-text-muted);
}
.share-copy:hover {
  border-color: var(--fpt-purple);
  color: var(--fpt-text-light);
}
```

- [ ] **Step 4: Verificar no browser**

Abrir `http://localhost:3000/post/<slug>`. Verificar que a share bar aparece abaixo do conteúdo. Clicar em WhatsApp → deve abrir whatsapp.com com o título e URL. Clicar em "Copiar link" → botão muda para "✓ Copiado!" por 2s.

- [ ] **Step 5: Commit**

```bash
git add public/post.html public/style.css
git commit -m "feat(fpt-portal): share buttons — WhatsApp + copiar link no final de cada artigo"
```

---

## Task 6: Página Sobre

**Files:**
- Create: `public/about.html`
- Modify: `server.js`
- Modify: `public/index.html` (nav + footer)
- Modify: `public/post.html` (nav)

- [ ] **Step 1: Criar public/about.html**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sobre — Frota Para Todos</title>
  <meta name="description" content="Frota Para Todos é o portal editorial de referência em gestão de frotas do Brasil, criado por Julio César.">
  <meta property="og:title" content="Sobre — Frota Para Todos">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Frota Para Todos">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="stylesheet" href="/style.css">
</head>
<body>

<header class="header">
  <a href="/" class="header-logo">Frota Para <span>Todos</span></a>
  <nav class="header-nav">
    <a href="/">Início</a>
    <a href="/?category=noticias">Notícias</a>
    <a href="/?category=analises">Análises</a>
    <a href="/?category=entrevistas">Entrevistas</a>
    <a href="/?category=videos">Vídeos</a>
    <a href="/about" class="nav-active">Sobre</a>
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
  <a href="/about" onclick="toggleMobileNav()">Sobre</a>
</div>

<main class="container">
  <div class="about-page">
    <div class="about-header">
      <span class="badge" data-cat="analises">Editorial</span>
      <h1 class="about-title">Uma casa para gestores de frota</h1>
      <p class="about-lead">O Portal FPT nasceu para ser o que faltava: um lugar onde gestores de frota encontram conteúdo aprofundado, buscam por tema, leem em texto e voltam por hábito.</p>
    </div>

    <div class="about-body">
      <div class="about-section">
        <h2>Quem faz</h2>
        <p><strong>Julio César</strong> é o criador e curador do Frota Para Todos. Com mais de 10 anos de experiência em gestão de frotas, ele construiu um dos maiores canais brasileiros do setor no YouTube — e agora expande esse conteúdo para um formato editorial mais robusto.</p>
        <p>O portal é produzido com curadoria humana assistida por IA. Todo artigo publicado passa pela revisão editorial antes de ir ao ar.</p>
      </div>

      <div class="about-section">
        <h2>O que você encontra aqui</h2>
        <ul class="about-list">
          <li><strong>Notícias</strong> — O que está acontecendo no setor de frotas no Brasil e no mundo</li>
          <li><strong>Análises</strong> — Interpretação de dados, tendências e impactos para gestores</li>
          <li><strong>Entrevistas</strong> — Conversas com profissionais e especialistas do setor</li>
          <li><strong>Casos de Sucesso</strong> — Como empresas resolveram problemas reais de gestão</li>
          <li><strong>Vídeos</strong> — O melhor do canal YouTube em formato de artigo</li>
        </ul>
      </div>

      <div class="about-section">
        <h2>Diferente do Blog Fleet</h2>
        <p>O <a href="https://contelerastreador.com.br/blog" target="_blank">Blog Fleet</a> é topo de funil SEO automatizado por IA. O Portal FPT é experiência editorial: curadoria humana, análises mais longas, comunidade de leitores e newsletter semanal.</p>
      </div>

      <div class="about-channels">
        <h2>Acompanhe também</h2>
        <div class="about-links">
          <a href="https://www.youtube.com/channel/UCz31CtOANqSFuLEdFTi1iCQ" target="_blank" class="about-channel-link">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.7 15.5V8.5l6.3 3.5-6.3 3.5z"/></svg>
            <div>
              <strong>Canal YouTube</strong>
              <span>@frotaparatodos</span>
            </div>
          </a>
          <a href="https://www.instagram.com/frotaparatodos" target="_blank" class="about-channel-link">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            <div>
              <strong>Instagram</strong>
              <span>@frotaparatodos</span>
            </div>
          </a>
        </div>
      </div>

      <div class="about-section">
        <h2>Patrocínio</h2>
        <p>O portal é realizado com o apoio da <a href="https://contelerastreador.com.br/?utm_source=portal-fpt&utm_medium=about&utm_campaign=master" target="_blank">Contele Fleet</a>. Se sua empresa quer alcançar gestores de frota com conteúdo relevante, <a href="mailto:contato@frotaparatodos.com.br">entre em contato</a>.</p>
      </div>
    </div>
  </div>
</main>

<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand">
      <span class="footer-logo">Frota Para <span>Todos</span></span>
      <p>Conteúdo prático e independente para gestores de frota do Brasil.</p>
      <a href="https://www.youtube.com/channel/UCz31CtOANqSFuLEdFTi1iCQ" target="_blank" class="footer-yt">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.7 15.5V8.5l6.3 3.5-6.3 3.5z"/></svg>
        Canal YouTube
      </a>
      <a href="https://www.instagram.com/frotaparatodos" target="_blank" class="footer-yt">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
        Instagram
      </a>
    </div>
    <div class="footer-links">
      <h4>Categorias</h4>
      <a href="/?category=noticias">Notícias</a>
      <a href="/?category=analises">Análises</a>
      <a href="/?category=entrevistas">Entrevistas</a>
      <a href="/?category=casos">Casos de Sucesso</a>
      <a href="/?category=videos">Vídeos</a>
    </div>
    <div class="footer-links">
      <h4>Portal</h4>
      <a href="/">Início</a>
      <a href="/about">Sobre</a>
      <a href="/admin">Admin</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2026 Frota Para Todos · Julio César · Patrocinado por <a href="https://contelerastreador.com.br" target="_blank">Contele Fleet</a></p>
  </div>
</footer>

<script>
  function toggleMobileNav() {
    const nav = document.getElementById('mobile-nav');
    const btn = document.getElementById('hamburger');
    nav.classList.toggle('open');
    btn.classList.toggle('open');
    document.body.style.overflow = nav.classList.contains('open') ? 'hidden' : '';
  }
  window.addEventListener('scroll', () => {
    document.querySelector('.header').classList.toggle('header--scrolled', window.scrollY > 10);
  }, { passive: true });
</script>
</body>
</html>
```

- [ ] **Step 2: Adicionar rota `/about` em server.js**

Após `app.get('/admin', ...)`, adicionar:

```js
app.get('/about', (req, res) => res.sendFile(path.join(__dirname, 'public', 'about.html')));
```

- [ ] **Step 3: Adicionar "Sobre" no nav de index.html**

Em `<nav class="header-nav">`, adicionar após o último `<a>`:

```html
<a href="/about">Sobre</a>
```

Em `<div class="mobile-nav">`, adicionar após o último `<a>`:

```html
<a href="/about" onclick="toggleMobileNav()">Sobre</a>
```

Em `<div class="footer-links">` (a coluna "Portal" no footer), adicionar `<a href="/about">Sobre</a>` antes de `<a href="/admin">`.

- [ ] **Step 4: Adicionar CSS da página About em style.css**

```css
/* About Page */
.about-page { max-width: 760px; margin: 0 auto; padding: 48px 0; }

.about-header { margin-bottom: 48px; }

.about-title {
  font-family: var(--fpt-font-display);
  font-size: 44px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.5px;
  margin: 16px 0 20px;
}

.about-lead {
  font-size: 18px;
  color: var(--fpt-text-muted);
  line-height: 1.7;
}

.about-body { display: flex; flex-direction: column; gap: 40px; }

.about-section h2 {
  font-family: var(--fpt-font-display);
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 16px;
}

.about-section p {
  font-size: 16px;
  color: #d4c8e8;
  line-height: 1.8;
  margin-bottom: 12px;
}

.about-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.about-list li {
  font-size: 15px;
  color: #d4c8e8;
  padding-left: 20px;
  position: relative;
  line-height: 1.6;
}
.about-list li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: var(--fpt-purple);
}

.about-channels h2 {
  font-family: var(--fpt-font-display);
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 20px;
}

.about-links { display: flex; gap: 16px; flex-wrap: wrap; }

.about-channel-link {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--fpt-card);
  border: 1px solid rgba(139,35,229,0.2);
  border-radius: 12px;
  padding: 16px 20px;
  color: var(--fpt-text-light);
  text-decoration: none;
  transition: border-color 0.25s ease-out, background 0.25s ease-out;
  flex: 1;
  min-width: 200px;
}
.about-channel-link:hover {
  border-color: var(--fpt-purple);
  background: rgba(139,35,229,0.08);
  color: var(--fpt-text-light);
}
.about-channel-link strong { display: block; font-size: 15px; }
.about-channel-link span { font-size: 13px; color: var(--fpt-text-muted); }
```

- [ ] **Step 5: Testar**

```bash
curl -I http://localhost:3000/about
# Esperado: HTTP/1.1 200 OK
```

Abrir `http://localhost:3000/about` no browser. Verificar que a página renderiza com o conteúdo editorial, links para YouTube e Instagram, e o nav "Sobre" aparece destacado.

- [ ] **Step 6: Commit**

```bash
git add public/about.html server.js public/index.html public/style.css
git commit -m "feat(fpt-portal): página Sobre + rota /about + link 'Sobre' no nav e footer"
```

---

## Task 7: Instagram + Social Links no Index e Post

**Files:**
- Modify: `public/index.html` (footer-brand)
- Modify: `public/post.html` (footer)

- [ ] **Step 1: Adicionar Instagram no footer de index.html**

Em `public/index.html`, dentro de `<div class="footer-brand">`, após o `<a class="footer-yt">` do YouTube, adicionar:

```html
<a href="https://www.instagram.com/frotaparatodos" target="_blank" class="footer-yt">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
  Instagram
</a>
```

Em `<div class="footer-links">` (coluna "Portal"), adicionar `<a href="/about">Sobre</a>` antes de `<a href="/admin">`.

- [ ] **Step 2: Atualizar footer de post.html**

Substituir o footer atual de `post.html`:

```html
<footer class="footer">
  <p>© 2026 Frota Para Todos · Julio César</p>
</footer>
```

Por:

```html
<footer class="footer">
  <div class="footer-grid">
    <div class="footer-brand">
      <span class="footer-logo">Frota Para <span>Todos</span></span>
      <p>Conteúdo prático e independente para gestores de frota do Brasil.</p>
      <a href="https://www.youtube.com/channel/UCz31CtOANqSFuLEdFTi1iCQ" target="_blank" class="footer-yt">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.7 15.5V8.5l6.3 3.5-6.3 3.5z"/></svg>
        Canal YouTube
      </a>
      <a href="https://www.instagram.com/frotaparatodos" target="_blank" class="footer-yt">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
        Instagram
      </a>
    </div>
    <div class="footer-links">
      <h4>Categorias</h4>
      <a href="/?category=noticias">Notícias</a>
      <a href="/?category=analises">Análises</a>
      <a href="/?category=entrevistas">Entrevistas</a>
      <a href="/?category=casos">Casos de Sucesso</a>
      <a href="/?category=videos">Vídeos</a>
    </div>
    <div class="footer-links">
      <h4>Portal</h4>
      <a href="/">Início</a>
      <a href="/about">Sobre</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2026 Frota Para Todos · Julio César · Patrocinado por <a href="https://contelerastreador.com.br" target="_blank">Contele Fleet</a></p>
  </div>
</footer>
```

- [ ] **Step 3: Verificar no browser**

Abrir `http://localhost:3000`. Rolar até o footer. Verificar dois botões: "Canal YouTube" e "Instagram" lado a lado. Clicar em Instagram → deve ir para instagram.com/frotaparatodos.

- [ ] **Step 4: Commit**

```bash
git add public/index.html public/post.html
git commit -m "feat(fpt-portal): Instagram link no footer (index + post) + link Sobre no nav"
```

---

## Task 8: Suporte a Múltiplos Patrocinadores

**Files:**
- Modify: `public/index.html` (função `loadSponsors()`)
- Modify: `public/style.css`

- [ ] **Step 1: Atualizar `loadSponsors()` em index.html para renderizar slots**

Localizar a função `loadSponsors()` no `<script>` de `index.html`. Após a renderização do `s.master`, adicionar renderização dos slots:

```js
if (s.slots && s.slots.length > 0) {
  const slotsHtml = s.slots.map(slot => `
    <a href="${slot.url.startsWith('https://') ? slot.url : '#'}" target="_blank" class="sponsor-slot">
      <strong>${esc(slot.name)}</strong>
      <span>${esc(slot.tagline)}</span>
    </a>`).join('');
  const existing = document.getElementById('footer-sponsors').innerHTML;
  document.getElementById('footer-sponsors').innerHTML = existing + `
    <div class="footer-slots">
      <p style="font-size:11px;color:#4a4a6a;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Apoiadores</p>
      <div class="sponsor-slots-grid">${slotsHtml}</div>
    </div>`;
}
```

A função `esc` já está definida no escopo global — reutilizá-la.

- [ ] **Step 2: Adicionar CSS para slots em style.css**

```css
/* Sponsor Slots */
.footer-slots {
  padding: 16px 0 24px;
  margin-bottom: 24px;
  border-bottom: 1px solid rgba(139,35,229,0.1);
}

.sponsor-slots-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.sponsor-slot {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: rgba(139,35,229,0.06);
  border: 1px solid rgba(139,35,229,0.15);
  border-radius: 8px;
  padding: 10px 16px;
  color: var(--fpt-text-light);
  text-decoration: none;
  transition: border-color 0.2s ease-out;
  min-width: 160px;
}
.sponsor-slot:hover { border-color: var(--fpt-purple); color: var(--fpt-text-light); }
.sponsor-slot strong { font-size: 13px; color: var(--fpt-purple); }
.sponsor-slot span { font-size: 12px; color: var(--fpt-text-muted); }
```

- [ ] **Step 3: Testar com slot de exemplo**

Temporariamente em `sponsors.js`, adicionar um slot de teste:

```js
slots: [
  { name: "Teste Patrocinador", tagline: "Descrição curta aqui", url: "https://example.com", cta: "Saiba mais" },
],
```

Reiniciar servidor, abrir `http://localhost:3000`, rolar até o footer, verificar que a seção "Apoiadores" aparece com o card do slot. Remover o slot de teste depois.

- [ ] **Step 4: Remover slot de teste de sponsors.js**

```js
slots: [
  // Slots disponíveis para outros patrocinadores
  // { name: "", tagline: "", url: "", cta: "" },
],
```

- [ ] **Step 5: Commit**

```bash
git add public/index.html public/style.css sponsors.js
git commit -m "feat(fpt-portal): suporte a múltiplos patrocinadores — slots renderizados no footer"
```

---

## Responsividade (ajustes nas media queries)

Após todas as tasks, adicionar em `style.css` dentro do bloco `@media (max-width: 640px)`:

```css
.related-grid { grid-template-columns: 1fr; }
.about-title { font-size: 28px; }
.about-links { flex-direction: column; }
.search-box input[type="search"] { width: 150px; }
```

Commit:

```bash
git add public/style.css
git commit -m "feat(fpt-portal): ajustes responsividade mobile — related grid, about, search"
```

---

## Self-Review

**Spec coverage:**
- ✅ Busca por tema → Tasks 1+2
- ✅ Instagram → Tasks 6+7
- ✅ SEO (sitemap, robots, JSON-LD, OG) → Task 3
- ✅ Artigos relacionados → Task 4
- ✅ Share buttons → Task 5
- ✅ Página Sobre → Task 6
- ✅ Múltiplos patrocinadores → Task 8

**Placeholder scan:** Nenhum TBD encontrado. Todos os steps têm código real.

**Type consistency:** `db.search()` retorna array de posts (mesmo formato de `getPublished()`). `db.getRelated()` idem. Funções `esc()` e `formatDate()` reutilizadas de cada página. `CATEGORY_LABELS` duplicado em `loadRelated()` — intencional, subagent pode estar lendo task isolada.
