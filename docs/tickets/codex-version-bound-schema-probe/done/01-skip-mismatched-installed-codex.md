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
