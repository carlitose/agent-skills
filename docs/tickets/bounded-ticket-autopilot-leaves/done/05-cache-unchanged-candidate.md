---
ticket_schema: 1
ticket_id: "05"
execution_mode: AFK
blocked_by:
  - "03"
---

# Cache immutable context and evidence for an unchanged CandidateRef

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Avoid rediscovery and repeated commands when the exact CandidateRef and leaf contract are
unchanged. Cache only validated, scope-bound context and evidence whose identities still
match.

## Acceptance Criteria

- [ ] Cache keys include CandidateRef, leaf-contract version, declared scope, artifact
      hashes, command identity, and relevant environment identity.
- [ ] A cache hit is allowed only when every key component and validated artifact still
      matches.
- [ ] Review inspection, command results, environment limitations, and deterministic audit
      checkpoints declare what may be reused and what remains semantic work.
- [ ] Status and final reports expose cache hits, misses, repeated commands avoided, and
      limitations.
- [ ] Corrupt, missing, contradictory, or mismatched cache entries fail closed and rerun the
      owning work rather than becoming a pass.
- [ ] Any CandidateRef or ticket-contract change invalidates review, QA execution,
      verification, and merge authorization exactly as D6 requires.
- [ ] Cache artifacts remain inside the managed run directory and do not retain credentials
      or unsanitized provider output.
- [ ] Tests demonstrate measurable repeated-work reduction for same-candidate resume without
      changing findings or claim ceilings.

## Frontier

Dependency-blocked by `03`. Deterministic QA/audit artifacts must exist before their cache
identity can be trusted.

## Step-by-Step Implementation Plan

1. Inventory reusable artifacts and define exact scope, contract, command, environment, and
   hash keys.
2. Add validated cache metadata under the managed run directory.
3. Consume cache entries only after CandidateRef and artifact validation.
4. Record cache decisions and avoided work in status and final metrics.
5. Reject cross-CandidateRef reuse and stale semantic results.
6. Measure the issue #9 workflow shape before and after same-candidate caching.

## Testing Plan

- Unit tests for keys, artifact hashing, corruption, missing inputs, environment drift, and
  invalidation.
- Integration tests for interruption/resume and repeated leaf invocation on the same
  CandidateRef.
- Mutation tests proving one content or ticket-contract change forces semantic cache misses.
- Evidence comparison proving cached and uncached runs return equivalent structured results.

## Out of Scope

- Any evidence reuse across different CandidateRef values.
- Weakening review completeness or causal verification.
- Global shared caches outside the managed run.
