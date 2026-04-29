# Changelog: conteleteams.com.br

Registro de mudancas no server / landings Teams servidos via Express.

---

## 29/04/2026: Dedup Pipedrive-aware no /api/lead + race guard no submit

**Sintoma**: planilha de leads tinha 2 linhas com mesmo `nome | email | telefone | empresa` e timestamp identico (caso Lucas / MP do Brasil 26/04 09:01:26). Casos similares com janela maior (Rogerio Siqueira 23/04 + 29/04) viravam deals duplicados na pipeline 12 que Daniel fechava como DUPLICADO toda semana.

**Fix em 2 camadas**:

1. **Frontend (index.html)**: flag sincrona `window._formSubmitting` no inicio de `handleInsideForm` e do click handler `btn-accept-small-team`. Antes, `submitBtn.disabled = true` so era setado depois das validacoes, e double-click no mesmo tick passava 2x. Agora bloqueia re-entry no primeiro byte da funcao.

2. **Backend (server.js)**: `findExistingTeamsDeal(email, phone)` busca pessoa no Pipedrive por email exato + phone, recupera deals abertos de cada match, retorna o mais recente em pipeline 12 com idade < 30d. Se achar, `/api/lead` posta `sales-tracking` no contele-os com o `pipedrive_deal_id` existente (atualiza UTMs/gclid/GA4 do retorno), loga sheet com status `6_duplicado_pipedrive`, posta Discord avisando, e sai sem criar pessoa/deal duplicado.

**Por que dois lados**: client cobre 99% (double-click humano), Pipedrive cobre o resto (multi-device, retorno em outro dia, browser limpou localStorage).

**Nao cobre** (out of scope, decisao consciente):
- Lead com email e telefone *diferentes* mas mesmo CNPJ/empresa: cria deal novo. Vira housekeeping cron separado.
- Re-engagement do Leo SDR pra leads em stage avancado: contele-os#376 trata.

---

## 29/04/2026: Forward de delete do Pipedrive pro contele-os

**PR**: contele/growth#113

Handler `/api/pipedrive-webhook` agora detecta delete de deal (Pipedrive v1 `event=deleted.deal`, v2 `meta.action=delete`, header `x-event-action=deleted`) **antes** do fluxo normal de `change.deal` e dispara fire-and-forget `POST /api/webhooks/sales-lead-delete` no contele-os com `{ pipedrive_deal_id, deleted_at }`.

**Por que**:
- Cutover SDR v2 (28/04) so capturava `change.deal`. Quando vendedor deletava deal no Pipedrive, lead virava fantasma na visao `/vendas` ate o cron horario `pipedrive-reconcile` reconciliar.
- Real-time corta latencia de ate 1h pra <30s.

**Tecnicamente**:
- Filtro `pipelineId === 12` (Teams). Outros pipelines: ignora (Fleet trata no proprio server).
- Fallback de extracao de `deal_id`: `previous.id || meta.id || data.id` (cobre v1 + v2).
- Notifica Discord (`DISCORD_WEBHOOK_URL`) com payload de delete pra observabilidade.
- Cron `/api/cron/pipedrive-reconcile` no contele-os continua como rede de protecao (caso webhook caia).

**Pre-deploy**:
- Criar subscription Pipedrive Teams: `event_action=deleted`, `event_object=deal` -> `https://conteleteams.com.br/api/pipedrive-webhook`.
- Endpoint `sales-lead-delete` no contele-os precisa estar no ar antes (issue separada).
