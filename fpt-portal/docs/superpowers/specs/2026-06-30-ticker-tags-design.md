# Spec: Ticker de Notícias + Tags Livres
**Data:** 2026-06-30  
**Status:** Aprovado

## 1. Ticker de Últimas Notícias

**O que é:** Faixa scrolling horizontal abaixo do header exibindo os 5 posts mais recentes.

**Comportamento:**
- Busca os 5 posts mais recentes via `/api/posts?limit=5` (já existe)
- Animação CSS marquee (scroll infinito da direita para a esquerda)
- Cada item: `• CATEGORIA — Título do artigo`
- Clique abre o artigo (`trackAndOpen`)
- Pausa animação ao hover

**Sem mudanças de backend** — usa endpoint existente.

---

## 2. Tags Livres

**O que é:** Sistema de tags livres por artigo (ex: `#cpk`, `#multa`) com filtro na listagem.

**Backend:**
- Novo campo `tags TEXT DEFAULT ''` na tabela `posts` (migration)
- `GET /api/posts` inclui campo `tags` na resposta
- `GET /api/posts?tag=cpk` filtra posts que contenham a tag
- `GET /api/tags` retorna lista de todas as tags únicas (para futuras melhorias)

**Cards (index.html):**
- Exibe pills de tags no rodapé do card (somente se houver tags)
- Clique numa tag: filtra listagem por aquela tag (sem recarregar página)

**Admin:**
- Campo de texto para tags separadas por vírgula no formulário de criação/edição

**Formato de armazenamento:** string separada por vírgula (`cpk,multa,telemetria`)
