---
type: source
title: "DBH-10 — Riprendere l'ultima richiesta interrotta di una catena"
identity_key: ticket:delivery-bench-hard/DBH-10
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/10-resume-last-interrupted-request.md
source_digest: sha256:63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-27
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# DBH-10 — Riprendere l'ultima richiesta interrotta di una catena

Compiled from `docs/tickets/delivery-bench-hard/done/10-resume-last-interrupted-request.md`. Identity is `ticket:delivery-bench-hard/DBH-10`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-27** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-02]] — `ticket:delivery-bench-hard/DBH-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-10.md","payload_bytes":4095,"payload_sha256":"63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389"}],"payload_bytes":4095,"payload_sha256":"63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389","schema":1,"source_digest":"sha256:63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389","source_identity":"ticket:delivery-bench-hard/DBH-10","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4095,"payload_sha256":"63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389","schema":1,"source_digest":"sha256:63ff375221040d3cd91c9e3156d03295b1650dad95ad341dbf01ca1d17880389","source_identity":"ticket:delivery-bench-hard/DBH-10"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-10"
execution_mode: AFK
blocked_by:
  - "DBH-02"
---

# DBH-10 — Riprendere l'ultima richiesta interrotta di una catena

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:10`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner trovato durante DBH-03. Quando l'host si ferma durante una richiesta, il
record della cella resta con quella richiesta in stato `running`. Il runner dovrebbe ripartire
dallo snapshot, registrare il tentativo perso come `infra:host` e rifare la richiesta. Lo fa solo
se la richiesta interrotta non è l'ultima della catena.
- **Osservato**: in `luna-calib` la richiesta 3 di una cella è rimasta `running` perché il lotto è
  stato fermato mentre il giudice lavorava. `run-lot --through 3` rilancia la cella, che esce
  subito con esito 0 senza eseguire niente. La cella resta incompleta e ogni rilancio la
  riseleziona.
- **Causa**: il ciclo di `_extend` gira solo finché la catena ha meno di `through` richieste.
  Una richiesta interrotta in posizione `through` ha già il suo posto nell'elenco, quindi il
  ciclo non parte. `cell_done` invece la conta come non finita.
- **Secondo difetto sullo stesso percorso**: alla ripresa, il costo dei tentativi superati si
  perde se il tentativo interrotto era già finito lato braccio (classe `agent`) e il giudice non
  l'aveva ancora giudicato. `infra_usage` somma solo i tentativi `infra:*`, e l'uso della
  richiesta è quello dell'ultimo tentativo.

Il comportamento atteso: una richiesta `running` con numero `<= through` si riprende sempre,
anche se è l'ultima. Una richiesta `running` oltre `through` resta com'è. Il costo di ogni
tentativo superato finisce in `infra_usage`.

## Acceptance Criteria
- [x] Un test riproduce l'interruzione dell'host durante il giudizio dell'ultima richiesta, e
  fallisce prima della correzione.
- [x] Dopo la correzione la ripresa riesegue la richiesta dallo snapshot, la giudica e lascia i
  tentativi `agent`, `infra:host`, `agent`. La cella risulta finita.
- [x] Il costo del tentativo superato compare in `infra_usage` della richiesta.
- [x] Una richiesta interrotta oltre `through` non si riprende con un `through` minore.
- [x] I record dei lotti vecchi non cambiano: la correzione tocca solo il percorso di ripresa.

## Outcome
2026-09-27. Il test nuovo di `test_runner.py` simula l'arresto dell'host durante il giudizio
della richiesta 3 di una catena da 3. Prima della correzione falliva: la ripresa non rieseguiva
la richiesta (3 chiamate al braccio invece di 4). Dopo la correzione passa, insieme agli altri 23
test di `test_runner.py`.
- `_extend` riprende la richiesta in corso quando il suo numero è al massimo `through`, anche se
  è l'ultima della catena. Una richiesta in corso oltre `through` resta com'è.
- `infra_usage` somma ogni tentativo tranne quello contato.
- I record salvati non si riscrivono e `profile_report.py` non cambia, quindi i report dei lotti
  vecchi restano uguali.
- Il contratto dell'oracolo (§9) descrive la ripresa.

La ripresa reale della cella interrotta di `luna-calib` fa parte di DBH-03.

## Frontier
Chiuso. Sbloccava il completamento di DBH-03.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: un giudice che simula l'arresto dell'host alla richiesta 3,
   poi una seconda esecuzione con il giudice normale.
2. In `_extend`, riprendere la richiesta `running` quando il suo numero è al massimo `through`,
   anche se la catena ha già `through` elementi.
3. Sommare in `infra_usage` tutti i tentativi superati, non solo quelli `infra:*`.
4. Aggiornare il contratto dell'oracolo (§9) se descrive la ripresa.

## Testing Plan
Test offline di `test_runner.py` con il braccio finto. Poi la ripresa reale della cella di
`luna-calib` in DBH-03.

## Out of Scope
- Cambiare la classificazione dei guasti o il numero di retry.
- Riscrivere i record già salvati.

```
