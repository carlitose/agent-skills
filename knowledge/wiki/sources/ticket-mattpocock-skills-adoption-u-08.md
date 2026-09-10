---
type: source
title: "Add safe intent-based conflict resolution"
identity_key: ticket:mattpocock-skills-adoption/U-08
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/08-add-safe-conflict-resolution.md
source_digest: sha256:15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: a19d686c3a604ae0
---

# Add safe intent-based conflict resolution

Compiled from `docs/tickets/mattpocock-skills-adoption/done/08-add-safe-conflict-resolution.md`. Identity is `ticket:mattpocock-skills-adoption/U-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `a19d686c3a604ae0`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-08.md","payload_bytes":1693,"payload_sha256":"15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec"}],"payload_bytes":1693,"payload_sha256":"15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec","schema":1,"source_digest":"sha256:15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec","source_identity":"ticket:mattpocock-skills-adoption/U-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1693,"payload_sha256":"15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec","schema":1,"source_digest":"sha256:15280554870183b66afbb74d15493fc3e31eb03bbd387900159a3af26a30b8ec","source_identity":"ticket:mattpocock-skills-adoption/U-08"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-08"
execution_mode: AFK
blocked_by: []
---

# Add safe intent-based conflict resolution

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a merge-conflict resolution skill that traces both sides' intent and resolves compatible hunks with validation. Abort, staging, commit, rebase continuation, or scheduler-worktree mutation requires explicit caller authority; ambiguous incompatible intent gates.

## Acceptance Criteria
- [ ] Each resolution records both intents and verifies the combined behavior.
- [ ] Incompatible or insufficiently evidenced intent stops without destructive fallback.
- [ ] The skill never assumes authority to abort, commit, continue a rebase, or mutate a scheduler-owned worktree.
- [ ] Synthetic repository tests cover compatible, incompatible, and unauthorized operations.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Define read-only discovery and explicit mutation-authority boundaries.
2. Add the skill and metadata with hunk-by-hunk intent tracing.
3. Build synthetic conflict fixtures and prove no-commit/no-continuation defaults.

## Testing Plan
Use disposable Git repositories; compare refs, index, and worktree before rejected operations and run focused behavior checks after authorized resolution.

## Out of Scope
- Automatic commit, push, rebase continuation, or scheduler recovery.
- A blanket “never abort” or “always resolve” policy.

```
