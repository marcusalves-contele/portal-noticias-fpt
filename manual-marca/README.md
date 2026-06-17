# Manual de Marca : Contele

Material-fonte dos manuais de marca dos dois produtos Contele. Esta pasta é a **semente**: contém o conteúdo aprovado/em-construção que serve de fonte da verdade para o **manual de marca hospedado** que será montado em cima.

**Responsável pela construção do site:** Leonardo Teixeira (`leonardo.teixeira@contele.com.br`).

---

## O que tem aqui

| Pasta | Produto | Status do conteúdo |
|-------|---------|--------------------|
| `fleet-fpt/` | Contele Fleet (marca de conteúdo: Frota Para Todos / FPT) | **Maduro / canônico.** Manual fechado em mar/2026. |
| `teams/` | Contele Teams | **Em construção.** Plano de execução (Rarissa); ainda tem campos `[PENDENTE]` a preencher. |

### `fleet-fpt/`
- `brand-fpt.md` : manual de marca completo do FPT (posicionamento, arquétipo Sage Pragmático + Hero, voz, pilares, identidade visual).
- `brand-fpt-agent.md` : versão "bíblia da marca para IA". Tem os **design tokens exatos** (paleta `#8B23E5` etc., tipografia Montserrat) e os IDs das pastas de assets no Google Drive (logos, master). Carregar antes de produzir qualquer peça FPT.

> **Versão visual (humana) já hospedada:** `../contele-io/public/brand-fpt/index.html`, servido em **https://contele.com.br/brand-fpt/** (rota no `contele-io/server.js`). É a representação visual deste conteúdo para time/parceiros. Antes ficava no site pessoal do Marco (marcofassa-cto.web.app); migrada pro growth em jun/2026.
> Pendência de sync: o apêndice de agentes embutido no HTML ainda cita a URL antiga (marcofassa-cto). Atualizar via fluxo canônico (editar `brand-fpt-agent.md` → regenerar HTML), não direto no HTML.

### `teams/`
- `brand-contele-teams-plano.md` : plano + entregável do brand book Teams, seguindo o mesmo framework do FPT. É o ponto de partida; a Rarissa (`5513996542205`) é dona do conteúdo e tem base coletada no Notion (09/04).

---

## Fonte da verdade (lineage)

Estes arquivos são **cópias semeadas** do segundo cérebro do Marco (`obsidian-marco/DOCS/`):
- `fleet-fpt/brand-fpt.md` ← `DOCS/brand-fpt.md`
- `fleet-fpt/brand-fpt-agent.md` ← `DOCS/brand-fpt-agent.md`
- `teams/brand-contele-teams-plano.md` ← `DOCS/brand-contele-teams-plano-rari.md`

A decidir com o Marco: a partir de agora a cópia deste repo vira a fonte da verdade, ou continua espelho do vault? Enquanto não definido, **mudança de conteúdo de marca volta pro vault** para não divergir.

---

## Quando montar o site (convenção do monorepo growth)

> **Status FPT (jun/2026):** a versão visual do FPT já está hospedada, servida pelo serviço `contele-io/` em `https://contele.com.br/brand-fpt/` (não exigiu serviço novo). O caminho abaixo vale para um hub dedicado das duas marcas, se/quando for montado.

Este repo é um monorepo: cada serviço hospedado tem a própria pasta com `railway.json` + `watchPatterns` (deploy seletivo, ver README da raiz). **Esta pasta é só conteúdo (markdown): não tem `railway.json`, então não dispara deploy nenhum.**

Para publicar o manual hospedado:
1. Criar a pasta/serviço do site (ex: `manual-marca-site/` ou servir dentro de um site existente).
2. Adicionar `railway.json` com `watchPatterns` escopado pra pasta do serviço.
3. Branch principal = `master` (auto-deploy). Código em branch `fix/` ou `feat/` **não vai pra produção** até mergear no `master`.
4. Consumir o conteúdo de marca desta pasta como fonte.

Sugestão de escopo do site: um hub único com as duas marcas (Fleet/FPT e Teams), respeitando que a paleta/tipografia de cada produto é diferente.
