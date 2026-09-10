---
type: source
title: "Redact diagnostic evidence"
identity_key: ticket:mattpocock-skills-adoption/U-01
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/01-redact-diagnostic-evidence.md
source_digest: sha256:3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: faad3c316f8f4afd
---

# Redact diagnostic evidence

Compiled from `docs/tickets/mattpocock-skills-adoption/done/01-redact-diagnostic-evidence.md`. Identity is `ticket:mattpocock-skills-adoption/U-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `faad3c316f8f4afd`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-01.md","payload_bytes":1682,"payload_sha256":"3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a"}],"payload_bytes":1682,"payload_sha256":"3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a","schema":1,"source_digest":"sha256:3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a","source_identity":"ticket:mattpocock-skills-adoption/U-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1682,"payload_sha256":"3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a","schema":1,"source_digest":"sha256:3858131ba05df386dfb9e4ca58db14834ffb747f27b4120505c24fc1cbaf890a","source_identity":"ticket:mattpocock-skills-adoption/U-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-01"
execution_mode: AFK
blocked_by: []
---

# Redact diagnostic evidence

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add secret-redaction rules to `diagnose` for displayed commands, outputs, and captured artifacts while retaining its single-diagnosis ownership. Touch `triangulate-diagnosis` only if shared handoff wording must point to the same redaction boundary.

## Acceptance Criteria
- [ ] Credentials, tokens, secrets, and secret-bearing command arguments are redacted before display or durable capture.
- [ ] The contract preserves useful non-secret diagnostic evidence and gates when only a redacted artifact can be requested safely.
- [ ] Static fixtures cover representative command, log, and artifact examples without embedding a real secret.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Inventory the evidence surfaces owned by `diagnose` and define one explicit redaction invariant.
2. Update the skill and only directly shared references without expanding diagnostic orchestration.
3. Add causal static fixtures that fail on unredacted examples and pass on safe placeholders.

## Testing Plan
Run the focused skill-contract tests and repository link/frontmatter checks. Record that no external secret store or live credential was exercised.

## Out of Scope
- Replacing `diagnose` or `triangulate-diagnosis` ownership.
- Collecting, printing, or persisting a live credential.

```
