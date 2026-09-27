---
ticket_schema: 1
ticket_id: "DBH-06"
execution_mode: AFK
blocked_by:
  - "DBH-02"
  - "DBH-04"
---

# DBH-06 — Scenario `sql-engine`

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:06`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Lo scenario Python nel repo privato (`scenarios/sql-engine/`), secondo il contratto
dell'oracolo.
- **Seme**: sqlglot a una release fissata, con la licenza MIT originale. Il lavoro riguarda
  l'executor in puro Python: parser, ottimizzatore, piano, esecuzione.
- **12 richieste originali** in spagnolo, ciascuna con il canarino. Ognuna vale una voce di
  release e attraversa ottimizzatore, planner ed executor.
- **Suite nascosta:**
  - un confronto differenziale su corpora di query generati con seed fisso e risultati attesi
    calcolati una volta da SQLite o DuckDB, poi congelati nella suite come in sqllogictest;
  - come invarianti, i test dell'executor di sqlglot e le feature delle richieste precedenti;
  - come latenti, i bug reali della release corretti upstream in seguito, ciascuno con il suo
    test di regressione;
  - le trappole del catalogo v2.
- **Immagine del giudice** con Python e dipendenze installate offline, usata con
  `--network none`.
- **Overlay** `reference/01..12` e `trap/01..12`, e `scenario.json` con `requests: 12`.

## Acceptance Criteria
- [ ] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [ ] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [ ] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [ ] I risultati attesi non si ricalcolano al momento del giudizio. Due giudizi dello stesso
  albero danno risultati identici. La suite resta sotto il timeout, e il tempo misurato è
  registrato.
- [ ] Un braccio può installare le dipendenze e provare dall'host Windows con il comando di test
  dello scenario.
- [ ] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Frontier
Bloccato da DBH-02 e DBH-04.

## Step-by-Step Implementation Plan
1. Fissare la release e le versioni delle dipendenze, e costruire l'immagine offline.
2. Scrivere il generatore dei corpora con seed, e congelare risultati attesi e digest.
3. Per ogni richiesta: testo, overlay di riferimento e controlli, più l'overlay trappola.
4. Verificare con `verify_scenario.py` e committare nel repo privato.

## Testing Plan
`verify_scenario.py` nel container: riferimento, stub, trappole e doppio giudizio per ogni N.

## Out of Scope
- Gli altri scenari.
- Lanciare bracci.
