---
type: source
title: "Adopt to-questionnaire with a no-send boundary"
identity_key: ticket:mattpocock-skills-adoption/U-07
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/07-adopt-to-questionnaire.md
source_digest: sha256:62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: a19d686c3a604ae0
---

# Adopt to-questionnaire with a no-send boundary

Compiled from `docs/tickets/mattpocock-skills-adoption/done/07-adopt-to-questionnaire.md`. Identity is `ticket:mattpocock-skills-adoption/U-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `a19d686c3a604ae0`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-07.md","payload_bytes":1525,"payload_sha256":"62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9"}],"payload_bytes":1525,"payload_sha256":"62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9","schema":1,"source_digest":"sha256:62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9","source_identity":"ticket:mattpocock-skills-adoption/U-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1525,"payload_sha256":"62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9","schema":1,"source_digest":"sha256:62caff07a0cb62d7669ddb62b6a51c30b220ba143e8f352f7aadb24b704645c9","source_identity":"ticket:mattpocock-skills-adoption/U-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-07"
execution_mode: AFK
blocked_by: []
---

# Adopt to-questionnaire with a no-send boundary

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add `to-questionnaire` for externalizing a decision the current user cannot answer. Require an explicit intended destination, minimize sensitive context, and render only a draft; sending remains outside the skill.

## Acceptance Criteria
- [ ] The questionnaire identifies the decision owner, destination, context, questions, and response criteria.
- [ ] It follows “grill the send, not the subject” without running a live interview itself.
- [ ] It never sends, posts, emails, or selects a recipient implicitly.
- [ ] Template and metadata tests cover redaction and the no-send boundary.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Define the draft questionnaire structure and destination requirement.
2. Add the skill and Codex metadata with sensitive-context minimization.
3. Test output shape and fail-closed behavior when destination is absent.

## Testing Plan
Run template/frontmatter/link tests with fake recipients and no connector or provider calls.

## Out of Scope
- Sending the questionnaire or contacting a third party.
- Replacing live `grilling` ownership.

```
