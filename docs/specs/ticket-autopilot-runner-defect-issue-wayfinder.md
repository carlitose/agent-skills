# Ticket Autopilot Runner-Defect Issue Escalation

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-runner-defect-issue-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [RD-01 Map runner-defect evidence and escalation seams](../tickets/ticket-autopilot-runner-defect-issues/done/01-map-runner-defect-escalation-seams.md)
- [RD-02 Prototype fingerprinted issue escalation](../tickets/ticket-autopilot-runner-defect-issues/done/02-prototype-fingerprinted-issue-escalation.md)
- [RD-03 Freeze issue-publication authority](../tickets/ticket-autopilot-runner-defect-issues/done/03-freeze-issue-publication-authority.md)
- [RD-04 Implement audited runner-defect issue escalation](../tickets/ticket-autopilot-runner-defect-issues/done/04-implement-audited-runner-defect-issue-escalation.md)
- [RD-05 Forward-test live GitHub issue idempotency](../tickets/ticket-autopilot-runner-defect-issues/05-forward-test-live-github-issue-idempotency.md)
- [Runner-defect issue-publication decision](./ticket-autopilot-runner-defect-issue-publication-decision.md)

## Type

Wayfinding spec

## Status

Active

## Destination

When `ticket-autopilot` or one of its owned scripts proves a defect in the runner itself,
an explicitly authorized AFK run can create at most one secret-safe, evidence-backed issue
in `carlitose/agent-skills`. Replays and equivalent failures reuse the same fingerprint and
never create duplicates. The issue receipt is durable and auditable, and issue escalation
never substitutes for a gate, repairs a ledger, authorizes a merge, or upgrades uncertain
diagnosis into fact.

## Decisions So Far

- The target repository is fixed to `carlitose/agent-skills`; this is not a generic
  issue-tracker abstraction in the first slice.
- Only defects attributed to runner-owned code or contracts are eligible. Project test
  failures, candidate regressions, provider outages, permission failures, and ordinary
  human gates remain local run outcomes unless diagnosis proves a runner defect.
- A runner error is not automatically a bug report. Eligibility needs a normalized,
  secret-redacted diagnosis with a reproducible symptom, owning component, confidence,
  and regression-test or feedback-loop evidence.
- The canonical fingerprint must exclude volatile paths, timestamps, run IDs, tokens,
  branch names, and raw stack traces. It must include stable ownership and failure-shape
  facts sufficient for deduplication.
- Before creation, the GitHub adapter must search for the exact fingerprint marker. An
  existing open or closed issue is a deduplication receipt, not permission to create or
  comment again.
- Raw ledgers, transcripts, environment dumps, credentials, private repository content,
  and provider headers never enter an issue body. Evidence crosses the external boundary
  only after the diagnostic secret-redaction contract accepts it.
- Existing merge grants, gate approvals, and AFK execution mode do not imply issue-write
  authority. Publication requires its own explicit, bounded grant.
- **RD-03 accepted the publication contract.** The
  [decision](./ticket-autopilot-runner-defect-issue-publication-decision.md) selects a
  repository-scoped, separately revocable `current-and-future-runs` grant for exactly
  `carlitose/agent-skills`, valid until explicit revocation. Only high-confidence,
  deterministic, source-traced, secret-safe runner defects may publish. Open or closed exact
  matches are no-op deduplication; ambiguous dispatch never retries automatically; receipts
  do not expire; the fixed template uses only the existing `bug` label. Revocation blocks
  every later mutation while permitting read-only recovery of a possibly completed dispatch.
- Failure to publish leaves the original run state unchanged and records a resumable or
  terminal escalation receipt separately. It cannot hide, pass, or replace the underlying
  runner gate.
- **Exception type is not defect classification.** `cli.main` currently catches the runner's
  public exception families and emits only their Python type and message. Gate categories are
  selected locally by operation-specific handlers. Neither surface proves that the runner is
  at fault: a `TransitionError` can be a correct stale-event rejection, while a
  `ProviderError` can still expose a runner parser defect after diagnosis.
- **Escalation starts after diagnosis, not in the broad CLI catch.** Raw exception messages are
  ineligible input. `ProviderExecutor._run` and `_json`, for example, can include a rendered
  command and provider stderr/stdout in an error. Copying that text would bypass the accepted
  diagnostic redaction boundary and could disclose PR content or secret-bearing arguments.
- **The current provider abstraction has no issue capability.** `providers.py` exposes PR
  create/update, readback, retarget, checks, approvals, and expected-head merge. Issue search
  and issue creation must be a separate, explicitly negotiated GitHub boundary rather than a
  hidden extension of `REQUIRED_CAPABILITIES`.
