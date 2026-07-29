# Bounded Ticket-Autopilot Leaf Protocol

## Type

Architecture spec

## Status

Planning baseline

## Source

- [GitHub issue #9 — Bound verbosity and enforce progress budgets for review/audit leaves](https://github.com/carlitose/agent-skills/issues/9)
- [Current ticket-autopilot contract](../../ticket-autopilot/SKILL.md)

## Problem

The deterministic scheduler protects review independence, evidence integrity, exact-SHA
delivery, and honest claim ceilings. A real two-ticket AFK run nevertheless showed that
leaf execution can remain opaque and consume many turns even when the candidate is stable:

- incomplete leaf handoffs require follow-up turns;
- interaction limits are confused with quality-failure limits;
- long review and verification leaves expose no durable phase progress;
- unchanged context and evidence are rediscovered;
- delivery checkpoints are crash-safe but may require another caller request;
- polling and repeated status prose add cost without advancing state.

The target is bounded and observable execution with the same quality and authority
boundaries.

## Goals

- Configure and persist separate quality-failure, leaf-interaction, tool-call, and wall-time
  budgets.
- Reserve enough execution capacity for mandatory QA execution and verification.
- Require every leaf to return a complete or partial structured handoff.
- Persist progress phases so unchanged healthy work does not require user-facing polling.
- Reuse immutable context and evidence while the exact `CandidateRef` is unchanged.
- Make verification bundle assembly, validation, reduction, and hashing deterministic and
  resumable.
- Let one delivery request advance through all idempotent checkpoints until it reaches a
  terminal result or a real gate.
- Report cost, waits, cache use, invalidations, and limitations without raising the claim
  ceiling.

## Non-Goals

- Weakening independent review, QA, verification, exact-SHA merge authorization, or provider
  capability gates.
- Auto-merging pull requests or fabricating human decisions, credentials, or live evidence.
- Replacing provider-neutral delivery with GitHub- or Azure-specific orchestration.
- Treating timeouts, partial inspection, skipped environments, or cached context as passing
  evidence.
- Reusing review, QA execution, or verification artifacts across different
  `CandidateRef` values without a later explicit decision.
- Guaranteeing token counts when the host does not expose them.

## Current Behavior

- `--max-quality-failures` counts code-affecting gate failures; there is no persisted total
  leaf-interaction, tool-call, or wall-time budget.
- A leaf may remain running or return an incomplete narrative without a machine-readable
  continuation point.
- The ledger records ticket stages and delivery effects but not leaf phase heartbeats.
- Candidate drift invalidates review, QA, verification, and merge authorization.
- Delivery is idempotent internally but can return `revalidation-required`, requiring a
  repeated caller event.
- Verification consumes structured artifacts but leaf-side bundle construction remains an
  opaque semantic turn.

## Target Behavior

### Immutable leaf context

The scheduler prepares one versioned `LeafContext` per ticket and `CandidateRef` containing:

- normalized Ticket Envelope identity and digest;
- exact `CandidateRef`;
- frozen diff manifest with expected files and content identities;
- stage contract and allowed result schema;
- prior findings and dispositions;
- normalized command/evidence manifest with artifact hashes;
- environment limitations and open gates;
- remaining and reserved budgets;
- the latest compatible partial handoff.

The package is an input contract, not proof that its claims are true. Leaves inspect only the
semantic scope they own and cite the artifacts they consume.

### Orthogonal budgets

Persist and report:

- `max_quality_failures` and consumed code-quality failures;
- `max_leaf_interactions` and consumed delegated turns;
- optional `max_leaf_tool_calls`;
- optional `max_leaf_wall_time`;
- reserved interactions for QA execution and verification audit.

Budget exhaustion returns a structured partial result. It never becomes a quality pass,
verification pass, or release waiver. Unsupported host telemetry is recorded as
`unavailable`, not estimated.

### Bounded leaf handoff

Every leaf terminates its turn with a versioned result equivalent to:

```json
{
  "schema": 3,
  "complete": false,
  "candidate_ref": {},
  "stage": "review",
  "phase_contract": [
    "context-loaded",
    "diff-inspected",
    "findings-normalized",
    "handoff-ready"
  ],
  "scope": {
    "files_expected": [],
    "files_inspected": [],
    "files_remaining": []
  },
  "phases_remaining": [
    "findings-normalized",
    "handoff-ready"
  ],
  "commands_run": [],
  "findings": [],
  "progress_phase": "diff-inspected",
  "stop_reason": "wall-time-budget"
}
```

`scope.files_remaining` is structural, ordered scope. It must equal
`files_expected - files_inspected`. `stage` selects one canonical leaf contract and the
persisted `phase_contract` must equal that contract exactly. `phases_remaining` is its
ordered suffix after `progress_phase`, so a leaf interrupted after inspecting every file
still carries resumable checkpoint work without claiming phases owned by another leaf.
Continuation actions are derived from those fields and are never accepted as free-form
persisted work. The ledger, every progress event/log, and the handoff carry the same exact
`CandidateRef`. Every progress event and its log also persist the same `stage` and
`phase_contract` as the handoff; each event phase must belong to that contract. A mismatch
rejects the artifact before it can mutate accounting or establish semantic pass.
The latest admitted budget interaction must equal the persisted progress/handoff stage.
A complete mandatory-stage handoff additionally requires that stage's consumed reservation
to be marked complete; phase artifacts cannot manufacture mandatory completion.
All handoff scope, phase-contract, remaining-phase, command, and finding collections are
JSON arrays of non-empty strings; `complete` is an actual boolean and `stop_reason` is null
or a non-empty string. Values with coercible but incorrect JSON types fail closed before
construction.

Budget configuration is valid only with exactly one reserved interaction for
`qa-execute` and exactly one for `verify`; review cannot omit, duplicate, reorder, or
consume those slots. Quality becomes terminal on the transition where
`quality_failures >= max_quality_failures`. This is a quality-limit result, not resource
exhaustion. A live or restored state at that threshold rejects every subsequent leaf;
serialization cannot make terminal quality state resumable.

Ledger schema `2` is a replayable snapshot, not only configuration: it persists evolved
interaction, quality, tool-call, wall-time, reservation, and mandatory-completion state;
candidate-bound progress events; and nullable candidate-bound continuation handoff.
Restoration preserves raw reservation mappings, replays interaction history through
mandatory-capacity admission, and requires the handoff phase to match the latest
persisted progress event.
Duplicate progress events remain idempotent at the live transition boundary, but a
persisted event array containing duplicates is corruption and fails closed rather than
being normalized during restoration.
Unconfigured tool-call and wall-time dimensions report `enforcement: unavailable`;
configured dimensions report `enforcement: hard`.
Observed live tool-call and wall-time deltas are exact non-negative integers; booleans,
fractions, and negative values fail before any accounting mutation.

The exact schema is owned by the deterministic contract implementation. An incomplete
handoff cannot satisfy the stage gate, but a compatible continuation may resume the named
remaining scope without repeating recorded work.

### Durable progress

The ledger accepts monotonic, idempotent phase events such as:

- `context-loaded`;
- `diff-inspected`;
- `findings-normalized`;
- `qa-plan-built`;
- `bundle-built`;
- `bundle-validated`;
- `bundle-reduced`;
- `handoff-ready`.

`status` exposes the last phase, elapsed time, budget consumption, and whether progress is
healthy, timed out, or gated. Repeated unchanged status reads do not append duplicate
events.

### Evidence reuse

For an unchanged `CandidateRef`, validated command results, immutable file inspection,
environment limitations, and deterministic bundle stages may be reused when their declared
scope and artifact hashes still match.

The accepted architecture decision D6 remains authoritative and is explicitly preserved by
the [candidate invalidation decision](candidate-invalidation-decision.md): any candidate
content or ticket-contract change invalidates prior review, QA execution, verification, and
merge authorization. Cross-`CandidateRef` semantic reuse is not authorized. Plans, templates,
or facts may carry forward only as untrusted inputs, never as evidence or a pass.

### Deterministic verification

Scripts own bundle assembly from validated inputs, schema validation, hashing, reduction,
claim-ceiling computation, and persisted phase checkpoints. The verification leaf owns
semantic ambiguity, boundary authorization, contradictions, and truthful wording. Resume
starts at the first missing or invalid checkpoint for the same `CandidateRef`.

### One-request delivery

One caller-level delivery request repeatedly advances the existing idempotent internal
effects:

`prepare -> CandidateRef revalidate -> commit -> push -> PR create/update -> readback`

The command stops only at a terminal result, configured resource budget, or real
human/environment/provider gate. Every external mutation retains its existing keyed receipt,
remote-head checks, and exact-SHA authorization.

## Semantic Invariants

- A changed candidate cannot inherit a passing semantic artifact from the prior candidate.
- Quality failures and resource/interaction exhaustion remain different states.
- Partial inspection is visible and cannot be normalized to a complete review.
- Reserved mandatory stages cannot be consumed by optional review retries.
- Cached evidence supports only its declared causal segment and exact artifact identity.
- A progress heartbeat is observability, not verification evidence.
- Delivery retries do not duplicate commits, pushes, PRs, retargets, or merges.
- Open live, credential, provider, browser, database, payment, or human gates continue to
  cap claims.

## External Contract Changes

- New CLI budget options and status/report fields.
- New versioned `LeafContext`, partial handoff, progress-event, and evidence-manifest shapes.
- New persisted ledger fields/events and possibly a ledger schema version.
- Delivery changes from caller-repeated continuation to one caller-level resumable command.

Backward compatibility is opt-in. Existing active-run ledgers must either be migrated by an
explicit validated command or rejected with a clear version error; silent interpretation is
forbidden. The prototype ticket owns the concrete versioning recommendation.

## Failure Modes

- A leaf times out without serializing its partial state.
- Claimed inspected files do not match the frozen diff manifest.
- A cached artifact hash or `CandidateRef` differs from the current context.
- Heartbeats repeat, regress, or advance without the required artifact.
- Host tool/time telemetry is unavailable.
- Reserved mandatory capacity cannot be satisfied by the configured total budget.
- Delivery resumes after an ambiguous external side effect without readback.
- A ledger from an older schema is interpreted as the new protocol.

All fail closed with a structured gate, partial result, or version error.

## Security and Data Concerns

- Context packages and progress events must not persist credentials, provider tokens, or
  unsanitized command output.
- Artifact paths must stay inside the managed run directory.
- External receipts retain sanitized identifiers and hashes needed for idempotency.
- Human approval and merge authorization remain explicit, actor-bound, and SHA-bound.

## Implementation Slices

1. Prototype budget accounting, reservations, progress, partial handoff, and ledger
   compatibility against deterministic fixtures.
2. Implement the generic protocol through one real review leaf and status/final reporting.
3. Extend the protocol to QA planning/execution and deterministic verification checkpoints.
4. Add immutable same-`CandidateRef` context/evidence reuse.
5. Drive delivery checkpoints from one caller request.
6. Grill cross-`CandidateRef` reuse as a separate human decision.
7. After that decision, emit the final integrated two-ticket forward-test slice.

## Verification Strategy

- Unit: budget reduction, reservations, schema validation, phase transitions, cache keys,
  timeout/partial results, and ledger replay.
- Integration: interrupt and resume review, QA, audit, and delivery in isolated repositories
  without repeating completed work.
- Forward test: reproduce the issue’s two-ticket shape, preserve discovery of a planted
  blocker and should-fix, and measure interactions, waits, repeated commands, and wall time.
- Provider simulation: exact-SHA, readback, and idempotent delivery remain fail closed.
- Live/manual: no live provider, database, browser, payment, or human-controlled behavior is
  inferred from local checks.

## Not Yet Specified

- The minimum heartbeat interval and stuck-versus-healthy threshold.
- Whether any evidence category may survive a changed `CandidateRef`; this requires the
  explicit HITL decision ticket.

## Prototype Resolution from Ticket 01

The disposable logic prototype under
[`docs/prototypes/bounded-ticket-autopilot-leaves`](../prototypes/bounded-ticket-autopilot-leaves/)
resolves the initial production defaults:

- retain `max_quality_failures=3`;
- add `max_leaf_interactions=10`, constrained to `3..100`;
- reserve one interaction for `qa-execute` and one for `verify`;
- optional positive tool-call and wall-time budgets default to `null` and report
  `unavailable` unless the host supplies enforceable telemetry;
- use leaf-result schema `3` with CandidateRef contract version `1`; schema `3` persists
  the owning leaf stage, its exact canonical phase contract, and the deterministic
  remaining-phase suffix required for late-phase interruption;
- use ledger schema `2` and reject schema-1 active runs with an explicit
  migration-or-new-run error;
- do not add an implicit or compatibility migrator. An explicit migrator remains separate
  opt-in work if preserving active schema-1 runs is later required.

Prototype tests cover separate counters, impossible reservations, complete/partial handoff,
file-scope and late-phase round-trip resume, monotonic/idempotent progress, configured
resource exhaustion, and stale CandidateRef rejection.

## Acceptance Outcomes

- Every leaf ends within configured limits with a complete or usable partial handoff.
- Status distinguishes progress, waiting, timeout, gate, and quality failure.
- Total leaf interactions and quality failures are separately configured and reported.
- Verification resumes from validated checkpoints for the same `CandidateRef`.
- Unchanged-candidate cache hits avoid repeated commands and inspection without raising
  claims.
- One delivery request reaches a terminal result or real gate without duplicate effects.
- The issue’s real blocker and should-fix remain discoverable.
- Candidate changes preserve D6 until an explicit replacement decision is accepted.
- Missing live evidence never raises the claim ceiling.
