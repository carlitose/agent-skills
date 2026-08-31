# Change Status Ticket

## Artifact Graph

- Artifact ID: `artifact:change-status-ticket`
- Role: `spec`
- Parent: [Lightweight Ticket Status Changes](./lightweight-ticket-status-change-wayfinder.md)

### Children

- [CST-01 — Add the repository lifecycle transaction and ignored-source slice](../tickets/change-status-ticket/01-add-repository-lifecycle-transaction.md)
- [CST-02 — Deliver tracked status candidates through terminal proof](../tickets/change-status-ticket/02-deliver-tracked-status-candidates.md)
- [CST-03 — Enforce mutation barriers and safe-boundary projection](../tickets/change-status-ticket/03-enforce-safe-boundary-projection.md)
- [CST-04 — Publish the dedicated skill and routing contract](../tickets/change-status-ticket/04-publish-status-change-skill.md)

Evidence: [Lifecycle-only status transaction prototype](../prototypes/lifecycle-only-status-transaction/NOTES.md).

## Status

Proposed production contract. The four tracer tickets below are required before the public
capability exists. This specification grants no ticket-disposition, provider, merge,
publication, wiki, Pi-sync, or cleanup authority.

## Problem

Holding, canceling, or reopening a ticket is an administrative decision, not an
implementation request. The current runner already owns the source transition primitive,
run-ledger disposition receipts, and reopen gate, but its CLI requires a usable run and
stages in that run's worktree. Wrapping that CLI would risk committing an active
candidate's unrelated state and would stop before tracked Git/provider delivery.

`change-status-ticket` must provide one concise lifecycle-only lane without fabricating an
`execute-ticket` implementation, review, QA, or Verification Record. A tracked source move
is still repository delivery and needs exact Git truth. An ignored source must remain
external and unpublished.

## Goals and non-goals

Goals:

- make one explicit hold/cancel/reopen request exact, durable, replayable, and concise;
- isolate administrative delivery from every implementation candidate;
- preserve tracked and ignored publication boundaries;
- retain separate user, provider, merge, terminal, projection, wiki, Pi, and cleanup
  authorities;
- expose the exact terminal result or gate without conflating disposition, attempt state,
  readiness, and stop reason.

Non-goals:

- implementing or completing the selected ticket;
- editing dependencies, acceptance criteria, or ticket prose;
- adding disposition vocabulary or cancellation cascade;
- direct default-branch pushes or provider-specific orchestration;
- retroactively rewriting legacy/retired ledgers or unreceipted source history;
- performing a real administrative change while delivering this capability.

## Accepted evidence and unresolved gaps

TSC-01 causally established these reusable properties in disposable fixtures:

1. one repository lifecycle transaction can own the operation while a unique usable run is
   only an optional projection target;
2. a detached clean administrative worktree excludes staged and unstaged target-run dirt;
3. the tracked candidate can be constrained to old ticket path, new disposition path, and
   deterministic inbound-link repoints;
4. the existing source transition recovers before and after the move and replays exactly;
5. provider dispatch ambiguity must reconcile without redispatch, and provider `MERGED`
   cannot replace fresh terminal reachability;
6. ignored source transitions can finish as `external-unpublished` without Git/provider
   effects.

The prototype did **not** implement a repository-wide mutation barrier, content-complete
candidate binding, terminal run projection, live provider flow, or `gated`/`waiting`
support. Current kernel preflight accepts only `pending` and `active`; it rejects `gated`
and `waiting`. CST-01 and CST-02 must gate unsupported states. CST-03 is the only ticket
allowed to widen the exact safe-boundary projection after causal tests preserve prior
attempt and gate evidence.

## Vocabulary and axis separation

This capability sets only **administrative disposition**:

- `open`
- `on-hold`
- `canceled`

It rejects `completed`, `blocked`, `paused`, `stopped`, `waiting`, `gated`, `ready`,
`failed`, and every other execution lifecycle, readiness, or stop-reason value. It does
not set dependency readiness directly and never cascades cancellation.

`completed` remains finalization-owned. `pause` remains run-scoped. `stopped` remains an
attempt outcome. A passed gate is evidence for its exact purpose, never a disposition or
merge grant.

## Public capability

The agent-facing skill is named `change-status-ticket`.

### Required normalized inputs

