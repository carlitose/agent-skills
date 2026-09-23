---
ticket_schema: 1
ticket_id: "TDK-01"
execution_mode: AFK
blocked_by: []
---

# TDK-01 — Isolate the Jev key from model leaves

## Artifact Graph
- Artifact ID: `ticket:ticket-driver-jev-key-isolation:01`
- Role: `ticket`
- Parent: [ticket-driver-jev-key-isolation.md](../../specs/ticket-driver-jev-key-isolation.md)

## Parent Spec
[ticket-driver-jev-key-isolation.md](../../specs/ticket-driver-jev-key-isolation.md)

## What to Build
On a live c2/c3/c4 invocation, move the Jev credential from the process environment into the driver process before worktree, Git, project test, or Pi child launch. Typed judgments still use it. Keep the direct one-off `arbiter.ask` environment behavior and the existing model/process-tree contract. This is a security fix to unblock the already-authorized TDR-05 c2 benchmark, not a benchmark attempt.

## Acceptance Criteria
- [ ] A real fake Pi leaf, a project test subprocess and an approval recheck observe no `TYPESAFE_API_KEY`, while the in-process typed arbiter receives the credential and produces the same answer/usage via a fake transport.
- [ ] A live c2+ request with no key rejects before worktree or ledger creation; fake-leaf tests may still exercise the unavailable cascade.
- [ ] Failure and success restore the caller's environment; no key appears in argv, prompt, receipt or session output. One bounded isolation scope covers all children without changing frozen `ticket-autopilot` or bypassing its Windows containment.
- [ ] Targeted tests and required profile pass; artifact graph and diff clean. No live Jev request or benchmark run in this ticket.

## Frontier
Ready from preflight evidence QB-tdr05-2. User has authorized separate c2a/c2b benchmark lots but those are blocked by this defect. Provider delivery and local sync require their own exact authority and readbacks.

## Step-by-Step Implementation Plan
1. Write causal RED tests on environment inheritance and missing-key preflight.
2. Implement process-local Jev key isolation at the ticket-driver CLI/arbiter boundary; keep `capture_command` unchanged and all child invocations inside the isolated scope.
3. Run causal checks, review and QA, build verification handoff. Separately deliver/sync only under existing explicit authority, then rebind the live c2 batch files to the integrated head.

## Testing Plan
Use temporary synthetic Git repositories and fake leaves/transports; no external models or Jev. Assert absence by a boolean from an actual subprocess, never print the key. Include success, exception and missing-key paths. Run targeted `ticket-driver` tests and repository-mandated local profile.

## Out of Scope
- Any c2 attempt, hidden benchmark result, customer code, provider merge by implication, or modification of frozen `ticket-autopilot`.
