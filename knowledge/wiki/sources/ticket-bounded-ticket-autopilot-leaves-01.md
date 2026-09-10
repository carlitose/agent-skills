---
type: source
title: "Prototype bounded leaf accounting and resumable handoffs"
identity_key: ticket:bounded-ticket-autopilot-leaves/01
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/done/01-prototype-bounded-leaf-accounting.md
source_digest: sha256:cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-07-28
created_provenance: git-commit
disposition_changed: 2026-07-29
disposition_changed_provenance: git-rename
run_id: issue9-bounded-leaves-quality-epoch-03
---

# Prototype bounded leaf accounting and resumable handoffs

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/done/01-prototype-bounded-leaf-accounting.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **2026-07-29** via `git-rename`

## Run

Completed under autopilot run `issue9-bounded-leaves-quality-epoch-03`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-01.md","payload_bytes":3108,"payload_sha256":"cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667"}],"payload_bytes":3108,"payload_sha256":"cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667","schema":1,"source_digest":"sha256:cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667","source_identity":"ticket:bounded-ticket-autopilot-leaves/01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3108,"payload_sha256":"cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667","schema":1,"source_digest":"sha256:cdaaa40a2d01bb53c2bb944102354b4357c98ea163223388a05b7b0083b33667","source_identity":"ticket:bounded-ticket-autopilot-leaves/01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Prototype bounded leaf accounting and resumable handoffs

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Build a disposable deterministic prototype for the budget, reservation, progress, partial
handoff, and ledger-version decisions required by
[GitHub issue #9](https://github.com/carlitose/agent-skills/issues/9). Model the real
two-ticket shape without modifying production scheduler behavior.

## Acceptance Criteria

- [ ] The model tracks quality failures, total leaf interactions, optional tool calls, and
      optional wall time as separate dimensions.
- [ ] Mandatory QA execution and verification reservations cannot be consumed by earlier
      review retries, and impossible configurations fail before a run starts.
- [ ] A leaf can stop with a versioned partial handoff containing exact CandidateRef,
      expected/inspected scope, commands, findings, remaining work, phase, and stop reason.
- [ ] Replaying a compatible partial handoff resumes only the remaining scope and does not
      repeat completed modeled work.
- [ ] Progress events are monotonic and idempotent; repeated status reads do not create
      duplicate progress.
- [ ] A changed CandidateRef invalidates every modeled semantic handoff and artifact.
- [ ] Fixtures reproduce a complete leaf, a timeout, an interruption/resume, budget
      exhaustion, reserved-stage protection, and stale-candidate rejection.
- [ ] The result recommends exact production schemas, budget arithmetic, and either an
      explicit ledger migration or a fail-closed version boundary.

## Frontier

Ready. This prototype resolves the contract and compatibility questions that block
production tickets `02` and `04`.

## Step-by-Step Implementation Plan

1. Capture the current ledger counters, stage transitions, CandidateRef invalidation, and
   delivery continuation as the known baseline.
2. Define small versioned prototype records for budgets, leaf context, progress, and partial
   handoff.
3. Implement pure transition/reduction functions and deterministic fixtures.
4. Exercise invalid configurations, interruption windows, stale references, and ledger
   replay.
5. Compare migration, version-bump, and fail-closed options for existing active runs.
6. Record the selected production contract and rejected alternatives in the parent spec or
   a linked decision record.

## Testing Plan

- Unit tests for arithmetic, reservations, transitions, replay, idempotency, and stale
  CandidateRef rejection.
- Scenario tests matching the interaction accounting and mandatory-stage pressure described
  in issue #9.
- Static comparison with current ledger and CLI contracts.
- No result from the prototype is runtime or live-provider evidence.

## Out of Scope

- Editing production scheduler, leaf skills, verification contracts, or delivery code.
- Choosing cross-CandidateRef evidence reuse.
- Live provider, database, browser, payment, credential, or human verification.

```
