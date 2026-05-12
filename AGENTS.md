# AGENTS.md - Guia para Claude em Pipeline Autonomo

Este arquivo e lido pelo Claude rodando em GitHub Actions (workflows em `.github/workflows/auto-*.yml`). Tudo aqui e norma para implementacao automatizada de issues.

## Modo de operacao

Quando uma issue ganha label `auto-implement`, o pipeline dispara e Claude opera autonomamente. Sem humano no loop ate o PR estar pronto para review.

Fluxo:
1. **auto-implement.yml**: issue label -> PR draft
2. **auto-review.yml**: PR draft -> review autonomo -> APROVA ou solicita mudancas
3. **Merge manual** (humano final): aprovacao + merge pela UI do GitHub
4. **auto-notify.yml**: PR merged -> CHANGELOG + comentario na issue

## Regras nao-negociaveis

### Git
- NUNCA commit direto em `master`. Sempre branch + PR draft.
- Branch: `auto/issue-<numero>-<slug-curto>`
- Commits: `fix(prism-os): ...`, `feat(prism-os): ...`, `chore: ...` (Conventional Commits)
- Mensagem em portugues, sem emojis, sem travessao (`:` ou `-`).
- Co-author obrigatorio: `Co-Authored-By: Claude <noreply@anthropic.com>`
- Quando criar commit, use `git config user.email "claude@anthropic.com"` e `git config user.name "Claude"`.

### Escopo
- Resolva APENAS o que a issue pede. Nao refatore ao redor.
- Se identificar bug adjacente ou debito tecnico, abra issue separada via `gh issue create`, nao consolide.
- Se a issue estiver mal-especificada, abra PR draft com analise tecnica e marque label `needs-refinement`, nao implemente as cegas.

### Seguranca
- NUNCA exponha secrets em logs, codigo, ou commits.
- NUNCA toque em `.github/workflows/` (esses arquivos so o Marco autoriza alteracao).
- NUNCA mexa em `.env` ou arquivos com credenciais.
- Se precisar de variavel de ambiente nova, documente no PR e adicione em `.env.example` (nao commit `.env`).

### Codigo
- Siga convencoes do submodulo afetado. Leia o `CLAUDE.md` local primeiro.
- Sem comentarios desnecessarios (so quando o "porque" nao for obvio).
- Sem error handling defensivo demais (so em fronteira: input do usuario, API externa).
- Imports organizados (stdlib -> third-party -> local).
- Python: respeitar PEP 8, type hints quando ja existirem no arquivo.

## Estrutura do repo

```
growth-contele/
├── .github/workflows/      # PROTEGIDO. So Marco edita.
├── AGENTS.md               # Este arquivo
├── CLAUDE.md               # Visao geral do repo
├── prism-os/               # Sistema de producao de conteudo (Python)
│   ├── CLAUDE.md           # Biblia do PRISM OS
│   ├── nutella-creator/    # Dashboard URL -> cortes + thumbs
│   │   └── CLAUDE.md       # Detalhes do submodulo
│   └── thumbnail-ai-creator/ # CLI thumbnails standalone
├── contele-referral-page/  # Landing "Indique e Ganhe" (React + Vite)
├── contele-io/             # Site contele.io
├── conteleteams.com.br/    # Landing Teams
├── contelefleet.com.br/    # Landing Fleet
└── ... outros projetos
```

## Como investigar antes de mexer

1. Leia o CLAUDE.md mais proximo do arquivo afetado.
2. Use `grep -r "termo" prism-os/` para localizar pontos relevantes.
3. Use `gh issue view <num>` para reler a issue completa, incluindo comentarios.
4. Cheque git log do arquivo: `git log --oneline -10 -- path/to/file.py`.
5. Se encontrar codigo similar resolvendo problema parecido, prefira reusar.

## Validacao local

PRISM OS nao tem suite de testes formal. Pra cada mudanca:
- **Python**: `python3 -m py_compile path/to/file.py` (valida sintaxe)
- **JS/TS**: `node --check path/to/file.js` ou `npx tsc --noEmit` se vite/tsconfig presente
- Se a mudanca afeta endpoint/UI, descreva no PR como testar manualmente (passos exatos)

## PR draft: o que descrever

Template obrigatorio no body do PR:

```markdown
## Issue
Closes #<numero>

## Problema (como entendi)
<descricao do bug/feature em 2-3 linhas>

## Causa raiz
<o que causa o problema>

## Mudanca aplicada
<o que foi feito tecnicamente, qual arquivo, qual linha>

## Como testar
<passos exatos>

## Riscos
<o que pode quebrar / o que nao foi alterado mas e adjacente>
```

## Cenarios de bloqueio (escalar pro Marco)

Pare a execucao e pinge `@MarcoFassa` em comentario se:
- A issue exige decisao de produto (escolha entre A vs B, mudanca de comportamento publico).
- Codigo afetado mexe em integracao externa que voce nao consegue testar (Pipedrive, n8n, WhatsApp).
- Identificou bug critico em producao adjacente.
- O fix exige mudanca em mais de 3 arquivos ou >100 linhas.

## Modelos

- Implementacao: Opus 4.7 (`--model claude-opus-4-7`)
- Review: Opus 4.7
- Notify/changelog: Haiku 4.5 (`--model claude-haiku-4-5`)

## Wikilinks de contexto

- `prism-os/CLAUDE.md` - Visao geral do PRISM OS
- `prism-os/nutella-creator/CLAUDE.md` - Dashboard nutella
- `prism-os/thumbnail-ai-creator/CLAUDE.md` - Thumbs standalone
- `CLAUDE.md` - Repo growth como um todo
