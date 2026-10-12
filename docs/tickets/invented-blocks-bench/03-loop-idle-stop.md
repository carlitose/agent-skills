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
- [x] Due giri senza novità fermano il loop con un messaggio; un giro con lavoro azzera il conto.
- [ ] Test mirati; pubblicazione da parte dell'utente (2FA) e pin. Test e merge fatti; manca la
      pubblicazione di 0.2.0 e il pin.

## Evidence
- carlitose/pi-loop #1 (`d0940ff`): confronto di novità con un modello per giro (scelta (a)
  dell'utente: nella `main-stop` ogni giro riscrive `OUTBOX.md` con parole diverse, un confronto
  meccanico non lo vedrebbe); `PI_LOOP_NOVELTY=0` lo spegne.
- carlitose/pi-loop #2 (`bd58b26`): si confrontano solo i giri del loop; un turno avviato da
  un'altra estensione (il rimando di `block-check`) non conta e non azzera.
- Misura con pi-loop locale: `main-stop` 3/3, loop fermo dopo 2 giri (era 0/3, fino a 326 giri).

## Frontier
Manca solo: l'utente pubblica `@carlitose86/pi-loop` 0.2.0 (2FA), poi pin e reload.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Modifica e test in pi-loop. 2. Pubblicazione e pin. 3. Rimisura con IB-01.

## Testing Plan
- Test di pi-loop; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.
