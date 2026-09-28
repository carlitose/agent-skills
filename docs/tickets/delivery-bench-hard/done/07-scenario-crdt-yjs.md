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
- [x] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [x] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [x] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [x] Due giudizi dello stesso albero danno risultati identici con gli stessi seed. La suite
  resta sotto il timeout, e il tempo misurato è registrato.
- [x] Un braccio può installare e provare dall'host Windows con il comando di test dello
  scenario.
- [x] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Outcome
2026-09-28. Lo scenario è `scenarios/crdt-yjs/` nel repo privato, commit `2bc0b55`.
- **Seme**: il sorgente di Yjs 13.6.27 con la sua licenza MIT, la sua suite di test e il suo
  lockfile, più `dev.py` e una nota di sviluppo in spagnolo: 73 file in tutto. Dall'host Windows,
  `python dev.py test` usa un'immagine di sviluppo con Node fissato per digest e le dipendenze
  del lockfile, e passa la suite della release (206 test) in 22 s. Anche `python dev.py lint`
  passa.
- **Richieste**: 12, in spagnolo, ciascuna con il canarino.
- **Suite nascosta**: a N=12 conta 78 controlli: 46 feature, 24 latenti, 7 trappole e un
  invariante, la suite pristina della release. La convergenza si prova con client simulati e
  seed fissi. La compatibilità del formato si prova con 9 fixture congelate: i documenti
  scritti dal seme e dai riferimenti alle prime 7 richieste, più il copione che li genera,
  identico dal seme all'ultimo tag. Il giudice le decodifica e basta. L'immagine del giudice è
  Node 22 fissato per digest con i 419 pacchetti del lockfile, installati alla costruzione, e il
  giudizio gira con `--network none`.
- **Riferimento e trappole**: il riferimento è stato scritto in un repo di lavoro, con un tag
  per richiesta, e gli overlay si generano per differenza dal seme con lo stesso strumento di
  DBH-05. L'overlay trappola aggiunge al riferimento una modifica puntuale per ogni tentazione.
- **Verifica** (`verify_scenario.py --twice`, giudice pubblico di `main` `ca9bf56`): 36 giudizi
  su 36 con l'esito atteso (riferimento, stub e trappola per ogni N), e le trappole non hanno
  collaterali. Lo stub passa l'invariante e un latente, come previsto dal catalogo: quel latente
  coglie la regressione che la prima correzione upstream del bug aveva introdotto. Il doppio
  giudizio a N=12 è identico (78 controlli, 31,9 e 31,8 s). Un giudizio dura da 20 a 37 s, con
  un timeout di 1200 s. Il report è `results/dbh07-crdt-yjs-verify.json` (sha256 `e17a9efa…`), e
  la suite ha sha256 `be281cb4…`.
- **Scostamenti e difetti trovati**:
  - Le prove di convergenza hanno trovato tre difetti nel riferimento di una richiesta e uno in
    quello di una richiesta successiva. Sono stati corretti prima dei tag, riscrivendo la storia
    del repo di lavoro. Dopo le correzioni, 600 seed casuali convergono tutti.
  - Quattro controlli che lo stub passava a vuoto ora esercitano prima la feature.
  - Cinque controlli chiedevano cose che Yjs non garantisce, e sono stati corretti.
  - Una limitazione di Yjs 13.6.27, che si vede anche sul seme senza modifiche, è neutralizzata
    nella suite, così non pesa sui bracci.
  - Un caso resta fuori scopo, senza controlli, ed è descritto nella nota dello scenario.

## Frontier
Chiuso.

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
