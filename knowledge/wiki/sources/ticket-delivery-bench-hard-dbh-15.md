---
type: source
title: "DBH-15 — Aspettare un buco di rete lungo prima di esaurire le ripetizioni"
identity_key: ticket:delivery-bench-hard/DBH-15
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/15-long-outage-wait.md
source_digest: sha256:facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# DBH-15 — Aspettare un buco di rete lungo prima di esaurire le ripetizioni

Compiled from `docs/tickets/delivery-bench-hard/done/15-long-outage-wait.md`. Identity is `ticket:delivery-bench-hard/DBH-15`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-14]] — `ticket:delivery-bench-hard/DBH-14`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-15.md","payload_bytes":2896,"payload_sha256":"facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269"}],"payload_bytes":2896,"payload_sha256":"facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269","schema":1,"source_digest":"sha256:facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269","source_identity":"ticket:delivery-bench-hard/DBH-15","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2896,"payload_sha256":"facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269","schema":1,"source_digest":"sha256:facc1dceba76d1b1b10e86f700206ff66d78ff5568c7c845ae9aa7287a4aa269","source_identity":"ticket:delivery-bench-hard/DBH-15"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-15"
execution_mode: AFK
blocked_by:
  - "DBH-14"
---

# DBH-15 — Aspettare un buco di rete lungo prima di esaurire le ripetizioni

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:15`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner osservato nella rimisura dei driver (lotto `dbh-drivers`).
- **Osservato**: il 29/09 fra le 16:02 e le 16:45 UTC le foglie del driver sono uscite con
  `fetch failed`, in circa 25 s ciascuna e senza spesa. Le attese di DBH-14 (1 e 10 minuti)
  coprono circa 11 minuti. Il buco è durato 42 minuti, e 10 richieste su 72 della catena da 4
  hanno esaurito le ripetizioni: contano come non accettate (contratto §9).
- **Causa**: 2 ripetizioni con 11 minuti di attesa bastano per il buco di 9 minuti del lotto
  `dbh`, non per uno di tre quarti d'ora.

Il comportamento atteso:
- fino a 5 ripetizioni, con attese crescenti di 1, 5, 15, 30 e 60 minuti, quasi due ore in
  tutto;
- un buco di 9 minuti e uno di 42 minuti non esauriscono le ripetizioni;
- l'attesa resta fuori dai tetti ed è registrata come in DBH-14.

## Acceptance Criteria
- [x] Un test modella i due buchi osservati, 9 e 42 minuti con tentativi di 25 s. Prima della
  correzione quello da 42 minuti esaurisce le ripetizioni; dopo, nessuno dei due.
- [x] Dopo 6 tentativi falliti la richiesta è esaurita, con 5 attese crescenti registrate nel
  ledger e nella richiesta.
- [x] Dopo un tentativo dell'agente il runner non aspetta. Il contratto §9 descrive le attese.

## Outcome
2026-09-29. Il test `test_infrastructure_retries_wait_out_the_observed_outages` fallisce prima
della correzione nel caso da 42 minuti, e passa dopo. Anche `..._stop_after_five` fallisce prima
(3 tentativi invece di 6). Dopo la correzione passano tutti i test di `benchmarks/delivery-bench`.
- `MAX_INFRA_RETRIES` passa da 2 a 5, e le attese diventano 1, 5, 15, 30 e 60 minuti.
- Un tentativo fallito in un buco di rete costa circa 25 s e nessun token.
- I record già scritti non cambiano. Le 10 richieste perse della catena da 4 di `dbh-drivers`
  restano non accettate, come vuole il contratto.

## Frontier
Chiuso. Vale dal prossimo `run-lot`: la catena da 12 di `dbh-drivers` gira con la correzione.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: tentativi che falliscono finché dura il buco, dato il tempo
   delle attese del runner.
2. Più ripetizioni e attese più lunghe.
3. Contratto §9 aggiornato.

## Testing Plan
Test offline di `benchmarks/delivery-bench`, con le attese registrate senza dormire.

## Out of Scope
- Rigiocare le 10 richieste perse: il contratto §9 le conta come non accettate.
- Sondare la rete prima di ripetere.

```
