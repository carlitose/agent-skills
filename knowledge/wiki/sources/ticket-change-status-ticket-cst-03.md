---
type: source
title: "Enforce mutation barriers and safe-boundary projection"
identity_key: ticket:change-status-ticket/CST-03
identity_strength: stable
source_path: docs/tickets/change-status-ticket/done/03-enforce-safe-boundary-projection.md
source_digest: sha256:3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: change-status-ticket-production-20260831
---

# Enforce mutation barriers and safe-boundary projection

Compiled from `docs/tickets/change-status-ticket/done/03-enforce-safe-boundary-projection.md`. Identity is `ticket:change-status-ticket/CST-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-change-status-ticket]]
- Blocked by: [[sources/ticket-change-status-ticket-cst-01]] — `ticket:change-status-ticket/CST-01`
- Blocked by: [[sources/ticket-change-status-ticket-cst-02]] — `ticket:change-status-ticket/CST-02`

## Run

Completed under autopilot run `change-status-ticket-production-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-change-status-ticket-cst-03.md","payload_bytes":4010,"payload_sha256":"3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea"}],"payload_bytes":4010,"payload_sha256":"3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea","schema":1,"source_digest":"sha256:3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea","source_identity":"ticket:change-status-ticket/CST-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4010,"payload_sha256":"3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea","schema":1,"source_digest":"sha256:3b402406510c4643436a84409a2080c561c21a091bf03c06c4a491d5566b42ea","source_identity":"ticket:change-status-ticket/CST-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CST-03"
execution_mode: AFK
blocked_by:
  - "CST-01"
  - "CST-02"
---

# Enforce mutation barriers and safe-boundary projection

## Artifact Graph

- Artifact ID: `artifact:cst-03-safe-boundary-status-projection`
- Role: `ticket`
- Parent: [Change Status Ticket](../../specs/change-status-ticket.md)

## Parent Spec

[Change Status Ticket](../../specs/change-status-ticket.md)

## What to Build

Make the repository lifecycle intent authoritative at every runner mutation boundary and add append-only disposition projection for active, gated, and waiting attempts after an exact atomic safe boundary. Preserve candidates, checkpoints, provider observations, gates, waits, stop reasons, and historical evidence; prohibit new work after the barrier; and project only from ignored-source readback or tracked terminal truth rather than a stale run worktree.

## Acceptance Criteria

- [ ] Every implementation, Git, provider, delivery, merge, reconciliation, completion, wiki, and Pi mutation boundary checks an exact repository lifecycle intent under repository/run locks.
- [ ] An in-flight atomic effect settles and is read back truthfully before the barrier; interruption or uncertain outcome gates.
- [ ] Active work receives one append-only stopped-at-safe-boundary receipt with non-empty reason; candidate, checkpoints, evidence, PR, and external-effect receipts remain literal history.
- [ ] Gated and waiting attempts preserve their exact gate/wait evidence and become administratively unschedulable without treating a gate as user or merge authority.
- [ ] Pending, active, gated, waiting, verified, PR-open/delivery, integrated, and completed states have an explicit tested matrix; integrated/completed transitions reject and uncertain delivery states gate.
- [ ] A usable run projection validates repository transaction identity and terminal/ignored source truth, not the stale run worktree path; missing and retired runs need no rewrite.
- [ ] Hold/cancel never cascades to dependents; readiness is recomputed with existing held/canceled dependency reasons.
- [ ] Reopen consumes one passed ticket-bound human gate, creates pending work, invalidates current candidate-through-merge authority, and preserves old evidence only as history.
- [ ] Barrier/projection crash replay is single-shot and contradictory intent, source, gate, receipt, or projection fails closed.
- [ ] Existing schema-4 ledgers are extended versionedly; legacy/retired ledgers and current run-bound lifecycle commands are not silently migrated.
- [ ] Concurrency tests prove an active runner cannot begin a new mutation after the barrier is durable.
- [ ] No real ticket status, provider object, worktree cleanup, wiki, or Pi operation is verification evidence.

## Frontier

Dependency-blocked by CST-01 and CST-02. It remains AFK only because concurrency, provider, and state evidence must use disposable fixtures; any real status action requires separate user authority.

## Step-by-Step Implementation Plan

1. Define the repository-intent lookup and immediate mutation-boundary guard.
2. Add lock ordering and safe-boundary receipts for active and settled gated/waiting attempts.
3. Implement terminal/ignored source-bound run projection and exact replay.
4. Extend reopen invalidation and readiness/no-cascade behavior without reusing authority.
5. Add concurrent runner, in-flight effect, stale worktree, crash, and contradiction fixtures.

## Testing Plan

Use concurrent disposable processes or deterministic lock fixtures across every mutation seam. Inject provider and Git outcomes around the barrier, preserve exact candidate/evidence snapshots, and exercise the full state matrix plus dependencies and reopen. Verify no post-barrier effect begins.

## Out of Scope

- Public skill/routing changes.
- New lifecycle vocabulary or cancellation cascade.
- Provider merge without separate authority.
- Real disposition, provider publication, issue close/reopen, wiki, Pi-sync, or cleanup.

```
