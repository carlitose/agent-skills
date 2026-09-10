---
type: source
title: "Implement audited runner-defect issue escalation"
identity_key: ticket:ticket-autopilot-runner-defect-issues/RD-04
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-issues/done/04-implement-audited-runner-defect-issue-escalation.md
source_digest: sha256:ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-31
disposition_changed_provenance: git-rename
run_id: runner-defect-issues-20260829
---

# Implement audited runner-defect issue escalation

Compiled from `docs/tickets/ticket-autopilot-runner-defect-issues/done/04-implement-audited-runner-defect-issue-escalation.md`. Identity is `ticket:ticket-autopilot-runner-defect-issues/RD-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-31** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-issue-wayfinder]]
- Blocked by: [[sources/ticket-ticket-autopilot-runner-defect-issues-rd-03]] — `ticket:ticket-autopilot-runner-defect-issues/RD-03`

## Run

Completed under autopilot run `runner-defect-issues-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-issues-rd-04.md","payload_bytes":2890,"payload_sha256":"ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d"}],"payload_bytes":2890,"payload_sha256":"ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d","schema":1,"source_digest":"sha256:ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2890,"payload_sha256":"ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d","schema":1,"source_digest":"sha256:ad698d61c25c2cbd4e1fb54abd56402562fbab8f8c0f73b6b7969d80a4eb988d","source_identity":"ticket:ticket-autopilot-runner-defect-issues/RD-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RD-04"
execution_mode: AFK
blocked_by:
  - "RD-03"
---

# Implement audited runner-defect issue escalation

## Artifact Graph

- Artifact ID: `artifact:rd-04-implement-audited-runner-defect-issue-escalation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Implement the RD-03 contract as an orthogonal runner escalation lifecycle: eligible defect
record, secret-safe renderer, stable fingerprint, audited grant, local reservation/outbox,
GitHub exact-repository search/create/readback, and replay-safe receipt. Preserve every
existing ticket, gate, verification, delivery, and merge invariant.

## Acceptance Criteria

- [ ] The command and ledger schemas are versioned and reject missing, stale, ambiguous, or
      unredacted defect records and grants.
- [ ] Only the exact `carlitose/agent-skills` target is accepted, and provider capability
      negotiation fails before mutation when issue operations are unavailable.
- [ ] An exact fingerprint match deduplicates without a comment, reopen, label, or second
      issue mutation.
- [ ] Create and readback receipts bind repository, issue number, URL, fingerprint, sanitized
      body hash, actor, authority, and provider evidence.
- [ ] Crash and lost-response tests prove at-most-once observable creation or a durable
      ambiguous gate; no replay silently duplicates an issue.
- [ ] Escalation failure never changes the underlying ticket state, passes a gate, edits the
      ledger outside canonical transitions, or authorizes merge.
- [ ] Skill and operator docs explain opt-in, dry-run, redaction, dedupe, revocation, and
      recovery.

## Frontier

Blocked by RD-03. It becomes AFK-ready only after the external publication policy is accepted.

## Step-by-Step Implementation Plan

1. Add normalized contracts and canonical ledger transitions for grant, reservation, and receipt.
2. Add GitHub provider operations with exact-repository guards, search, create, and readback.
3. Connect eligible diagnoses at the accepted runner seam without changing run outcome state.
4. Add redaction, dedupe, crash, permission, ambiguity, and invariant regression tests.
5. Update skill and operator documentation and validate migrations or fail-closed compatibility.

## Testing Plan

Use fake-provider causal tests, disposable repositories, schema/ledger invariant tests, secret
fixtures, crash injection, and full runner regressions. Live provider behavior remains RD-05.

## Out of Scope

- Automatic fixing or merging of the reported bug.
- Commenting, closing, reopening, assigning, or triaging existing issues.
- Reporting project-owned candidate failures.

```
