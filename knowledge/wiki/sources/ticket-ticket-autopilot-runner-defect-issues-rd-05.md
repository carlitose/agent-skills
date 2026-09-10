---
type: source
title: "Forward-test live GitHub issue idempotency"
identity_key: ticket:ticket-autopilot-runner-defect-issues/RD-05
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-issues/05-forward-test-live-github-issue-idempotency.md
source_digest: sha256:83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-08-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Forward-test live GitHub issue idempotency

Compiled from `docs/tickets/ticket-autopilot-runner-defect-issues/05-forward-test-live-github-issue-idempotency.md`. Identity is `ticket:ticket-autopilot-runner-defect-issues/RD-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-issue-wayfinder]]
- Blocked by: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-04]] — `ticket:ticket-autopilot-runner-defect-issues/RD-04`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-issues-rd-05.md","payload_bytes":2555,"payload_sha256":"83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536"}],"payload_bytes":2555,"payload_sha256":"83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536","schema":1,"source_digest":"sha256:83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2555,"payload_sha256":"83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536","schema":1,"source_digest":"sha256:83894f26c8c2ec7d2cfd212d4a3424a0cdb7f0a573c61cf33dc2e151187b0536","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RD-05"
execution_mode: HITL
blocked_by:
  - "RD-04"
---

# Forward-test live GitHub issue idempotency

## Artifact Graph

- Artifact ID: `artifact:rd-05-forward-test-live-github-issue-idempotency`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

With explicit live-boundary authorization, run one controlled synthetic runner-defect
escalation against `carlitose/agent-skills`, verify the created or deduplicated issue and
receipt, then replay the same fingerprint to prove no second external mutation occurs.

## Acceptance Criteria

- [ ] The user authorizes the exact repository, sanitized issue preview, and test fingerprint
      before the first provider mutation.
- [ ] Live readback binds issue number, URL, body hash, fingerprint marker, repository, and
      provider identity to the durable receipt.
- [ ] Replaying the exact defect observes the same issue and performs no second create,
      comment, reopen, close, label, or assignment mutation.
- [ ] Permission denial, ambiguous search, and unavailable API behavior remain separately
      gated or explicitly unobserved; local fakes cannot upgrade those live claims.
- [ ] The test issue receives the user-confirmed cleanup recommendation; cleanup itself is
      not performed without separate authorization.
- [ ] The Wayfinder records live evidence, residual limits, and whether the destination is
      reached or another bounded ticket is required.

## Frontier

Blocked by RD-04 and by explicit human authorization for the exact live GitHub mutation.

## Step-by-Step Implementation Plan

1. Render and validate the synthetic sanitized issue preview and exact fingerprint.
2. Obtain explicit live-boundary authorization and execute one create-or-dedupe attempt.
3. Read back the provider issue and validate the durable receipt.
4. Replay the same input, prove no second mutation, and record limitations and cleanup advice.

## Testing Plan

Run the production dry-run first, then one authorized live provider scenario and an exact
replay. Capture only sanitized status, IDs, hashes, and URLs; never credentials or headers.

## Out of Scope

- Testing with a real private bug or raw production ledger.
- Closing or deleting the test issue without separate authorization.
- Claiming non-GitHub provider support.

```
