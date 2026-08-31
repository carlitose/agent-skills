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
