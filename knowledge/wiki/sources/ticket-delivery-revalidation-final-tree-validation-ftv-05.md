---
type: source
title: "Enable the Bounded Tracked Final-Tree Lane"
identity_key: ticket:delivery-revalidation-final-tree-validation/FTV-05
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-final-tree-validation/done/05-enable-bounded-tracked-lane.md
source_digest: sha256:da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-02
created_provenance: git-commit
disposition_changed: 2026-09-03
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-validation-ftv04-corrective-v2-20260903
---

# Enable the Bounded Tracked Final-Tree Lane

Compiled from `docs/tickets/delivery-revalidation-final-tree-validation/done/05-enable-bounded-tracked-lane.md`. Identity is `ticket:delivery-revalidation-final-tree-validation/FTV-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-02** via `git-commit`
- Disposition changed: **2026-09-03** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-final-tree-validation-decision]]
- Blocked by: [[sources/ticket-delivery-revalidation-final-tree-validation-ftv-04]] — `ticket:delivery-revalidation-final-tree-validation/FTV-04`

## Run

Completed under autopilot run `delivery-revalidation-final-tree-validation-ftv04-corrective-v2-20260903`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-final-tree-validation-ftv-05.md","payload_bytes":3758,"payload_sha256":"da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016"}],"payload_bytes":3758,"payload_sha256":"da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016","schema":1,"source_digest":"sha256:da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3758,"payload_sha256":"da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016","schema":1,"source_digest":"sha256:da7ecafa0a596e7223c48f7fbf966403fa067e0fbc72b18d47fe2a465894c016","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-05"} -->
```markdown
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

```
