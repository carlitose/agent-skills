---
ticket_schema: 1
ticket_id: "03"
execution_mode: AFK
blocked_by:
  - "02"
---

# Checkpoint QA and deterministic verification

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Extend the bounded leaf protocol through QA planning/execution and verification. Move
verification bundle assembly, validation, hashing, reduction, and checkpoint resume into
deterministic scripts while keeping semantic ambiguity with the verification agent.

## Acceptance Criteria

- [ ] QA planning and execution return versioned complete or partial handoffs with exact
      CandidateRef, causal scope, commands/evidence, remaining work, and limitations.
- [ ] Progress phases for QA and verification are persisted monotonically and exposed by
      `status`.
- [ ] Deterministic code assembles the canonical verification bundle only from validated
      inputs and retains its artifact hash.
- [ ] Bundle-built, validated, reduced, and handoff-ready checkpoints are resumable for the
      same CandidateRef without repeating completed deterministic phases.
- [ ] The verification agent owns boundary authorization, contradictions, semantic
      uncertainty, gates, and final wording rather than manual JSON serialization.
- [ ] Timeout or interruption leaves a non-passing partial result and preserves mandatory
      budget accounting.
- [ ] CandidateRef drift rejects every prior QA and verification semantic artifact and
      checkpoint.
- [ ] Skipped or unavailable live boundaries remain visible and cannot raise the claim
      ceiling.
- [ ] The existing verification validator/reducer remains the sole claim authority.

## Frontier

Dependency-blocked by `02`. It consumes the production handoff/progress contract proven by
the review slice.

## Step-by-Step Implementation Plan

1. Extend the shared context and handoff contract with causal QA fields and artifact
   identities.
2. Persist QA and verification phase transitions through the validated ledger.
3. Add a deterministic resumable bundle builder around the canonical verification
   validator and reducer.
4. Route only semantic unknowns and authorization questions to the verification leaf.
5. Bind every checkpoint and output hash to the exact CandidateRef.
6. Update status/final metrics for progress, waits, repeated work, and deterministic resume.
7. Document simulation and unavailable-live boundaries without changing their claims.

## Testing Plan

- Unit tests for handoff schemas, phase ordering, bundle construction, hashes, validation,
  reduction, and checkpoint replay.
- Integration tests interrupting QA plan, QA execution, bundle build, validation, and
  reduction.
- Regression fixtures for failed QA, skipped live evidence, unknown boundaries, and stale
  CandidateRef rejection.
- Comparison proving resumed deterministic phases do not rerun already validated work.

## Out of Scope

- Cross-CandidateRef evidence reuse.
- Provider delivery continuation.
- Any new claim level or waiver.
