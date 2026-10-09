---
ticket_schema: 1
ticket_id: "DBH-43"
execution_mode: AFK
blocked_by:
  - "DBH-39"
---

# DBH-43 — Condizione del `/goal` senza la premessa «TASK.md ha cambiado»

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:43`
- Role: `ticket`
- Parent: [delivery-bench-hard-chain-12.md](../../specs/delivery-bench-hard-chain-12.md)

## Parent Spec
[delivery-bench-hard-chain-12.md](../../specs/delivery-bench-hard-chain-12.md), Failure modes e
Verification: difetto del banco trovato nel report di DBH-36.

## What to Build
Dalla richiesta 2 in poi, `NEXT_GOAL_CONDITION` in `runner.py` inizia con «TASK.md ha cambiado:
ahora contiene un encargo nuevo, distinto del anterior». Il valutatore la tratta come un requisito
da provare. Il modello rilegge TASK.md, trova il compito che ha appena finito e lo dice; il
valutatore lo rimanda indietro. In `dbh-chain12` succede in 1.118 dei 1.500 verdetti «not yet met»
(fino a 469 giri in un tentativo, poi timeout). Nelle catene da 4 succede meno (luna3d pi-full 40
su 55).

La premessa resta nel prompt (`NEXT_PROMPT`, che serve contro DBH-25); la condizione del goal dice
solo cosa deve essere vero alla fine: «Lo que pide ahora TASK.md … esta hecho por completo …».

## Acceptance Criteria
- [x] `NEXT_GOAL_CONDITION` non afferma che TASK.md è cambiato; `NEXT_PROMPT` resta com'è.
- [x] Un test in `test_runner.py` fissa che la condizione della richiesta 2+ non contiene
      «ha cambiado» né «distinto».
- [ ] Il report del primo lotto dopo la correzione riporta la stessa misura (verdetti che
      incolpano un TASK.md non cambiato), attesa vicina a zero.

## Evidence
- `runner.py`: `NEXT_GOAL_CONDITION` = `GOAL_CONDITION` con «Lo que pide ahora»; la premessa resta
  solo in `NEXT_PROMPT`. `test_runner.py` lo fissa; suite `test_runner` 67 test OK.
- Fatto dopo la fine di `dbh-vague` (2026-10-08T23:54Z).

## Frontier
Manca il criterio 3: la misura nel report del primo lotto dopo la correzione (`dbh-crew3`, DBH-42).

## Gates
- **Attempt:** una PR su `agent-skills` con CI verde, fatta dopo la fine di `dbh-vague` e prima di
  `dbh-crew3` (DBH-42).
- **Budget:** nessuna spesa; solo test locali e CI. **Time:** 2 ore. **Maximum attempts:** 2.
- **Approvals:** l'agente fa il merge con CI verde (regola dei ticket DBH).
- **Exact version:** il commit di `main` che contiene la correzione; `dbh-crew3` lo registra in
  `lot.json`.
- **Existing blocks searched:** un solo lotto alla volta; il checkout principale non si aggiorna
  durante un lotto (memoria `dbh-chain12-gates`).

## Step-by-Step Implementation Plan
1. Test che fallisce sulla condizione attuale.
2. Nuova `NEXT_GOAL_CONDITION`.
3. Suite `test_runner`.

## Testing Plan
- `python -B -m unittest test_runner` in `benchmarks/delivery-bench`.

## Out of Scope
- Rifare i lotti già chiusi; i loro numeri restano con questa nota.
