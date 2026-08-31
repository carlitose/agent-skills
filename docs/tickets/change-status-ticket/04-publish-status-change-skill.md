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
