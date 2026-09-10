---
type: source
title: "Add a safe human-run wizard template"
identity_key: ticket:mattpocock-skills-adoption/U-09
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/09-add-safe-wizard.md
source_digest: sha256:8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: 6a003743a1394d91
---

# Add a safe human-run wizard template

Compiled from `docs/tickets/mattpocock-skills-adoption/done/09-add-safe-wizard.md`. Identity is `ticket:mattpocock-skills-adoption/U-09`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `6a003743a1394d91`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-09.md","payload_bytes":1687,"payload_sha256":"8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351"}],"payload_bytes":1687,"payload_sha256":"8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351","schema":1,"source_digest":"sha256:8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351","source_identity":"ticket:mattpocock-skills-adoption/U-09","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1687,"payload_sha256":"8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351","schema":1,"source_digest":"sha256:8410da1bc87f3cfe5055458454817e8490212d6127c9cd2aabb1a0f0aa16d351","source_identity":"ticket:mattpocock-skills-adoption/U-09"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-09"
execution_mode: AFK
blocked_by: []
---

# Add a safe human-run wizard template

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a wizard skill, `template.sh`, and Codex metadata using stage counts instead of time estimates, hidden input for sensitive values, idempotent environment updates, and cross-platform URL opening. Live wizard execution is explicitly human-run; automated fixtures must disable provider and browser effects.

## Acceptance Criteria
- [ ] Progress uses deterministic stage counts and no duration estimate.
- [ ] Sensitive input is hidden and never echoed or embedded in test artifacts.
- [ ] Environment updates are idempotent and external/provider/browser actions require explicit human execution.
- [ ] Fixture mode proves it cannot call `gh`, a provider, or a browser.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Adapt the pinned template to local safety and portability boundaries.
2. Add a non-mutating fixture mode before any live integration path.
3. Add metadata and tests for syntax, idempotence, hidden input, and disabled side effects.

## Testing Plan
Run `bash -n`, `shellcheck` when available, static metadata/link tests, and a fixture with fake environment/provider/browser commands.

## Out of Scope
- Running a live setup wizard during AFK ticket implementation.
- Unattended `.env`, credential-store, provider, or browser mutation.

```
