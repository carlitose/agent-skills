---
ticket_schema: 1
ticket_id: "02"
execution_mode: AFK
blocked_by:
  - "01"
---

# Merge immediately after exact-SHA authorization

## Parent Spec

[ticket-autopilot-delivery-merge-wayfinder.md](../../specs/ticket-autopilot-delivery-merge-wayfinder.md)

## What to Build

Resolve the normal-runner critical-path half of
[GitHub issue #17](https://github.com/carlitose/agent-skills/issues/17). Once a human
authorizes the exact observed PR head, keep the ticket on one guarded path that performs a
fresh provider observation, persists the authorization, invokes the provider's
expected-head merge, reads the result back, and records integration before unrelated AFK
ticket activation can take priority.

Persist merge-phase progress and replay-safe external-effect receipts. Expose the current
merge-critical-path phase and elapsed time through pure status/report projections. A crash
or provider failure must preserve exact-SHA safety and resume the same critical path
without issuing a second merge.

## Evidence

- `ticket-autopilot/scripts/autopilot/cli.py::_approve` currently persists merge
  authorization and returns; a later `resume` event with operation `integrate` performs
  provider readback and ledger integration.
- `ticket-autopilot/scripts/autopilot/providers.py` defines the normalized
  `merge-with-expected-head` capability and GitHub's `--match-head-commit` command, but the
  live executor does not expose the merge operation.
- `ticket-autopilot/scripts/autopilot/kernel.py::report` projects only the latest delivery
  phase/result and no merge-critical elapsed time.
- The issue records a reconciled head followed by delayed authorization, unrelated ticket
  activation, and eventual manual merge despite an otherwise eligible PR.

## Acceptance Criteria

- [ ] Normal runner merge still requires an explicit human authorization bound to the
      recorded PR ID and exact freshly observed head SHA.
- [ ] One approval command enters the merge critical path, performs the guarded provider
      merge immediately, reads the provider state back, and records `integrated` without a
      separate semantic authorization or caller-driven `integrate` step.
- [ ] Candidate or provider-head drift invalidates the prior authorization and fails
      closed before a merge command is accepted.
- [ ] After authorization is persisted, scheduler selection and resume prioritize the
      authorized merge over unrelated AFK activation until it integrates or reaches a real
      provider/human/environment gate.
- [ ] Provider mutation and readback receipts are keyed and replay-safe; a crash before or
      after provider success cannot cause a second merge or an optimistic integration.
- [ ] Status and final reports expose merge-critical-path phase, start/elapsed time, head
      SHA, and gate/failure state without mutating history on repeated reads.
- [ ] PR explanation work cannot occur after merge authorization; ticket `01`'s validated
      body receipt is a prerequisite for entering this path.
- [ ] Automated forward tests reproduce verified PR -> reconciled head -> exact-SHA
      authorization -> immediate merge, plus failures before mutation, after mutation,
      during readback, and on changed head.

## Frontier

Dependency-blocked by ticket `01`. The merge critical path must begin only after delivery
has a provider-read, canonically validated PR body and the final observed head.

## Step-by-Step Implementation Plan

1. Define merge-critical-path phases and replay-safe timestamps/elapsed projection in the
   ledger contract; keep status reads pure and reject incompatible active ledgers clearly.
2. Extend the normalized provider executor with expected-head merge execution and receipts
   while retaining provider capability negotiation and exact authorization validation.
3. Refactor normal merge approval under the run lock to perform fresh PR readback,
   exact-head authorization, immediate guarded mutation, and post-mutation readback as one
   resumable control path.
4. Persist keyed intent/applied receipts around the provider crash windows and make resume
   reconcile observed state before deciding whether any mutation remains.
5. Adjust scheduler frontier selection so an authorized merge cannot be displaced by
   unrelated activation, while a real gate still permits safe fail-forward behavior.
6. Extend reports and causal tests for timing, priority, exact-SHA failure, provider errors,
   crash recovery, and idempotent repeated commands.

## Testing Plan

Run the ticket-autopilot kernel, CLI, ledger replay, provider, scheduler, and forward-test
suites. Use isolated Git repositories and stateful fake providers that can crash before
merge, apply then lose the response, change the head, and report merged/open states.
Assert exact command counts, authorization identity, state transitions, critical-path
status, and pure repeated status reads.

## Out of Scope

- Reconciling a merge already performed externally; ticket `03` owns that path.
- Auto-merge, inferred authorization, or authorization that survives candidate/head drift.
- PR-body rendering or provider body mutation beyond ticket `01`.
- Unrelated scheduling, stack retargeting, or leaf-execution changes.