- **The safest state seam is orthogonal to the run ledger.** RD-02 will model one
  content-addressed escalation reservation/outbox per fingerprint under the run's Git-common
  state, guarded by its own per-fingerprint lock and atomic writes. It may read a validated run
  binding, but may not rewrite `tickets`, `gates`, `effects`, verification results, delivery,
  merge authorization, or ledger history. RD-03 still owns whether this candidate seam and its
  exact lifetime become policy.

## Observed Ownership Map

These are current code owners, not proposed issue-escalation owners.

| Concern | Current owner | Observed contract |
| --- | --- | --- |
| Public exception envelope | `autopilot.cli.StructuredArgumentParser`, `_response`, `_emit`, and `main` | Argument failures and the public exception families become schema-1 JSON containing `type` and `str(error)`; `main` does not perform root-cause classification or redaction |
| Exception families | `ContractError`, `ContextBudgetError`, `GitError`, `LifecycleError`, `LedgerError`, `ProviderError`, `TransitionError`, plus checkpoint/docs-only/leaf-specific errors in their owning modules | Types describe the boundary that rejected an operation, not whether the runner contains a defect |
| Ticket inventory diagnostics | `ticket_inventory.inventory_tickets` and `render_ticket_inventory` | Provider-free diagnostics for malformed/duplicate tickets, dependency gaps, cycles, disposition, and readiness; they are user/project input findings, not runner defects by default |
| Workflow invariant enforcement | `kernel.Kernel`, especially `_validate_shape`, `_transaction`, stage methods, and `preflight_mutation_boundary` | A failed transaction restores the in-memory snapshot; transition errors reject impossible or stale state without granting progress |
| Gate creation and approval | `Kernel._open_gate`, `open_gate`, `approve_gate`, and `refresh_gate_reason` | Gates are durable ticket- or run-scoped state with category, reason, actor, evidence, resume state, and append-only events |
| Error-to-gate mapping | Operation handlers in `cli.py`, including `_reconciliation_error_gate`, `_leaf_budget_exhaustion_gate`, the delivery exception handler, and `_drive_runner_merge`; `finalizer.py` and `wiki_sync.py` own their local mappings | Classification is deliberately contextual: the same broad exception family can map to source drift, provider environment, finalization environment, recovery, resource budget, or merge gates |
| Ledger persistence and replay | `ledger.AtomicLedger`; semantic transition validation in `AtomicLedger._validate` and `Kernel` event sealing | A non-blocking run lock serializes decisions; integrity envelope, hash chain, transition validation, compare-before-save, fsync, and atomic replace reject corruption, stale writers, and torn writes |
| Diagnostic evidence safety | `diagnose/SKILL.md` and `diagnose/references/secret-redaction.md` | Redact before display, handoff, or durable capture; retain only the smallest causal non-secret signal; loss of necessary signal becomes an evidence gate |
| Provider capability negotiation | `providers.RemoteProvider.negotiate`, provider capability sets, `detect_provider`, and `cli._provider` | Unsupported operations fail before mutation. GitHub has atomic expected-head merge; Azure deliberately does not advertise it |
| Provider observations and mutation receipts | `providers.ProviderExecutor` | Only the executor can mint live receipts; simulated receipts are marked unobserved, provider readback is shape-checked, and expected-head/intent bindings guard merge operations |
| Last-safe mutation checks | `cli._mutation_boundary` and `_guarded_execute`, `Kernel.preflight_mutation_boundary`, and `DeliveryFinalizer`'s boundary callback | Pause, disposition, canonical ticket source state/digest, source mode, and repository binding are rechecked before Git, delivery, and every provider command |
| Merge replay and crash ambiguity | `_drive_autonomous_merge`, `_complete_runner_merge`, `_drive_runner_merge`, plus GitHub queue readback in `ProviderExecutor` | Intent, attempt, mutation, and readback are separate receipts. An unobservable or contradictory prior mutation gates instead of sending a blind second mutation |
| Pre-ledger setup | `cli._run` before the first `AtomicLedger.save` | Repository discovery, ticket-source inspection, provider negotiation, snapshot persistence, and worktree creation can fail with no durable run ledger; cleanup removes a created worktree, but no run-bound escalation state exists yet |

The ownership map exposes two gaps relevant to this initiative. There is no canonical
runner-defect classifier, and there is no secret-safe structured diagnostic record at the CLI
boundary. The existing `type` plus message envelope must therefore remain operator output, not
become issue input.

