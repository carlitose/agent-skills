---
ticket_schema: 1
ticket_id: "CBF-01"
execution_mode: AFK
blocked_by: []
---

# CBF-01 — Recognize prose findings safely

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-review-findings-01`
- Role: `ticket`
- Parent: [ticket-driver-review-findings.md](../../specs/ticket-driver-review-findings.md)

## Parent Spec
[ticket-driver-review-findings.md](../../specs/ticket-driver-review-findings.md)

## What to Build
In `ticket-driver/scripts/findings.py` and the reviewer prompt, recognize explicit severity/path/explanation review lines in the three observed prose forms while keeping malformed or contradictory review text fail-closed. The parser is shared by c1b, c2 and risk-directed review; do not relax safety or alter the QA-command limit.

## Acceptance Criteria
- [ ] Canonical lines and structurally representative variants from c1b-r1/r2/r3 produce findings with original severity, first source path, original line or `None`, and nonempty text.
- [ ] A blocker found in a bold, multi-path line still triggers the existing blocker path. Multiple findings preserve order and no severity is silently dropped.
- [ ] Fenced examples and `No blockers` never become findings or `clean`; exact `No findings.` is clean only without any severity marker, and a malformed marked line remains `unparsed` even when a clean marker or another valid finding is present.
- [ ] Prompt allows normal prose but asks reviewers to use explicit severity/path/explanation lines or `No findings.`; it does not request JSON or a status schema.
- [ ] RED/GREEN causal tests, shared c1b/c2/c3 suites and the admitted local quick profile pass; no live c1b rerun is inferred from tests.

## Frontier
Ready. User explicitly requested fixing c1b. No benchmark retry is authorized by this ticket.

## Step-by-Step Implementation Plan
1. Freeze synthetic structural examples of the three review artifacts and ambiguous cases in unit tests; demonstrate RED.
2. Update parser and reviewer prompt minimally; preserve closed-on-uncertainty behavior and canonical output shape.
3. Run focused suites and admitted profile; review exact diff, QA and validate a standalone verification bundle.

## Testing Plan
Run focused parser/c1b/c2/c3 tests, graph audit and applicable local quick profile. No Jev or model network call is required. Retain failures and limitations in verification record.

## Out of Scope
- Rerunning c1b/c2b, changing old receipts, resolving c2b retry uncertainty or oversized QA plan, altering ticket-autopilot, Jev billing, authorization, or provider policy.
