---
type: source
title: "Restore natural-language repository-wide merge-all intent"
identity_key: ticket:ticket-autopilot-natural-language-merge-all-intent/MAR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-natural-language-merge-all-intent/done/01-restore-natural-language-merge-all-intent.md
source_digest: sha256:039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-04
created_provenance: git-commit
disposition_changed: 2026-09-04
disposition_changed_provenance: git-rename
run_id: ticket-autopilot-natural-language-merge-all-mar01-v2-20260904
---

# Restore natural-language repository-wide merge-all intent

Compiled from `docs/tickets/ticket-autopilot-natural-language-merge-all-intent/done/01-restore-natural-language-merge-all-intent.md`. Identity is `ticket:ticket-autopilot-natural-language-merge-all-intent/MAR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-04** via `git-commit`
- Disposition changed: **2026-09-04** via `git-rename`

## Graph

- Parent source: [[sources/spec-ticket-autopilot-natural-language-merge-all-intent]]

## Run

Completed under autopilot run `ticket-autopilot-natural-language-merge-all-mar01-v2-20260904`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-natural-language-merge-all-intent-mar-01.md","payload_bytes":4472,"payload_sha256":"039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34"}],"payload_bytes":4472,"payload_sha256":"039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34","schema":1,"source_digest":"sha256:039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34","source_identity":"ticket:ticket-autopilot-natural-language-merge-all-intent/MAR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4472,"payload_sha256":"039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34","schema":1,"source_digest":"sha256:039fda88ebb7774e4393eb483caa2936ee66b4416c2ef1754df49735b6522b34","source_identity":"ticket:ticket-autopilot-natural-language-merge-all-intent/MAR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "MAR-01"
execution_mode: AFK
blocked_by: []
---

# Restore natural-language repository-wide merge-all intent

## Artifact Graph

- Artifact ID: `artifact:ticket-ticket-autopilot-natural-language-merge-all-intent-mar-01`
- Role: `ticket`
- Parent: [Natural-language repository-wide merge-all intent](../../specs/ticket-autopilot-natural-language-merge-all-intent.md)

## Parent Spec

[Natural-language repository-wide merge-all intent](../../specs/ticket-autopilot-natural-language-merge-all-intent.md)

## What to Build

Restore the agent-facing route for an unambiguous affirmative repository-wide “merge all” imperative. The route must use Ticket Autopilot’s existing repository-wide `current-and-future-runs` grant and `merge-all` flow without asking the operator for a PR head SHA, while keeping quoted text, examples, questions, negations, revocations, policy requests, and regression reports outside provider authority.

## Acceptance Criteria

- [ ] `ask-skills` routes an unambiguous affirmative “merge all”, “merge everything”, or “mergia tutto” for one known repository to Ticket Autopilot’s repository-wide grant followed by `merge-all`.
- [ ] The route uses the human actor and durable affirmative-message evidence and never requests a caller-supplied PR head SHA; Ticket Autopilot continues discovering and revalidating each exact live head.
- [ ] Quoted text, examples, questions, negations, revocations, policy/change requests, and regression reports do not create merge authority or provider mutation.
- [ ] Ambiguous repository identity asks only for repository disambiguation; it does not infer a repository or narrow the request to one displayed PR.
- [ ] Mandatory workflow policy and Ticket Autopilot operator guidance preserve the same classification and state that merge authority grants no conflict resolution, force push, code change, publication, wiki, Pi-sync, cleanup, visibility, or history-rewrite authority.
- [ ] Existing schema-2 repository authority, live expected-head revalidation, revocation, conflicts, and non-merge gates remain unchanged and covered by tests.
- [ ] The parent wayfinder records MAR-01’s current frontier without claiming its wiki or local-Pi projections are complete.

## Frontier

Ready. WCA-01 and MRA-01 code and separately protected wiki projections have terminal receipts. No human product decision is required; this bug report itself is not live merge-all authority.

## Step-by-Step Implementation Plan

1. Add a narrow repository-wide affirmative-intent route and explicit non-authority boundary to `ask-skills` without duplicating Ticket Autopilot orchestration.
2. Add the same durable classification to the mandatory workflow policy, preserving its existing manual-authority and delivery-lane rules.
3. Clarify Ticket Autopilot operator guidance: the runner owns live head discovery/revalidation and no caller-supplied head is needed for repository-wide authority.
4. Update the repair wayfinder frontier for MAR-01 while preserving separate wiki, Pi-sync, reload, reconciliation, and conflict gates.
5. Add static and behavioral regression tests for positive multilingual imperatives and quoted, descriptive, negative, revocation, ambiguity, and regression-report cases.
6. Run focused extension and contract tests, repository-authority tests, context budgets, the full relevant suites, compile checks, `git diff --check`, and Artifact Graph audit.

## Testing Plan

- Static contract tests for `ask-skills` and Ticket Autopilot guidance.
- Mandatory extension tests for affirmative route wording, no-SHA behavior, non-authority boundaries, and unchanged ordinary natural-language routing.
- Existing repository merge/reconciliation authority and CLI tests for live-head, grant, revocation, conflict, and non-merge gates.
- Context-budget, TypeScript extension, full Ticket Autopilot, compile, diff, and Artifact Graph checks.
- No live provider mutation is required or authorized by implementation testing.

## Out of Scope

- Changing runner merge algorithms, expected-head checks, repository authority schemas, reconciliation, or provider adapters.
- Resolving conflicts, force-pushing, publishing sources or wiki candidates, synchronizing Pi, reloading sessions, changing visibility, deleting branches/worktrees, or rewriting history.
- Treating this ticket, its tests, or the originating bug report as a live repository-wide merge instruction.

```
