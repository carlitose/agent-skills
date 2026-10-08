---
ticket_schema: 1
ticket_id: "DBH-42"
execution_mode: AFK
blocked_by:
  - "DBH-40"
  - "DBH-41"
---

# DBH-42 — Lotto crew-3 e confronto

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:42`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md)

## Parent Spec
[delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md), Decisions 6–7, Target behavior 4 e Gates.

## What to Build
Installare `crew-delivery` (pin in `pi-personal-config`, `update:personal`, reload) tra due lotti;
poi il lotto `dbh-crew3` con `crew-3`, catene da 4, 3 ripetizioni × 3 scenari, `gpt-6-luna`
medium, lanciato in modo visibile. Report accanto a `pi-tools` (`dbh-luna3d`) e `crew-2`
(`dbh-crew`), verdetto sulla soglia, poi il giudizio di qualità.

## Acceptance Criteria
- [ ] La skill installata è quella mergiata in DBH-40 e il lotto la lega.
- [ ] Il lotto finisce entro 24 ore, oppure si ferma con il motivo registrato.
- [ ] Il report confronta accettazione, latenti, costo, tempo mediano per catena e compiti con
      `pi-tools` e `crew-2`, e dice se la soglia (≥ 30/36, tempo ≤ 1,5 × `pi-tools`) è rispettata.
- [ ] Il giudizio di qualità è riportato a parte.

## Frontier
Bloccato da DBH-41 e dalla fine di `dbh-chain12` e `dbh-vague`.

## Gates
Come la spec: un lotto completo per tentativo, nessun tetto di spesa, 24 ore, al massimo 2
tentativi; un solo lotto alla volta; installazione e aggiornamento del checkout principale solo
tra due lotti.

## Step-by-Step Implementation Plan
1. Installazione tra due lotti, preflight `crew-3`, autorità con i gate, `init-lot`.
2. Avvio visibile e watcher.
3. Report, verdetto sulla soglia, giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Portare le regole nei progetti fuori dal banco.
