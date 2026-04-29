# Changelog: conteleteams.com.br

Registro de mudancas no server / landings Teams servidos via Express.

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
