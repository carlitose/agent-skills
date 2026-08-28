---
ticket_schema: 1
ticket_id: "CR-04"
execution_mode: HITL
blocked_by:
  - "CR-02"
  - "CR-03"
  - "CR-06"
---

# Prove cross-host rollover live

## Artifact Graph

- Artifact ID: `artifact:cr-04-prove-cross-host-rollover-live`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Type

Live proof

## What to Prove

Run one user-controlled Codex rollover and one user-controlled Claude Code rollover using the
two disposable tracer bullets after the CR-06 Claude retrofit. Observe the real session
boundary, hook events, handoff
validation, new-session creation, bootstrap submission, and durable frontier reconstruction.

This ticket owns the human authority and live host boundary. It does not turn a passing
prototype into a production release by implication.

## Acceptance Criteria

- [ ] The user confirms the two source sessions, working directory, threshold fixture, and
      permission to create replacement sessions before the runs begin.
- [ ] Each run records the source session identity, observed count, trigger, handoff path and
      digest, replacement session identity, hook events, and reconstruction result without
      retaining transcript content.
- [ ] Each host records the current-context value immediately below and at/above 150,000,
      proves that crossing only arms `rollover_pending`, and proves no active task is
      interrupted.
- [ ] No replacement session starts until the handoff validates and the source turn has
      stopped.
- [ ] Each replacement reads the Wayfinder map, canonical ticket inventory, current run
      status, and correct next frontier from durable pointers.
- [ ] Expiry, cleanup, one-shot consumption, retry, and multi-chat collision behavior are
      exercised or explicitly left unobserved.
- [ ] Codex and Claude Code limitations are compared without treating one host's evidence as
      proof for the other.
- [ ] The Claude run requires no `--autocompact`; it records the supported CR-05 capability
      or reports a visible `no-go` if early compaction prevents the fixed threshold.
- [ ] The result recommends operator-visible, controller-managed, compaction-only, or no-go
      production direction for each host.
- [ ] Any production follow-up is recorded through `to-spec` and new tracer-bullet tickets;
      this live proof does not silently install hooks or controllers.

## Frontier

Blocked by `CR-02`, `CR-03`, and `CR-06`, then by human availability and permission to
create the two
replacement sessions.

## Step-by-Step Implementation Plan

1. Review the reduced evidence and limitations from both prototypes plus CR-05/CR-06 with
   the user.
2. Bind the live run inputs and authority to the exact prototype versions.
3. Execute the Codex rollover and capture sanitized causal evidence.
4. Execute the Claude Code rollover and capture sanitized causal evidence.
5. Compare the two observations and record the production-design recommendation.
6. Delete or retain each private handoff according to the confirmed expiry policy.

## Testing Plan

The evidence is the two live, user-controlled observations. Local fixtures remain supporting
evidence only. Failure to observe a host boundary is recorded as unavailable or blocked, not
converted into a passing simulated claim.

## Out of Scope

- Installing a production controller, global hook, scheduled task, or service.
- Clearing unrelated chats or selecting sessions by recency alone.
- Copying provider transcripts into repository artifacts.
- Claiming production readiness from one successful rollover per host.
- Restoring `--autocompact` as a prerequisite or treating its help entry as live evidence.
