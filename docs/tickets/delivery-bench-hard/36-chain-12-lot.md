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
- [x] Preflight senza lotto dei tre bracci riuscito.
- [x] Il lotto finisce entro 24 ore, oppure si ferma al tetto di tempo con il motivo
      registrato; la spesa a prezzo di listino è riportata.
- [x] Il report confronta i bracci per richiesta 1–12 e con le catene da 4, giri di `/goal`
      compresi.

## Evidence
- Preflight senza lotto dei tre bracci ok prima del lancio (2026-10-07).
- Lotto `dbh-chain12`: 2026-10-07T17:07Z → 2026-10-08T16:52Z (23 h 45 min), 27 celle,
  318 tentativi, 304 richieste giudicate, nessun tetto di catena raggiunto. Spesa a listino
  43,20 USD (40,84 agent, 2,36 ritentativi `infra:provider`), valutatore `/goal` escluso.
- Celle invalidate dall'audit: `crdt-yjs.pi-full.r1` (cross-cell), `sql-engine.pi-full.r2`
  (private-path), `sql-engine.pi-full.r3` (cross-cell, private-path).
- Accettazione (celle valide) per richieste 1-4 / 5-8 / 9-12, totale; catene da 4, richieste 1-4:
  - pi-tools 64% / 58% / 72%, 70/108; catene da 4 30/36 (83%).
  - pi-full 88% / 62% / 88%, 57/72; catene da 4 29/36 (81%).
  - bare-goal 83% / 67% / 69%, 79/108; catene da 4 25/36 (69%).
- Giri di `/goal` per richiesta: mediana 1 / 1 / 2 (pi-tools / pi-full / bare-goal), massimo
  97 / 32 / 500. Quasi tutto l'eccesso è un difetto del banco: 1.118 dei 1.500 verdetti
  «not yet met» chiedono la prova che TASK.md sia «nuovo e distinto» (DBH-43). Tempo, costo e
  giri sono gonfiati da questo; l'accettazione sui test nascosti molto meno.
- Report completo nel repo privato: `results/dbh-chain12/report.md`.

## Frontier
Manca solo il giudizio di qualità, dopo la fine di `dbh-vague` (un lotto alla volta).

## Gates
Come la spec: nessun tetto di spesa (abbonamento a canone fisso), 24 ore per tentativo, al massimo 2 tentativi; un solo
lotto alla volta; il checkout principale di `agent-skills` non si aggiorna durante il lotto.

## Step-by-Step Implementation Plan
1. Preflight, autorità del lotto con i gate, `init-lot`.
2. Avvio visibile e watcher; controllo della spesa proiettata.
3. Report e giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Bracci Crew sulle catene da 12.
