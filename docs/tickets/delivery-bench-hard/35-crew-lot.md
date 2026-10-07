---
ticket_schema: 1
ticket_id: "DBH-35"
execution_mode: AFK
blocked_by:
  - "DBH-34"
---

# DBH-35 — Lotto Crew e confronto con pi-tools

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:35`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md)

## Parent Spec
[delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md), Verification e Gates.

## What to Build
Il lotto `dbh-crew` con `crew-1` e `crew-2`, catene da 4, 3 ripetizioni × 3 scenari, stesse
suite e stesso modello di `dbh-luna3d`, lanciato in modo visibile come i lotti precedenti. Poi il
report a confronto con `pi-tools` e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [ ] Il lotto finisce entro 25 $ e 24 ore, oppure si ferma al tetto con il motivo registrato.
- [ ] Il report confronta accettazione, costo (principale e worker), tempo e test nascosti extra
      con `pi-tools` di `dbh-luna3d`.
- [ ] Niente sotto `~/.pi/agent/messenger` è cambiato durante il lotto.

## Frontier
Pronto: DBH-34 fatto e giudizio di qualità finito.

## Gates
Come la spec: 25 $ a prezzo di listino e 24 ore per tentativo, al massimo 2 tentativi; prima del
lotto da 12; un solo lotto alla volta; il checkout principale di `agent-skills` non si aggiorna
durante il lotto.

## Step-by-Step Implementation Plan
1. Preflight, autorità del lotto con i gate, `init-lot`.
2. Avvio visibile e watcher.
3. Report e giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Lotto da 12.
