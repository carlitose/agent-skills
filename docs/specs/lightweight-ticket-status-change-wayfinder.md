# Lightweight Ticket Status Changes

## Artifact Graph

- Artifact ID: `artifact:lightweight-ticket-status-change-wayfinder`
- Role: `wayfinder`
- Standalone: true

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

## Not Yet Specified

- **Transaction owner when no usable run exists.** Current commands require a schema-4 run,
  while repository tickets may be unmanaged, belong only to retired legacy runs, or appear
  in several historical ledgers. The production lane needs one canonical lifecycle-only
  identity rather than silently choosing a run.
- **Isolation from an active candidate.** The current command uses the target run worktree.
  The delivery candidate must not accidentally include an active ticket’s staged or
  unstaged implementation. Whether to use a clean administrative worktree, a constrained
  index, or a runner-authored lifecycle commit needs crash-tested proof.
- **Gated and waiting tickets.** Product semantics permit a user to cancel inactive work,
  but the current kernel rejects states outside `pending` and `active`. The exact admissible
  execution-state matrix and safe-boundary receipt for `gated`, `waiting`, and stopped
  attempts must be made explicit without treating a gate as approval.
- **Tracked delivery replay.** The point at which lifecycle intent, source move, commit
  intent, push, PR, merge, terminal proof, and ledger projection become recoverable needs a
  single ordered protocol. Provider `MERGED` alone remains insufficient.
- **Ignored-source result.** The lane must define whether a receipt-only external transition
  is terminal and how it is read back without granting tracked completion projection or
  publication authority.
- **Routing contract.** `ask-skills` currently sends canonical ticket Markdown to
  `execute-ticket`. The new route must take precedence only when the user explicitly asks
  for an administrative disposition change; ordinary ticket execution must remain
  unchanged.
- **Policy wording.** The mandatory delivery policy needs a narrow, auditable recognition of
  this lifecycle-only lane. A generic “docs-only” exception would be too broad.

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

- **Lifecycle-only transaction shape:** ready for a throwaway prototype. It must compare an
  existing-run transition with an unmanaged/retired-run transition, and prove that a dirty
  target worktree cannot leak files into the administrative candidate.
- **Execution-state matrix:** blocked on the prototype’s observation of `pending`, `active`,
  `gated`, and `waiting` fixtures. Existing product semantics are fixed; the question is the
  safe implementation boundary.
- **Production spec and tickets:** blocked on the transaction prototype. Do not guess the
  Git/ledger ordering in an implementation ticket.
- **Real ticket mutation:** blocked on a later exact ticket-scoped disposition authority.
  This Wayfinder is not that authority.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| TSC-01 | prototype | AFK | — | Prove a lifecycle-only status transaction | Disposable fixtures comparing tracked/ignored source, usable/missing/retired run, pending/active/gated/waiting state, dirty-index isolation, crash boundaries, exact replay, and the minimum Git/ledger ordering; recommendation for the v1 seam, with no production mutation |
| TSC-02 | task | AFK | TSC-01 | Specify the dedicated status-change lane | A focused production spec for `change-status-ticket`, its precedence in `ask-skills`, exact inputs/outputs, authority and merge separation, transaction states, compatibility boundary, and tracer-bullet delivery tickets emitted through the canonical Ticket Envelope |

These are planned frontier units only. No Ticket Envelope has been emitted by this
Wayfinder, and neither row authorizes execution.

## Next Review

Inspect the TSC-01 result for one decisive property: can the runner produce and recover an
exact lifecycle-only candidate without reading or committing unrelated active-candidate
state? If yes, freeze that seam in TSC-02. If no, keep the capability at the map/prototype
boundary rather than disguising a manual Git workflow as a safe skill.

After the status-change frontier is recorded, return to the operational roadmap. RD-03 and
RD-04 are integrated. Keep `gate:RD-05:start:2` open until separate exact live-publication
authority exists; no implementation, merge, reconciliation, Pi-sync, or broad AFK authority
may satisfy that gate.
