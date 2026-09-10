---
type: source
title: "Drive delivery to a terminal result in one request"
identity_key: ticket:bounded-ticket-autopilot-leaves/04
identity_strength: stable
source_path: docs/tickets/bounded-ticket-autopilot-leaves/done/04-single-request-delivery.md
source_digest: sha256:25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-07-28
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: all-afk-bounded-20260811
---

# Drive delivery to a terminal result in one request

Compiled from `docs/tickets/bounded-ticket-autopilot-leaves/done/04-single-request-delivery.md`. Identity is `ticket:bounded-ticket-autopilot-leaves/04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-07-28** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-bounded-ticket-autopilot-leaves-01]] — `ticket:bounded-ticket-autopilot-leaves/01`

## Run

Completed under autopilot run `all-afk-bounded-20260811`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[3],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[4],"status":"present"},"intent":{"headings":[2],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-bounded-ticket-autopilot-leaves-04.md","payload_bytes":2717,"payload_sha256":"25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545"}],"payload_bytes":2717,"payload_sha256":"25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545","schema":1,"source_digest":"sha256:25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545","source_identity":"ticket:bounded-ticket-autopilot-leaves/04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 2: What to Build |
| acceptance | 3: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | 4: Frontier |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2717,"payload_sha256":"25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545","schema":1,"source_digest":"sha256:25d53fd1246eb9691fa061a0e1c2879bb01b6b94fce5f1704bd3eebb9fc51545","source_identity":"ticket:bounded-ticket-autopilot-leaves/04"} -->
```markdown
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

```
