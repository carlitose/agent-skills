---
type: source
title: "Implement budgets and a bounded review handoff"
identity_key: ticket:bounded-ticket-autopilot-leaves/02
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/done/02-implement-budgets-bounded-review.md
source_digest: sha256:c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-07-28
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: all-afk-bounded-20260811
---

# Implement budgets and a bounded review handoff

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/done/02-implement-budgets-bounded-review.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-bounded-ticket-autopilot-leaves-01]] — `ticket:bounded-ticket-autopilot-leaves/01`

## Run

Completed under autopilot run `all-afk-bounded-20260811`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-02.md","payload_bytes":3125,"payload_sha256":"c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9"}],"payload_bytes":3125,"payload_sha256":"c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9","schema":1,"source_digest":"sha256:c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9","source_identity":"ticket:bounded-ticket-autopilot-leaves/02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3125,"payload_sha256":"c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9","schema":1,"source_digest":"sha256:c8706b1d2612219a072aadeb8ab8fde29e277c71b6e13d2e18512c98db53a4a9","source_identity":"ticket:bounded-ticket-autopilot-leaves/02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "02"
execution_mode: AFK
blocked_by:
  - "01"
---

# Implement budgets and a bounded review handoff

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Implement the first production vertical slice of the bounded leaf protocol: persisted
resource budgets, observable progress, and a complete-or-partial structured handoff for the
independent review stage.

## Acceptance Criteria

- [ ] The CLI accepts separate quality-failure and total leaf-interaction limits; supported
      tool-call and wall-time limits follow ticket `01`'s contract.
- [ ] Run creation validates totals and mandatory QA/verification reservations atomically
      before creating a ledger.
- [ ] Ledger, `status`, and final reports expose configured, consumed, remaining, and
      reserved budgets without conflating exhaustion with quality failure.
- [ ] Review results use the versioned context/handoff contract and record exact
      CandidateRef plus expected and inspected file scope.
- [ ] A complete review cannot pass unless its declared scope is complete and its structured
      findings handoff validates.
- [ ] Timeout, interruption, or resource exhaustion persists usable partial progress,
      remains non-passing, and does not consume a quality failure unless a real finding
      returns the pipeline to implementation.
- [ ] A compatible follow-up receives the remaining review scope; CandidateRef drift
      invalidates the partial handoff.
- [ ] Mandatory QA and verification reservations remain available after review retries.
- [ ] Existing review independence, blocker handling, and claim ceilings are preserved.

## Frontier

Dependency-blocked by `01`. It becomes ready after the prototype freezes schemas, budget
arithmetic, and ledger compatibility.

## Step-by-Step Implementation Plan

1. Apply ticket `01`'s accepted schema/version decision to CLI arguments and ledger state.
2. Add validated budget and progress transitions with deterministic status projection.
3. Add the immutable review context and structured complete/partial handoff contract.
4. Update the review skill boundary to consume the context and always return the handoff.
5. Resume incomplete review from its declared remaining scope without treating it as a
   prior pass.
6. Add final-report verbosity metrics and fail-closed CandidateRef checks.
7. Update public references and UI metadata for the new CLI/status contract.

## Testing Plan

- Unit tests for CLI validation, ledger transitions, reservations, report projection, and
  handoff schemas.
- Integration tests for complete review, incomplete scope, timeout, interruption/resume,
  real blocker discovery, quality-failure accounting, and candidate invalidation.
- Regression tests proving QA/verification slots remain reserved.
- Platform tests for persisted ledger behavior where supported.
- No live-provider claim is required.

## Out of Scope

- QA/audit checkpoint implementation.
- Evidence caching.
- Cross-CandidateRef semantic reuse.
- Delivery continuation changes.

```
