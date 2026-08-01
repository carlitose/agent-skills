# Ticket Autopilot Delivery and Merge Recovery

## Type

Wayfinding spec

## Status

Active

## Destination

Resolve [GitHub issue #16](https://github.com/carlitose/agent-skills/issues/16) and
[GitHub issue #17](https://github.com/carlitose/agent-skills/issues/17) without weakening
the accepted exact-SHA and human-authorization invariants.

The reachable outcome is:

- `delivery` reaches `pr-open` only after `explain-pr` has rendered a body from the exact
  validated verification bundle, the body has passed local validation, the provider has
  published it, and provider readback of both body and HEAD has passed the same validation;
- the normal runner merge follows exact-SHA authorization immediately, before unrelated
  ticket work can extend the critical path;
- a merge already performed by the human in the provider is reconciled by one idempotent
  `approve --external-merge` operation;
- delivery and merge failures remain durable, visible, resumable gates rather than
  optimistic lifecycle states.

## Decisions So Far

- The current scheduler architecture and safety rules in
  [Bounded Ticket-Autopilot Leaves](./bounded-ticket-autopilot-leaves-wayfinder.md) and
  [`ticket-autopilot/SKILL.md`](../../ticket-autopilot/SKILL.md) remain authoritative:
  provider-neutral core, one PR per ticket, CandidateRef invalidation, no inferred
  authorization, and exact observed-head binding.
- PR explanation is part of delivery, not optional post-processing. It must complete
  before the ledger records `pr-open`; therefore explanation work also completes before
  merge authorization is requested.
- `explain-pr` remains the semantic renderer. Deterministic code owns the content-addressed
  handoff, local validation, provider mutation/readback, state transitions, receipts, and
  retry behavior.
- Current code confirms both reported gaps: `DeliveryFinalizer` supplies
  `ledger://<run>/<ticket>` as `body_artifact`; the GitHub adapter updates PRs through
  `gh pr edit` and does not read the body back; `_approve` records authorization while a
  later `integrate` event performs provider readback and ledger integration.
- The GitHub body-only update path must avoid GraphQL project-card queries. Provider
  adapters may use provider-specific transport internally, but normalized receipts and
  core state remain provider-neutral.
- Normal runner authorization and external-merge reconciliation are distinct operations.
  The former authorizes an immediate guarded merge; the latter proves that the recorded
  exact head is already merged and must never invoke a merge command.
- Backward compatibility remains opt-in. If persisted delivery or ledger shapes change,
  incompatible active runs must fail clearly or use an explicit validated migration.

## Not Yet Specified

- The exact versioned shape and storage location of the `explain-pr` render request and
  rendered-body receipt. Ticket `01` owns this contract and must bind it to ticket ID,
  CandidateRef, verification-bundle identity, PR ID when available, and expected HEAD.
- The exact normalized provider operation names for body publication and body/HEAD
  readback. Ticket `01` owns them and must preserve GitHub and Azure DevOps capability
  negotiation.
- The precise persisted clock representation for merge-critical-path phase and elapsed
  time. Ticket `02` owns a replay-safe representation; status reads must remain pure.
- The recovery event sequence for a crash after provider merge but before ledger
  integration. Tickets `02` and `03` must make replay converge without a second merge or
  second semantic authorization.

## Out of Scope

- Executing these tickets, mutating or closing the GitHub issues, or merging a real PR in
  this Wayfinder pass.
- Auto-merge, inferred approval, authorization for a different head SHA, or weakening
  CandidateRef invalidation.
- Reworking bounded-leaf budgets, selective invalidation, stacked-PR reconciliation, or
  unrelated scheduler behavior.
- Fabricating live provider, credential, policy, or human evidence.
- Replacing `explain-pr` or `verification-audit` with a second renderer or validator.

## Frontier / Blocking Edges

- **Untrusted placeholder body:** `pr-open` is currently reachable without a contract-valid
  explanation. Ticket `01` unblocks delivery by carrying the validated bundle through
  render, validate, publish, readback, and revalidate.
- **Authorization is separated from the guarded merge:** after ticket `01` fixes delivery
  ordering, ticket `02` can make normal exact-SHA approval enter and finish the merge
  critical path atomically enough to survive provider and process failures.
- **External merge needs a second semantic transition:** ticket `03` is blocked by the
  authorization-path changes in ticket `02`; it then collapses live external readback,
  external evidence, and integration into one idempotent command.

## Ticket Plan

- [`01`](../tickets/ticket-autopilot-delivery-merge/01-publish-verified-pr-body.md)
  — task, AFK, ready — **Publish and verify the `explain-pr` body before `pr-open`.**
  Expected output: a CandidateRef-bound render handoff, canonical validation, provider
  publication/readback, durable failure phases, REST-safe GitHub updates, and end-to-end
  idempotency tests. Covers issue #16.
- [`02`](../tickets/ticket-autopilot-delivery-merge/02-merge-immediately-after-authorization.md)
  — task, AFK, blocked by `01` — **Merge immediately after exact-SHA authorization.**
  Expected output: one guarded runner authorization/merge/reconciliation critical path,
  replay-safe receipts, pure status phase/elapsed reporting, and scheduler priority over
  unrelated work. Covers the normal-runner half of issue #17.
- [`03`](../tickets/ticket-autopilot-delivery-merge/03-reconcile-external-merge-atomically.md)
  — task, AFK, blocked by `02` — **Reconcile an external merge atomically.** Expected
  output: one live-readback `approve --external-merge` command that validates PR identity
  and exact head, records external evidence, reaches `integrated`, and replays
  idempotently. Covers the external-merge half of issue #17.

## Next Review

Route ticket `01` to `execute-ticket`. Before accepting it, inspect the forward tests for
the literal placeholder regression, invalid/overclaiming bodies, provider publication and
readback failures, changed HEAD, and crash-resume idempotency. Only then advance ticket
`02`; ticket `03` follows after the shared authorization path is stable.
