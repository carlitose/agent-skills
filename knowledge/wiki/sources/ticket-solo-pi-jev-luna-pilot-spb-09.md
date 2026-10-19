---
type: source
title: "SPB-09 — Una sola misura Yjs L4 sul braccio corretto"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-09
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/09-run-adjudicated-l4.md
source_digest: sha256:4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-09 — Una sola misura Yjs L4 sul braccio corretto

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/09-run-adjudicated-l4.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-09`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-adjudicated-l4]]
- Child source: [[sources/artifact-solo-pi-jev-luna-adjudicated-l4-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-08]] — `ticket:solo-pi-jev-luna-pilot/SPB-08`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-09.md","payload_bytes":2396,"payload_sha256":"4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca"}],"payload_bytes":2396,"payload_sha256":"4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca","schema":1,"source_digest":"sha256:4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-09","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2396,"payload_sha256":"4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca","schema":1,"source_digest":"sha256:4c440af6d6f0d0a7dd76450dfbf3d597d36beda55a0efa47d1b83e7a920246ca","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-09"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-09"
execution_mode: AFK
blocked_by:
  - "SPB-08"
---

# SPB-09 — Una sola misura Yjs L4 sul braccio corretto

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-09`
- Role: `ticket`
- Parent: [Luna adjudicated L4](../../specs/solo-pi-jev-luna-adjudicated-l4.md)

### Produces
- [Risultato osservato](../../research/solo-pi-jev-luna-adjudicated-l4-results.md)

## Parent Spec
[Luna adjudicated L4](../../specs/solo-pi-jev-luna-adjudicated-l4.md).

## What to Build
Una nuova cella persistente Yjs L4 Luna medium sul runtime congelato SPB-08, con source e
scope grant distinti da SPB-07; readback e report score/causa senza replay o source storico mutato.

## Acceptance Criteria
- [ ] SPB-08/target/tree/graph, runtime/SDK/skills/request/seed/suite/question/policy/immagini e grant «1» verificati prima della spesa.
- [ ] Costi cumulativi originali ammessi senza perdere i 10/47/7/367, uso operatore aggiornato e separato dalle stime sperimentali/invoice/FX.
- [ ] Esattamente un processo/cella nuovi; candidato e delivered con prove osservate, blocchi distinti dai tentativi; nessun secondo launch o replay dopo errore.
- [ ] Decisioni reali/port/input/causa e score riportati, oracle caller-only immutabile; nessun hidden feedback, confronto storico solo descrittivo e invariato.
- [ ] Frozen report/review/QA/audit inline con limiti, costi e tentativi preservati; nessuna suite runtime invariata ripetuta né delivery/installazione/delega/runner.

## Frontier
Ready: SPB-08 implementation-complete/release-blocked con handoff canonico validabile;
nuova authority di scope selezionata esplicitamente «1» nella conversazione corrente.

## Step-by-Step Implementation Plan
1. Canonical admission and cumulative ledger/source snapshot, reuse observed one-cell caller.
2. One prepare and one run on new paths; never replace failed setup/launch.
3. Bounded score/cause readback, preserved history/costs, frozen aggregate report and handoff.

## Testing Plan
Graph/serializer/Git/source/input/package/images and cost preflight; one authorized real
cell; readback/hash/accounting/decision/candidate/delivered after. No runtime suite replay.

## Out of Scope
Other model/scenario/cell, historical mutation, new ports/thresholds/budgets, paired bare,
hidden prompts, independent reviewer, runner, publication/commit/push/merge/install/reload/wiki sync.

```
