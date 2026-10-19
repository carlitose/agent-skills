---
type: source
title: "SLH-01 — Short skills-only handoff instead of a full Verification Record"
identity_key: ticket:skills-only-light-handoff/SLH-01
identity_strength: stable
source_path: docs/tickets/skills-only-light-handoff/01-short-handoff.md
source_digest: sha256:9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SLH-01 — Short skills-only handoff instead of a full Verification Record

Compiled from `docs/tickets/skills-only-light-handoff/01-short-handoff.md`. Identity is `ticket:skills-only-light-handoff/SLH-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-skills-only-light-handoff]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-skills-only-light-handoff-slh-01.md","payload_bytes":1644,"payload_sha256":"9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832"}],"payload_bytes":1644,"payload_sha256":"9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832","schema":1,"source_digest":"sha256:9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832","source_identity":"ticket:skills-only-light-handoff/SLH-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1644,"payload_sha256":"9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832","schema":1,"source_digest":"sha256:9e6766398235b15a482ed2f61a49435ff2d7d708839e8188aa6af405332e1832","source_identity":"ticket:skills-only-light-handoff/SLH-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SLH-01"
execution_mode: AFK
blocked_by: []
---

# SLH-01 — Short skills-only handoff instead of a full Verification Record

## Artifact Graph
- Artifact ID: `artifact:skills-only-light-handoff-slh-01`
- Role: `ticket`
- Parent: [skills-only-light-handoff.md](../../specs/skills-only-light-handoff.md)

## Parent Spec
[skills-only-light-handoff.md](../../specs/skills-only-light-handoff.md): Target behavior, Invariants.

## What to Build
Define the short handoff note in the skills-only contract, make the full Verification Record and
`explain-pr` opt-in for skills-only, and state it in the injected policy, `execute-ticket`,
`verification-audit`, `explain-pr` and `README.md`.

## Acceptance Criteria
- [ ] The skills-only contract defines the note fields and when a full record is required.
- [ ] The injected policy says skills-only ends with the short note, full record only on the listed triggers.
- [ ] `execute-ticket`, `verification-audit` and `explain-pr` describe the same split.
- [ ] Failed, skipped and not-run checks, exact-head CI and provider readback stay required.
- [ ] Extension tests cover the new text; lint passes.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Extension tests first (RED), then policy and skills-only contract (GREEN).
2. Align `execute-ticket`, `verification-audit`, `explain-pr`, `README.md`.
3. Run extension tests, skill-graph tests and lint.

## Testing Plan
`node --test extensions/mandatory-agent-skills.test.ts`; skill-graph unit tests; `npm run lint`; CI.

## Out of Scope
- Verification contract code and schema; Autopilot; historical bundles.

```