| Field | Contract |
| --- | --- |
| `repository_identity` | Canonical stable repository root plus Git common-directory identity; aliases and noncanonical worktrees fail closed |
| `ticket_identity` | Exact Artifact ID plus canonical source path and ticket digest; a short ticket ID is accepted only when globally unique after fixture exclusion |
| `target_disposition` | Exactly `open`, `on-hold`, or `canceled` |
| `actor` | Non-empty explicit user identity; never inferred from provider login, prior run owner, or agent identity |
| `reason` | Non-empty durable motivation |
| `authority_ref` | Durable reference bound to actor, exact ticket, prior disposition, target disposition, and reason |
| `reopen_gate_id` | Required only for `open`; exact ticket-bound passed human reopen gate |

Hold/cancel reject `reopen_gate_id`. Reopen rejects caller-supplied actor/reason/evidence
that differs from the passed gate. Target source digest, prior disposition, repository
identity, or authority drift stops before mutation.

Merge authority is not an input to the disposition decision. A tracked transaction may
later consume the repository's separate exact-head merge grant. Absence of that grant
leaves the transaction at `merge-gated` without weakening the applied user intent.

### Terminal outputs

| Result | Meaning |
| --- | --- |
| `changed-integrated` | Tracked source, exact candidate and provider head, separate merge decision, terminal proof, source readback, and projections agree |
| `external-unpublished` | Ignored source receipt and source readback agree; no tracked publication or completion was inferred |
| `already-applied` | The exact transaction identity and every required readback replay without a second effect |
| `gated` | One named authority, safe-boundary, ambiguity, drift, provider, merge, or terminal proof remains open |
| `rejected` | Input vocabulary, identity, actor, reason, authority, source, ownership, or gate is invalid before effects |

Every result reports repository identity, ticket Artifact ID/path/digest, prior/target
disposition, transaction ID, source mode, current durable phase, actor, reason,
authority reference, optional projection run, and explicit non-authorities. Credentials and
raw provider payloads are excluded.

## Routing contract

`ask-skills` routes to `change-status-ticket` only when the user explicitly asks to hold,
cancel, or reopen an exact ticket, or explicitly names an administrative disposition.
Words such as “blocked”, “pause the run”, “stop this attempt”, “complete”, “work on”, or a
bare ticket path do not trigger this lane.

Precedence is:

1. explicit administrative-disposition request → `change-status-ticket`;
2. explicit run pause/unpause → Ticket Autopilot runtime control;
3. ordinary shippable ticket work → `to-spec -> to-tickets -> ticket-autopilot`;
4. read-only lifecycle questions → research/diagnosis as routed.

The mandatory package policy may recognize only this named lifecycle-only lane. It must not
add a generic docs-only or “small change” exception. The skill composes the runner
transaction; it does not call `execute-ticket`, manufacture quality stages, or implement
the target ticket.

## Transaction identity and owner

The transaction owner is a repository-common store, not an implementation run. Its ID is a
SHA-256 over canonical schema version, repository identity, ticket Artifact ID/path/digest,
prior and target dispositions, actor, reason, authority reference, reopen gate, source
mode, target branch, and observed target SHA.

The store persists a versioned append-only journal and uses repository-level and exact
usable-run locks. Unknown schemas, duplicate identities with contradictory content,
symlink/path escape, noncanonical repository identity, or lock uncertainty fail closed.

### Run ownership resolution

| Observation | Result |
| --- | --- |
| One usable run whose managed source identity and digest match | Repository transaction proceeds; run is optional projection target |
| No run | Repository transaction proceeds; no run projection |
| Retired matching run(s) only | Repository transaction proceeds; historical run IDs are recorded, never rewritten |
| More than one usable matching run | `ambiguous-run-ownership` gate before mutation |
| Usable run source/digest contradiction | `run-source-drift` gate before mutation |

Historical ledgers are evidence, not transaction owners. A retired run is never migrated or
reactivated merely to change disposition.

## Execution-state matrix and mutation barrier

| State at request | Initial behavior | Final production behavior after CST-03 |
| --- | --- | --- |
| `pending` | Apply at the locked inactive boundary | Same |
| `active` with atomic effect in flight | Persist request and wait; no interruption | Settle effect, append stop receipt, arm barrier, then apply |
| `active` at proved boundary | Supported only after run lock and mutation barrier exist | Append stopped attempt and preserve candidate/evidence |
| `gated` | `safe-boundary-projection-unavailable` until CST-03 | Preserve gate and attempt evidence, arm barrier, then apply |
| `waiting` | `safe-boundary-projection-unavailable` until CST-03 | Preserve wait/stop evidence, arm barrier, then apply |
| `pr-open`, `verified`, or delivery in progress | Gate unless exact effect has settled and provider state is read back | Preserve provider/evidence truth; never close or unwind it |
| `integrated` or disposition `completed` | Reject | Reject |

