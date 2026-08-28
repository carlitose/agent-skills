---
ticket_schema: 1
ticket_id: "WS-06"
execution_mode: AFK
blocked_by:
  - "WS-04"
---

# Synchronize once after ticket integration

## Artifact Graph
- Artifact ID: `artifact:ws-06-sync-after-ticket-integration`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
Compose `llm-wiki sync-project` after `ticket-autopilot` has durably recorded `integrated`.
Untracked sync remains direct; tracked sync receives its decided fresh docs-only identity and
separate guarded delivery path.

## Acceptance Criteria
- [ ] No sync starts at implementation-complete, PR-open, queued, pending, failed, unknown,
      or any state before durable `integrated`.
- [ ] Repeated resume/delivery calls cannot create duplicate sync work.
- [ ] A tracked wiki candidate never mutates or reuses the integrated application
      CandidateRef and never dirties the protected base worktree.
- [ ] Sync failure is visible and retryable without rolling back `integrated`.
- [ ] Provider delivery and merge use the existing exact-head authorization boundary.

## Frontier
Blocked by `WS-04`.

## Step-by-Step Implementation Plan
1. Add an idempotent post-integration effect keyed as selected by `WS-03`.
2. Route tracked and untracked results through their decided adapters.
3. Persist sync status in the owning run projection without changing ticket completion.
4. Exercise resume, retry, drift, and merge-authorization paths.

## Testing Plan
Kernel and CLI tests cover every pre-integration rejection, duplicate delivery, semantic and
lineage drift, direct untracked writes, tracked candidates, provider gates, and retries.

## Out of Scope
- Changing application implementation, QA, or Verification Record claims.
- Treating an autonomous application merge grant as implicit wiki-sync authorization.
