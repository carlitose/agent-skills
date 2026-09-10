---
type: source
title: "Refresh a conflict-blocked reconciliation intent before prepare"
identity_key: ticket:ticket-autopilot-preprepare-reconciliation-target-refresh/PRT-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-preprepare-reconciliation-target-refresh/done/01-refresh-conflict-blocked-intent-before-prepare.md
source_digest: sha256:93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-31
created_provenance: git-commit
disposition_changed: 2026-08-31
disposition_changed_provenance: git-rename
run_id: preprepare-reconciliation-target-refresh-20260831
---

# Refresh a conflict-blocked reconciliation intent before prepare

Compiled from `docs/tickets/ticket-autopilot-preprepare-reconciliation-target-refresh/done/01-refresh-conflict-blocked-intent-before-prepare.md`. Identity is `ticket:ticket-autopilot-preprepare-reconciliation-target-refresh/PRT-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-31** via `git-commit`
- Disposition changed: **2026-08-31** via `git-rename`

## Graph

- Parent source: [[sources/spec-ticket-autopilot-preprepare-reconciliation-target-refresh]]

## Run

Completed under autopilot run `preprepare-reconciliation-target-refresh-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-preprepare-reconciliation-target-refresh-prt-01.md","payload_bytes":3297,"payload_sha256":"93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb"}],"payload_bytes":3297,"payload_sha256":"93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb","schema":1,"source_digest":"sha256:93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb","source_identity":"ticket:ticket-autopilot-preprepare-reconciliation-target-refresh/PRT-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3297,"payload_sha256":"93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb","schema":1,"source_digest":"sha256:93ba757daacb5bfc2a03b3b6f938a27acd57da3b578d39a1682b62a47aebc3cb","source_identity":"ticket:ticket-autopilot-preprepare-reconciliation-target-refresh/PRT-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PRT-01"
execution_mode: AFK
blocked_by: []
---

# Refresh a conflict-blocked reconciliation intent before prepare

## Artifact Graph

- Artifact ID: `artifact:prt-01-refresh-conflict-blocked-intent-before-prepare`
- Role: `ticket`
- Parent: [Ticket Autopilot Pre-prepare Reconciliation Target Refresh](../../specs/ticket-autopilot-preprepare-reconciliation-target-refresh.md)

## Parent Spec

[Ticket Autopilot Pre-prepare Reconciliation Target Refresh](../../specs/ticket-autopilot-preprepare-reconciliation-target-refresh.md)

## What to Build

Add a crash-safe pre-prepare target-refresh transaction for an initial reconciliation intent
that persisted before a real conflict. Permit only exact target SHA/tree advancement, retain
all old and superseded pending intents, apply the existing authorized proposal against the
newest target, and install the replacement only with exact `reconcile-prepare` readback.

## Acceptance Criteria

- [ ] A conflict-blocked intent without `reconcile-prepare` can refresh only target SHA/tree
      and reach the exact proposal resolver.
- [ ] Target branch/ref, old/local/remote head, parent, source, run, ticket, grant, and every
      non-target intent field remain exact and fail closed on drift.
- [ ] Old intent and repeated pending refreshes are append-only, persisted before Git, and
      consumed exactly once only when prepare is created.
- [ ] An exact proposal against the newest target records adoption/application, consumes only
      covered gates, and triggers normal fresh CandidateRef quality.
- [ ] Crash/replay before Git, after proposal application, and around prepare installation is
      idempotent without provider mutation or lost history.
- [ ] Existing prepared-candidate refresh, provider, merge, completion, publication, wiki,
      Pi, source, and cleanup authority contracts remain unchanged.
- [ ] Full regressions, forward scenarios, static/context checks, and Artifact Graph delta
      pass with no stronger live-provider claim.

## Frontier

Ready. No human decision or provider mutation is required. RD-04 remains gated and must not
be manually rewritten while this runner correction is delivered.

## Step-by-Step Implementation Plan

1. Add exact target-only intent delta validation and fail-closed pending-refresh state.
2. Persist initial refresh and repeated-replacement history before worktree mutation.
3. Extend kernel prepare to atomically archive the old intent, install the replacement, and
   consume pending state exactly once.
4. Add disposable real-Git conflict/proposal/crash coverage plus strict negative tests.
5. Run focused/full regressions, extension/forward, context/static, and Artifact Graph checks.

## Testing Plan

Use real disposable repositories/remotes and the production reconciliation proposal path.
Exercise one and repeated target advances, non-target drift, revoked/malformed authority,
conflict persistence, exact application, prepare consumption, crash replay, and provider
mutation guards. No live provider action is needed.

## Out of Scope

- Manual RD-04 intent, branch, gate, or ledger mutation.
- Semantic conflict resolution without the exact proposal.
- Live issue publication or RD-05 authorization.
- Post-provider-mutation target refresh.

```
