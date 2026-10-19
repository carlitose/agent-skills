---
type: source
title: "MP13-03 — Skills-only PR body"
identity_key: ticket:mattpocock-skills-1-3-parity/MP13-03
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-1-3-parity/03-skills-only-pr-body.md
source_digest: sha256:f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# MP13-03 — Skills-only PR body

Compiled from `docs/tickets/mattpocock-skills-1-3-parity/03-skills-only-pr-body.md`. Identity is `ticket:mattpocock-skills-1-3-parity/MP13-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-mattpocock-skills-1-3-parity]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-1-3-parity-mp13-03.md","payload_bytes":1927,"payload_sha256":"f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846"}],"payload_bytes":1927,"payload_sha256":"f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846","schema":1,"source_digest":"sha256:f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1927,"payload_sha256":"f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846","schema":1,"source_digest":"sha256:f25035998d5f5da6a3c242364f9283ee9dda6155ff2c83d5388dea25533ad846","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "MP13-03"
execution_mode: AFK
blocked_by: []
---

# MP13-03 — Skills-only PR body

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-03`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Decision 3.

## What to Build
Extend the short PR body of the skills-only lane, adapted from upstream `pr`: a **Summary** with
the smallest visual that makes the change clear (pseudocode, call tree, file tree, Mermaid, or a
diff sketch), **Evidence** as before/after (failing then passing check, or output), **Merge danger**
(one-way or two-way door, plus blast radius in a few words), then the existing checks and open
gates. The body stays short.

## Acceptance Criteria
- [ ] The "Separately authorized delivery" section of `execute-ticket/references/skills-only.md`
      defines the PR body template with Summary, Evidence, Merge danger, Checks, Open gates.
- [ ] It says to pick one visual (at most two) and to skip a section rather than invent evidence;
      not-run checks stay visible.
- [ ] `explain-pr`, the Verification Record, and the Autopilot PR-body contract are unchanged.

## Frontier
Ready; no blocker. Files: `execute-ticket/references/skills-only.md` only.

## Step-by-Step Implementation Plan
1. Replace "Write a short PR body (summary, checks, open gates)" with a compact template.
2. Add the one-way/two-way door definition in one sentence and credit upstream `pr`.

## Testing Plan
Run any test that reads `skills-only.md` (grep the tests for it) and the artifact audit. Manual:
write the body of this ticket's own PR with the new template.

## Out of Scope
- Screenshots or other tooling for evidence capture.
- Changes to `explain-pr`, `validate-pr`, or the Autopilot delivery body.

```
