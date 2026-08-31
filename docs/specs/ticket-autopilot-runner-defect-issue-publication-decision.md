# Ticket Autopilot runner-defect issue-publication decision

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-runner-defect-issue-publication-decision`
- Role: `spec`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](./ticket-autopilot-runner-defect-issue-wayfinder.md)

## Type

Decision spec

## Status

Accepted on 2026-08-31 for ticket `RD-03`.

Authority: the user approved `gate:RD-03:start:1`, completed the one-question-at-a-time
policy interview, and confirmed the complete contract in Pi session
`01a04e2a-0b7a-70fd-be3b-06500686244a`, user message `dc3a6451` at
`2026-08-31T14:26:59.364Z`.

This authority accepts the contract for RD-04 implementation. It does not itself register a
production grant, authorize a live issue search or mutation, resolve `gate:RD-05:start:2`,
or authorize any merge, reconciliation, cleanup, wiki, or local-Pi effect.

## Context

RD-01 established that exception families, gates, and failed commands do not prove a runner
defect. RD-02 then proved, with a disposable fake adapter, that one strictly allowlisted
post-diagnosis record can be fingerprinted, serialized in an orthogonal sidecar, deduplicated,
and replayed across crash boundaries without changing ticket, gate, verification, delivery,
or merge state.

The remaining product decision was whether and under what authority a future AFK run may
cross the external GitHub issue boundary. Existing AFK, merge, reconciliation, gate, provider,
and repository-bootstrap grants intentionally do not answer that question.

## Decision

### Separate repository-scoped grant

Issue publication requires a dedicated, explicitly registered grant with all of these
properties:

- target repository exactly `carlitose/agent-skills`;
- scope `current-and-future-runs` for that repository only;
- exact repository identity, normalized GitHub remote, and Git common directory binding;
- non-empty human actor and durable evidence reference;
- immutable grant identity and canonical digest;
- validity until an explicit, separately persisted revocation;
- no transfer to another repository, provider, fork, worktree identity, issue operation, or
  future authority type.

The grant is reusable across runs because runner defects and their fingerprint history span
run boundaries. It is not reusable across repositories. Registering, observing, or revoking
this grant never grants merge, reconciliation, gate approval, implementation, source,
verification, cleanup, wiki, Pi, bootstrap, or provider-policy authority.

The production authority log belongs under the repository Git common state, separate from
run ledgers. RD-04 may choose final filenames, but the logical owner is repository-scoped and
the persisted grant/revocation lineage must be append-only, integrity-checked, lock-guarded,
and exactly replayable.

### Publication eligibility

A record is publishable only when it satisfies the complete RD-01 allowlist and all of these
minimums:

- classification is exactly `runner-defect`;
- confidence is exactly `high`;
- confidence basis contains both `deterministic-reproduction` and `runner-source-trace`;
- the feedback loop is observed and content-addressed;
- at least one `local-deterministic` evidence item supplies the smallest sanitized causal
  observation;
- the diagnostic redaction contract is marked applied;
- validation rejects unknown fields, raw exception/output text, absolute paths, volatile
  identities, private content, authority data, and secret-bearing material before durable
  capture or provider access.

Project/candidate failures, provider or environment failures, expected gates, unsupported
configurations, user/input errors, low or medium confidence, missing evidence, malformed or
unbound ledgers, and failures before the first validated repository/run binding are
ineligible. They remain local outcomes and perform no issue-provider operation.

A broad CLI exception catch, an exception type, a gate category, a nonzero command result,
or an LLM assertion can never manufacture eligibility.

### Stable fingerprint and exact deduplication

The canonical fingerprint remains the RD-02 SHA-256 projection over stable schema,
classification, owner, failure code, phase, and invariant fields. Volatile context and issue
presentation do not affect identity.

Every provider path searches for the exact hidden fingerprint marker before creation.
An exact match is terminal deduplication whether the issue is open or closed. The runner must
not automatically create a replacement, reopen, comment, label, assign, or otherwise mutate
an existing issue. Any such later action requires a separate human-authorized capability.

The contract permits at most one create dispatch for one fingerprint without a new explicit
human recovery decision. GitHub search is readback evidence, not an idempotency guarantee and
not the only durable store.

### Revocation and in-flight effects

Revocation must become durable under the authority lock before any later issue mutation can
begin. Once active:

- no new reservation, create dispatch, comment, reopen, or other issue mutation may start;
- a reservation that has not dispatched becomes terminally revoked;
- already published or deduplicated receipts remain historical facts;
- a potentially dispatched request may perform exact-marker **read-only** search solely to
  discover and record an effect that may already have happened;
- revocation can never reinterpret an ambiguous dispatch as absent or authorize a second
  create.

Read-only reconciliation after revocation is evidence recovery, not publication authority.
Replaying an old grant after its revocation cannot reactivate it; only a new explicit grant
may create a later active authority entry.

### Retry and ambiguity policy

Automatic retry is allowed only while the grant remains active and the persisted state proves
that no create dispatch occurred. Examples include a failed pre-dispatch capability check,
exact-marker search, or other conclusively pre-mutation provider failure. Each retry starts
from fresh provider capability, credential, repository, grant, and exact-marker readback.

After create dispatch begins, a lost response, timeout, crash, contradictory response, or
inconclusive observation becomes `dispatch-ambiguous`. The runner may search the exact marker
in read-only mode:

- a found exact match records the observed issue and ends mutation;
- an absent or inconclusive result never triggers an automatic second create;
- unresolved ambiguity stops at a human recovery gate.

Permission or environment failures never alter the underlying run state. A conclusively
pre-dispatch transient failure may remain retryable; a malformed, contradictory, wrong-target,
or unsafe provider result is terminal until a new diagnosed candidate or explicit recovery
path exists.

### Repository-scoped outbox and retention

The issue-escalation store is orthogonal Git-common state keyed by fingerprint. It owns the
reservation, dispatch intent, provider observations, publication or deduplication receipt,
retryable or terminal failure, ambiguity, and revocation readback. It must not be embedded in
or mutate tickets, gates, effects, verification, delivery, PR, merge, or ledger history.

Receipts and fingerprint identities have no automatic expiry. They remain available across
runs to preserve audit and deduplication. Deletion or garbage collection requires a separate
explicit administrative design and authority; RD-04 must not add automatic cleanup.

Missing, malformed, corrupt, contradictory, path-unsafe, unlocked, or repository-mismatched
state fails closed before provider mutation. Corruption is not repaired by discarding the
sidecar or recreating the issue.

### Fixed secret-safe issue presentation

The first production slice uses one deterministic issue template and only the existing GitHub
label `bug`. It does not create or infer labels.

The title and body may contain only bounded sanitized values derived from the accepted record:

- runner component/module and stable failure code;
- violated invariant and sanitized observable symptom;
- high-confidence basis;
- feedback-loop kind and repository-relative anchor;
- minimized evidence summaries and content digests;
- the exact hidden fingerprint marker.

They must not contain raw logs, stack traces, exception messages, commands, stdout/stderr,
diffs, transcripts, ledgers, environment dumps, provider payloads, absolute paths, user or
host identities, run/branch/worktree IDs, actor or authority evidence, credentials, private
content, or arbitrary Markdown passthrough. Evidence digests may be visible; the underlying
artifacts remain local and are never uploaded by this capability.

### External contract and live proof

RD-04 may implement a dedicated GitHub issue adapter with only the capabilities needed for
exact-fingerprint search and issue creation. These capabilities remain separate from the PR
provider operation set and must be explicitly negotiated before use.

RD-04 uses fake or injected provider evidence for causal tests. It cannot claim live GitHub
behavior. `gate:RD-05:start:2` remains the separate authority to begin the controlled live
forward test, and that start approval still does not by itself supply the production
issue-publication grant or authorize an arbitrary issue.

## Semantic invariants

- No publishable record exists without affirmative high-confidence runner ownership proof.
- No existing authority type silently becomes issue-publication authority.
- No provider mutation begins without a fresh exact active grant and validated repository
  binding.
- One fingerprint has at most one automatic create dispatch.
- Open and closed exact matches are terminal no-op deduplication receipts.
- Revocation precedes and blocks every later mutation while preserving read-only recovery.
- Ambiguous dispatch never becomes automatic permission to create again.
- Issue escalation never changes the originating run’s ticket, gate, quality, delivery, or
  merge outcome.
- Durable receipts are retained until a future separately authorized cleanup contract.
- Live publication remains unproven and unauthorized until RD-05’s distinct gates are
  satisfied.

## Failure scenarios

| Scenario | Required result |
| --- | --- |
| Existing merge or AFK grant, no issue grant | Reject before issue-provider access |
| High-confidence deterministic runner defect and active exact grant | Reserve, search exact marker, and create at most once if conclusively absent |
| Medium confidence or missing source trace | Ineligible local result; no provider operation |
| Existing open issue | Deduplication receipt; no mutation |
| Existing closed issue | Deduplication receipt; no mutation |
| Temporary failure before create dispatch | Persist retryable state; retry only under fresh active-grant/provider readback |
| Lost response after dispatch | Persist ambiguity; exact read-only search; no automatic second create |
| Grant revoked before dispatch | Persist revoked outcome; no provider mutation |
| Grant revoked after possible dispatch | Read-only exact-marker reconciliation only |
| Missing, corrupt, or unbound state | Fail closed; do not recreate state by publishing |
| Wrong repository, label, fingerprint, or provider receipt | Terminal contradiction; no retry mutation |
| Failure before validated run/repository binding | Local diagnostic only; no publication |

## Consequences and trade-offs

- A repository-scoped grant enables genuinely AFK escalation across future runs but has a
  larger lifetime than a per-run grant. Exact target binding, append-only revocation, strict
  eligibility, and at-most-one dispatch constrain that authority.
- Closed issues intentionally suppress automatic follow-up. This may hide a recurrence from
  GitHub activity, but it prevents policy-free issue churn; local receipts retain the event.
- Indefinite receipt retention consumes small Git-common storage. The audit and deduplication
  value outweigh automatic cleanup, whose authority and safety are not yet designed.
- Ambiguous provider outcomes may require human recovery even when a later empty search seems
  plausible. Avoiding duplicate external writes takes precedence over liveness.
- Using only the existing `bug` label avoids a label-management capability in the first
  slice. A specialized label may be added only through a later explicit contract.

## Rejected alternatives

- **Per-run authority:** too narrow for repository-wide fingerprints and future AFK runs.
- **Cross-repository reusable authority:** unnecessarily broad and incompatible with the
  fixed destination.
- **Automatic expiry:** rejected in favor of explicit append-only revocation and stable AFK
  behavior.
- **Medium-confidence publication:** rejected because external issue text must state only a
  proven runner defect.
- **Automatic reopen, comment, or follow-up for closed matches:** rejected as an independent
  external mutation requiring separate human policy.
- **Blind retry after timeout or lost response:** rejected because GitHub issue creation has
  no proven idempotency precondition.
- **Automatic outbox cleanup:** rejected because deleting fingerprint history can recreate
  duplicates and erase audit evidence.
- **Raw diagnostic attachments or free-form issue bodies:** rejected at the secret-redaction
  boundary.
- **Reuse PR-provider or merge authority:** rejected because capability and authority
  boundaries must remain explicit.

## Implementation boundary for RD-04

RD-04 owns the smallest production vertical slice that implements this decision without
performing a live issue mutation. It must include:

1. strict record validation and fingerprint rendering;
2. repository-bound append-only grant and revocation storage;
3. orthogonal content-addressed outbox with per-fingerprint locking and crash replay;
4. a dedicated exact-search/create adapter seam and fake/injected causal tests;
5. fixed secret-safe `bug` issue rendering;
6. provider-free status/readback that distinguishes ineligible, reserved, retryable,
   ambiguous, deduplicated, published, revoked, and terminal outcomes;
7. explicit rejection of every substitute authority and protected run-state mutation.

No compatibility shim or migration is required because no production issue-escalation state
exists yet. Stored contracts must be explicitly versioned; incompatible or corrupt future
state fails closed rather than being guessed.

## Verification plan

RD-04 must prove locally, without GitHub mutation:

- strict allowlist and redaction rejection before durable or provider work;
- grant repository binding, replay, conflict, revocation ordering, and non-reactivation;
- stable/sensitive fingerprint projections and exact marker rendering;
- open and closed deduplication, concurrency, every pre/post-dispatch crash boundary,
  bounded retry, ambiguous recovery, and zero blind second create;
- indefinite receipt readback and fail-closed corrupt/missing/contradictory state;
- byte-identical protected run projections across success and failure;
- fixed title/body/label output and forbidden-content checks;
- zero dependence on existing merge, reconciliation, gate, provider, or AFK grants.

RD-05 separately owns live exact-marker search/create/readback evidence. No RD-04 test or
simulated receipt may be presented as live provider proof.

## Unresolved questions

None for RD-04’s production contract. Live credential capability, the exact controlled issue
candidate, and any post-test cleanup recommendation remain RD-05 concerns behind its own
human gate.
