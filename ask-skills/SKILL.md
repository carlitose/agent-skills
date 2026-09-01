---
name: "ask-skills"
description: "Route a request to the smallest composable local skill flow without duplicating orchestration or removed super-autopilot behavior."
---

# Ask Skills

Owns: routing. It does not implement ticket parsing, restate stage policy, schedule runs,
implement work, finalize runs, or manufacture approvals.

## Routing map

- Explicit request to hold, cancel, reopen, or set the administrative disposition of one
  exact ticket to `open`, `on-hold`, or `canceled`: `change-status-ticket`. This route has
  precedence over implementation only for that explicit disposition intent. “Open” means
  reopen/set disposition here, never open a file, issue, or PR.
- Loose feature, decision, diagnosis, architecture, or bug-analysis request:
  `to-spec`; add `to-tickets` only when executable slices are wanted.
- Existing spec needing executable slices: `to-tickets`.
- One canonical ticket Markdown file: resolve `TICKET_AUTOPILOT_ROOT` as the absolute
  skill root from the catalog and run
  `python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" ticket-parse
  <ticket.md>`. Hand its normalized Ticket Envelope, source artifact reference, and the
  runner CandidateRef to `execute-ticket`; do not send this single-ticket route through
  the folder scheduler.
- One already-normalized Ticket Envelope plus runner CandidateRef: `execute-ticket`
  directly.
- Legacy ticket Markdown: only the explicit `migrate` command may convert it; then use the
  canonical route above.
- Ticket folder requiring AFK orchestration: `ticket-autopilot`.
- Huge, foggy, multi-session effort or unclear frontier: `wayfinder`; use `research`,
  `prototype`, or `grilling` for its investigation tickets as appropriate.
- Hard bug needing independent cross-checks: `triangulate-diagnosis`; use `diagnose` for a
  single evidence-backed pass.
- Runner candidate or standalone PR, commit, local diff review, or user-requested review
  scope: `code-review`.
- Runner candidate or standalone PR, commit, local diff QA planning, or user-requested QA
  scope: `qa-test-plan`.
- Runtime/release claim audit: `verification-audit`.
- PR explanation from a validated bundle: `explain-pr`.
- Focused cleanup of a GREEN candidate: `code-simplification`.

Use the smallest flow that reaches the requested outcome. Do not route a single ticket
through the folder scheduler or recreate its orchestration in prose.

Bare ticket paths and requests to work on, implement, finish, or complete a ticket remain
ordinary delivery requests. Blocked, pause/unpause, stop, waiting, gated, readiness, and
lifecycle questions are not administrative dispositions: route runtime controls to Ticket
Autopilot and read-only questions to research or diagnosis. Never use
`change-status-ticket` as a generic docs-only or small-change bypass.

## Response

State the chosen skill or short composition, why it fits, and the input needed next. If the
user already supplied sufficient input, invoke the route instead of asking again.
