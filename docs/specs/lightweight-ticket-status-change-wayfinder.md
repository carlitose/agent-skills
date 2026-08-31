# Lightweight Ticket Status Changes

## Artifact Graph

- Artifact ID: `artifact:lightweight-ticket-status-change-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [TSC-01 — Prove a lifecycle-only status transaction](../tickets/lightweight-ticket-status-change/done/01-prove-lifecycle-only-status-transaction.md)
- [TSC-02 — Specify the dedicated status-change lane](../tickets/lightweight-ticket-status-change/done/02-specify-dedicated-status-change-lane.md)
- [Change Status Ticket](./change-status-ticket.md)

## Type

Wayfinding spec

## Status

Active

## Destination

A request such as “hold this ticket”, “cancel this ticket”, or “reopen this ticket” reaches
one concise administrative lane without invoking `execute-ticket` or pretending that a code
candidate exists.

The public agent capability should be named `change-status-ticket` for discoverability, but
it must normalize “status” to the existing **administrative disposition** vocabulary:
`open`, `on-hold`, or `canceled`. It must reject attempts to set execution lifecycle,
readiness, `blocked`, `paused`, `stopped`, or `completed` through this lane.

For tracked ticket sources, success means more than moving a file: the exact source move,
inbound-link repoints, lifecycle receipt, Git candidate, provider delivery, and terminal
integration must be mutually consistent. Human disposition authority and merge authority
remain separate. For ignored sources, the lane must retain the existing external-source
boundary rather than silently publishing the ticket.

## Current Evidence

- The accepted
  [ticket lifecycle decision](./ticket-lifecycle-disposition-decision.md) already fixes the
  four axes, actor/reason requirements, no-cascade rule, active-work safe boundary, and
  human-only reopen semantics. This Wayfinder does not reopen those product decisions.
- The runner already owns the hard state transition:
  `ticket-hold`, `ticket-cancel`, `ticket-reopen-request`, and `ticket-reopen` call
  `transition_ticket_source`, bind an idempotent receipt, update the run ledger, repoint
  inbound documentation links, and stage tracked paths. Reopen consumes a ticket-bound
  passed human gate and invalidates candidate-through-merge state.
- That CLI is **not an end-to-end status-change lane**. It requires an existing `run_id`,
  operates in the run’s bound worktree, and stops before commit, push, PR, merge, and fresh
  terminal-branch reachability. A skill that merely wraps the current command would leave a
  tracked administrative decision staged but not durably integrated.
- The current kernel accepts hold/cancel only when execution state is `pending` or `active`.
  Commit `711e574b79c8f6ad618dae873a2ebc13e8c9b0e9` records that WT-07 had to be moved by
  hand because it was human-gated. The later run snapshots WT-07 as canceled but carries no
  disposition receipt. This is evidence of a real repository-level gap, not authority to
  repeat the workaround.
- Commit `09d9ad25d30f7c250441ae2e06a637d1135b0729` and PR #114 are the closest historical
  vertical slice: AG-05 was canceled with a two-path docs-only commit (source move plus
  inbound-link repoint), while the lifecycle receipt remained in its run journal. It proves
  the desired no-code diff shape, but Git delivery was manually stitched to the lifecycle
  command.
- A fresh provider-free `ticket-list` observation at repository head
  `46bc170a1db3103ee8f5a86494b69c316f350241` on 2026-08-31 finds 101 project
  tickets: 96 completed, two canceled, and three open (`TK-09`, bounded-leaves `06`,
  and `RD-05`). Test fixtures are excluded from those counts. RD-04 is integrated; its
  completion does not grant RD-05's separate issue-publication authority.
- [TSC-01's disposable prototype](../prototypes/lifecycle-only-status-transaction/NOTES.md)
  now proves that a repository-owned transaction plus a clean detached administrative
  worktree can exclude staged and unstaged target-run dirt, recover the existing source
  receipt before and after its move, and retain separate provider/merge/terminal phases.
  It also observes that the current kernel accepts `pending`/`active` hold/cancel but
  rejects `gated`/`waiting`; the prototype does not claim production support.

## Decisions So Far

- **Use a dedicated agent boundary.** `change-status-ticket` is smaller and semantically
  truer than `execute-ticket`: there is no implementation, simplification, code review, QA,
  Verification Record, or CandidateRef claim to manufacture for a pure administrative
  decision.
- **Reuse runner lifecycle primitives.** The capability may orchestrate existing commands
  or a new lifecycle-only runner entry point, but it must not duplicate the transition
  matrix, receipt format, source-digest checks, locking, link repointing, or reopen gate.
- **Keep delivery narrow, not absent.** A tracked source move is still a repository change.
  Its lane needs an exact allowlist (ticket rename plus deterministic inbound-link repoints),
  clean-tree/index checks, an idempotent administrative commit, provider-neutral PR
  readback, separate exact-head merge authority, and terminal integration proof. “No code”
  removes the code-quality loop; it does not remove Git truth.
- **Make the repository own the transaction.** A unique usable run is only an optional
  append-only projection target. Missing or retired ownership does not block repository
  truth, multiple usable owners fail closed, and no active run worktree is a delivery
  candidate input.
- **Authority is never inferred from routing.** Mentioning a ticket, selecting a target
  disposition, invoking the skill, or naming a gate is not actor/evidence authority.
  Hold/cancel require the exact user identity, non-empty reason, and durable authority
  reference. Reopen remains request → exact human gate approval → apply.
- **Preserve current axes.** Pause remains run-scoped; blocked remains derived; stopped
  remains an attempt outcome; completed remains finalization-owned. The new lane must refuse
  requests that conflate them with administrative disposition.
- **Do not mutate the current backlog during discovery.** This map and any prototype grant
  no authority to hold, cancel, reopen, commit, publish, or merge a ticket change.

## Proposed Capability Boundary

`change-status-ticket` should own only:

1. resolve the exact repository, ticket source, target disposition, and any owning active
   run without guessing across duplicate ticket IDs;
2. read back current source disposition and run lifecycle;
3. collect or validate the exact authority required by the existing lifecycle decision;
4. invoke one deterministic lifecycle transaction and replay it safely after a crash;
5. for tracked source, freeze and deliver only the lifecycle allowlist, under independent
   merge authority and fresh terminal proof;
6. read back the canonical source, receipt, ledger projection when one exists, provider
   state when delivery occurred, and final terminal reachability;
7. report a concise terminal result or the exact open gate.

It must not implement the target ticket, edit its body, change dependencies, infer a reason,
resolve unrelated gates, reuse implementation evidence, delete a worktree, close external
objects, or publish ignored sources.

## Production Contract

[Change Status Ticket](./change-status-ticket.md) freezes the production interface,
repository transaction identity, run-ownership matrix, tracked and ignored outcomes,
crash-safe ordering, routing precedence, and authority boundaries. It adopts only the
prototype's proved isolation and replay properties.

The remaining gaps are delivery work, not implicit capability:

- `CST-01` creates the repository transaction and ignored-source vertical slice while
  gating tracked and non-pending states.
- `CST-02` adds content-complete tracked admin-worktree delivery through separate merge
  authority and fresh terminal proof.
- `CST-03` adds the repository mutation barrier and active/gated/waiting safe-boundary
  projections without erasing attempt or gate evidence.
- `CST-04` publishes the skill and narrow routing/mandatory-policy contract only after the
  runner seams are integrated.

## Out of Scope

- Changing the accepted lifecycle vocabulary or dependency consequences.
- Setting `completed`, execution lifecycle, readiness, or stop reasons directly.
- Editing ticket content, dependencies, acceptance criteria, or Artifact IDs.
- Cascading a cancellation to dependents.
- Reusing old review, QA, verification, CandidateRef, merge, publication, wiki, or Pi-sync
  authority.
- Provider-specific orchestration, direct default-branch pushes, inferred merge consent, or
  cleanup of retained worktrees and checkpoints.
- Applying a real status change while this Wayfinder is active.

## Frontier / Blocking Edges

- **Repository transaction:** ready as CST-01; no usable-run prerequisite may be
  reintroduced.
- **Tracked delivery:** blocked only by CST-01's durable handoff contract; path-only equality
  remains insufficient.
- **State matrix:** active/gated/waiting production support remains blocked until CST-03
  proves the mutation barrier and append-only projection. Earlier slices must gate.
- **Public routing:** blocked until CST-02 and CST-03 integrate; no skill wrapper may precede
  the runner capability.
- **Real ticket mutation:** blocked on a later exact ticket-scoped user authority. This map,
  spec, prototype, and ticket batch grant none.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| TSC-01 | prototype | AFK | — | Prove a lifecycle-only status transaction | Completed disposable evidence and repository-owner/admin-worktree recommendation; no production mutation |
| TSC-02 | task | AFK | TSC-01 | Specify the dedicated status-change lane | This production spec plus canonical CST-01..CST-04 Ticket Envelopes |
| CST-01 | task | AFK | — | Add the repository lifecycle transaction and ignored-source slice | Exact journal/resolver/authority and ignored `external-unpublished` vertical slice |
| CST-02 | task | AFK | CST-01 | Deliver tracked status candidates through terminal proof | Clean admin candidate, provider readback, separate merge authority, terminal source projection |
| CST-03 | task | AFK | CST-01, CST-02 | Enforce mutation barriers and safe-boundary projection | Active/gated/waiting preservation and no post-barrier effects |
| CST-04 | task | AFK | CST-02, CST-03 | Publish the dedicated status-change skill and routing contract | Public skill, narrow routing precedence, mandatory-policy integration, forward matrix |

The CST Ticket Envelopes are emitted under `docs/tickets/change-status-ticket/`. They
require ordinary Ticket Autopilot delivery and authorize no real disposition.

## Next Review

Review CST-01 for one property: repository-common intent and ignored-source truth must be
terminal without a usable run and without a Git/provider effect. Do not schedule CST-02 if
CST-01 makes an active run or its dirty worktree the transaction owner.

RD-03 and RD-04 remain integrated. Keep `gate:RD-05:start:2` open until separate exact
live-publication authority exists; no status lane, implementation, merge, reconciliation,
Pi-sync, or broad AFK authority may satisfy that gate.
