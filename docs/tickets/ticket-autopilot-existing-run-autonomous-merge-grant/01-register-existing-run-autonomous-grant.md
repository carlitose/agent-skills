---
ticket_schema: 1
ticket_id: "EMG-01"
execution_mode: AFK
blocked_by: []
---

# Register an autonomous merge grant on an existing run

## Artifact Graph

- Artifact ID: `artifact:emg-01-register-existing-run-autonomous-grant`
- Role: `ticket`
- Parent: [Existing-Run Autonomous Merge Grant Bug Analysis](../../specs/ticket-autopilot-existing-run-autonomous-merge-grant.md)

## Parent Spec

[Existing-Run Autonomous Merge Grant Bug Analysis](../../specs/ticket-autopilot-existing-run-autonomous-merge-grant.md)

## What to Build

Add one append-only `grant-autonomous-merge` transition for a non-terminal manual Ticket
Autopilot run. Bind actor and durable evidence to the existing repository, run ID, ticket-set
digest, provider, and policy; then continue through the existing fresh-eligibility and exact-head
merge critical path without requiring one approval phrase per PR.

Covers the parent spec's Target Behavior, Semantic Invariants, Failure Modes, Acceptance Outcomes,
and Verification Strategy.

## Acceptance Criteria

- [ ] `grant-autonomous-merge <run-id> --actor <identity> --evidence <durable-ref>` is a documented
      public command and requires the repository binding when it cannot be resolved safely.
- [ ] A validated non-terminal manual run receives exactly one immutable autonomous grant bound to
      repository identity, run ID, ticket-set digest, provider, and autonomous policy.
- [ ] The transition is append-only, lock-serialized, visible in `status`, and exact replay with the
      same actor/evidence is idempotent.
- [ ] Missing authority, terminal runs, contradictory replay, forged binding, or an unresolved
      provider merge mutation fail without changing the ledger or calling the provider.
- [ ] A manual run already at `pr-open` resumes through fresh live head/check/rule/approval/
      mergeability reads and the existing atomic expected-head merge path without a per-PR approval.
- [ ] One accepted run grant covers later eligible tickets in the same ticket set; every PR still
      receives a new current-head eligibility receipt and expected-head mutation.
- [ ] Changed heads, pending/failed/unknown checks, simulated provider evidence, queue uncertainty,
      pause/disposition/source drift, and wiki-sync authority preserve their existing gates.
- [ ] Crash replay after grant persistence neither requests authority again nor duplicates a merge
      mutation.
- [ ] Existing manual and autonomous run creation behavior, CandidateRef semantics, delivery lineage,
      and ledger history validation remain compatible.
- [ ] Focused tests, full Ticket Autopilot tests, context-budget checks, and the applicable forward
      scenario pass.

## Frontier

Ready. The current CLI exposes grant creation only at `run`; the existing eligibility and merge
critical path can be reused after a safe policy transition.

## Step-by-Step Implementation Plan

1. Add red kernel and ledger tests for manual-to-autonomous transition binding, append-only history,
   exact idempotence, contradiction, terminal states, and forged persisted state.
2. Add red CLI integration tests that stop a manual run at `pr-open`, register the grant, and prove
   fresh expected-head delivery plus multi-ticket reuse and crash replay.
3. Implement the lock-serialized kernel transition and ledger validator using the current immutable
   run fields; reject unsafe in-flight merge state before any mutation.
4. Add the public command, normalized output, scheduler continuation, and status/history projection.
5. Reuse the existing autonomous eligibility/provider path without adding an unpinned or direct
   fallback.
6. Update `ticket-autopilot/SKILL.md`, README/help references, forward selectors, and measured context
   fixtures only where the new public surface requires it.
7. Run focused, complete, and forward verification; keep simulated and live claims separate.

## Testing Plan

Use disposable repositories and deterministic provider adapters for causal integration tests.
Assert exact ledger bytes/history on rejection, provider call counts and expected head on success,
idempotent replay, multi-ticket reuse, changed-head revalidation, and crash recovery. Run the full
Ticket Autopilot suite and forward-test matrix after focused tests.

## Out of Scope

- Global or cross-run merge preferences.
- Natural-language parsing inside Ticket Autopilot.
- Grant revocation, replacement, or downgrade.
- Transferring application authority to wiki-sync delivery.
- Weakening checks, branch rules, approval policy, queues, provider readback, or exact-head mutation.
