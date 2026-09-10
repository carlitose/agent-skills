---
type: source
title: "Cache immutable context and evidence for an unchanged CandidateRef"
identity_key: ticket:bounded-ticket-autopilot-leaves/05
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/done/05-cache-unchanged-candidate.md
source_digest: sha256:b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-07-28
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: all-afk-bounded-20260811
---

# Cache immutable context and evidence for an unchanged CandidateRef

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/done/05-cache-unchanged-candidate.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-bounded-ticket-autopilot-leaves-03]] — `ticket:bounded-ticket-autopilot-leaves/03`

## Run

Completed under autopilot run `all-afk-bounded-20260811`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-05.md","payload_bytes":2810,"payload_sha256":"b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b"}],"payload_bytes":2810,"payload_sha256":"b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b","schema":1,"source_digest":"sha256:b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b","source_identity":"ticket:bounded-ticket-autopilot-leaves/05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2810,"payload_sha256":"b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b","schema":1,"source_digest":"sha256:b0a9f3f59c67532f463d417266dd4408f0a0c33b5c1a6dbf783325a0d603f63b","source_identity":"ticket:bounded-ticket-autopilot-leaves/05"} -->
```markdown
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

```
