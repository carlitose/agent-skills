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
