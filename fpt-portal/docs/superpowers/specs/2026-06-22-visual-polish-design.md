# Visual Polish — Portal FPT

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevar o portal de "funcional" para "editorial profissional" com polish completo: micro-interações, tipografia, animações e detalhes visuais — sem redesenhar a identidade existente.

**Architecture:** Todas as mudanças são em arquivos estáticos (`public/style.css`, `public/index.html`, `public/post.html`). Nenhuma alteração de backend. O servidor Express serve os arquivos como estão.

**Tech Stack:** HTML/CSS/JS vanilla, Montserrat (já carregado), sem dependências novas.

---

## Seção 1 — Home (`public/index.html` + `public/style.css`)

### Skeleton Loading
- Substitui `<div class="loading">Carregando artigos...</div>` por 6 cards skeleton animados
- CSS: `@keyframes skeleton-pulse` com `background` alternando entre `#0f0520` e `#1a0835`
- Skeleton tem as mesmas dimensões de um card real (imagem placeholder 180px + 3 linhas de texto)
- Removido após `loadPosts()` retornar dados

### Card Destaque (Featured Post)
- O primeiro post do grid ocupa 2 colunas: `grid-column: span 2`
- Imagem do card destaque tem altura 260px (vs 180px dos demais)
- Título do card destaque: 20px (vs 16px)
- Em mobile (≤640px): card destaque volta para 1 coluna

### Hover dos Cards
- `box-shadow: 0 8px 32px rgba(139, 35, 229, 0.2)` ao hover
- `border-color: rgba(139, 35, 229, 0.5)` ao hover (já existe, mantém)
- `transform: translateY(-6px)` ao hover (era -4px)
- Transição: `all 0.25s ease-out`

### Scroll-Reveal nos Cards
- `IntersectionObserver` com `threshold: 0.1`
- Cards começam com `opacity: 0; transform: translateY(20px)`
- Ao entrar no viewport: `opacity: 1; transform: translateY(0)` com `transition: 0.4s ease-out`
- Delay escalonado: cada card tem `transition-delay` de `index * 60ms` (máx 300ms)

---

## Seção 2 — Página de Artigo (`public/post.html` + `public/style.css`)

### Barra de Progresso de Leitura
- `<div id="reading-progress">` fixo no topo, `z-index: 200`, height: 3px
- Background: `linear-gradient(90deg, #8B23E5, #b56fff)`
- `width` atualizado via `scroll` event: `scrollY / (documentHeight - viewportHeight) * 100`
- Aparece apenas na página de artigo (inserido no `post.html`)

### Tempo Estimado de Leitura
- Calculado em JS: `Math.ceil(wordCount / 200)` minutos (200 palavras/minuto)
- `wordCount` = `content_html` sem tags HTML, split por espaços
- Exibido na `.article-meta`: `· 5 min de leitura`
- Mínimo exibido: 1 min

### Botão Voltar ao Topo
- `<button id="back-to-top">↑</button>` fixo no canto inferior direito
- Aparece com `opacity: 1` quando `scrollY > 400`, some com `opacity: 0`
- Click: `window.scrollTo({ top: 0, behavior: 'smooth' })`
- CSS: `position: fixed; bottom: 32px; right: 32px; width: 44px; height: 44px; border-radius: 50%; background: var(--fpt-purple); transition: opacity 0.3s`

### Tipografia do Artigo
- `.article-content` font-size: 17px → 18px
- `.article-content` line-height: 1.8 → 1.9
- `.article-content p` margin-bottom: 16px → 24px
- `.article` max-width: 780px → 760px (leve ajuste para conforto de leitura)

### Imagem de Capa
- Se `post.image_url` existir, inserida como banner full-width antes do conteúdo
- CSS: `width: 100%; max-height: 420px; object-fit: cover; border-radius: 12px; margin-bottom: 32px`
- Aparece após o `article-header`, antes do `article-content`

---

## Seção 3 — Global (todas as páginas)

### Header ao Rolar
- `scroll` event listener no `window`
- Quando `scrollY > 10`: adiciona classe `.header--scrolled`
- `.header--scrolled`: `border-bottom-color: rgba(139,35,229,0.5)` + `box-shadow: 0 4px 24px rgba(0,0,0,0.4)`
- Transição: `border-color 0.3s, box-shadow 0.3s`
- Implementado via `<script>` inline no final de cada HTML (index, post, admin)

### Transições Uniformes
- Substituir todos os `transition: X 0.2s` por `transition: X 0.25s ease-out` no style.css
- Afeta: `.card`, `.filter-btn`, `.btn`, `.back-link`, `.header-nav a`, `.sponsor-master`

### Scrollbar Customizada
- Adicionado no `:root` do style.css:
  ```css
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--fpt-dark); }
  ::-webkit-scrollbar-thumb { background: var(--fpt-purple-deep); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--fpt-purple); }
  ```

### Favicon
- Arquivo `public/favicon.svg`: círculo roxo com texto "FP" em branco, fonte Montserrat bold
- `<link rel="icon" type="image/svg+xml" href="/favicon.svg">` em todos os HTML

---

## Arquivos Modificados

| Arquivo | Tipo de mudança |
|---|---|
| `public/style.css` | Skeleton, hover cards, tipografia, back-to-top, scrollbar, header scroll, transições |
| `public/index.html` | Skeleton HTML, scroll-reveal JS, header scroll JS, featured card lógica |
| `public/post.html` | Reading progress HTML+JS, back-to-top HTML+JS, tempo de leitura JS, imagem de capa |
| `public/admin.html` | Header scroll JS |
| `public/favicon.svg` | Novo arquivo |

## Não incluído neste ciclo
- Mudanças de backend
- Redesign de identidade visual (cores, fontes)
- Novas funcionalidades (busca, paginação)
- Melhorias no admin além do header scroll
