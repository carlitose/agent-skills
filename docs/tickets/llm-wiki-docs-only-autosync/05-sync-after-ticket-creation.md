---
ticket_schema: 1
ticket_id: "WS-05"
execution_mode: AFK
blocked_by:
  - "WS-04"
---

# Synchronize once after ticket creation

## Artifact Graph
- Artifact ID: `artifact:ws-05-sync-after-ticket-creation`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
Compose `llm-wiki sync-project` into `to-tickets` after the full batch has been emitted,
parsed back, and linked reciprocally. The hook runs once per batch and never makes
`wayfinder` own wiki behavior.

## Acceptance Criteria
- [ ] No wiki yields the canonical no-op result without changing ticket creation.
- [ ] An untracked wiki is updated once after the complete batch and passes wiki validation.
- [ ] A tracked wiki produces a separate docs-only candidate rather than a mixed
      ticket-source/wiki candidate.
- [ ] Broken or ambiguous sync is reported with the decided retry state and does not hide
      successfully created tickets.
- [ ] Reports include ticket paths, frontier, and normalized wiki sync result.

## Frontier
Blocked by `WS-04`.

## Step-by-Step Implementation Plan
1. Add the post-batch composition point after ticket and reciprocal-link validation.
2. Pass only project identity and configured/discovered wiki input to `sync-project`.
3. Preserve the normalized result in the final report and test one invocation per batch.

## Testing Plan
Use batch fixtures with zero, one, and multiple tickets across absent, untracked, tracked,
and ambiguous wiki states. Assert no mixed candidate is produced.

## Out of Scope
- Scheduling or implementing the emitted tickets.
- Post-integration synchronization owned by `WS-06`.
