# Ticket Autopilot Operational Debt Recovery

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-operational-debt-recovery`
- Role: spec
- Standalone: true

### Children

- [ODR-01 — Validate start gates only for non-terminal HITL tickets](../tickets/ticket-autopilot-operational-debt-recovery/01-validate-start-gates-only-for-non-terminal-hitl-tickets.md)
- [ODR-02 — Recover or retire the exact legacy run inventory](../tickets/ticket-autopilot-operational-debt-recovery/02-recover-or-retire-the-exact-legacy-run-inventory.md)
- [ODR-03 — Restore the exact AWI-01 completion provenance](../tickets/ticket-autopilot-operational-debt-recovery/03-restore-the-exact-awi-01-completion-provenance.md)

## Type

Architecture and bug-recovery specification.

## Status and authority

Accepted for implementation by Carlo on 2026-08-30 through the request to repair the
separately reported legacy-ledger and AWI catalog debt and then run `WT-04`, `WT-05`, and
`WT-06`. The durable local-application evidence reference is
`decision://2026-08-30/ticket-autopilot-operational-debt-recovery`.

This authority is limited to the exact inventory in this specification. It does not approve
`gate:RD-03:start:1`, `gate:RD-05:start:2`, provider issue publication, arbitrary run
retirement, semantic conflict selection, or any future ledger mutation.

## Observed state

### Terminal HITL validation blocks an AFK-only frontier

Planning the canonical `windows-text-fidelity` folder fails before mutation with:

`HITL ticket requires exactly one persisted start gate`

`WT-04`, `WT-05`, and `WT-06` are open AFK tickets. The unrelated `WT-07` source is
canceled HITL and therefore has no start gate. `Kernel._validate()` currently requires one
start gate from every non-preexisting HITL ticket whenever history exists, regardless of
terminal administrative disposition. The validator therefore contradicts the scheduler rule
that canceled and completed tickets are not schedulable.

### Legacy run inventory

`merge-all` discovers fifteen integrity-enveloped legacy ledgers and fails before mutation.
All file digests below were observed before this specification.

Nine schema-3 ledgers already carry CandidateRef v2 and have an existing explicit
`migrate-run-lifecycle` path:

| Run | Exact ledger SHA-256 | Current run state |
| --- | --- | --- |
| `635f9e80c8e64fbe` | `4accb1e13264f3ec79043114679633bda4f952a5fec056c24573b0d79fd03863` | aborted |
| `8287211ddf2d4172` | `011ecadd027fa4b8ef6be782d55160c4490afa995a05c7d61d8a702357a2774c` | running |
| `9f1a49b6584d429d` | `7cf18b1d3c317f2a1701c19fc186c655de9dc1380d635eb54b1eed8cc1a4ba92` | waiting |
| `a8e4e5119f6a4b4f` | `719acbde6efc069aa04f7aead4ac7e3a9135a9222e4dc3e4061877914912654a` | aborted |
| `cb11025adc814e3c` | `2492d57bc8daf3ee18fc199dfc511aa7fcd6e194c6b8989d7364792f9ccea715` | completed |
| `issues21-23-autonomous-stack-v3-20260805` | `923056f5138481cc5ad13621d182fc2221bdfb462fadae683029fd7addb43e32` | failed |
| `issues21-23-autonomous-stack-v5-20260806` | `0909df0e18f94b713e27ee6e6aa343c8fc1314c7d1827fb62fcc5e8f05a15966` | failed |
| `issues21-23-autonomous-stack-v6-20260806` | `0ba950f7bdf47abf22aa0d6b287fc66d8f0df9e1edff63b14dee6c15ec8209b0` | failed |
| `issues21-23-autonomous-stack-v7-20260806` | `f70962220f923f6f4c8a0ae779770fb1f8fc6ab4fa931daec7ac74b27fa8e336` | completed |

Six schema-1/2 ledgers contain CandidateRef v1 or incomplete pre-CandidateRef state. Their
semantic trees and modern lifecycle facts must not be fabricated:

| Run | Schema | Exact ledger SHA-256 | Recovery disposition |
| --- | ---: | --- | --- |
| `issue16-17-delivery-merge-20260801` | 2 | `50e7a0bbc602a5a9ff3fe76fce018c90b02d998b9980afb65c75829ea64df51c` | retire terminal history; all three recorded tickets are integrated |
| `issue9-bounded-leaves-20260728` | 1 | `3c2fc3d695d1e9086dfbaeb283689780461846aeea1ca805ceeec6918c375d24` | retire superseded attempt; canonical ticket sources remain authoritative |
| `issue9-bounded-leaves-quality-epoch-02` | 1 | `70f51d594ed8e8887c7f3d81f85078121cf71ede6dc9e23724210adb9d4a25d9` | retire superseded attempt; canonical ticket sources remain authoritative |
| `issue9-bounded-leaves-quality-epoch-03` | 1 | `9999e7f3ade2ca4d6fe9fe6229880d40b381b48ccf3bdfed8c0fece519c4f65d` | retire superseded attempt; canonical ticket sources remain authoritative |
| `issues21-23-autonomous-stack-20260805` | 2 | `c8c38eb88de0737ca5983164d5c4b5dbb78193fd234b8d762c6deb1eb51d8a1a` | retire superseded by the later stack lineage |
| `issues21-23-autonomous-stack-v2-20260805` | 2 | `20a53a71059fcd8e3bab64e96d44f773cab5d393d0fb061735a8a98c756486d0` | retire superseded by the later stack lineage |

