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
- [x] La skill installata è quella mergiata in DBH-40 e il lotto la lega.
- [x] Il lotto finisce entro 24 ore, oppure si ferma con il motivo registrato.
- [x] Il report confronta accettazione, latenti, costo, tempo mediano per catena e compiti con
      `pi-tools` e `crew-2`, e dice se la soglia (≥ 30/36, tempo ≤ 1,5 × `pi-tools`) è rispettata.
- [ ] Il giudizio di qualità è riportato a parte.

## Evidence
- Lotto `dbh-crew3` 2026-10-09 13:53Z → 2026-10-10 00:41Z (10 h 48), 3 celle alla volta, runner `167d60b`,
  skill installate `d269ca4` (con `crew-delivery`); 3 ritentativi d'infrastruttura non contati.
- Accettazione: crew-3 29/36, pi-tools 30/36, crew-2 30/36. Tempo mediano per catena 185 min
  (pi-tools 67, crew-2 173). Listino 12,13 $ (pi-tools 3,69, crew-2 5,71).
- Soglia (≥ 30/36 e tempo ≤ 1,5 × pi-tools): **non rispettata** su entrambi i criteri.
- Report: `results/dbh-crew3/report.md` nel repo privato.

## Frontier
Manca il criterio 4: il giudizio di qualità (ore di CPU, da lanciare quando l'utente lo dice).

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
