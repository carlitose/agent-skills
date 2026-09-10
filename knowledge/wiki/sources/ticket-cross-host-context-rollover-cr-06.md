---
type: source
title: "Remove the Claude rollover autocompact dependency"
identity_key: ticket:cross-host-context-rollover/CR-06
identity_strength: stable
source_path: docs/tickets/cross-host-context-rollover/done/06-remove-autocompact-dependency.md
source_digest: sha256:4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: cr-autocompact-removal-20260829
---

# Remove the Claude rollover autocompact dependency

Compiled from `docs/tickets/cross-host-context-rollover/done/06-remove-autocompact-dependency.md`. Identity is `ticket:cross-host-context-rollover/CR-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-cross-host-context-rollover-wayfinder]]
- Blocked by: [[sources/ticket-cross-host-context-rollover-cr-05]] — `ticket:cross-host-context-rollover/CR-05`

## Run

Completed under autopilot run `cr-autocompact-removal-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-cross-host-context-rollover-cr-06.md","payload_bytes":3053,"payload_sha256":"4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85"}],"payload_bytes":3053,"payload_sha256":"4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85","schema":1,"source_digest":"sha256:4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85","source_identity":"ticket:cross-host-context-rollover/CR-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3053,"payload_sha256":"4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85","schema":1,"source_digest":"sha256:4abf4e0a2d831f0afba10b5856b057c5bf9ba4c0a4c87f3322fee02d6ebcee85","source_identity":"ticket:cross-host-context-rollover/CR-06"} -->
```markdown
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

```