## Failure Taxonomy and Counterexamples

Publication eligibility is diagnosis-backed. The classifier must require affirmative evidence
for `runner-defect`; it must not infer ownership from a class name, gate, or nonzero exit.

| Family | Classification test | Counterexample that must not publish |
| --- | --- | --- |
| Runner defect | A deterministic feedback loop plus source trace proves runner-owned code or contract violates its declared invariant on valid inputs | A caller sends a stale CandidateRef and `Kernel` correctly raises `TransitionError` |
| Project/candidate failure | The changed project, its tests, build, lint, or candidate behavior fails while runner transitions remain valid | A candidate test regression recorded by the quality loop |
| Provider/environment failure | Network, credentials, permissions, provider policy/state, local Git, filesystem, tool availability, or malformed external output prevents an operation without proof of a runner defect | GitHub returns 401, checks remain pending, disk is full, or a PR head changes concurrently |
| Expected gate | A declared human, credential, provider, source-drift, recovery, budget, or live-evidence boundary is open and the runner preserves it correctly | `resource-budget`, HITL start approval, or `provider-merge` waiting for passing checks |
| Unsupported configuration | A capability or version is intentionally outside the contract and is rejected before mutation | Azure lacks atomic expected-head completion, or schema 3 requires explicit migration |
| User/input error | Arguments, Ticket Envelope, graph, disposition request, approval, or command payload violate the public contract | Duplicate ticket IDs, a dependency cycle, an incomplete delivery payload, or approval for the wrong head |

A diagnosed parser, mapping, or recovery bug can promote an observation from another row to
`runner-defect`, but only the diagnosis evidence does that. For example, a `ProviderError` caused
by an undocumented provider response remains environmental; the same exception caused by a
fixture proving that the adapter rejects a documented valid response is a runner defect.

## Secret-Safe Defect Record for RD-02

RD-02 consumes exactly one allowlisted document. It does not accept an exception object, stack
trace, raw CLI error, ledger snapshot, provider response, or arbitrary metadata map.

```json
{
  "schema": 1,
  "classification": "runner-defect",
  "owner": {
    "component": "ticket-autopilot",
    "module": "autopilot.kernel",
    "anchor": "Kernel.preflight_mutation_boundary"
  },
  "failure": {
    "code": "stable-kebab-case-code",
    "phase": "pre-provider-mutation",
    "invariant": "One sanitized sentence describing the violated runner invariant.",
    "symptom": "One sanitized sentence describing the observable failure.",
    "exception_family": "TransitionError"
  },
  "confidence": {
    "level": "high",
    "basis": ["deterministic-reproduction", "runner-source-trace"]
  },
  "feedback_loop": {
    "kind": "unit-test",
    "anchor": "ticket-autopilot.tests.test_kernel.Example.test_case",
    "observed": "fails on baseline with the sanitized invariant mismatch",
    "artifact_sha256": "<64 lowercase hex characters>"
  },
  "evidence": [
    {
      "class": "local-deterministic",
      "summary": "Smallest sanitized causal observation.",
      "artifact_sha256": "<64 lowercase hex characters>"
    }
  ],
  "redaction": {
    "contract": "diagnose/references/secret-redaction.md",
    "applied": true
  }
}
```

Required publication input is the full record above. `confidence.level` may be `high`, `medium`,
or `low` in the prototype, but RD-03 selects the minimum publishable level. Evidence classes are
an allowlist fixed by the prototype; `local-deterministic` is the first required class. Anchors
are repository-relative symbols or test IDs, never absolute paths. Summaries are bounded plain
text, not Markdown passthrough.

The proposed fingerprint projection is narrower than the record:

```text
schema + classification + owner.component + owner.module + owner.anchor
+ failure.code + failure.phase + failure.invariant
```

RD-02 canonicalizes that projection as sorted-key UTF-8 JSON and hashes it with SHA-256. The
prototype must prove that changing a timestamp, run ID, branch, worktree, absolute path, actor,
provider request ID, evidence ordering, or explanatory symptom leaves the fingerprint unchanged,
while changing ownership or the violated invariant changes it.

### Fields excluded before durable capture or issue rendering

The diagnostic redaction boundary excludes the value and the containing secret-bearing argument
or header for every credential, token, cookie, authorization header, private key, connection
credential, and secret. It also forbids raw environment dumps and unredacted command/output or
archive metadata. If removing them destroys the causal signal, the record is ineligible and an
evidence-loss gate is required.

