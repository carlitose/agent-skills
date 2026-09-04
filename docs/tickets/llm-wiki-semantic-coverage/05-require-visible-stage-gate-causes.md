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
