---
ticket_schema: 1
ticket_id: "IB-03"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-03 — `/loop` si ferma dopo giri senza novità

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:03`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../specs/invented-blocks-bench.md), Decision.

## What to Build
In `@carlitose86/pi-loop`: se due giri di fila non usano strumenti che cambiano qualcosa e la
risposta resta la stessa, il loop si ferma e lo dice all'utente.

## Acceptance Criteria
- [ ] Due giri senza novità fermano il loop con un messaggio; un giro con lavoro azzera il conto.
- [ ] Test mirati; pubblicazione da parte dell'utente (2FA) e pin.

## Frontier
Dopo IB-01 (serve la misura di oggi).

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Modifica e test in pi-loop. 2. Pubblicazione e pin. 3. Rimisura con IB-01.

## Testing Plan
- Test di pi-loop; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.
