---
type: source
title: "Bytecode caches are not skill drift"
identity_key: spec:pi-sync-bytecode-drift
identity_strength: stable
source_path: docs/specs/pi-sync-bytecode-drift.md
source_digest: sha256:8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-30
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Bytecode caches are not skill drift

Compiled from `docs/specs/pi-sync-bytecode-drift.md`. Identity is `spec:pi-sync-bytecode-drift`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-30** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-pi-sync-bytecode-drift-pbd-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[5],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/spec-pi-sync-bytecode-drift.md","payload_bytes":1593,"payload_sha256":"8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98"}],"payload_bytes":1593,"payload_sha256":"8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98","schema":1,"source_digest":"sha256:8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98","source_identity":"spec:pi-sync-bytecode-drift","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 5: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1593,"payload_sha256":"8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98","schema":1,"source_digest":"sha256:8e1f188932e42c4f76b5ef92500bc557f8beb89200460b988fd2ea8792be8c98","source_identity":"spec:pi-sync-bytecode-drift"} -->
```markdown
# Bytecode caches are not skill drift

## Artifact Graph
- Artifact ID: `spec:pi-sync-bytecode-drift`
- Role: `spec`
- Standalone: true

### Children
- [PBD-01](../tickets/pi-sync-bytecode-drift/done/01-ignore-bytecode-caches.md)

## Incident
On 2026-09-29 the personal updater of pi-personal-config (ASP-08) refused to advance the
installed skills: `Pi sync installed skill drifted: llm-wiki`. The installed `llm-wiki` and
`ticket-autopilot` skills held `__pycache__` directories that Python had written while their
scripts ran without `-B`. Without those directories all 34 owned skills matched their
manifest digests: nothing a user had changed was at risk. Removing the caches let the same
update complete and verify.

The drift check exists so an update never overwrites a skill the user edited. `_tree_digest`
counted every file, so ordinary use of an installed skill looked like an edit.

## Required behavior
- The skill digest leaves out `__pycache__` directories at any depth, for the source checkout,
  the installed skills, staged copies and backups alike.
- Any other added, removed or changed file or directory is still drift.
- A skill without `__pycache__` keeps its digest, so existing manifests stay valid.

## Verification
Test first in `ticket-autopilot/tests/test_pi_sync.py`: after an install, caches in a changed and
in an unchanged skill let the next head install; an edited file next to a cache is still refused.
Then the existing `test_pi_sync` and `test_pi_sync_windows` suites. The local update that adopts
this fix is a separate pin advance in pi-personal-config.

```
