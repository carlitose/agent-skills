# Ticket Autopilot Delivery, Merge, and Open-Issue Recovery

## Type

Wayfinding spec

## Status

Active

## Destination

Preserve the integrated resolutions of
[GitHub issue #16](https://github.com/carlitose/agent-skills/issues/16) and
[GitHub issue #17](https://github.com/carlitose/agent-skills/issues/17), then resolve the
currently open issues [#21](https://github.com/carlitose/agent-skills/issues/21),
[#22](https://github.com/carlitose/agent-skills/issues/22), and
[#23](https://github.com/carlitose/agent-skills/issues/23). Preserve exact-head provider
mutation while making merge authority explicitly configurable and semantic validation
independent of lineage-only SHA churn.

The reachable outcome is:

- `delivery` reaches `pr-open` only after `explain-pr` has rendered a body from the exact
  validated verification bundle, the body has passed local validation, the provider has
  published it, and provider readback of both body and HEAD has passed the same validation;
- the normal runner merge follows exact-SHA authorization immediately, before unrelated
  ticket work can extend the critical path;
- a merge already performed by the human in the provider is reconciled by one idempotent
  `approve --external-merge` operation;
- delivery and merge failures remain durable, visible, resumable gates rather than
  optimistic lifecycle states;
- a fully Git-ignored ticket folder can drive a run through a managed immutable snapshot
  without entering the implementation PR;
- an explicit run-scoped autonomous merge grant can replace per-PR prompts while every
  provider merge remains policy-checked and bound to the freshly observed head;
- when a parent merge changes only stack lineage, downstream PRs are rebased and retargeted
  without repeating review, QA, or verification; any changed base tree, candidate tree, or
  ticket contract still forces complete semantic revalidation;
- the root README explains the complete ticket-autopilot workflow, safety modes, ignored
  sources, stacked reconciliation, and recovery behavior.

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
- Tickets `01–03` are integrated through PRs
  [#18](https://github.com/carlitose/agent-skills/pull/18),
  [#19](https://github.com/carlitose/agent-skills/pull/19), and
  [#20](https://github.com/carlitose/agent-skills/pull/20). Their completion records bind
  the implementation to exact CandidateRefs and the canonical folder parser recognizes
  their dependencies as satisfied.
- The GitHub body-only update path must avoid GraphQL project-card queries. Provider
  adapters may use provider-specific transport internally, but normalized receipts and
  core state remain provider-neutral.
- Normal runner authorization and external-merge reconciliation are distinct operations.
  The former authorizes an immediate guarded merge; the latter proves that the recorded
  exact head is already merged and must never invoke a merge command.
- Backward compatibility remains opt-in. If persisted delivery or ledger shapes change,
  incompatible active runs must fail clearly or use an explicit validated migration.
- Issue #21 is governed by
  [Ticket Autopilot Ignored Ticket Sources](./ticket-autopilot-ignored-ticket-sources.md):
  only positively ignored in-repository ticket inputs gain the external snapshot path;
  arbitrary untracked folders remain rejected.
- Issue #23 and the added stack requirement are governed by
  [Ticket Autopilot Autonomous Stacked Delivery](./ticket-autopilot-autonomous-stacked-delivery.md):
  manual merge remains the default, autonomous authority is an explicit run-scoped grant,
  and semantic candidate identity uses base/candidate tree OIDs rather than commit lineage.
- The human request explicitly authorizes avoiding redundant semantic review for an exact
  content-equivalent stack reconciliation. It does not authorize path-based selective
  reuse, policy bypass, or stale-head merge.
- GitHub CLI's current manual documents `gh pr merge --match-head-commit` as the atomic
  stale-head guard. Autonomous mode uses the normalized expected-head capability and never
  `--admin`; provider auto-merge/queue behavior remains gated unless exact-head pinning is
  proven.

## Not Yet Specified

- The exact cross-filesystem intent/applied receipt used when an ignored caller ticket is
  moved to `done/`. Ticket `04` must make its crash windows replay-safe.
- The concrete persisted contract/version split between semantic candidate identity and
  delivery lineage. Ticket `05` owns it and must reject incompatible active ledgers.
- Whether a live provider merge queue can retain an exact-head guarantee after enqueue.
  Ticket `06` must prove that capability or keep autonomous execution gated instead of
  falling back to an unpinned provider auto-merge.

## Out of Scope

- Executing these tickets, mutating or closing the GitHub issues, or merging a real PR in
  this Wayfinder pass.
- Making autonomous merge the default, inferring its grant from `AFK`, using `--admin`, or
  authorizing a different head than the provider operation observes.
- Selective path-based evidence reuse, unchanged-filename heuristics, or preservation after
  a changed semantic candidate.
- Accepting ticket folders outside the repository or arbitrary untracked non-ignored input.
- Reworking bounded-leaf budgets or unrelated scheduler behavior.
- Fabricating live provider, credential, policy, or human evidence.
- Replacing `explain-pr` or `verification-audit` with a second renderer or validator.

## Frontier / Blocking Edges

- **Ignored sources are rejected before execution:** ticket `04` is independently ready and
  owns source classification, managed snapshots, and dual-mode finalization for issue #21.
- **Commit lineage is conflated with semantic identity:** ticket `05` is blocked by ticket
  `02`'s stable merge critical path; it then splits content identity from delivery lineage
  and preserves evidence only for exact tree-equivalent stack reconciliation.
- **Autonomous authority has no durable scope:** ticket `06` is blocked by `05`; it records
  an explicit run grant and applies it only through live policy checks and the exact-head
  merge path. This resolves issue #23 without turning `AFK` into implicit merge consent.
- **README precedes the final public contract today:** ticket `07` waits for external merge,
  ignored-source, and autonomous-stack behavior, then documents only the implemented CLI
  and recovery semantics. This resolves issue #22.

## Ticket Plan

- [`01`](../tickets/ticket-autopilot-delivery-merge/done/01-publish-verified-pr-body.md)
  — task, AFK, integrated — **Publish and verify the `explain-pr` body before `pr-open`.**
  Expected output: a CandidateRef-bound render handoff, canonical validation, provider
  publication/readback, durable failure phases, REST-safe GitHub updates, and end-to-end
  idempotency tests. Covers issue #16.
- [`02`](../tickets/ticket-autopilot-delivery-merge/done/02-merge-immediately-after-authorization.md)
  — task, AFK, integrated — **Merge immediately after exact-SHA authorization.**
  Expected output: one guarded runner authorization/merge/reconciliation critical path,
  replay-safe receipts, pure status phase/elapsed reporting, and scheduler priority over
  unrelated work. Covers the normal-runner half of issue #17.
- [`03`](../tickets/ticket-autopilot-delivery-merge/done/03-reconcile-external-merge-atomically.md)
  — task, AFK, integrated — **Reconcile an external merge atomically.** Expected
  output: one live-readback `approve --external-merge` command that validates PR identity
  and exact head, records external evidence, reaches `integrated`, and replays
  idempotently. Covers the external-merge half of issue #17.
- [`04`](../tickets/ticket-autopilot-delivery-merge/04-support-ignored-ticket-sources.md)
  — task, AFK, ready — **Support Git-ignored ticket sources.** Expected output: strict
  tracked/ignored classification, an immutable managed ticket snapshot, dual-mode
  finalization, drift/crash protection, and status visibility. Covers issue #21.
- [`05`](../tickets/ticket-autopilot-delivery-merge/05-preserve-stack-evidence-across-lineage-rebases.md)
  — task, AFK, blocked by `02` — **Preserve semantic evidence across lineage-only stack
  rebases.** Expected output: semantic candidate v2, separate delivery lineage, exact
  tree-equivalence receipts, no redundant review/QA/verification, and full invalidation on
  semantic drift.
- [`06`](../tickets/ticket-autopilot-delivery-merge/06-add-opt-in-autonomous-merge-grant.md)
  — task, AFK, blocked by `05` — **Add an opt-in autonomous merge grant.** Expected output:
  manual-by-default policy, durable run-scoped authority, fresh check/policy observation,
  exact-head provider mutation, crash-safe receipts, and stacked-chain progression. Covers
  issue #23.
- [`07`](../tickets/ticket-autopilot-delivery-merge/07-rewrite-readme-for-ticket-autopilot.md)
  — task, AFK, blocked by `03`, `04`, and `06` — **Rewrite the README around the shipped
  ticket-autopilot workflow.** Expected output: install/use examples, modes, lifecycle,
  safety boundaries, ignored sources, stacked PRs, merge recovery, and troubleshooting.
  Covers issue #22.

## Next Review

The ready frontier is tickets `04` and `05`. Inspect `04` for mixed source modes, snapshot
drift, symlink/path escape, and move/receipt crash windows. Inspect `05` for exact base/candidate
tree equality, semantic invalidation, ledger compatibility, and repeated leaf counts. Ticket
`06` follows `05`; integrated ticket `03` and ticket `04` join with `06` at README ticket
`07`.
