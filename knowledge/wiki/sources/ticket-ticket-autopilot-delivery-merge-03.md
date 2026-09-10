---
type: source
title: "Reconcile an external merge atomically"
identity_key: ticket:ticket-autopilot-delivery-merge/03
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-delivery-merge/done/03-reconcile-external-merge-atomically.md
source_digest: sha256:a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-01
created_provenance: git-commit
disposition_changed: 2026-08-01
disposition_changed_provenance: git-rename
run_id: issue16-17-delivery-merge-20260801
---

# Reconcile an external merge atomically

Compiled from `docs/tickets/ticket-autopilot-delivery-merge/done/03-reconcile-external-merge-atomically.md`. Identity is `ticket:ticket-autopilot-delivery-merge/03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-01** via `git-commit`
- Disposition changed: **2026-08-01** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-ticket-autopilot-delivery-merge-02]] — `ticket:ticket-autopilot-delivery-merge/02`

## Run

Completed under autopilot run `issue16-17-delivery-merge-20260801`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-delivery-merge-03.md","payload_bytes":4682,"payload_sha256":"a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c"}],"payload_bytes":4682,"payload_sha256":"a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c","schema":1,"source_digest":"sha256:a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c","source_identity":"ticket:ticket-autopilot-delivery-merge/03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4682,"payload_sha256":"a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c","schema":1,"source_digest":"sha256:a66ec7a3b76598167b3efc4bbea69212604d59cddadac2c4cdb1001e5b01af8c","source_identity":"ticket:ticket-autopilot-delivery-merge/03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "03"
execution_mode: AFK
blocked_by:
  - "02"
---

# Reconcile an external merge atomically

## Parent Spec

[ticket-autopilot-delivery-merge-wayfinder.md](../../specs/ticket-autopilot-delivery-merge-wayfinder.md)

## What to Build

Resolve the external-merge half of
[GitHub issue #17](https://github.com/carlitose/agent-skills/issues/17). Make
`approve --external-merge` perform live provider readback for the ledger-recorded PR,
verify that the exact recorded head is already merged, persist the human/external evidence,
and transition the ticket to `integrated` in the same locked, replay-safe operation.

This path observes and reconciles a merge; it never invokes a merge command. Repeating the
command after success must converge on the same integrated state and receipt without
requiring a second semantic authorization or `integrate` event.

## Evidence

- Current `_approve` chooses external mode only when the provider lacks the expected-head
  merge capability, then calls `Kernel.authorize_merge` without live PR readback.
- Current `integrate` separately calls `GET_PR_STATE`, records its receipt, and requires the
  prior authorization, creating the two-command recovery reported in the issue.
- `Kernel.record_integration` rejects an already provider-merged exact head until
  authorization has been stored, even though that same external action is the evidence
  being reconciled.
- The existing Azure external-merge test explicitly performs `approve --external-merge`
  and a later `integrate`; it is the direct regression fixture to replace and extend.

## Acceptance Criteria

- [ ] `approve --external-merge` performs live provider readback using only the PR ID stored
      in the ledger and validates provider identity, PR identity, merged state, and exact
      recorded head SHA.
- [ ] A matching observation records external authorization evidence and integration
      atomically under the run lock, returning `integrated` in that command.
- [ ] The external path never invokes a provider merge/complete operation.
- [ ] A provider head mismatch, wrong PR/provider, open/closed-unmerged state, simulated
      receipt, or missing evidence fails closed without partially authorizing or integrating.
- [ ] Repeating the exact reconciliation after integration is idempotent and returns the
      same terminal identity without appending contradictory effects or history.
- [ ] Crash recovery after provider readback but before ledger save converges on one
      external receipt and one integration transition.
- [ ] Run completion, dependent-ticket readiness, and status/report projections update in
      the same command; no later `integrate` event is required.
- [ ] GitHub and Azure DevOps fake-provider tests cover successful reconciliation,
      mismatches, provider failure, and replay.

## Frontier

Dependency-blocked by ticket `02`, which establishes the shared authorization and
merge-critical-path state/receipt contract that this external observation path reuses.

## Step-by-Step Implementation Plan

1. Define the external reconciliation command result and receipt identity as a distinct
   non-mutating provider path within the merge-critical ledger contract from ticket `02`.
2. Refactor `approve --external-merge` to require live provider mode, read the recorded PR,
   and validate provider/PR/head/merged state before any authorization or lifecycle write.
3. Add one kernel transaction that records external actor/evidence, the validated provider
   observation, and `integrated`, with an exact idempotent replay rule for already
   integrated tickets.
4. Remove the need for a follow-up caller `integrate` event on this path while keeping any
   internal compatibility behavior explicit and fail closed.
5. Update run-state/dependency projections and replace the two-step Azure regression test;
   add GitHub parity, mismatch, crash-window, and repeated-command tests.

## Testing Plan

Run ticket-autopilot CLI, kernel, ledger replay, provider, scheduling, and forward-test
suites. Stateful fake providers must prove that no merge command occurs, the exact stored
PR/head is read, partial writes do not survive failed validation, one successful command
completes the run or unblocks dependents, and a repeated command is a no-op projection of
the same integration.

## Out of Scope

- Performing a normal runner merge or weakening its explicit human authorization.
- Accepting a merge of a different head, another PR, or an unverified provider receipt.
- PR-body generation/publication or unrelated delivery effects.
- Live credentials, remote cleanup, or provider-specific orchestration in the core.


```
