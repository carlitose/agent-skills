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
  "complete": false,
  "candidate_ref": {},
  "scope": {
    "files_expected": [],
    "files_inspected": []
  },
  "commands_run": [],
  "findings": [],
  "remaining_work": [],
  "progress_phase": "diff-inspected",
  "stop_reason": "wall-time-budget"
}
```

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

The accepted architecture decision D6 remains authoritative: any candidate content or
ticket-contract change invalidates prior review, QA execution, verification, and merge
authorization. Cross-`CandidateRef` reuse is not authorized by this spec. A later HITL
decision may preserve D6 or define narrower categories only with a fail-closed causal
contract and independent evidence.

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

- Exact default and maximum values for each budget.
- Whether tool-call and wall-time budgets are hard enforcement or best-effort when host
  telemetry is incomplete.
- Exact ledger version and migration policy for active runs.
- The minimum heartbeat interval and stuck-versus-healthy threshold.
- Whether any evidence category may survive a changed `CandidateRef`; this requires the
  explicit HITL decision ticket.

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
