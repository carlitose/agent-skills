---
type: source
title: "Publish the dedicated status-change skill and routing contract"
identity_key: ticket:change-status-ticket/CST-04
identity_strength: stable
source_path: docs/tickets/change-status-ticket/done/04-publish-status-change-skill.md
source_digest: sha256:b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: change-status-ticket-production-20260831
---

# Publish the dedicated status-change skill and routing contract

Compiled from `docs/tickets/change-status-ticket/done/04-publish-status-change-skill.md`. Identity is `ticket:change-status-ticket/CST-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-change-status-ticket]]
- Blocked by: [[sources/ticket-change-status-ticket-cst-02]] — `ticket:change-status-ticket/CST-02`
- Blocked by: [[sources/ticket-change-status-ticket-cst-03]] — `ticket:change-status-ticket/CST-03`

## Run

Completed under autopilot run `change-status-ticket-production-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-change-status-ticket-cst-04.md","payload_bytes":4170,"payload_sha256":"b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881"}],"payload_bytes":4170,"payload_sha256":"b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881","schema":1,"source_digest":"sha256:b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881","source_identity":"ticket:change-status-ticket/CST-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4170,"payload_sha256":"b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881","schema":1,"source_digest":"sha256:b6e045396396d9fc7b2f1fe03604159293a4e4198a54d586d82d16e9efba4881","source_identity":"ticket:change-status-ticket/CST-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CST-04"
execution_mode: AFK
blocked_by:
  - "CST-02"
  - "CST-03"
---

# Publish the dedicated status-change skill and routing contract

## Artifact Graph

- Artifact ID: `artifact:cst-04-status-change-skill-routing`
- Role: `ticket`
- Parent: [Change Status Ticket](../../specs/change-status-ticket.md)

## Parent Spec

[Change Status Ticket](../../specs/change-status-ticket.md)

## What to Build

Publish `change-status-ticket` as the smallest agent-facing administrative-disposition lane. Route only explicit hold, cancel, or reopen requests ahead of ordinary ticket execution; update the mandatory package policy with a narrow named lifecycle-only exception; compose the repository transaction without `execute-ticket` quality stages; and report exact terminal outcomes, gates, and non-authorities.

## Acceptance Criteria

- [ ] A new `change-status-ticket` skill accepts the exact normalized repository, ticket, disposition, actor, reason, authority, and reopen-gate inputs and delegates all state transitions to the repository transaction.
- [ ] The skill never edits the target ticket body/dependencies, implements it, invokes `execute-ticket`, invents review/QA/verification evidence, or infers user identity/authority.
- [ ] `ask-skills` gives precedence only to explicit administrative `open`, `on-hold`, `canceled`, hold, cancel, or reopen intent.
- [ ] Bare ticket paths and requests to work on/complete/implement a ticket remain on the delivery lane; blocked, pause/unpause, stop, waiting, gated, readiness, and lifecycle questions do not become dispositions.
- [ ] Mandatory workflow wording names only `change-status-ticket` as the lifecycle-only lane and creates no generic docs-only, small-change, or direct-edit exception.
- [ ] Tracked results distinguish `changed-integrated`, `merge-gated`, provider ambiguity, and terminal-proof gates; ignored results report `external-unpublished` without publication/completion claims.
- [ ] Output keeps disposition, execution lifecycle, readiness, stop reason, transaction phase, provider state, merge authority, terminal proof, and optional run projection as separate fields.
- [ ] Repeated exact requests return `already-applied`; contradictory actor/reason/authority/source/provider/terminal state fails closed.
- [ ] No disposition, merge, publication, wiki, Pi-sync, cleanup, issue, or target-ticket implementation authority is inferred from routing.
- [ ] End-to-end forward tests cover tracked/ignored, pending/active/gated/waiting, reopen, dirty target state, ambiguous provider dispatch, merge grant absence/presence, and terminal reachability using only disposable fixtures.
- [ ] Existing run-bound lifecycle commands and ordinary mandatory delivery routing remain compatible unless the user explicitly invokes administrative disposition.
- [ ] Documentation states that post-integration Pi sync and `/reload` remain separate.

## Frontier

Dependency-blocked by CST-02 and CST-03. After both runner seams integrate, skill/routing work is AFK and uses only disposable forward fixtures.

## Step-by-Step Implementation Plan

1. Add the skill contract, concise workflow, terminal report, and explicit non-authorities.
2. Extend `ask-skills` intent recognition and negative routing fixtures.
3. Add the named mandatory-policy lane without weakening the normal delivery lane.
4. Compose runner transaction phases and gate/readback reporting.
5. Add forward and extension tests across disposition, state, source mode, provider, merge, and terminal boundaries.

## Testing Plan

Use extension routing tests, skill trigger/negative fixtures, disposable repositories, fake providers, and bare remotes. Prove ordinary delivery requests remain unchanged and no live ticket/provider operation is needed. Run controlled-context and full adjacent regressions.

## Out of Scope

- Applying a real status change or manufacturing user authority.
- New disposition vocabulary, direct readiness/lifecycle editing, or cancellation cascade.
- Provider-specific skill behavior, issue close/reopen, wiki, Pi update/reload, or cleanup.
- Bypassing Ticket Autopilot's manual merge policy.

```