The repository intent does not itself claim final disposition. Once an authorized request
reaches a proved safe boundary, however, every runner mutation boundary must consult it and
forbid new implementation, provider, or delivery effects until the transaction reaches a
terminal result or an authorized reversal is recorded. Worktrees, checkpoints, PRs, and
evidence are retained.

## Tracked-source transaction

All phases are durable, append-only, and exact-replayable:

1. **validated-request** — normalize identities and authority; read exact source and target
   branch; reject contradiction before effects.
2. **safe-boundary** — acquire repository/optional run locks, settle any in-flight atomic
   effect, append stop intent when required, and arm the mutation barrier.
3. **lifecycle-intent** — persist the repository transaction before moving a source.
4. **source-applied** — invoke `transition_ticket_source` in a clean detached admin
   worktree at the observed target SHA; read back the exact receipt and source bytes.
5. **candidate-frozen** — repoint inbound documentation links deterministically; require a
   clean admin index before the operation and an exact changed-path set afterward. Bind
   statuses, modes, old/new blobs, file bytes, parent tree, and candidate tree—not paths
   alone. Reject submodules, symlinks, conflict stages, or unrelated files.
6. **commit-intent / committed** — persist intended tree and parent, create one
   runner-authored administrative commit, then read back exact parent/tree/diff. Unknown
   commit outcome reconciles locally before retry.
7. **provider-intent / pr-read-back** — persist branch/head/base intent before push or PR
   dispatch. After an armed dispatch, never redispatch until exact provider readback proves
   absence or returns the matching object. Push and PR head/base are exact-SHA bound.
8. **merge-gated / merge-read-back** — consume only a separate repository merge grant
   bound to canonical repository identity and exact PR head. Provider mutation uses expected
   head and fresh checks/policies. External merge observation grants no merge authority.
9. **provider-merged** — record sanitized exact PR/head/base/merge observation. This is not
   integration.
10. **terminal-proved** — fetch the terminal branch without moving unrelated refs; prove
    the exact delivered head reachable from fresh terminal SHA and persist the proof.
11. **projected** — read the ticket at its exact terminal disposition path and digest;
    append the repository terminal receipt; then append optional usable-run disposition
    projection from terminal truth, not from the run's stale worktree.
12. **complete** — report `changed-integrated`. Cleanup remains separately authorized.

If target advances before commit preparation, rebuild the administrative candidate from the
fresh target and revalidate authority/source identity. Once provider intent exists, target
or head drift requires exact reconciliation; it is never silently rebased.

## Ignored-source transaction

Ignored mode uses the same request, ownership, lock, intent, transition receipt, and source
readback contracts. It then records repository transaction outcome
`external-unpublished` and optional usable-run disposition projection.

It must not create a Git candidate, stage the ignored path, publish a ticket, push a branch,
open/close a provider object, invoke merge or terminal proof, move the source into tracked
storage, project tracked completion, sync a wiki, or sync Pi. A contradictory ignored/tracked
classification gates before source mutation.

## Reopen

Reopen is request → exact human gate approval → apply. The gate binds ticket identity,
prior disposition, target `open`, user actor, reason, and durable evidence. The transaction
consumes it once after source and terminal truth agree.

A successful projection creates pending work, invalidates candidate-through-merge current
authority, preserves prior evidence as history, and requires managed snapshot and dependency
revalidation. It never resumes an old attempt or reuses old quality/provider authority.
`completed` cannot reopen.

## Crash and ambiguity policy

| Last durable fact | Replay action |
| --- | --- |
| Request validated; no intent | Known non-mutation; recompute and persist intent |
| Lifecycle intent; source still original | Invoke exact source transition |
| Source destination exists; receipt says intent | Reconcile through existing source primitive and read back applied receipt |
| Candidate frozen; no commit intent | Persist commit intent |
| Commit intent with unknown outcome | Read exact local object/tree/parent; do not create a second commit until absence is proved |
| Provider intent; dispatch not armed | Dispatch once |
| Provider/merge dispatch armed; no readback | Read-only reconciliation only; no redispatch |
| Provider says `MERGED`; no terminal proof | Fetch/read terminal branch and remain gated until exact reachability |
| Terminal proof; no projection | Read terminal source and append projection exactly once |
| Complete | Return the identical terminal receipt without effects |

Contradictory journals, receipts, provider identities, terminal proofs, source locations, or
projections stop with an exact diagnostic. A timeout never proves non-mutation.

## Authority boundaries

The lane receives only ticket-scoped disposition authority. It grants none of:

