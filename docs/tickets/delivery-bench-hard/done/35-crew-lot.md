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
- Parent: [delivery-bench-hard-crew-arms.md](../../../specs/delivery-bench-hard-crew-arms.md)

## Parent Spec
[delivery-bench-hard-crew-arms.md](../../../specs/delivery-bench-hard-crew-arms.md), Verification e Gates.

## What to Build
Il lotto `dbh-crew` con `crew-1` e `crew-2`, catene da 4, 3 ripetizioni × 3 scenari, stesse
suite e stesso modello di `dbh-luna3d`, lanciato in modo visibile come i lotti precedenti. Poi il
report a confronto con `pi-tools` e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [x] Il lotto finisce entro 25 $ e 24 ore, oppure si ferma al tetto con il motivo registrato.
- [x] Il report confronta accettazione, costo (principale e worker), tempo e test nascosti extra
      con `pi-tools` di `dbh-luna3d`.
- [x] Niente sotto `~/.pi/agent/messenger` è cambiato durante il lotto.

## Evidence
- Lotto `dbh-crew` (runner `bf297b9`, skill installate `4ff8ee9`), avvio visibile il
  2026-10-07 alle 07:34Z, 18 celle su 18 giudicate alle 14:10Z; nessuna cella invalidata o
  ferma; 3 tentativi infrastrutturali `infra:provider` ripetuti dal runner. Spesa a listino
  circa 9,8 $, sotto il tetto di 25 $.
- Report `profile_report.py --lot dbh-crew --arm-from pi-tools=dbh-luna3d` (catene da 4):

  | Braccio | Accettate | Latenti trovati | USD | Catena mediana s |
  |---|---:|---:|---:|---:|
  | pi-tools | 30/36 | 82/99 | 3,69 | 4044 |
  | crew-1 | 24/36 | 75/99 | 4,09 (principale 4,01, worker 0,18) | 4798 |
  | crew-2 | 30/36 | 71/99 | 5,72 (principale 2,46, worker 3,24) | 10404 |

  Sessioni worker: crew-1 24, crew-2 423. Giri di `/goal`: crew-1 121, crew-2 59.
  Invarianti rotti a fine catena: pi-tools 1/126, crew-1 e crew-2 0/126.
- `host-messenger-before.json` e `host-messenger-after.json` identici.
- Il giudizio di qualità delle unità (copertura, mutazioni, review Opus) è una misura separata:
  avviato il 2026-10-07 durante `dbh-chain12`, con le mutazioni a 2 job; risultati in
  `results/quality-crew`. Non cambia il verdetto ufficiale.

## Frontier
Fatto.

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