### AWI dependency target is present only as ignored completed provenance

The tracked `AWI-02` completion source declares `blocked_by: ["AWI-01"]`, but terminal
`main` does not track the `AWI-01` completion source. The exact ignored completion mirror
exists in both the stable checkout and the completed AWI worktree with:

- SHA-256: `10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2`
- Git blob: `0c20e73c897cdd8474bc83ccd2e1d32539038ced`
- destination: `docs/tickets/llm-wiki-agent-skills-ingest/done/01-keep-session-digests-in-the-wiki-catalog.md`

The missing target is a provenance projection defect, not permission to erase or rewrite
`AWI-02`'s historical dependency.

## Goals

1. Let terminal canceled/completed HITL sources coexist with open AFK work without requiring
   a live start gate or weakening validation for schedulable HITL tickets.
2. Recover the nine exact schema-3 ledgers to schema 4 through an authority-bound,
   crash-replay-safe path that preserves history and reports exact before/after identities.
3. Retire the six exact schema-1/2 ledgers without rewriting their bytes or inventing
   CandidateRef v2 facts, and make aggregate discovery skip only an exact active retirement.
4. Restore the exact tracked `AWI-01` completion mirror so dependency and Artifact Graph scans
   resolve both AWI tickets.
5. Re-run the canonical Windows folder and reach `WT-04`, `WT-05`, then `WT-06` without
   copying, editing, or bypassing its tickets.

## Non-goals

- Resuming schema-1/2 execution, upgrading CandidateRef v1, or declaring their unfinished
  tickets complete.
- Automatically merging or reconciling provider objects exposed by a recovered schema-3 run.
- Compacting history unless explicitly requested and separately reported.
- Approving either runner-defect publication gate.
- Reopening `WT-07`, introducing CI, or claiming a live Windows result from macOS.
- Rewriting AWI ticket metadata or regenerating the completed mirror.

## Decisions

### Terminal disposition controls start-gate necessity

For a non-preexisting HITL ticket in a ledger with history:

- `open` and `on-hold` require exactly one well-formed persisted start gate, because they can
  become schedulable without changing historical identity;
- `canceled` and `completed` require no start gate;
- if a terminal ticket retains one historical start gate, its structure must still validate;
- more than one start gate always fails closed;
- AFK tickets continue to reject every start gate.

This change affects validation only. It cannot make terminal work ready, remove gates, reopen
sources, or infer approval.

### Schema-3 migration and schema-1/2 retirement are different operations

A schema-3 ledger may be rewritten only when its envelope integrity and exact file SHA match
the approved inventory. Migration preserves the prior payload/history head and appends one
new audited schema-4 event carrying actor, evidence, original file SHA, and original
integrity. Exact replay returns the existing receipt; drift or contradiction fails before
mutation.

A schema-1/2 ledger is never rewritten. Retirement creates an integrity-wrapped append-only
sidecar under Git-common run state, binding repository identity, run ID, exact ledger SHA,
schema, actor, evidence, reason, and optional successor reference. Only the newest
non-revoked exact receipt is active. `merge-all` may classify that run as
`retired-legacy`/skipped before loading the incompatible ledger. A missing, stale, malformed,
contradictory, or revoked receipt retains the current fail-closed result.

Retirement means only “do not treat this historical run as current schedulable state.” It
never completes tickets, changes provider state, removes worktrees, or transfers authority.

### Application uses an exact manifest

A provider-free preparation command emits the fifteen-run action manifest outside the
repository. The applying command requires its exact SHA-256 plus actor and evidence, persists
one immutable intent before the first ledger/sidecar mutation, serializes against run and
repository locks, rechecks every ledger digest immediately before its action, and records a
per-run receipt. Crash replay resumes remaining entries without duplicating events or
retirements. No action is inferred for an unlisted run.

The application manifest must use exactly the actions and input digests listed above. A
new digest requires a new human decision; it cannot be silently refreshed.

### AWI repair preserves exact historical bytes

