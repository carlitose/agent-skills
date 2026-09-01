# Ticket Autopilot Runner Defect Remediation

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-runner-defect-remediation`
- Role: `spec`
- Standalone: true

### Children

- [RDR-01 Reset stale delivery preparation after candidate invalidation](../tickets/ticket-autopilot-runner-defect-remediation/done/01-reset-stale-delivery-preparation.md)
- [RDR-02 Prioritize explicit reconciliation over pending merge](../tickets/ticket-autopilot-runner-defect-remediation/02-prioritize-explicit-reconciliation.md)
- [RDR-03 Consume all resolved reconciliation gates](../tickets/ticket-autopilot-runner-defect-remediation/03-consume-reconciliation-gates.md)
- [RDR-04 Make PR-body persistence byte-stable across platforms](../tickets/ticket-autopilot-runner-defect-remediation/04-canonicalize-pr-body-bytes.md)
- [RDR-05 Unify autonomous readiness for precompleted dependencies](../tickets/ticket-autopilot-runner-defect-remediation/05-unify-precompleted-autonomous-readiness.md)

## Type

Bug-analysis and correction specification

## Status

Ready for implementation

## Scope and Evidence Baseline

This specification deduplicates the five open runner defects reported in GitHub issues
[#200](https://github.com/carlitose/agent-skills/issues/200),
[#201](https://github.com/carlitose/agent-skills/issues/201),
[#202](https://github.com/carlitose/agent-skills/issues/202),
[#203](https://github.com/carlitose/agent-skills/issues/203), and
[#205](https://github.com/carlitose/agent-skills/issues/205) against the canonical repository at
`origin/main` commit `21805f72c5024f9b320687e67dd670dc0b24c51f`.

The five issues describe five distinct violated invariants. Issues #200 through #202 share the
reconciliation orchestration boundary but require separate state, scheduling, and gate fixes.
Issue #203 is a platform text-fidelity defect. Issue #205 is a kernel/ledger replay drift that
existing PCR-01 and TIP-01 specs explicitly named as out of scope but never assigned to an
executable correction ticket.

The issue bodies state that patches exist in another candidate. Those statements are diagnostic
leads, not repository evidence: none of the named fixes exists on the pinned `origin/main`.
Each ticket must establish its own failing regression against the repository baseline before
implementation and must merge its verified correction to `origin/main`.

## Deduplication Matrix

| Issue | Current `origin/main` mechanism | Existing canonical owner | Deduplication result |
| --- | --- | --- | --- |
| #200 | Candidate revalidation/invalidation can leave `delivery.prepared` bound to an older CandidateRef; `DeliveryFinalizer.prepare()` discovers the contradiction only after branch/finalization work | Candidate invalidation, tracked completion, and reconciliation specs preserve exact identity but do not clear this stale pre-provider preparation | New slice RDR-01 |
| #201 | `_resume()` drives `_drive_pending_merge()` before processing the caller's explicit event file | Existing reconciliation tickets define audited head replacement but not resume-event priority | New slice RDR-02 |
| #202 | `_merge_gate_ids()` selects only `provider-merge`; successful reconciliation can advance while an open `stack-reconciliation` or recovery gate survives | Reconciliation proposal recovery consumes gates in its own path, but ordinary successful reconciliation has no shared closure contract | New slice RDR-03 |
| #203 | `_atomic_text()` uses text-mode persistence and `_load_rendered_body()` hashes the normalized readback of a string hashed before persistence | Windows text-fidelity tickets cover command output and lock/platform baselines, not content-addressed PR-body persistence | New slice RDR-04 |
| #205 | `Kernel.autonomous_merge_dependencies_ready()` accepts an exact precompleted parent without lineage, while `AtomicLedger._derived_run_state()` rejects it | PCR-01 and TIP-01 explicitly exclude the defect; no child ticket owns it | New slice RDR-05 |

The malformed literal `\\n` and control characters currently visible in the bodies of #200
through #203 are not attributed to `runner_defect_issues.render_issue`: those issues do not use
its title, marker, or body contract, while the production renderer constructs real LF strings.
That external intake anomaly is therefore not folded into RDR-04 or treated as a proven sixth
runner defect.

## Goals

- Make every semantic CandidateRef invalidation remove or archive incompatible pre-provider
  delivery preparation before it can be reused.
- Give a caller-supplied explicit reconciliation event precedence over automatic pending-merge
  work in the same resume transaction.
- Consume every open gate that represents the reconciliation condition actually resolved by a
  successful reconciliation, without approving unrelated gates.
- Bind PR-body validation, hashing, persistence, replay, and provider publication to one exact
  UTF-8 LF representation on every supported platform, with bounded recovery for legacy
  Windows-expanded artifacts.
- Use one autonomous dependency-readiness rule for scheduling and ledger replay, including the
  exact precompleted-without-lineage compatibility case.
- Land each correction and its causal regressions on `origin/main`; local or external patches do
  not satisfy the destination.

## Non-goals

- Importing an unaudited external patch or trusting issue-reported test results as local evidence.
- Weakening CandidateRef, ticket digest, delivery lineage, expected-head, provider readback,
  terminal integration, or merge-authority checks.
- Treating every completed parent without lineage as safe; the compatibility case requires
  `state=integrated`, `disposition=completed`, and `candidate_ref=null`.
- Auto-closing, editing, commenting on, or otherwise mutating GitHub issues.
- Fixing application-repository defects, incomplete external ticket-70 artifacts, or an
  unbound report of a naïve stacked rebase without a repository-bound reproduction.
- Combining the five corrections into one large implementation commit.

## Current and Target Behavior

### Stale preparation (#200)

Current behavior retains generic delivery preparation when reconciliation or another exact
transition installs a different semantic candidate. The finalizer then compares stale prepared
identity with the current Git-derived candidate and fails late.

Target behavior detects incompatible preparation at the candidate transition or the first
pre-provider delivery boundary, archives enough identity for audit, clears the complete stale
pre-provider preparation set exactly once, records a deterministic reset event, and prepares the
new candidate from scratch. Any observed provider mutation, contradictory lineage, or ambiguous
artifact remains fail-closed rather than reset.

### Resume ordering (#201)

Current behavior processes repository-authorized reconciliation, then a pending runner merge,
then explicit events. An explicit `reconcile` event can therefore lose to a merge attempt for the
head it was meant to replace.

Target behavior inspects the validated event batch before automatic pending-merge dispatch. If
that batch contains an explicit reconciliation for the pending ticket, reconciliation executes
first; pending merge is re-derived only after event persistence. Other event batches retain
existing ordering and replay semantics. Invalid or unreadable event input cannot suppress a
pending merge silently.

### Gate closure (#202)

Current behavior has separate selectors and consumers for provider-merge and stack reconciliation
gates. A success path can update candidate and PR lineage while leaving a resolved stack gate
open.

Target behavior computes the exact set of open reconciliation-condition gates for the ticket,
consumes that set with explicit scheduler evidence in the same persisted transition that accepts
the Git-derived reconciliation result, and leaves unrelated human, source, provider-environment,
resource, publication, wiki, and Pi gates untouched. Replay observes the same closed set.

### PR-body bytes (#203)

Current behavior hashes the incoming Python string, persists through platform text mode, then
rehashes universal-newline readback. Mixed LF/CRLF input can therefore become a different logical
string on Windows.

Target behavior canonicalizes accepted Markdown to UTF-8 LF before validation and hashing,
persists exact bytes atomically, reads exact bytes, and uses the same canonical representation for
provider mutation and readback validation. Legacy artifacts are accepted only when a deterministic
bounded compatibility transform proves the recorded hash and normalized body; contradictions
remain `delivery-pr-body` gates.

### Precompleted readiness (#205)

Current behavior has two implementations of the same autonomous dependency predicate. The kernel
accepts a precompleted parent without CandidateRef/lineage, but ledger replay requires lineage on
both parent and child, causing `merge-authorized` validation to derive incompatible run states.

Target behavior moves the predicate to one pure shared owner used by both kernel scheduling and
ledger replay. It accepts the exact precompleted compatibility shape and rejects every other
missing, malformed, mismatched, or non-integrated lineage shape.

## Semantic Invariants

1. Semantic candidate identity and delivery lineage remain separate, exact, and replayable.
2. Stale pre-provider state is never reused, but provider-observed state is never erased under a
   generic reset.
3. Caller event priority cannot manufacture reconciliation authority or bypass event validation.
4. Reconciliation closes only gates whose recorded condition the successful result resolves.
5. PR-body content identity is the SHA-256 of exact canonical UTF-8 LF bytes used end to end.
6. Ledger replay and runtime scheduling derive autonomous readiness from the same pure contract.
7. A precompleted no-lineage parent is compatible only when it was already integrated at snapshot,
   has completed disposition, and has no semantic CandidateRef.
8. Every provider mutation remains expected-head-bound and every integration claim retains fresh
   terminal reachability.
9. Issue publication, merge, reconciliation, wiki, Pi, and administrative authorities remain
   independent.

## Failure Modes

| Failure | Required outcome |
| --- | --- |
| Stale preparation after candidate change, before provider mutation | Archive/reset once and prepare the current candidate |
| Preparation conflicts with observed provider or reconciliation lineage | Fail closed; do not erase evidence |
| Explicit event file malformed or stale | Reject normally; do not use it to suppress pending merge |
| Explicit reconciliation resolves to revalidation-required | Persist that result, then re-derive merge readiness; do not attempt the old merge |
| Unrelated open gate on reconciled ticket | Preserve it unchanged |
| Mixed LF/CRLF rendered body | Canonicalize before validator/hash/persistence |
| Non-UTF-8 or contradictory legacy body artifact | Open/retain the existing PR-body gate |
| Precompleted parent has CandidateRef, open disposition, non-integrated state, or malformed lineage | Autonomous child remains not ready |
| Kernel/ledger predicate result differs in any fixture | Regression failure before release |

## Compatibility and Migration

No Ticket Envelope, CandidateRef, delivery-lineage, or provider schema migration is intended.
RDR-01 and RDR-03 may add append-only internal events or history records. RDR-04 must read the
existing schema-1/schema-2 PR-body records and support only the exact legacy Windows expansion it
can prove; it must not accept arbitrary newline or byte drift. RDR-05 preserves the already
intentional precompleted-parent compatibility branch while removing duplicated interpretation.

## Implementation Slices

1. RDR-01 owns stale pre-provider delivery preparation invalidation and replay.
2. RDR-02 owns resume scheduler priority for explicit reconciliation events.
3. RDR-03 owns reconciliation-condition gate selection and atomic consumption.
4. RDR-04 owns canonical PR-body text/byte persistence and legacy Windows recovery.
5. RDR-05 owns the shared autonomous dependency-readiness predicate and replay equivalence.

The slices are independently verifiable and have no semantic dependency on one another. The
scheduler may execute them serially, but integration order does not redefine ownership.

## Verification Strategy

### Unit

- Exact stale/current preparation classification, reset set, replay, and provider-state negatives.
- Event-batch priority detection and non-reconcile controls.
- Gate selection for provider merge, stack reconciliation, recovery, and unrelated categories.
- LF/CRLF/CR/mixed Unicode canonicalization, exact byte hashes, and rejected invalid bytes.
- Shared autonomous readiness matrix for no blockers, multi-parent, matching lineage,
  precompleted compatibility, and every rejected near miss.

### Integration

- Candidate invalidation followed by delivery proves no obsolete preparation is reused.
- A pending autonomous merge plus explicit reconciliation proves zero old-head merge mutation
  before the reconciliation result.
- Successful ordinary and proposal-backed reconciliation close the same resolved gate classes and
  preserve unrelated gates.
- Crash-resumable render persistence/reload/provider readback uses exact canonical bytes, including
  a Windows-shaped trailing CRLF input and one bounded legacy artifact.
- A precompleted parent and autonomous child reach pending runner merge and survive full
  `AtomicLedger` save/load/derived-state validation.

### Regression

Run the focused kernel, ledger, CLI, finalizer/provider-body, Windows text-fidelity, reconciliation,
and terminal-boundary tests, then the complete Ticket Autopilot suite and Python compilation.
Each ticket records exact counts at its frozen candidate rather than inheriting issue-body claims.

### Live boundary

Local fake-provider and real-Git fixtures are sufficient for correction evidence. GitHub issue
mutation is not required. PR publication/merge for these repository tickets still follows the
normal provider and terminal-integration contracts.

## Acceptance Outcomes

1. Each issue has one canonical owning ticket and no overlap is represented as completion.
2. Every ticket starts with a failing repository-bound regression and ends with causal coverage of
   the reported mechanism and adjacent negatives.
3. The five fixes remain separate reviewable candidates and preserve all stated invariants.
4. Each exact delivered head is reachable from fresh `origin/main` after integration.
5. The five GitHub issues may remain open until separately authorized issue administration; merge
   evidence does not imply issue closure.
