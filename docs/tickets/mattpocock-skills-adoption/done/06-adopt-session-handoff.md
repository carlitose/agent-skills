---
ticket_schema: 1
ticket_id: "U-06"
execution_mode: AFK
blocked_by: []
---

# Adopt redacted temporary session handoff

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a session-handoff skill that writes a small pointer-based, redacted artifact in the operating-system temporary directory with explicit expiry/deletion guidance. It must not become scheduler state or a Git-tracked project artifact.

## Acceptance Criteria
- [ ] The output contract records purpose, durable pointers, remaining work, limitations, and redacted context.
- [ ] Sensitive values and unnecessary transcript content are excluded.
- [ ] Storage is temporary, untracked, and accompanied by cleanup/expiry guidance.
- [ ] Tests validate output shape and redaction without mutating runner state.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Define the minimal handoff schema and redaction boundary.
2. Add the skill and Codex metadata with an OS-temp-only workflow.
3. Test deterministic shape, pointer preservation, and cleanup guidance.

## Testing Plan
Use temporary-directory fixtures and static metadata/link checks; assert the repository and scheduler ledger remain unchanged.

## Out of Scope
- Ticket-autopilot checkpoints, resumability, or ledger ownership.
- Persisting session transcripts or secrets in Git.
