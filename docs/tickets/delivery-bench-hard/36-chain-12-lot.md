---
ticket_schema: 1
ticket_id: "DBH-36"
execution_mode: AFK
blocked_by:
  - "DBH-35"
---

# DBH-36 — Lotto delle catene da 12

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:36`
- Role: `ticket`
- Parent: [delivery-bench-hard-chain-12.md](../../specs/delivery-bench-hard-chain-12.md)

## Parent Spec
[delivery-bench-hard-chain-12.md](../../specs/delivery-bench-hard-chain-12.md), Target behavior e Gates.

## What to Build
Il lotto `dbh-chain12`: `pi-tools`, `pi-full` e `bare-goal`, catene da 12, 3 ripetizioni × 3
scenari, `gpt-6-luna` medium, stesse suite di `dbh-luna3d`. Avvio visibile con il watcher, poi
il report a confronto con le catene da 4 (accettazione, costo, tempo, giri di `/goal`,
regressioni) e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [ ] Preflight senza lotto dei tre bracci riuscito.
- [ ] Il lotto finisce entro 60 $ e 24 ore, oppure si ferma prima del tetto con il motivo
      registrato.
- [ ] Il report confronta i bracci per richiesta 1–12 e con le catene da 4, giri di `/goal`
      compresi.

## Frontier
Bloccato dal lotto Crew (DBH-35): un solo lotto alla volta.

## Gates
Come la spec: 60 $ a prezzo di listino e 24 ore per tentativo, al massimo 2 tentativi; un solo
lotto alla volta; il checkout principale di `agent-skills` non si aggiorna durante il lotto.

## Step-by-Step Implementation Plan
1. Preflight, autorità del lotto con i gate, `init-lot`.
2. Avvio visibile e watcher; controllo della spesa proiettata.
3. Report e giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Bracci Crew sulle catene da 12.
