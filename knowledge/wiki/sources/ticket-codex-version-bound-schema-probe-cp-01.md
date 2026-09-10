---
type: source
title: "Skip mismatched installed Codex schema probes"
identity_key: ticket:codex-version-bound-schema-probe/CP-01
identity_strength: stable
source_path: docs/tickets/codex-version-bound-schema-probe/done/01-skip-mismatched-installed-codex.md
source_digest: sha256:e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: cp01-codex-probe-20260829
---

# Skip mismatched installed Codex schema probes

Compiled from `docs/tickets/codex-version-bound-schema-probe/done/01-skip-mismatched-installed-codex.md`. Identity is `ticket:codex-version-bound-schema-probe/CP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-cross-host-rollover-codex-version-bound-probe-diagnostic]]

## Run

Completed under autopilot run `cp01-codex-probe-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-codex-version-bound-schema-probe-cp-01.md","payload_bytes":3154,"payload_sha256":"e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b"}],"payload_bytes":3154,"payload_sha256":"e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b","schema":1,"source_digest":"sha256:e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b","source_identity":"ticket:codex-version-bound-schema-probe/CP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3154,"payload_sha256":"e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b","schema":1,"source_digest":"sha256:e0b8b73b36f97aa7ee24839428b6b5ff2fa720c6621650ce9caf7109165c053b","source_identity":"ticket:codex-version-bound-schema-probe/CP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CP-01"
execution_mode: AFK
blocked_by: []
---

# Skip mismatched installed Codex schema probes

## Artifact Graph

- Artifact ID: `artifact:cp-01-skip-mismatched-installed-codex`
- Role: `ticket`
- Parent: [Codex version-bound probe diagnostic](../../specs/cross-host-context-rollover-codex-version-bound-probe-diagnostic.md)

## Parent Spec

[Cross-host rollover Codex version-bound probe diagnostic](../../specs/cross-host-context-rollover-codex-version-bound-probe-diagnostic.md)

## What to Build

Make the optional installed Codex schema probe execute only when the selected executable
reports the exact CLI version recorded by the frozen fixture. Treat absence or a different
installed version as explicit non-applicability while preserving strict failures for an exact
version whose generated hashes drift.

## Acceptance Criteria

- [ ] The fixture-only test always checks the frozen Codex CLI 0.147.0 version, protocol,
      bundle hash, and selected file hashes independently of the local installation.
- [ ] No installed Codex executable produces an explicit skip and does not attempt schema
      generation.
- [ ] An installed executable with a version different from `generated_schema.installed_cli`
      produces an explicit skip that names the expected and observed versions and does not
      attempt schema generation.
- [ ] The exact expected version still runs schema generation and compares the bundle and
      every recorded per-file SHA-256 value.
- [ ] A version-command failure, schema-generation failure, missing generated file, or hash
      mismatch for the exact selected version remains a hard failure.
- [ ] Deterministic regressions cover absent, mismatched, and exact-version paths without
      depending on the ambient developer installation.
- [ ] The ambient Codex 0.150.1 probe skips and the complete cross-host prototype suite passes.
- [ ] No fixture, production rollover behavior, trigger threshold, or live-host claim changes.

## Step-by-Step Implementation Plan

1. Add red tests that inject an available mismatched version and prove schema generation must
   not run, plus an exact-version case that must continue through generation.
2. Extract the smallest test-side selection seam that reports the executable or an explicit
   skip reason.
3. Keep all existing exact-version schema and per-file hash assertions unchanged after the
   selection seam.
4. Run focused projection tests, the Codex prototype suite, and the complete cross-host suite
   in both ambient and Codex-absent environments.

## Testing Plan

Use `unittest.mock` or injected callables for executable discovery and version output. Assert
the skip reason, schema-generation call boundary, and exact-version hash path. Then run the real
ambient suite to prove a newer Codex installation no longer creates an unrelated failure.

## Out of Scope

- Regenerating or upgrading the Codex 0.147.0 fixture.
- Claiming schema compatibility between Codex releases.
- Changing Codex or Claude rollover runtime behavior.
- Installing or pinning a user-global Codex executable.
- Executing the CR-04 live host proof.

```