Track the existing `AWI-01` Markdown blob exactly at its completed destination. Do not edit
its envelope/body, create a replacement ticket, or remove `AWI-02`'s dependency. Prove the
blob, SHA-256, normalized Ticket Envelope, AWI run snapshot identity, and terminal catalog
readback. No wiki content regeneration is part of this repair.

## Semantic invariants

- Administrative disposition, execution lifecycle, readiness, and gate state remain
  separate.
- Open/on-hold HITL work cannot become schedulable without its exact human gate.
- Legacy input bytes, envelope integrity, history hashes, CandidateRefs, provider receipts,
  and source snapshots are never fabricated or silently retargeted.
- Every recovery/retirement authority is repository-, run-, digest-, actor-, and
  evidence-bound and is persisted before mutation.
- A retired ledger stays available for audit at its original path.
- Aggregate operations may skip an exactly retired run but cannot use retirement as merge,
  cleanup, source, provider, reconciliation, wiki, Pi, or completion authority.
- The AWI fix adds one exact missing provenance node and makes no semantic content choice.
- Failure at any boundary preserves truthful partial receipts and never reports all debt
  cleared.

## Failure modes

- Ledger digest changes after preparation: fail before that run's mutation and retain the
  manifest/partial receipts.
- Schema-3 migration produces an invalid schema-4 kernel projection: roll back that file
  atomically and record failure; do not retire it as a fallback.
- Retirement sidecar conflicts with another actor/evidence/reason or ledger digest: fail
  closed.
- Crash after a schema-3 write but before batch progress: identify the exact embedded
  migration receipt and continue without a second event.
- Terminal HITL ticket carries malformed or duplicate historical gates: reject the ledger.
- AWI source bytes differ from either frozen digest: gate instead of choosing content.
- Windows execution is unavailable: complete only macOS/simulated branch evidence and retain
  the exact Windows environment gate for `WT-06`.

## Implementation slices

1. **ODR-01 — terminal HITL start-gate validation:** correct kernel validation and add
   planner/real-ledger regression coverage sufficient to unblock the Windows folder.
2. **ODR-02 — exact legacy run recovery:** add exact manifest preparation/application,
   authority-bound schema-3 migration receipts, schema-1/2 retirement sidecars, aggregate
   skip behavior, crash replay, and tamper tests.
3. **ODR-03 — AWI completion provenance:** add only the exact `AWI-01` completed mirror and
   prove a diagnostic-free ticket/dependency graph.
4. **Post-integration application:** apply the exact fifteen-run manifest under the authority
   above, read all nine schema-4 migration receipts and six retirement receipts, then run
   read-only `status`, `ticket-list`, and `merge-all` classification checks.
5. **Windows continuation:** start the canonical `windows-text-fidelity` folder and execute
   `WT-04`, `WT-05`, and `WT-06` through their existing contracts.

## Verification strategy

- **Unit:** disposition/start-gate matrix; malformed/duplicate gates; retirement receipt
  normalization, scope, revocation, and contradiction; manifest digest and action validation.
- **Integration:** plan the real Windows ticket folder; migrate copied schema-3 ledgers;
  retire copied schema-1/2 ledgers; aggregate discovery over mixed active/migrated/retired
  runs; exact AWI ticket-list scan.
- **Crash/replay:** interruption before and after each ledger or sidecar write, exact replay,
  stale manifest, changed ledger, partial batch, and lock contention.
- **Regression:** full Ticket Autopilot suite, extension tests, forward scenarios, context
  baseline, Artifact Graph audit, and static candidate checks.
- **Live local application:** only after integration, apply the exact manifest to Git-common
  state and retain machine receipts. This is local operational evidence, not repository
  candidate evidence.
- **Windows:** the existing `WT-06` contract owns a real Windows full-suite result. Until
  observed, no green-Windows claim is allowed.

## Acceptance outcomes

- Planning the unchanged canonical Windows folder succeeds and exposes exactly `WT-04`,
  `WT-05`, and `WT-06` as open AFK work while `WT-07` stays canceled.
- All nine listed schema-3 ledgers either carry one valid exact schema-4 migration receipt or
  remain visibly failed with no success claim.
- All six listed schema-1/2 ledger files remain byte-identical and carry one exact active
  retirement receipt; aggregate discovery reports them skipped, not failed.
- A second exact recovery application performs no duplicate ledger or sidecar mutation.
- `ticket-list docs/tickets` reports no `AWI-02 → AWI-01` missing dependency and the tracked
  AWI-01 blob remains `0c20e73c897cdd8474bc83ccd2e1d32539038ced`.
- No unrelated run, provider object, ticket source, wiki, Pi installation, worktree, or gate is
  mutated.
- The final report separates repository integration, local ledger application, Windows
  execution, and the still-human `RD-03`/`RD-05` decisions.
