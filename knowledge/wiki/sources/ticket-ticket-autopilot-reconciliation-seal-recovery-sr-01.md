---
type: source
title: "Gate an out-of-protocol reconciliation head"
identity_key: ticket:ticket-autopilot-reconciliation-seal-recovery/SR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-reconciliation-seal-recovery/done/01-gate-out-of-protocol-reconciliation-head.md
source_digest: sha256:9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: sr01-seal-recovery-20260829
---

# Gate an out-of-protocol reconciliation head

Compiled from `docs/tickets/ticket-autopilot-reconciliation-seal-recovery/done/01-gate-out-of-protocol-reconciliation-head.md`. Identity is `ticket:ticket-autopilot-reconciliation-seal-recovery/SR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-reconciliation-seal-recovery-diagnostic]]

## Run

Completed under autopilot run `sr01-seal-recovery-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-reconciliation-seal-recovery-sr-01.md","payload_bytes":3658,"payload_sha256":"9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de"}],"payload_bytes":3658,"payload_sha256":"9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de","schema":1,"source_digest":"sha256:9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de","source_identity":"ticket:ticket-autopilot-reconciliation-seal-recovery/SR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3658,"payload_sha256":"9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de","schema":1,"source_digest":"sha256:9df55f13f7baf29cd25909d7f60f43f8c9cbf809aeab491416e3f61854dc74de","source_identity":"ticket:ticket-autopilot-reconciliation-seal-recovery/SR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SR-01"
execution_mode: AFK
blocked_by: []
---

# Gate an out-of-protocol reconciliation head

## Artifact Graph

- Artifact ID: `artifact:sr-01-gate-out-of-protocol-reconciliation-head`
- Role: `ticket`
- Parent: [reconciliation seal recovery diagnostic](../../specs/ticket-autopilot-reconciliation-seal-recovery-diagnostic.md)

## Parent Spec

[Ticket-autopilot reconciliation seal recovery diagnostic](../../specs/ticket-autopilot-reconciliation-seal-recovery-diagnostic.md)

## What to Build

Turn an unexpected local head at the post-verification reconciliation sealing boundary into a
durable, actionable recovery gate. Preserve the replay-safe seal invariant and require explicit
repair plus gate approval before the runner can continue.

## Acceptance Criteria

- [ ] An unexpected reconciliation `HEAD` or invalid runner-seal lineage no longer escapes as
      an uncaught `GitError`; resume returns a durable `stack-reconciliation-recovery` gate.
- [ ] The gate records a stable schema and reason plus the ticket branch, absolute worktree,
      expected prepared head, observed head, and verified candidate tree OID.
- [ ] Recovery guidance requires preserving the unexpected head under a backup ref, restoring
      the prepared head while keeping the verified candidate tree staged, proving
      `git write-tree` equals the recorded tree, approving the exact gate with evidence, and
      resuming.
- [ ] Guidance offers starting a new run when the unexpected commit is intentional rather than
      instructing the operator to rewrite it into the current audited run.
- [ ] The runner never resets, deletes, force-pushes, or silently adopts the unexpected commit.
- [ ] Opening the recovery gate performs no provider mutation and leaves the unexpected local
      head unchanged.
- [ ] Gate approval alone does not bypass the Git checks; resume repeats the invariant until the
      documented repair is complete.
- [ ] After repair and approval, resume creates or reuses the canonical marker seal, records the
      new local head, and continues through the existing reconciliation publication flow.
- [ ] Other source-mode, lifecycle, pause, cancellation, provider, and reconciliation error
      categories retain their existing semantics.
- [ ] Targeted reconciliation tests and the complete ticket-autopilot suite pass.

## Frontier

Ready. The uncaught error, repeated-resume behavior, missing evidence, and supported
non-destructive recovery sequence are pinned in the diagnostic.

## Step-by-Step Implementation Plan

1. Add a red semantic reconciliation regression at the post-verification seal boundary.
2. Give out-of-protocol seal failures structured state and recovery details.
3. Route seal Git failures through a durable recovery gate without catching unrelated control
   flow.
4. Exercise approval without repair, then the documented backup/soft-reset/tree-proof repair
   and successful replay.
5. Run targeted reconciliation and full ticket-autopilot suites.

## Testing Plan

Use TDD in the existing semantic stack reconciliation integration test. Assert the complete
gate payload, ledger persistence, provider command count, unchanged unexpected `HEAD`, failed
replay after approval without repair, and successful replay after the documented repair. Run
the relevant CLI test and the full suite.

## Out of Scope

- Automatically modifying or deleting an unexpected commit.
- Treating arbitrary same-tree commits as canonical runner seals.
- Changing semantic candidate identity or verification invalidation.
- Changing provider merge, PR-body publication, or source-disposition contracts.

```
