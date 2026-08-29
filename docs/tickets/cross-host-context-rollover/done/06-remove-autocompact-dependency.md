---
ticket_schema: 1
ticket_id: "CR-06"
execution_mode: AFK
blocked_by:
  - "CR-05"
---

# Remove the Claude rollover autocompact dependency

## Artifact Graph

- Artifact ID: `artifact:cr-06-remove-autocompact-dependency`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## What to Build

Retrofit the Claude rollover tracer bullet and its documentation so no path requires,
configures, invokes, or claims behavior from `--autocompact`. Consume only the supported
capability result recorded by CR-05 and fail visibly when early host compaction makes the
fixed threshold unreachable.

## Acceptance Criteria

- [ ] No operational requirement, fixture field, validation rule, runner argument, or positive
      claim remains for `--autocompact`, `autocompact_tokens`, or the 160,000 fixture value.
      Documentation may retain only historical evidence and the explicit rejection.
- [ ] The adapter consumes only the CR-05 capability classification and never infers control
      from a CLI help entry.
- [ ] Supported prevention is isolated and explicit; observation-only or unsupported hosts
      return a visible incompatible or `no-go` result before claiming the 150,000-token path.
- [ ] `PreCompact` below the threshold never arms rollover or counts as success. An already
      pending generation keeps its identity and retry budget across observed compaction.
- [ ] Existing message projection, safe-boundary, handoff privacy, fresh-session, bootstrap,
      retry, and authoritative-readback invariants remain unchanged.
- [ ] Tests include the user-reported counterexample: a binary may advertise
      `--autocompact` while the controller receives no acceptable runtime guarantee.
- [ ] The complete cross-host prototype suite passes and documentation makes no live-host
      claim.

## Frontier

Blocked by CR-05's supported-control classification.

## Step-by-Step Implementation Plan

1. Add failing fixtures for advertised-but-ineffective autocompact and unsupported early
   compaction.
2. Remove the flag, token field, validation, and process argument from the Claude surface.
3. Add the versioned supported-capability adapter or the explicit `no-go` result selected by
   CR-05.
4. Update prototype notes, policy, and wayfinder evidence without changing the fixed trigger.
5. Run the complete prototype suite and candidate-scoped documentation checks.

## Testing Plan

Run the Claude and complete cross-host prototype suites. Cover supported, unsupported,
observation-only, advertised-but-ineffective, pre-threshold compaction, already-pending
compaction, and unchanged fresh-session restoration. Live provider and interactive behavior
remain CR-04 evidence.

## Out of Scope

- Lowering or dynamically changing the 150,000-token trigger.
- Installing production controllers or global Claude hooks.
- Changing Codex rollover behavior.
- Executing the HITL live proof.
