---
type: source
title: "Align TDD seam and test guidance"
identity_key: ticket:mattpocock-skills-adoption/U-03
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/03-align-tdd-guidance.md
source_digest: sha256:f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: 403b2e32460f4b18
---

# Align TDD seam and test guidance

Compiled from `docs/tickets/mattpocock-skills-adoption/done/03-align-tdd-guidance.md`. Identity is `ticket:mattpocock-skills-adoption/U-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-mattpocock-skills-adoption-u-02]] — `ticket:mattpocock-skills-adoption/U-02`

## Run

Completed under autopilot run `403b2e32460f4b18`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-03.md","payload_bytes":1644,"payload_sha256":"f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8"}],"payload_bytes":1644,"payload_sha256":"f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8","schema":1,"source_digest":"sha256:f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8","source_identity":"ticket:mattpocock-skills-adoption/U-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1644,"payload_sha256":"f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8","schema":1,"source_digest":"sha256:f0318cdecf754dd9315b859764ec21548fe75abcb0d3acc0b9cf3ab86d3165a8","source_identity":"ticket:mattpocock-skills-adoption/U-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-03"
execution_mode: AFK
blocked_by:
  - "U-02"
---

# Align TDD seam and test guidance

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Align `tdd` with pre-agreed seams and the tautological-test anti-pattern, consume the U-02 `codebase-design` vocabulary, and route post-GREEN cleanup to the existing `code-simplification` and review stages. Remove superseded local references only after every inbound link is replaced.

## Acceptance Criteria
- [ ] TDD requires an agreed seam before mocking or opens an explicit gate when the seam is material and unresolved.
- [ ] Guidance rejects tests that merely restate implementation details without causal behavior.
- [ ] Post-GREEN refactoring remains owned by the existing quality stages.
- [ ] Removed references have no remaining inbound links.

## Frontier
Dependency-blocked by U-02.

## Step-by-Step Implementation Plan
1. Map current `tdd` references to the shared U-02 vocabulary.
2. Add seam and tautological-test guidance with one causal RED/GREEN example.
3. Replace inbound links, then remove only demonstrably superseded references.
4. Verify the execute-ticket quality-stage ownership remains unchanged.

## Testing Plan
Run focused TDD/link/static-contract tests plus skill-graph ownership checks.

## Out of Scope
- Reimplementing `code-simplification`, review, or execute-ticket orchestration.
- Deleting a reference that still has an inbound consumer.

```
