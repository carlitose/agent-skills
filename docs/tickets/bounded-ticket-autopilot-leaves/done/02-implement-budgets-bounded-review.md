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
