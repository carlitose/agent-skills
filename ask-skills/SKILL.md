---
name: "ask-skills"
description: "Route a request to the smallest composable local skill flow without duplicating orchestration or removed super-autopilot behavior."
---

# Ask Skills

Owns: routing, not parsing, stage policy, scheduling, implementation, finalization, or approvals.

Before routing or composing skills, read the [operating defaults](OPERATING-DEFAULTS.md) for security and delegation scope.

## Routing map

First honor the user's execution lane: explicit skills-only, inline execution without the runner,
or suspension of Autopilot selects `to-spec -> to-tickets -> execute-ticket` inline.
Reuse validated artifacts via the [skills-only contract](../execute-ticket/references/skills-only.md)
for canonical inputs and separately authorized delivery. Do not start a runner, scheduler, or replacement driver.
Preserve this restriction across continuation and compaction until the user lifts it.
Autopilot routes below cannot override suspension. Missing its skill does not block inline work.

- Unambiguous affirmative “merge all”, “merge everything”, or “mergia tutto” in one known
  repository: `ticket-autopilot`, an operational repository-wide authority transaction, not
  a delivery request. Inspect `repository-autonomous-merge-status`: if authority is absent,
  use the human actor and durable affirmative message to invoke
  `grant-repository-autonomous-merge --scope current-and-future-runs`. Preserve an exact active grant
  and its provenance; fail closed on revoked, legacy, malformed, or contradictory state.
  Then invoke `merge-all`. Never ask for a caller-supplied PR head SHA or narrow intent to one PR:
  the runner discovers and revalidates every live exact head. If repository identity is
  ambiguous, ask only for that identity.
- Quoted text, examples, questions, negations, revocations, policy requests, and regression
  reports about merge-all are not merge authority. Route their actual discussion or change
  intent normally and perform no provider mutation.
- Explicit request to hold, cancel, reopen, or set the administrative disposition of one
  exact ticket to `open`, `on-hold`, or `canceled`: `change-status-ticket`. That route has
  precedence over implementation only for that explicit disposition intent, and “open” means
  reopen/set disposition, never open a file, issue, or PR.
- Loose feature, decision, diagnosis, architecture, or bug-analysis request:
  `to-spec`; add `to-tickets` only when executable slices are wanted.
- Existing spec needing executable slices: `to-tickets`.
- One canonical ticket Markdown file: normalize it through the canonical ticket contract.
  In skills-only, use its pure functions as described in the skills-only contract; otherwise
  use `ticket-parse` from the absolute `ticket-autopilot` skill root. Hand the normalized
  Ticket Envelope, source artifact reference, and current CandidateRef to `execute-ticket`.
  Do not send this single-ticket route through the folder scheduler or recreate orchestration.
- One already-normalized Ticket Envelope plus current CandidateRef: `execute-ticket` directly.
- Legacy ticket Markdown: only the explicit `migrate` command may convert it; then use the
  canonical route above.
- Ticket folder requiring AFK orchestration, when Autopilot is allowed: `ticket-autopilot`.
  In skills-only, work serially on one dependency-ready ticket at a time, using durable
  dependency evidence; do not recreate scheduler state or infer a dependency is complete.
- Huge, foggy, multi-session effort or unclear frontier: `wayfinder`; use `research`,
  `prototype`, or `grilling` for its investigation tickets as appropriate.
- Hard bug needing independent cross-checks: `triangulate-diagnosis`; use `diagnose` for a
  single evidence-backed pass.
- Runner candidate or standalone PR, commit, local diff, or user-requested scope:
  `code-review` for review, `qa-test-plan` for QA planning.
- Runtime/release claim audit: `verification-audit`.
- PR explanation from a validated bundle: `explain-pr`.
- Focused cleanup of a GREEN candidate: `code-simplification`.

Bare ticket paths and implementation/completion requests mean delivery, not disposition.
Blocked, pause/unpause, stop, waiting, gated, readiness and lifecycle questions are not
administrative dispositions: use Autopilot for runtime controls and research/diagnosis for
read-only questions. Never use `change-status-ticket` as a docs-only or small-change bypass.

## Execution defaults

After routing non-trivial work:

- If `update_plan` (Pi Plan) is available, initialize it after route selection, keep exactly one
  step `in_progress`, and finish or clear it at handoff. Reconcile it at the events named in the
  [plan review checkpoint](PLAN-REVIEW-CHECKPOINT.md).
- For research with a compatible project-bound `llm-wiki`, query it first as an index. Apply
  its RAG availability contract, state the selected query mode or fallback, and verify
  material claims against canonical pages and primary sources. Never scaffold a wiki by inference.
- When `code` from `pi-code-tool` is available, prefer it for loops, filtering, aggregation,
  repeated inspection, derived transformations and programmatic checks; use direct `edit`/`write` for authored edits.

Trivial work may omit Pi Plan and code mode. Missing tools require an explicit fallback, not
fabricated evidence. Tool availability or auto-approval grants no repository/provider authority.

## Response

State the skill/composition, why it fits and missing input; invoke it without asking again when input is sufficient.
