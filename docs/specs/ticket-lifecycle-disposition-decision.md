# Ticket lifecycle and disposition decision

## Status

Accepted on 2026-08-08. Authority: explicit user decisions for ticket `OI-03`.

## Type

Decision spec

## Source

- [Open GitHub Issues Remediation](./open-github-issues-wayfinder.md)
- GitHub issue [#27](https://github.com/carlitose/agent-skills/issues/27)
- Ticket `OI-03`, "Freeze ticket lifecycle terminology and consequences"

## Context

Canonical ticket sources currently distinguish open tickets at a ticket-folder root from
completed tickets under `done/`. The runner separately records execution states and derives
dependency blocking. A single editable status would conflate durable operator intent,
execution progress, scheduling eligibility, and the reason an attempt stopped.

This decision freezes the semantics needed by `OI-04`. It does not implement new source
folders, commands, ledger fields, scheduling behavior, or migrations.

## Decision

Ticket status is modeled on four orthogonal axes:

| Axis | Meaning | Authority | Persistence |
| --- | --- | --- | --- |
| Administrative disposition | Durable placement of the ticket: `open`, `on-hold`, `canceled`, or `completed` | User for hold, cancel, and reopen; existing successful finalization for completed | Canonical ticket source and audit history |
| Execution lifecycle | State and outcome of a particular run or attempt, including the existing ledger lifecycle | Runner, subject to user control at safe boundaries | Ledger and resumable checkpoints |
| Derived readiness | Whether the scheduler may start the ticket, computed from disposition, dependencies, mode, and gates | Scheduler derivation; never directly edited | Recomputed view, with reasons |
| Stop reason | Non-empty reason attached when an attempt pauses, stops, gates, or fails | Actor or subsystem causing the stop | Attempt history and evidence |

No value on one axis silently rewrites another. In particular, `blocked` is derived
readiness, `stopped` is an attempt outcome, and `pause` is temporary runtime control. None
is a durable administrative disposition.

### Administrative disposition

- `open`: eligible for readiness evaluation. It is not necessarily schedulable.
- `on-hold`: durable user intent to suspend the ticket. The ticket is not schedulable.
- `canceled`: durable user intent that the ticket must not execute. The ticket is not
  schedulable.
- `completed`: the existing durable result of successful finalization. It is not a synonym
  for stopped, failed, or canceled and is not set by hold/cancel commands.

The intended source mapping for `OI-04` is root `*.md` for `open`, `hold/*.md` for
`on-hold`, `canceled/*.md` for `canceled`, and `done/*.md` for `completed`. The directory
name `hold` is storage vocabulary; the public disposition remains `on-hold`.

### Execution lifecycle, pause, and stopped

The existing runner lifecycle remains authoritative for execution. This decision adds no
replacement state machine.

- `pause` is a temporary runtime suspension of an active attempt. It preserves resumable
  state and does not move the canonical ticket source or imply `on-hold`.
- `stopped` describes the outcome of an attempt that will perform no more work. It must be
  accompanied by a stop reason. A later attempt may start if the durable disposition and
  derived readiness permit it.
- A failed, gated, waiting, aborted, paused, or stopped attempt does not by itself cancel,
  hold, reopen, or complete the ticket.
- `completed` remains the successful durable finalization outcome, not a generic label for
  an attempt that ceased running.

### Derived readiness and dependency consequences

Readiness is recomputed; users do not set `blocked` directly.

- An `open` ticket may be ready only when its declared dependencies and other gates permit
  scheduling.
- An `on-hold`, `canceled`, or `completed` ticket is not schedulable.
- An open dependent of an `on-hold` ticket is blocked with a reason identifying the held
  dependency.
- An open dependent of a `canceled` ticket is blocked with reason
  `dependency-canceled`.
- Canceling a ticket never cascades cancellation to its dependents. They retain their own
  disposition and remain blocked until the graph is changed or the dependency is reopened.
- Existing completed-dependency behavior remains unchanged.

### Disposition changes during active execution

A user hold or cancellation request against an active ticket is honored at the next atomic
safe boundary:

1. The in-flight atomic operation is allowed to reach a consistent observable boundary;
   it is not torn down midway.
2. Its checkpoint, worktree, and evidence are preserved truthfully, including any result
   already returned by an external system.
3. At that boundary, the runner records the audited stop receipt and applies the durable
   disposition transition atomically. Together they form the only final administrative
   mutation authorized by the request.
4. Only after that receipt and transition are durable does the runner prohibit every new
   work mutation, external or provider call, and delivery step for that ticket.

If the runner cannot prove it is at a safe boundary, it must gate rather than claim the
hold or cancellation is complete. A source move without its matching authorized
transition receipt is source drift and must gate; it is not adopted as disposition. A
disposition change is not permission to delete a worktree, discard checkpoints, rewrite
evidence, close a provider object, or unwind an already completed remote effect.

### Reopening

Only the user may reopen `on-hold` or `canceled` work. The request must carry an auditable
user identity and a non-empty motivation. A successful reopen:

1. records the previous disposition, actor, reason, and transition identity;
2. moves the source to `open` atomically;
3. sets execution eligibility back to `pending`, without resuming an old active attempt;
4. revalidates the managed source snapshot, dependencies, CandidateRef inputs, retained
   evidence, provider state, and any applicable gates before further work.

Evidence is preserved as history but receives no automatic current-candidate authority.
Snapshot or evidence drift fails closed. Automated policy, dependency completion, elapsed
time, and a previous actor cannot reopen the ticket. This decision grants no reopen path
from `completed`.

## Semantic invariants

- Durable disposition has exactly one value and changes only through an atomic, audited
  transition.
- `blocked`, `paused`, and `stopped` never appear as durable dispositions.
- Every dependency block identifies the dependency and a stable reason; canceled
  dependencies use `dependency-canceled`.
- Cancellation affects only the selected ticket's disposition.
- A disposition request cannot erase or strengthen existing evidence.
- Together, the safe-boundary stop receipt and durable disposition transition form the
  only final administrative mutation; after both are recorded, no new work, provider, or
  delivery effect begins.
- A source transition without its matching authorized receipt is drift and gates.
- Reopening creates pending work that must be revalidated; it never silently resumes a
  stale attempt.

## Decision scenarios

| Scenario | Required result |
| --- | --- |
| User holds an inactive open ticket | Disposition becomes `on-hold`; it is unschedulable; actor and reason are audited |
| User pauses an active attempt | Attempt is temporarily paused with checkpoint and reason; disposition stays `open` |
| An attempt stops for a retryable reason | Attempt reports `stopped` plus reason; disposition is unchanged; readiness is recomputed |
| A dependency is held | Dependent stays open but is blocked by the held dependency |
| A dependency is canceled | Dependent stays open, is blocked with `dependency-canceled`, and is not canceled automatically |
| User holds or cancels active work | Current atomic operation settles; artifacts are preserved; the stop receipt and disposition transition are the only final administrative mutation; then no new work, provider, or delivery effect begins |
| Source moves without an authorized transition receipt | Move is treated as drift; the ticket gates and the runner does not adopt the disposition |
| Non-user actor requests reopen | Request is rejected without changing disposition or evidence |
| User reopens held or canceled work | Audited transition to `open`/`pending`; snapshots and evidence are revalidated before scheduling |
| Snapshot changed while held | Reopen remains pending or gated until drift is reconciled; old evidence is not promoted |

## Rejected alternatives

- **One editable status field:** rejected because it conflates intent, progress, readiness,
  and history.
- **Make `stopped` a fourth operator disposition:** rejected because stopped belongs to an
  attempt and does not answer whether future work is allowed.
- **Treat pause as on-hold:** rejected because a runtime checkpoint suspension must not
  perform a durable source move or require an administrative reopen.
- **Cascade cancellation through dependencies:** rejected because it destroys independent
  user intent and makes graph repair irreversible.
- **Treat a canceled dependency only as a malformed graph:** rejected as the runtime view;
  it must remain observable as blocked with `dependency-canceled` until repaired.
- **Interrupt active work immediately:** rejected because tearing an atomic mutation or
  provider call can lose the truthful result and corrupt recovery.
- **Automatically reopen when a dependency or timer changes:** rejected because only an
  audited user decision may reverse a durable hold or cancellation.
- **Reuse old evidence on reopen:** rejected because disposition is not evidence validity
  and the managed snapshot or CandidateRef may have drifted.

## Migration and compatibility

`OI-04` must preserve these mappings:

- root ticket sources normalize to `open`;
- `done/` sources continue to normalize to `completed`;
- new `hold/` and `canceled/` sources normalize to `on-hold` and `canceled`;
- existing ledger lifecycle values keep their current meaning;
- existing failed, aborted, gated, and waiting records are not backfilled as stopped,
  on-hold, or canceled;
- legacy dependency blocking is recomputed from the canonical graph rather than rewritten
  as user status.

No Ticket Envelope schema change is implied by this decision. If `OI-04` changes persisted
ledger or inventory schemas, it must version them explicitly, reject incompatible active
state clearly, and provide a deterministic migration or fail-closed recovery path. Public
JSON may add the new disposition values only under its documented versioning rules.

## Security and audit requirements

- Validate source paths and reject symlink or path-escape transitions.
- Bind each mutation to ticket identity, prior disposition, actor, non-empty reason, and a
  stable transition identity for idempotent crash recovery.
- Never infer user identity from a provider account or prior run owner.
- Preserve evidence and external-effect receipts without credentials or secret material.
- Contradictory source destinations or duplicate transition identities fail closed.

## Verification plan for OI-04

No verification below is claimed as executed by this decision-only ticket.

- **Unit:** disposition parsing, transition matrix, actor/reason validation, readiness
  derivation, stable block reasons, and idempotency identities.
- **Integration:** atomic hold/cancel/reopen source moves; held and canceled dependency
  chains; no cancellation cascade; source drift and contradictory destinations.
- **Crash/resume:** interruption before and after the source move and audit receipt; active
  safe-boundary stop with checkpoints, worktree, and evidence retained.
- **System/CLI:** status and versioned JSON distinguish disposition, lifecycle, readiness,
  and stop reason; reopen returns `pending` and requires revalidation.
- **Provider boundary:** inject or observe an in-flight external effect and prove no new
  provider or delivery effect begins after the safe boundary. If no live provider is
  authorized, retain this as an explicit verification gate.
- **Manual audit:** confirm actor identity and motivation are present for every reverse
  transition and that a non-user reopen is rejected.

## Implementation boundary

`OI-04` owns implementation and causal tests. It may choose concrete commands and persisted
field names only if they preserve this decision. Any change to dependency consequences,
reopening authority, safe-boundary behavior, or the four-axis model requires a new explicit
human decision.

## Unresolved questions

None for lifecycle semantics. Concrete storage schema, CLI spelling, and migration tooling
remain implementation choices for `OI-04`, bounded by the invariants above.