This initiative adds stricter minimization for the external issue boundary. The following never
enter the record, fingerprint, issue title, body, labels, or search marker:

- raw stack traces, exception messages, stdout, stderr, commands, diffs, PR bodies, provider
  bodies/headers, raw ledgers, transcripts, or complete captured artifacts;
- environment variable values, environment dumps, credentials, tokens, cookies, authorization
  material, private keys, connection strings, and secret-bearing arguments or URLs;
- private repository content, user-authored candidate content, unrelated source excerpts, or
  verification evidence outside the minimal sanitized causal observation;
- absolute paths, home/user names, run IDs, ticket run directories, worktree paths, branch names,
  timestamps, process IDs, host names, request/trace IDs unless a sanitized trace ID is causal,
  and provider-specific transient IDs;
- merge grants, approval evidence, gate evidence, actor identities, and any authority reference.

Safe module/function/test anchors, stable error codes, status/error codes, and content digests may
remain. A digest proves content identity; it does not authorize publishing the underlying
artifact.

## Escalation Lifecycle and Failure Matrix

RD-02 models a local state machine with `reserved`, `dispatch-ambiguous`, `published`,
`deduplicated`, `retryable-failure`, and `terminal-failure`. The issue provider is fake and the
prototype performs no network call.

| Boundary | Required replay behavior | Existing run state |
| --- | --- | --- |
| Before local reservation | Replay may create the one content-addressed reservation | Unchanged |
| Concurrent equivalent reports | Per-fingerprint lock admits one reservation; all callers observe the same record | Unchanged |
| Reservation saved, before search | Replay resumes search from the reservation | Unchanged |
| Search offline or permission denied | Record a retryable or terminal escalation failure according to the synthetic provider result; never create | Unchanged |
| Existing open issue found by exact marker | Bind a deduplication receipt; do not create or comment | Unchanged |
| Existing closed issue found | Bind a deduplication receipt and stop; RD-03 decides any later closed-issue policy | Unchanged |
| Search result absent, before create dispatch | Persist dispatch intent before the fake mutation | Unchanged |
| Crash during dispatch or before receipt save | Mark ambiguity. Replay searches for the exact marker first; if absence is not conclusive, gate instead of issuing a second create | Unchanged |
| Create receipt saved | Exact replay returns the same receipt byte-for-byte and performs zero provider mutations | Unchanged |
| Provider returns contradictory repository, fingerprint, or issue identity | Terminal fail-closed receipt; no retry mutation | Unchanged |
| Run ledger missing or corrupt | No automatic publication. Emit only a sanitized local diagnostic because the run binding cannot be proven | Unavailable or unchanged |
| Failure occurs before first ledger save | No run-scoped outbox and no publication. The normal CLI error remains the only result | No ledger exists |

GitHub text search is a recovery observation, not the sole local idempotency store. Because issue
creation has no proven expected-head/idempotency precondition, an ambiguous dispatch cannot use
"search returned nothing once" as permission for a second create.

## Safest Integration Seam

The candidate seam for RD-02 is a post-diagnosis escalation coordinator outside `Kernel` and
outside `ProviderExecutor`'s PR operation set:

1. A diagnostic producer constructs and validates the allowlisted record above. Broad CLI
   exception handling never constructs one from `str(error)`.
2. The coordinator validates the repository/run binding read-only, computes the fingerprint,
   and acquires a per-fingerprint lock in a separate escalation store adjacent to the run.
3. It atomically persists a reservation before invoking a dedicated fake issue adapter.
4. The adapter exposes exact-fingerprint search and create as distinct operations and returns
   normalized observations/receipts. RD-04 may later add GitHub transport only after RD-03 grants
   publication authority.
5. The coordinator updates only the escalation sidecar. Existing run state is an input and is
   byte-compared before/after; no issue result feeds a ticket transition, gate approval,
   verification result, delivery receipt, or merge path.

This seam has less authority than adding issue behavior to `Kernel.open_gate`, `cli.main`, or the
PR `ProviderExecutor`. It can observe a proven failure without becoming a recovery mechanism. The
final storage path, grant scope, and retention remain decisions; the prototype must keep them
replaceable.

## RD-02 Proof Contract

The prototype is complete only if deterministic tests prove all of the following without GitHub,
credentials, or a provider CLI:

- one accepted record and counterexamples for every non-defect taxonomy row;
- strict schema/allowlist validation, bounded text, lowercase SHA-256 fields, and rejection of raw
  messages, unknown metadata, unredacted fixtures, absolute paths, authority fields, and private
  content;
- fingerprint stability under every excluded volatile field and sensitivity to owner/invariant
  changes;
