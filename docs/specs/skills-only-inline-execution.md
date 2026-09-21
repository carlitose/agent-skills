# Skills-only inline execution

## Artifact Graph
- Artifact ID: `artifact:skills-only-inline-execution`
- Role: `spec`
- Standalone: true

### Children

- [SH-01](../tickets/skills-only-inline-execution/01-skills-only-inline.md)

## Problem and evidence

The mandatory Pi policy requires `to-spec -> to-tickets -> ticket-autopilot` for every
shippable change, reserves delivery and local synchronization to that runner, and requires
its skill globally. `execute-ticket` can compose stages inline, but its verification handoff
and the router still require runner-provided inputs. These rules deadlock a user who has
explicitly suspended Autopilot while asking to repair the harness itself.

The affected owners are `extensions/mandatory-agent-skills.ts`, `ask-skills`, `to-tickets`,
`execute-ticket`, and `verification-audit`. CandidateRef v2 and Ticket Envelope v1 already
have pure validators; their schemas do not require a scheduler identity or run ledger.

## Decision

Support an explicit skills-only lane: validated spec/ticket inputs, caller-owned canonical
candidate identity, and serial inline `execute-ticket` composition. Preserve Autopilot as
the default where the user has not selected the alternate lane or suspended it. No mode
settings, driver scripts, parser copies, new schemas, or alternative claim reducers.

The user restriction remains in the durable plan/handoff across continuation and compaction
until lifted. `/agent-skills-flow` reports skill availability; it does not select a mode or
infer that a suspension ended. Its core required skill is `execute-ticket` rather than
`ticket-autopilot`; lane-specific missing inputs fail at their owning stage.

The caller may perform delivery and exact-integrated-head local synchronization separately
from the implementation leaf, only within explicit authority and with current evidence,
provider readback, and existing CI gates. Runner state is neither required nor forged.

## Invariants

- Canonical parser, serializer, CandidateRef, validator, and reducer remain unchanged.
- Stale candidate evidence cannot support current claims. Prior failures, evidence, attempts,
  gates, and cumulative consumption remain intact when switching lanes.
- Shared-context review is not independent; unavailable checks remain explicit gaps.
- AFK, continuation, and compaction never enable a suspended runner or authorize subagents.
- No automatic wiki finalizer, runner, scheduler, or substitute driver in skills-only.
- Delivery, merge, cleanup, local installation, and reload require their own real authority.
- Local sync preserves settings/unrelated packages and verifies source, HEAD/tree, package
  version, and changed-file digests. It reports `/reload` required unless an explicitly
  requested runtime reload tool completes; installing files never implies an active reload.

## Verification strategy

Add focused policy/reference regressions for both lanes, missing core skills, suspension
precedence, canonical input ownership, delivery authority, and synchronization boundaries.
Review the complete composed policy for contradictory runner-only requirements. Check
syntax, whitespace, and local links before any authorized runtime checks. Tests not executed
must remain unclaimed; this policy change does not prove model compliance in a live Pi
session. No full suite is required solely by these policy/reference changes; existing
provider-required checks are not waived.

## Scope

One slice, SH-01, changes the policy and connected skill contracts. Do not repair the runner,
resume PCG-01, alter budgets/timeouts, add authorization semantics, reset Pi settings, or
change break-glass. Installation after proven integration is the separate local-sync step.
