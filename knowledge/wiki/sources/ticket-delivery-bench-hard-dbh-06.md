---
type: source
title: "DBH-06 — Scenario `sql-engine`"
identity_key: ticket:delivery-bench-hard/DBH-06
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/06-scenario-sql-engine.md
source_digest: sha256:d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-28
created_provenance: git-commit
disposition_changed: 2026-09-28
disposition_changed_provenance: git-rename
---

# DBH-06 — Scenario `sql-engine`

Compiled from `docs/tickets/delivery-bench-hard/done/06-scenario-sql-engine.md`. Identity is `ticket:delivery-bench-hard/DBH-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-28** via `git-commit`
- Disposition changed: **2026-09-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-02]] — `ticket:delivery-bench-hard/DBH-02`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-04]] — `ticket:delivery-bench-hard/DBH-04`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-06.md","payload_bytes":4995,"payload_sha256":"d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173"}],"payload_bytes":4995,"payload_sha256":"d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173","schema":1,"source_digest":"sha256:d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173","source_identity":"ticket:delivery-bench-hard/DBH-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4995,"payload_sha256":"d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173","schema":1,"source_digest":"sha256:d74a07bc3b61186b623eb216b325c38df0665941c31b2899fee987fdbce43173","source_identity":"ticket:delivery-bench-hard/DBH-06"} -->
```markdown
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
- [x] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [x] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [x] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [x] I risultati attesi non si ricalcolano al momento del giudizio. Due giudizi dello stesso
  albero danno risultati identici. La suite resta sotto il timeout, e il tempo misurato è
  registrato.
- [x] Un braccio può installare le dipendenze e provare dall'host Windows con il comando di test
  dello scenario.
- [x] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Outcome
2026-09-28. Lo scenario è `scenarios/sql-engine/` nel repo privato, commit `9bbc88d`.
- **Seme**: il sorgente di sqlglot 30.13.0 pubblicato su PyPI, con la sua licenza MIT e la sua
  suite di test, più `dev.py` e una nota di sviluppo in spagnolo: 335 file in tutto.
  `python dev.py test` dall'host Windows costruisce l'immagine di sviluppo con le dipendenze
  fissate e passa la suite della release (1247 test) in 77 s.
- **Richieste**: 12, in spagnolo, ciascuna con il canarino.
- **Suite nascosta**: a N=12 conta 90 controlli: 44 feature, 38 latenti, 7 trappole e un
  invariante, la suite pristina della release. I risultati attesi stanno in 9 corpora congelati
  (209 query): 8 calcolati una volta da DuckDB, uno dal riferimento e confrontato con DuckDB. Il
  giudice li confronta e basta. L'immagine del giudice è `python:3.12-slim` con 11 dipendenze a
  versione fissata, installate alla costruzione, e il giudizio gira con `--network none`.
- **Riferimento e trappole**: il riferimento è stato scritto in un repo di lavoro, con un tag
  per richiesta, e gli overlay si generano per differenza dal seme con lo stesso strumento di
  DBH-05. L'overlay trappola aggiunge al riferimento una modifica puntuale per ogni tentazione.
- **Verifica** (`verify_scenario.py --twice`, giudice pubblico di `main` `fd6c51e`): 36 giudizi
  su 36 con l'esito atteso (riferimento, stub e trappola per ogni N). Lo stub passa solo
  l'invariante, e le trappole non hanno collaterali. Il doppio giudizio a N=12 è identico (90
  controlli, 193,8 e 195,9 s). Un giudizio dura da 100 a 225 s, con un timeout di 1500 s. Il
  report è `results/dbh06-sql-engine-verify.json` (sha256 `8522ddfc…`), e la suite ha sha256
  `5b029cb4…`.
- **Scostamenti e difetti trovati**: due query dei corpora delle feature sono state cambiate
  perché non cadessero nel caso di una trappola: violare una trappola non deve costare anche una
  feature. Un latente che lo stub passava a vuoto ora esercita prima la feature. Il
  congelamento dei risultati attesi ora è deterministico byte per byte, e un corpus che aveva
  perso i riferimenti a gruppi delle sue sostituzioni li ha ritrovati. Le prove del riferimento
  dell'ultima richiesta hanno trovato un suo difetto, corretto prima del tag.

## Frontier
Chiuso.

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

```