- implementation of the target ticket;
- dependency edits or cancellation cascade;
- run pause/unpause;
- provider publication beyond the exact tracked administrative PR;
- merge without separate exact-head repository authority;
- issue close/reopen;
- wiki or Obsidian/RAG ingestion;
- tracked completion projection;
- Pi synchronization, Pi update, or active-session reload;
- worktree, branch, checkpoint, evidence, or PR cleanup.

Post-integration local Pi synchronization remains separately configured and may run only for
the exact integrated agent-skills head under its own actor/evidence binding. It never implies
`/reload` occurred.

## Compatibility

Compatibility is opt-in. Existing `ticket-hold`, `ticket-cancel`,
`ticket-reopen-request`, and `ticket-reopen` commands keep their current run-bound contract.
The new repository transaction may call their shared primitives but does not reinterpret old
receipts or auto-adopt unreceipted source moves.

Existing schema-4 ledgers receive only versioned append-only projections. Retired or legacy
ledgers are not rewritten. Existing ignored sources stay ignored. Ticket Envelope v1,
provider-neutral PRs, completion projection, merge grants, wiki, and Pi contracts retain
their current authority boundaries.

## Security and observability

- Disable Git replacement objects for authority-bearing object/tree/diff reads.
- Reject symlinks, path escapes, duplicate ticket locations, conflict stages, and alternate
  object tricks.
- Redact credentials and provider payloads before persistence.
- Bind every request, receipt, candidate, provider observation, terminal proof, and
  projection to canonical repository and exact ticket identity.
- Expose disposition, execution lifecycle, derived readiness, stop reason, transaction
  phase, and gate reason as separate output fields.
- Never accept user prose, provider labels, commit messages, patch IDs, or path-only equality
  as object proof.

## Verification plan

- **Resolver/unit:** vocabulary, actor/reason/authority, repository identity, Artifact ID,
  duplicate IDs, usable/missing/retired/ambiguous ownership, reopen gate, schema rejection.
- **Source integration:** tracked and ignored transitions, deterministic repoints,
  symlink/path escape, content drift, no-clobber, before/after-move crashes.
- **Isolation:** staged and unstaged target dirt, clean admin index, exact raw diff/tree,
  rogue allowed-path content, rogue path, conflict stage, target advance.
- **State matrix:** pending, active before/after atomic boundary, gated, waiting, PR-open,
  completed, no-cascade dependencies, preserved checkpoints/evidence/gates.
- **Provider:** dispatch-intent crash, ambiguous create/update/merge, changed PR head/base,
  checks/policies, external merge, expected-head merge, provider `MERGED` without terminal.
- **Terminal/projection:** fresh terminal branch, exact reachability, stale run worktree,
  missing/retired run, projection crash/replay, reopen invalidation.
- **Routing:** explicit hold/cancel/reopen precedence; blocked/pause/stop/complete and ordinary
  implementation negatives; mandatory policy names only the lifecycle lane.
- **Forward:** disposable bare remotes and simulated providers. Any real ticket disposition
  or live provider fixture requires separate exact human and provider authority.

## Alternatives rejected

- **Wrap the current run-bound lifecycle CLI:** rejected because it requires a usable run,
  stages in that run's worktree, and has no complete tracked delivery transaction.
- **Let the active run own the transaction:** rejected because dirty candidate state can
  leak and missing/retired ownership becomes impossible.
- **Treat source move or provider `MERGED` as terminal:** rejected because tracked canonical
  truth requires exact commit/provider identities and fresh terminal reachability.
- **Use direct default-branch pushes for small docs moves:** rejected because size does not
  grant merge authority or crash-safe readback.
- **Route all docs-only or “status” requests here:** rejected because that would bypass the
  delivery lane and conflate disposition with lifecycle/readiness questions.
- **Delay the source move until after provider merge:** rejected because the existing
  receipt primitive and candidate need one exact source transition; the repository journal
  and admin worktree make that transition recoverable without claiming final disposition.

## Delivery tickets

| ID | Mode | Blocked by | Tracer outcome |
| --- | --- | --- | --- |
| CST-01 | AFK | — | Repository-owned journal, exact resolver/authority, ignored-source terminal slice, pending-only tracked gate |
| CST-02 | AFK | CST-01 | Clean tracked admin candidate through provider readback, separate merge authority, terminal proof, and repository projection |
| CST-03 | AFK | CST-01, CST-02 | Repository mutation barrier and exact active/gated/waiting safe-boundary projections without evidence loss |
| CST-04 | AFK | CST-02, CST-03 | `change-status-ticket` skill, ask-skills precedence, mandatory-policy integration, and end-to-end forward matrix |

None of these tickets authorizes a real ticket status change. Each implementation remains on
Ticket Autopilot's manual merge policy unless an existing exact repository grant is
independently applicable.
