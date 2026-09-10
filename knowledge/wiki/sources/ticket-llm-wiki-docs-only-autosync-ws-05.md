---
type: source
title: "Synchronize once after ticket creation"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-05
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/05-sync-after-ticket-creation.md
source_digest: sha256:113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Synchronize once after ticket creation

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/05-sync-after-ticket-creation.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-04]] — `ticket:llm-wiki-docs-only-autosync/WS-04`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-05.md","payload_bytes":1811,"payload_sha256":"113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760"}],"payload_bytes":1811,"payload_sha256":"113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760","schema":1,"source_digest":"sha256:113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1811,"payload_sha256":"113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760","schema":1,"source_digest":"sha256:113e8876703b6749eef6536ea154f67056d26b633fb3af042d513b27c9bc8760","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-05"} -->
```markdown
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

```
