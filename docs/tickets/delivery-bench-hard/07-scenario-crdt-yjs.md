---
ticket_schema: 1
ticket_id: "DBH-07"
execution_mode: AFK
blocked_by:
  - "DBH-02"
  - "DBH-04"
---

# DBH-07 — Scenario `crdt-yjs`

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:07`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Lo scenario JavaScript nel repo privato (`scenarios/crdt-yjs/`), secondo il contratto
dell'oracolo.
- **Seme**: Yjs a una release fissata, con la licenza MIT originale. È JavaScript con tipi JSDoc
  controllati da `tsc`.
- **12 richieste originali** in spagnolo, ciascuna con il canarino. Ognuna vale una voce di
  release e attraversa tipi condivisi, struttura interna, encoding degli update e undo.
- **Suite nascosta:**
  - test casuali di convergenza fra client simulati, con seed fissi elencati nella suite;
  - la decodifica dei documenti prodotti dal riferimento alle richieste precedenti, così un
    cambio di encoding che rompe la compatibilità si vede;
  - come invarianti, la suite di Yjs e le feature delle richieste precedenti;
  - come latenti, i bug reali della release corretti upstream in seguito;
  - le trappole del catalogo v2.
- **Immagine del giudice** con Node e `node_modules` del lockfile preinstallati, usata con
  `--network none`.
- **Overlay** `reference/01..12` e `trap/01..12`, e `scenario.json` con `requests: 12`.

## Acceptance Criteria
- [ ] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [ ] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [ ] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [ ] Due giudizi dello stesso albero danno risultati identici con gli stessi seed. La suite
  resta sotto il timeout, e il tempo misurato è registrato.
- [ ] Un braccio può installare e provare dall'host Windows con il comando di test dello
  scenario.
- [ ] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Frontier
Bloccato da DBH-02 e DBH-04.

## Step-by-Step Implementation Plan
1. Fissare la release e il lockfile, e costruire l'immagine offline.
2. Scrivere l'harness di convergenza con seed e i documenti di compatibilità.
3. Per ogni richiesta: testo, overlay di riferimento e controlli, più l'overlay trappola.
4. Verificare con `verify_scenario.py` e committare nel repo privato.

## Testing Plan
`verify_scenario.py` nel container: riferimento, stub, trappole e doppio giudizio per ogni N.

## Out of Scope
- Gli altri scenari.
- Lanciare bracci.
