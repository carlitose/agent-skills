---
type: source
title: "Recognize an already-delivered wiki and recover its exact failure"
identity_key: ticket:ticket-autopilot-wiki-noop-reentry/WNOP-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-wiki-noop-reentry/done/01-recognize-already-delivered-wiki.md
source_digest: sha256:644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-15
created_provenance: git-commit
disposition_changed: 2026-09-15
disposition_changed_provenance: git-rename
run_id: wnop15
---

# Recognize an already-delivered wiki and recover its exact failure

Compiled from `docs/tickets/ticket-autopilot-wiki-noop-reentry/done/01-recognize-already-delivered-wiki.md`. Identity is `ticket:ticket-autopilot-wiki-noop-reentry/WNOP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-15** via `git-commit`
- Disposition changed: **2026-09-15** via `git-rename`

## Graph

- Parent source: [[sources/spec-ticket-autopilot-wiki-noop-reentry]]

## Run

Completed under autopilot run `wnop15`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-wiki-noop-reentry-wnop-01.md","payload_bytes":3563,"payload_sha256":"644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac"}],"payload_bytes":3563,"payload_sha256":"644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac","schema":1,"source_digest":"sha256:644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac","source_identity":"ticket:ticket-autopilot-wiki-noop-reentry/WNOP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3563,"payload_sha256":"644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac","schema":1,"source_digest":"sha256:644577283de8ae1f96c4605396b826211787d28b0b1fea6c72dfd864cf8a0dac","source_identity":"ticket:ticket-autopilot-wiki-noop-reentry/WNOP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WNOP-01"
execution_mode: AFK
blocked_by: []
---

# Recognize an already-delivered wiki and recover its exact failure

## Artifact Graph
- Artifact ID: `ticket:ticket-autopilot-wiki-noop-reentry:WNOP-01`
- Role: ticket
- Parent: [Wiki no-op reentry](../../specs/ticket-autopilot-wiki-noop-reentry.md)

## Parent Spec
[Tracked wiki already-at-target delivery and exact reentry](../../specs/ticket-autopilot-wiki-noop-reentry.md).

## What to Build
Recognize an exact frozen wiki already present on the current delivery base as a validated no-op, complete the post-integration wiki effect idempotently, and add narrowly scoped recovery for the historical terminal no-Git-diff failure.

## Acceptance Criteria
- [ ] Exact already-present content yields a head/tree/candidate-bound no-op after fresh base readback, without a new commit, branch, PR, provider call or merge authorization; the protected checkout stays untouched.
- [ ] Post-integration completion is durable and repeated resume is idempotent, without claiming a new merge or transferring application verification.
- [ ] Existing retry CLI accepts only the exact integrated pre-provider no-diff failure with intact candidate and matching persisted target receipt; failed-record digest and actor/evidence bind preparation, full predecessor retention, interrupted replay and readback. Preparation remains provider-free.
- [ ] Git errors, invalid content/modes/target/receipt, base movement during no-op materialization, stale digest and prior provider/authorization evidence cannot become success. Existing non-empty delivery and historical exact retry guards remain intact.
- [ ] Operational reference documents the successful no-op and exact recovery, with focused RED/GREEN and negative-path evidence on the frozen candidate; no installed runner or BetShareMarket ledger is patched.

## Frontier
Ready. The user authorized this follow-up after BetShareMarket PR #297 integrated and its wiki hit the no-diff terminal failure. Existing repository merge authority is separate from this ticket's wiki delivery grant.

## Step-by-Step Implementation Plan
1. Reproduce no-diff delivery and retry rejection using disposable Git/frozen-candidate fixtures.
2. Implement exact no-op recognition and driver completion, preserving non-empty delivery and target/file validation.
3. Extend only the historical no-diff retry shape, validating its persisted target and preserving existing provenance/replay protocol.
4. Run focused causal and negative tests, simplify, review, plan/execute QA, and validate the frozen Verification Record.
5. Deliver through the runner, then separately validate/deliver its wiki before bundle alignment and consumer recovery.

## Testing Plan
Focused unittest entrypoints for wiki no-op, driver/retry, byte fidelity and target validation. Use real temporary Git repositories and fake provider command transports; no live provider mutation inside tests. Announce any broader checks and retain timeout/platform limitations rather than rerunning long suites per change.

## Scope
`ticket-autopilot/scripts/autopilot/wiki_sync.py`, directly related wiki tests, and `ticket-autopilot/references/wiki-delivery.md`. Tracked spec/ticket completion effects belong to the runner.

## Out of Scope
Direct consumer-ledger edits, generic reset/force recovery, fabricated empty commits/PRs, unrelated terminal failures, normal merge-policy changes, package installation or Pi reload, bookmaker/LLM traffic, credentials/deployment/DNS, and broad timeout investigation.

```
