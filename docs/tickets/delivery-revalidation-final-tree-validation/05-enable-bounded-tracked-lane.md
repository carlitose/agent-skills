---
ticket_schema: 1
ticket_id: "FTV-05"
execution_mode: AFK
blocked_by:
  - "FTV-04"
---

# Enable the Bounded Tracked Final-Tree Lane

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-enable-bounded-lane`
- Role: `ticket`
- Parent: [Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## Parent Spec

[Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## What to Build

Enable the exact ordinary tracked pre-quality lane by default only after the integrated FTV-04
handoff proves observation parity, negative classification, crash replay, historical compatibility,
and rollback. Keep `off` and `observe` as explicit supported operator modes, and keep every
ineligible or ambiguous topology on the current full process.

Update operator documentation and status output so the selected mode, contract version, lane
reason, projection state, and rollback behavior are visible without implying completion, merge,
provider, terminal, wiki, Pi, status, cleanup, or reload authority.

## Acceptance Criteria

- [ ] Enablement refuses to proceed unless the exact integrated FTV-04 completion handoff and its
      required parity, matrix, rollback, and full-suite evidence validate.
- [ ] The default mode becomes `enabled`; explicit `observe` and `off` remain strict and tested.
- [ ] An exact ordinary tracked ticket uses one final quality cycle on `D` by default.
- [ ] Every excluded, stale, tampered, exceptional, historical, or ambiguous case retains the
      current full process or blocks exactly as specified.
- [ ] Switching to `off` affects only new projections; persisted intents finish exact replay or
      remain visibly blocked under their original contract version.
- [ ] Status and operator docs explain `projected-not-integrated`, failure remediation before
      integration, linked follow-up tickets after integration, and the separate authority gates.
- [ ] Exact final-tree, provider-head, expected-head merge, and fresh terminal reachability
      invariants remain unchanged.
- [ ] No speedup, wall-time, token, live-provider, or adjacent-authority claim exceeds the FTV-04
      evidence.

## Frontier

Dependency-blocked by `FTV-04`. The DRV-03 human architecture decision already authorizes this
bounded enablement when the exact evidence gate passes; no new design choice is delegated here.

## Step-by-Step Implementation Plan

1. Validate the integrated FTV-04 handoff and freeze its exact enablement prerequisites.
2. Change the default mode only, without weakening the planner, classifier, manifest, replay, or
   fallback contracts.
3. Document mode selection, visible state, safe operator rollback, pre-integration remediation,
   and post-integration follow-up behavior.
4. Run the exact positive, exclusion, crash, history, rollback, authority, provider, and terminal
   matrices under the new default.
5. Reproduce FTV-04 claims conservatively in the final Verification Record and PR body.

## Testing Plan

- Configuration tests for default `enabled`, explicit `observe`, explicit `off`, and malformed
  values.
- End-to-end ordinary tracked delivery proving one `D` quality generation under the default.
- Full exclusion and rollback matrix, including in-flight intent under a later `off` default.
- Broad Ticket Autopilot and extension suites plus static, diff, exact-tree, Artifact Graph, and
  context-budget checks.

## Out of Scope

- Broadening eligibility beyond the exact ordinary tracked contract.
- Removing the current full process.
- Automatic live-provider mutation or merge authorization.
- Wiki publication, Pi synchronization, cleanup, or active-session reload.
