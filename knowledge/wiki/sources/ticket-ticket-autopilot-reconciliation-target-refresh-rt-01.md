---
type: source
title: "Refresh a stale reconciliation target"
identity_key: ticket:ticket-autopilot-reconciliation-target-refresh/RT-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-reconciliation-target-refresh/done/01-refresh-stale-reconciliation-target.md
source_digest: sha256:50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Refresh a stale reconciliation target

Compiled from `docs/tickets/ticket-autopilot-reconciliation-target-refresh/done/01-refresh-stale-reconciliation-target.md`. Identity is `ticket:ticket-autopilot-reconciliation-target-refresh/RT-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-reconciliation-target-refresh-diagnostic]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[5],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[4],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-reconciliation-target-refresh-rt-01.md","payload_bytes":2299,"payload_sha256":"50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610"}],"payload_bytes":2299,"payload_sha256":"50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610","schema":1,"source_digest":"sha256:50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610","source_identity":"ticket:ticket-autopilot-reconciliation-target-refresh/RT-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 3: Acceptance Criteria |
| testing | 4: Testing |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 5: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2299,"payload_sha256":"50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610","schema":1,"source_digest":"sha256:50fe56f1330c9ecdd94594d24cd76c5d951941c613173f77be71e4498ca21610","source_identity":"ticket:ticket-autopilot-reconciliation-target-refresh/RT-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RT-01"
execution_mode: AFK
blocked_by: []
---

# Refresh a stale reconciliation target

## Artifact Graph

- Artifact ID: `artifact:rt-01-refresh-stale-reconciliation-target`
- Role: `ticket`
- Parent: [reconciliation target-refresh diagnostic](../../../specs/ticket-autopilot-reconciliation-target-refresh-diagnostic.md)

## What Was Built

Ticket Autopilot can now refresh a reconciliation target that advances during required
revalidation. It records the refresh before Git mutation, archives each superseded attempt,
replays safely across crash points, and never weakens provider or exact-head guards.

## Acceptance Criteria

- [x] The end-to-end semantic regression advances the target twice without restoring remote
      history and reaches reconciled provider readback.
- [x] Refresh requires an unchanged provider branch and is forbidden after reconciled push or
      retarget state.
- [x] Refresh intent precedes local mutation and archived attempts retain old/new target,
      intent, prepared CandidateRef, head, and render lineage.
- [x] Semantic target changes derive a new CandidateRef and invalidate review, QA,
      verification, PR-body binding, and merge authorization.
- [x] Crashes before mutation, after rebase, and before prepared-ledger persistence resume
      idempotently.
- [x] A second target advancement repeats the same bounded cycle.
- [x] Final publication keeps force-with-lease, provider retarget/readback, and exact-head
      requirements.
- [x] Same-tree refresh preserves evidence and existing provider-race gates still pass.
- [x] Ledger replay rejects forged refresh lineage.
- [x] Focused CLI, kernel, semantic-candidate, and replay suites pass.

## Testing

- Semantic target-refresh/rebind regression: pass, including three crash points and two
  consecutive semantic refreshes.
- Existing crash-resumable delivery regression: pass with same-tree evidence preservation and
  provider-retarget race coverage.
- Kernel plus semantic CandidateRef suites: 81 tests passed.
- Full CLI suite: 59 tests passed.

## Out of Scope

- Automatic rebase-conflict resolution.
- Refresh after provider mutation for the current attempt.
- Evidence reuse after semantic tree drift.
- Changes to merge policy or provider authorization.

```