- open and closed exact-marker dedupe, concurrent callers, exact replay, offline, permission,
  contradictory receipt, and every crash boundary in the matrix;
- zero create calls after an ambiguous dispatch until a conclusive exact-marker observation is
  available;
- byte-identical projections of `tickets`, `gates`, `effects`, verification leaf results,
  delivery, PR, merge authorization, merge policy/grant, and ledger history before and after every
  success and failure path;
- missing, malformed, corrupt, or unbound ledgers produce no provider operation;
- fake-adapter call counts establish search-before-create and at-most-one create;
- no production import, CLI command, provider capability, dependency, or tracked runtime state is
  introduced by the throwaway prototype.

## Not Yet Specified

RD-03 resolves the production grant, eligibility, revocation, deduplication, retry, retention,
and presentation policy. RD-04 still chooses internal names and module boundaries, but it may
not widen the accepted decision. Live credential behavior and the exact controlled issue used
for proof remain RD-05 concerns behind `gate:RD-05:start:2`.

## Out of Scope

- Creating issues for bugs in the project being processed by the runner.
- Automatically fixing, merging, closing, reopening, labeling, assigning, or commenting
  on an issue after its initial authorized creation.
- Uploading raw logs or relying on GitHub search text as the only local idempotency record.
- Treating issue creation as recovery from a corrupt ledger or as evidence that a gate
  passed.
- Supporting non-GitHub trackers or arbitrary destination repositories in the first
  implementation.

## Frontier / Blocking Edges

- **Current ownership and evidence seams** — integrated by RD-01. The normalized record and
  proof contract above are the authoritative input to the prototype.
- **Fingerprint and side-effect model** — modeled in the disposable RD-02 candidate. Its
  no-network matrix proves strict eligibility, stable projection, an orthogonal atomic sidecar,
  exact-marker deduplication, concurrent serialization, and crash replay without production
  imports or protected run-state mutation.
- **Publication authority** — resolved by the confirmed
  [RD-03 decision](./ticket-autopilot-runner-defect-issue-publication-decision.md). The
  decision defines the contract but registers no live grant and authorizes no issue effect.
- **Runner integration** — ready after RD-03 integrates, AFK. RD-04 connects the accepted
  contract to the runner and GitHub provider while keeping escalation state orthogonal to
  ticket and merge state.
- **Live provider proof** — blocked by RD-04, HITL. RD-05 creates or deduplicates one
  controlled issue and proves replay safety with a user-authorized GitHub boundary.

## Ticket Plan

| ID | Type | Mode | Blockers | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| `RD-01` | task | AFK | none | Map runner-defect evidence and escalation seams | Source-backed Wayfinder update defining eligibility, redaction boundary, state owners, provider seams, and unknowns |
| `RD-02` | prototype | AFK | `RD-01` | Prototype fingerprinted issue escalation | Disposable classifier, canonical fingerprint, dedupe/outbox model, crash replay, and counterexamples |
| `RD-03` | grilling | HITL | `RD-01`, `RD-02` | Freeze issue-publication authority | Accepted [publication decision](./ticket-autopilot-runner-defect-issue-publication-decision.md) for grant scope, lifetime, revocation, eligibility, deduplication, retry, retention, and presentation |
| `RD-04` | task | AFK | `RD-03` | Implement audited runner-defect issue escalation | Runner/provider integration, durable receipts, redaction and dedupe guards, tests and docs |
| `RD-05` | forward test | HITL | `RD-04` | Forward-test live GitHub issue idempotency | One controlled live creation or dedupe observation, replay evidence, cleanup recommendation, and limitations |

## Prototype Evidence

- [RD-02 runner-defect issue escalation prototype](../prototypes/runner-defect-issue-escalation/NOTES.md)
  is disposable no-network evidence. It validates the RD-01 record, compares the stable
  fingerprint projection, exercises the local outbox lifecycle and all crash boundaries, and
  records keep/discard guidance plus the exact RD-03 decisions. The active RD-02 ticket remains
  immutable while its digest is bound to the runner.

## Next Review

After RD-03 integrates, execute RD-04 against the accepted publication decision and preserve
its no-live-provider claim ceiling. Review the production candidate for strict grant
separation, high-confidence eligibility, exact-marker deduplication, append-only revocation,
ambiguous-dispatch recovery, indefinite receipts, fixed secret-safe rendering, and
byte-identical protected run state. Then stop at `gate:RD-05:start:2`; neither the decision nor
RD-04 authorizes a real issue search or mutation.
