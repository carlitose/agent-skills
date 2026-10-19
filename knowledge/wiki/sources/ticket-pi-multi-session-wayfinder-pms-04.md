---
type: source
title: "PMS-04 — Write the multi-session protocol into the skills"
identity_key: ticket:pi-multi-session-wayfinder/PMS-04
identity_strength: stable
source_path: docs/tickets/pi-multi-session-wayfinder/04-protocol-in-skills.md
source_digest: sha256:e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PMS-04 — Write the multi-session protocol into the skills

Compiled from `docs/tickets/pi-multi-session-wayfinder/04-protocol-in-skills.md`. Identity is `ticket:pi-multi-session-wayfinder/PMS-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-pi-multi-session-wayfinder]]
- Blocked by: [[sources/ticket-pi-multi-session-wayfinder-pms-03]] — `ticket:pi-multi-session-wayfinder/PMS-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-multi-session-wayfinder-pms-04.md","payload_bytes":1593,"payload_sha256":"e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300"}],"payload_bytes":1593,"payload_sha256":"e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300","schema":1,"source_digest":"sha256:e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300","source_identity":"ticket:pi-multi-session-wayfinder/PMS-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1593,"payload_sha256":"e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300","schema":1,"source_digest":"sha256:e3f710c28e771f8e62da479016aad4fa01f246aa9fc145e7b2ee66fb857ba300","source_identity":"ticket:pi-multi-session-wayfinder/PMS-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PMS-04"
execution_mode: AFK
blocked_by:
  - "PMS-03"
---

# PMS-04 — Write the multi-session protocol into the skills

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-04`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Destination, Decisions So Far.

## What to Build
Put the protocol confirmed in PMS-03 into the skills where a session reads it (expected: the
skills-only contract of `execute-ticket`, with a pointer from `wayfinder`), and add the rule: after a
PR is merged or closed, always remove its worktree and local branch, then fast-forward the main
checkout.

## Acceptance Criteria
- [ ] The skills-only contract states the confirmed protocol in a few rules.
- [ ] The worktree-removal rule is stated once and applies to every lane that creates a worktree.
- [ ] The Autopilot static-closure budget test still passes (the margin is small).
- [ ] Affected tests and lint pass.

## Frontier
Done: rules in the skills-only contract, pointer in wayfinder, worktree rule in the injected policy.

## Step-by-Step Implementation Plan
1. Test for the new rule text first (RED), then the skill text (GREEN).
2. Keep wording short; check the context-budget and skill-graph tests.

## Testing Plan
Extension and skill-graph tests, `test_context_budget`, `test_artifact_audit`, `npm run lint`, CI.

## Out of Scope
- Changes to pi-messenger or its pin.
- Any runner, scheduler or Crew automation.

```
