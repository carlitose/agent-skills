---
type: source
title: "DBH-13 — Riprendere una richiesta il cui task è già consegnato"
identity_key: ticket:delivery-bench-hard/DBH-13
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/13-resume-after-task-delivery.md
source_digest: sha256:2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# DBH-13 — Riprendere una richiesta il cui task è già consegnato

Compiled from `docs/tickets/delivery-bench-hard/done/13-resume-after-task-delivery.md`. Identity is `ticket:delivery-bench-hard/DBH-13`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-12]] — `ticket:delivery-bench-hard/DBH-12`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-13.md","payload_bytes":2961,"payload_sha256":"2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5"}],"payload_bytes":2961,"payload_sha256":"2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5","schema":1,"source_digest":"sha256:2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5","source_identity":"ticket:delivery-bench-hard/DBH-13","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2961,"payload_sha256":"2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5","schema":1,"source_digest":"sha256:2dca0317efcedcd0c96ffb8bd71a86d233344c93858fb0b432bf6703aed708f5","source_identity":"ticket:delivery-bench-hard/DBH-13"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-13"
execution_mode: AFK
blocked_by:
  - "DBH-12"
---

# DBH-13 — Riprendere una richiesta il cui task è già consegnato

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:13`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner trovato riprendendo le celle ferme per DBH-12, durante la misura completa
(DBH-09). Per ogni richiesta il runner fa tre cose, in quest'ordine:
1. consegna il task: scrive `TASK.md` e lo registra con un commit;
2. prende l'istantanea della cartella del braccio;
3. aggiunge la richiesta al record della cella.
- **Osservato**: nel lotto `dbh` due celle si erano fermate all'istantanea della richiesta 3
  (DBH-12). Con il runner corretto, al `run-lot` successivo, si fermano di nuovo e subito: il
  commit di `TASK 3` fallisce.
- **Causa**: la consegna del task sta prima dell'istantanea, quindi il commit di `TASK 3` c'era
  già. Il record non aveva ancora la richiesta, e il runner l'ha ripresa da capo. Con niente da
  registrare, `git commit` esce con 1. DBH-12 dichiarava che la cella avrebbe ripreso, ma nessun
  test faceva fallire un passo fra la consegna e l'istantanea.

Il comportamento atteso: se il task della richiesta è già nella storia, la consegna non fa un
secondo commit e la richiesta riprende.

## Acceptance Criteria
- [x] Un test fa fallire l'istantanea della richiesta 2 e poi riprende la cella. Prima della
  correzione la ripresa fallisce sul commit di `TASK 2`, come nel lotto.
- [x] Dopo la correzione la richiesta 2 va al braccio una volta sola ed è accettata, e la storia
  di `TASK.md` ha un commit per richiesta.
- [x] Una consegna nuova fa ancora il suo commit.

## Outcome
2026-09-28. Il test nuovo di `test_runner.py` fallisce prima della correzione con lo stesso errore
del lotto. Dopo la correzione passa, insieme agli altri test di `test_runner.py`,
`test_judge.py` e `test_profile_report.py` (52, 2 saltati).
- La consegna fa il commit solo se `TASK.md` differisce da quello della storia.
- Su copie dei progetti delle due celle ferme, la consegna della richiesta 3 con il runner
  corretto non fa un commit nuovo.
- I record salvati non cambiano.

## Frontier
Chiuso. Le due celle ferme riprendono al `run-lot` successivo della misura completa (DBH-09).

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: l'istantanea fallisce dopo la consegna, poi la cella riprende.
2. Commit del task solo se c'è qualcosa da registrare.

## Testing Plan
Test offline di `test_runner.py`, una prova su copie delle due celle ferme, poi la ripresa vera
nel lotto `dbh`.

## Out of Scope
- Cambiare l'ordine fra consegna e istantanea: l'istantanea deve contenere il task, perché un
  ripristino lo conservi.
- Riscrivere i record già salvati.

```
