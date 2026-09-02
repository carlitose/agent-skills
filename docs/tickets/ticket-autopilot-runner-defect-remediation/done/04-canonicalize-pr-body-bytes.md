---
ticket_schema: 1
ticket_id: "RDR-04"
execution_mode: AFK
blocked_by: []
---

# Make PR-body persistence byte-stable across platforms

## Artifact Graph

- Artifact ID: `artifact:rdr-04-canonicalize-pr-body-bytes`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#203](https://github.com/carlitose/agent-skills/issues/203). Canonicalize accepted rendered Markdown to one UTF-8 LF representation before validation and hashing, persist exact bytes atomically, and use those bytes for replay and provider publication. Recover only provable legacy Windows text-mode expansion.

## Acceptance Criteria

- [ ] A platform-shaped regression fails on the current baseline with LF content plus trailing CRLF transported through the reconciliation render payload and reproduces the false persisted-body hash gate.
- [ ] One canonicalization owner converts CRLF and lone CR to LF before PR-body validation, head binding, hashing, storage, and provider publication; Unicode bytes remain exact.
- [ ] New PR-body artifacts are written and read as exact UTF-8 bytes with deterministic fsync/replace behavior and content-addressed paths matching the persisted bytes.
- [ ] Immediate readback, crash/replay, reconciliation rebind, provider body readback, and validation all use the same canonical string/bytes.
- [ ] A bounded compatibility reader accepts only a legacy Windows-expanded artifact whose deterministic reconstruction proves the recorded identity and canonical body; arbitrary byte, newline, path, hash, bundle, or head drift remains a `delivery-pr-body` failure.
- [ ] LF, CRLF, lone CR, mixed Unicode, trailing newline, no-trailing-newline, legacy recovery, and contradiction fixtures pass on every host; Windows-conditional coverage exercises real newline semantics where available.
- [ ] Delivery, reconciliation, provider-body, Windows text-fidelity, ledger replay, and full runner regressions pass.

## Frontier

Ready. The current finalizer hashes the input string but persists it with text-mode `os.fdopen(..., "w")` and reloads through universal-newline `read_text()`.

## Step-by-Step Implementation Plan

1. Add the mixed-newline reconciliation failure and exact-byte hash fixtures.
2. Introduce one canonical Markdown text/byte function at render ingestion.
3. Replace content-addressed body writes/reads with binary atomic persistence and exact decoding.
4. Add narrowly proven legacy Windows recovery without widening arbitrary drift acceptance.
5. Run focused/full finalizer, CLI, reconciliation, provider-body, Windows, compilation, diff/tree, and graph checks.

## Testing Plan

Use byte-level unit fixtures plus crash-resumable delivery/reconciliation integration with a fake provider echoing canonical body content. On Windows, assert actual artifact bytes; elsewhere, inject the Windows-expanded legacy bytes deterministically.

## Out of Scope

- Reformatting ordinary Git-tracked Markdown files.
- Repairing the malformed prose currently visible in unrelated GitHub issue bodies.
- Weakening Verification Bundle, expected-head, provider readback, or content-addressed artifact checks.
