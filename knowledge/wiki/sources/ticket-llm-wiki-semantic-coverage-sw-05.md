---
type: source
title: "Require and display concrete stage-gate causes"
identity_key: ticket:llm-wiki-semantic-coverage/SW-05
identity_strength: stable
source_path: docs/tickets/llm-wiki-semantic-coverage/done/05-require-visible-stage-gate-causes.md
source_digest: sha256:2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-05
created_provenance: git-commit
disposition_changed: 2026-09-08
disposition_changed_provenance: git-rename
run_id: clarity-wiki-flow-20260908
---

# Require and display concrete stage-gate causes

Compiled from `docs/tickets/llm-wiki-semantic-coverage/done/05-require-visible-stage-gate-causes.md`. Identity is `ticket:llm-wiki-semantic-coverage/SW-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **2026-09-08** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]

## Run

Completed under autopilot run `clarity-wiki-flow-20260908`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-semantic-coverage-sw-05.md","payload_bytes":3849,"payload_sha256":"2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28"}],"payload_bytes":3849,"payload_sha256":"2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28","schema":1,"source_digest":"sha256:2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28","source_identity":"ticket:llm-wiki-semantic-coverage/SW-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3849,"payload_sha256":"2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28","schema":1,"source_digest":"sha256:2d61722d339ea3cb16e27603627cece94efb33a001ff5d36077a62e93c5e0f28","source_identity":"ticket:llm-wiki-semantic-coverage/SW-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SW-05"
execution_mode: AFK
blocked_by: []
---

# Require and display concrete stage-gate causes

## Artifact Graph
- Artifact ID: `artifact:sw-05-require-visible-stage-gate-causes`
- Role: `ticket`
- Parent: [LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Parent Spec
[LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## What to Build
Close the write/read information gap for Ticket Autopilot stage gates. A stage event whose result is `gated` must carry a specific non-empty reason; `Kernel.record_stage` must persist that exact reason instead of generating `<stage> reported a gate`; and `status` must expose structured open-gate records while preserving the existing ordered `open_gates` ID projection for compatible callers.

Keep old durable ledgers readable. Existing generic reasons remain literal historical data and are never rewritten or presented as newly recovered facts. Add an explicit versioned status field such as `open_gate_records` containing the gate ID, ticket owner, category, scope, kind, state, reason, and any safe existing details needed to act.

This ticket covers new transition and visibility behavior only. Evidence-bound repair of historical records belongs to `SW-06`.

## Acceptance Criteria
- [ ] A `gated` stage event without `reason`, with a blank reason, or with a non-string reason fails before ledger mutation.
- [ ] A valid gated event stores the exact normalized reason supplied by the caller; the generic generated text is no longer used for new stage gates.
- [ ] Kernel and CLI APIs agree on the reason requirement and do not accept a hidden alternate path that loses it.
- [ ] `status` keeps `open_gates` and adds deterministic structured records for every open gate, including ID, owner, category, scope, kind, state, and reason.
- [ ] Structured status records are deep copies/projections: mutating a returned report cannot mutate the ledger.
- [ ] Existing schema-4 ledgers containing generic reasons load unchanged and display those literal reasons without inferred detail.
- [ ] Event replay, ledger validation, gate refresh, HITL gates, dynamic gates, and non-gated stage results retain their existing behavior.
- [ ] Kernel, CLI, migration/compatibility, and status-purity tests include red-before/green-after causal cases.

## Frontier
Ready and AFK. It is independent of the semantic projection decision and can proceed in parallel with `SW-01` at the scheduler frontier.

## Step-by-Step Implementation Plan
1. Trace every stage-event producer and `record_stage` caller. Checkpoint: there is one documented reason contract and no bypass.
2. Extend event and kernel validation so gated results require a concrete cause before mutation.
3. Add the structured status projection while preserving existing ID-only output. Checkpoint: all gate kinds render consistently without exposing mutable ledger references.
4. Prove legacy ledgers remain readable and unchanged. Checkpoint: the four reported generic-history shapes would remain literal, not backfilled.
5. Update Ticket Autopilot documentation and run focused plus full regression suites.

## Testing Plan
Add unit tests for missing/blank/non-string/exact reasons, transaction rollback, status shape and purity, legacy generic reasons, and each gate kind. Add CLI integration tests that submit stage events and inspect `status`. Run the full Ticket Autopilot suite and forward tests applicable to stage events and status.

Provider behavior is not required to prove this local ledger/API contract. No external ledger is mutated.

## Out of Scope
- Guessing or repairing historical causes.
- Resolving or approving any gate.
- Changing merge, reconciliation, lifecycle, or provider authority.
- Semantic wiki compilation.

```
