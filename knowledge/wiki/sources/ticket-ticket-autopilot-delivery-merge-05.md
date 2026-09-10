---
type: source
title: "Preserve stack evidence across lineage-only rebases"
identity_key: ticket:ticket-autopilot-delivery-merge/05
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-merge/done/05-preserve-stack-evidence-across-lineage-rebases.md
source_digest: sha256:7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-05
created_provenance: git-commit
disposition_changed: 2026-08-05
disposition_changed_provenance: git-rename
run_id: issues21-23-autonomous-stack-v2-20260805
---

# Preserve stack evidence across lineage-only rebases

Compiled from `docs/tickets/ticket-autopilot-delivery-merge/done/05-preserve-stack-evidence-across-lineage-rebases.md`. Identity is `ticket:ticket-autopilot-delivery-merge/05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-05** via `git-commit`
- Disposition changed: **2026-08-05** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-02]] — `ticket:ticket-autopilot-delivery-merge/02`

## Run

Completed under autopilot run `issues21-23-autonomous-stack-v2-20260805`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-merge-05.md","payload_bytes":4408,"payload_sha256":"7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa"}],"payload_bytes":4408,"payload_sha256":"7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa","schema":1,"source_digest":"sha256:7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa","source_identity":"ticket:ticket-autopilot-delivery-merge/05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4408,"payload_sha256":"7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa","schema":1,"source_digest":"sha256:7e11a4bd48d1042b2c822b254538971902f9fe7f041b02e0190cfcf353fe42aa","source_identity":"ticket:ticket-autopilot-delivery-merge/05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "05"
execution_mode: AFK
blocked_by:
  - "02"
---

# Preserve stack evidence across lineage-only rebases

## Parent Spec

[ticket-autopilot-autonomous-stacked-delivery.md](../../specs/ticket-autopilot-autonomous-stacked-delivery.md)

## What to Build

Separate semantic candidate identity from Git delivery lineage and use that boundary during
single-parent stack reconciliation. A parent merge that changes commit SHAs but preserves
the exact base tree, child tree, and ticket contract must not rerun code review, QA, or
verification. Any semantic change must retain the existing fail-closed invalidation path.

## Acceptance Criteria

- [ ] Semantic candidate contract v2 binds exactly to base tree OID, candidate tree OID,
      normalized ticket digest, and contract version; provider/PR/base/head lineage is a
      separate versioned record.
- [ ] Leaf handoffs, cache entries, QA/verification artifacts, checkpoints, ledger replay,
      and reports consistently bind to the semantic candidate rather than a mutable commit
      lineage SHA.
- [ ] Reconciliation derives the new base and child tree OIDs from local Git state after a
      guarded rebase; caller-supplied equivalence claims are forbidden.
- [ ] Exact old/new semantic equality preserves validated stages, semantic leaf artifacts,
      cache identity, artifact generation, and claim ceiling without invoking review,
      QA-plan, QA-execute, or verify again.
- [ ] A changed base tree, candidate tree, ticket digest, or contract version clears all
      semantic artifacts and returns `revalidation-required` at the normal review boundary.
- [ ] Every reconciliation records old/new semantic refs, old/new heads, target base, and
      the deterministic equivalence/invalidation result in replay-valid ledger history.
- [ ] Remote divergence, rebase conflict, tree-resolution failure, and retarget/readback
      contradiction remain durable gates and never preserve evidence optimistically.
- [ ] A changed PR head always clears a one-shot manual merge authorization even when the
      semantic candidate is equal.
- [ ] Incompatible active ledgers or candidate contracts fail with an actionable version
      error; no silent legacy interpretation or hand-maintained alternate parser is added.
- [ ] A three-ticket stack test proves lineage-only parent merges do not increase semantic
      review counts, while planted base, child, and ticket drift each force complete
      revalidation and rediscover their findings.

## Frontier

Dependency-blocked by ticket `02`. The immediate expected-head merge critical path and its
replay receipts must be stable before stack reconciliation changes the identity feeding it.

## Step-by-Step Implementation Plan

1. Introduce semantic candidate v2 and delivery-lineage contracts with one canonical
   serializer/validator path; version ledger and downstream artifact bindings explicitly.
2. Update candidate construction for uncommitted implementation and committed rebased
   branches so both resolve base/candidate tree OIDs correctly.
3. Refactor kernel, leaf, cache, QA, verification, and reporting bindings around the semantic
   identity while keeping merge authorization tied to delivery head.
4. Add a deterministic stack-equivalence transition that preserves semantic state only on
   exact ref equality and records a complete causal receipt.
5. Integrate the transition into guarded rebase, force-with-lease push, retarget, and live
   provider readback without adding an agent-authored semantic judgment.
6. Add compatibility errors and the full unit, ledger replay, Git integration, and stacked
   forward-test matrix.

## Testing Plan

Run ticket-autopilot, verification-audit, skill-graph, and forward-test suites. Add isolated
Git fixtures for fast-forward, squash-equivalent, merge-commit-equivalent, unrelated base
advance, merge resolution, child amendment, conflict, dropped commit, generated-file drift,
ticket drift, force-with-lease failure, and crash/replay. Assert leaf invocation counts and
artifact identities, not only final states.

## Out of Scope

- Path-based, dependency-graph, or agent-asserted selective evidence reuse.
- Autonomous merge authority; ticket `06` owns that policy.
- Preserving a one-shot manual authorization after any head change.
- Live-provider readiness claims without disposable credentialed evidence.

```
