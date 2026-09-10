---
type: source
title: "Freeze issue-publication authority"
identity_key: ticket:ticket-autopilot-runner-defect-issues/RD-03
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-issues/done/03-freeze-issue-publication-authority.md
source_digest: sha256:e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-31
disposition_changed_provenance: git-rename
run_id: runner-defect-issues-20260829
---

# Freeze issue-publication authority

Compiled from `docs/tickets/ticket-autopilot-runner-defect-issues/done/03-freeze-issue-publication-authority.md`. Identity is `ticket:ticket-autopilot-runner-defect-issues/RD-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-31** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-issue-wayfinder]]
- Blocked by: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-01]] — `ticket:ticket-autopilot-runner-defect-issues/RD-01`
- Blocked by: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-02]] — `ticket:ticket-autopilot-runner-defect-issues/RD-02`

## Run

Completed under autopilot run `runner-defect-issues-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-issues-rd-03.md","payload_bytes":2400,"payload_sha256":"e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299"}],"payload_bytes":2400,"payload_sha256":"e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299","schema":1,"source_digest":"sha256:e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2400,"payload_sha256":"e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299","schema":1,"source_digest":"sha256:e823b07b75b478bd6cb9649127069eb91bf72ebfbb2115aef3348a5fbcf20299","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RD-03"
execution_mode: HITL
blocked_by:
  - "RD-01"
  - "RD-02"
---

# Freeze issue-publication authority

## Artifact Graph

- Artifact ID: `artifact:rd-03-freeze-issue-publication-authority`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Invoke canonical `grilling` and obtain explicit user confirmation of the external publication
contract. Freeze grant scope and lifetime, revocation, minimum diagnosis confidence, allowed
evidence, closed-issue behavior, labels, and failure/retry behavior without changing the
already confirmed destination repository.

## Acceptance Criteria

- [ ] The interview asks one question at a time and distinguishes per-run, repository-scoped,
      and reusable authority with their audit and revocation consequences.
- [ ] The user confirms the minimum diagnosis confidence and evidence required for an
      automatic issue write.
- [ ] Closed matches, ambiguous matches, provider unavailability, lost responses, and grant
      expiry each receive an explicit fail-closed decision.
- [ ] Existing merge, AFK, gate, and provider grants are explicitly rejected as substitutes
      for issue-publication authority.
- [ ] The accepted decision is recorded through `to-spec`, linked from the Wayfinder, and
      narrow enough for RD-04 to implement without guessing.

## Frontier

Blocked by RD-01 and RD-02. Human confirmation is required because the choice authorizes an
external write and materially changes AFK behavior.

## Step-by-Step Implementation Plan

1. Present the research facts and prototype tradeoffs without reopening settled destination.
2. Use `grilling` to resolve grant, claim, lifecycle, and closed-match choices.
3. Restate the complete policy and obtain explicit confirmation.
4. Record the accepted decision spec and update Wayfinder ownership edges.

## Testing Plan

Validate decision completeness against every RD-02 state. No live GitHub mutation occurs in
this ticket; acceptance is the explicit human-confirmed durable decision.

## Out of Scope

- Implementing the chosen contract.
- Creating a real GitHub issue.
- Expanding beyond `carlitose/agent-skills`.

```
