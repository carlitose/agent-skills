---
ticket_schema: 1
ticket_id: "DBH-32"
execution_mode: AFK
blocked_by:
  - "DBH-29"
  - "DBH-30"
  - "DBH-31"
---

# DBH-32 — Pilota e giudizio completo

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:32`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
Pilota su 10 unità: una per braccio e scenario, più una scelta a caso con seme fisso. Per ogni unità si fanno due revisioni Opus e si applica la regola della spec:
- una revisione per unità, se i voti differiscono al massimo di 1 punto e i bug gravi coincidono;
- altrimenti tre revisioni, con la mediana.

Poi il giudizio completo di `dbh-luna3d` e `dbh-luna3e` e il report finale, con la spesa reale.

Spec: Pilot rule e Gates.

## Acceptance Criteria
- [x] Il pilota riporta tempo e costo per misura e per unità, e l'accordo tra le due revisioni.
- [x] Il giudizio completo copre tutte le 144 unità, con il report in `results/<lot>/quality/`.
- [x] Spesa reale e tempo sono riportati; i tentativi restano registrati.

## Evidence
- Pilota: 12 unità, accordo 10/12 tra le due revisioni, quindi tre revisioni con la mediana nel
  giudizio completo; spesa 5,52 $ (`results/quality-pilot/pilot.md`).
- Giudizio completo: 144 unità (136 con codice) con copertura, mutazione e 3 revisioni Opus
  ciascuna. I file per unità sono in `results/<lot>/quality/{coverage,mutation,review}/`, il
  report unico dei due lotti in `results/quality-full/report.md`.
- Tempo 9,6 ore; 408 revisioni per 105,32 $ a prezzo di listino (abbonamento).
- `lot files identical: True`: digest dei due lotti uguali prima e dopo (`run.json`).

## Frontier
Fatto.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Eseguire il pilota.
2. Scegliere il numero di revisioni.
3. Eseguire il giudizio completo.
4. Riportare all'utente.

## Testing Plan
- Esecuzione reale, controllando che `cell.json` e il ledger restino identici byte per byte.

## Out of Scope
- Rigiocare i bracci.
- Cambiare l'esito ufficiale.
