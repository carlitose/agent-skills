---
type: source
title: "Synchronize once after ticket integration"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-06
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/06-sync-after-ticket-integration.md
source_digest: sha256:61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Synchronize once after ticket integration

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/06-sync-after-ticket-integration.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-04]] — `ticket:llm-wiki-docs-only-autosync/WS-04`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-06.md","payload_bytes":1981,"payload_sha256":"61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7"}],"payload_bytes":1981,"payload_sha256":"61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7","schema":1,"source_digest":"sha256:61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1981,"payload_sha256":"61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7","schema":1,"source_digest":"sha256:61cc1a099bdf82848f3a654f6e9d8fb2124a67eb3a7f5c383500b1361328f2a7","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-06"} -->
```markdown
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

```
