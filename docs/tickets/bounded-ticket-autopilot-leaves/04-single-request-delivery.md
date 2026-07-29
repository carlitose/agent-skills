---
ticket_schema: 1
ticket_id: "04"
execution_mode: AFK
blocked_by:
  - "01"
---

# Drive delivery to a terminal result in one request

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Make one caller-level delivery request advance through the existing crash-safe prepare,
CandidateRef revalidation, commit, push, PR mutation, and readback checkpoints until it
reaches a terminal result or a real gate.

## Acceptance Criteria

- [ ] One delivery request continues across internal revalidation checkpoints without
      requiring the caller to submit the same event again.
- [ ] Existing keyed receipts make every completed commit, push, PR creation/update,
      retarget, and readback effect idempotent across interruption and resume.
- [ ] CandidateRef and staged delivery-tree checks remain fail closed before publication.
- [ ] Remote divergence, provider capability failure, credentials, policy/check state, and
      human authorization stop at explicit gates with precise progress.
- [ ] The command never auto-merges and never weakens exact-head merge authorization.
- [ ] `status` exposes the last delivery phase, elapsed time, and terminal/gated result
      without requiring duplicate ledger events.
- [ ] GitHub and Azure DevOps retain the same normalized provider contract.
- [ ] Interruption at every external-effect boundary resumes without duplicating the
      completed side effect.

## Frontier

Dependency-blocked by `01`. It may proceed independently of ticket `02` after the prototype
freezes progress events and resource-stop semantics.

## Step-by-Step Implementation Plan

1. Map every current delivery return point and persisted receipt to a caller-level state.
2. Implement an internal continuation loop that advances only after validated readback.
3. Persist monotonic delivery progress and stop reasons.
4. Preserve CandidateRef, remote-head, force-with-lease, provider capability, and
   authorization guards.
5. Make interruption/re-entry consult receipts before any external mutation.
6. Update CLI/status/final reporting and provider-neutral documentation.

## Testing Plan

- Unit tests for continuation transitions, terminal/gated outcomes, and progress projection.
- Local Git integration tests for prepare, commit, push, interruption, resume, divergence,
  and force-with-lease.
- Simulated GitHub/Azure tests for PR creation, retarget, checks, authorization, and
  readback.
- No live provider mutation is inferred from simulation.

## Out of Scope

- Auto-merge or inferred human approval.
- Provider-specific delivery state machines.
- Review, QA, verification, or evidence-cache changes.
