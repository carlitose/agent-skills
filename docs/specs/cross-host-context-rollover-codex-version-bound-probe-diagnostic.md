# Cross-host Rollover Codex Version-bound Probe Diagnostic

## Artifact Graph

- Artifact ID: `artifact:cross-host-rollover-codex-version-bound-probe-diagnostic`
- Role: `spec`
- Parent: [Cross-host Context Rollover](cross-host-context-rollover-wayfinder.md)

### Children

- [CP-01 skip mismatched installed Codex probes](../tickets/codex-version-bound-schema-probe/01-skip-mismatched-installed-codex.md)

## Type

Diagnostic spec

## Status

Diagnosed — reproduced locally on 2026-08-29 with Codex CLI 0.150.1.

## Symptom

The complete cross-host prototype suite fails in
`ProjectionTests.test_available_installed_schema_matches_version_binding` whenever `codex` is
available on `PATH` but its version differs from the fixture's frozen Codex CLI 0.147.0:

```text
AssertionError: 'codex-cli 0.147.0' != 'codex-cli 0.150.1'
```

The same test skips when Codex is absent. As a result, unrelated Claude-only changes can pass
in an environment without Codex and fail merely because a newer Codex is installed.

## Expected behavior

The fixture's static binding must always be checked. The live installed-schema probe is
optional and may compare generated hashes only when the selected executable reports the exact
fixture version. An absent or different version must produce an explicit skip with both
expected and observed versions, not a failure and not an implicit fixture refresh.

## Reproduction and evidence

1. The fixture-only assertion passes and still binds `codex-cli 0.147.0`, protocol `v2`, the
   bundle SHA-256, and seven selected generated files.
2. With the normal environment, `codex --version` reports `codex-cli 0.150.1`; the probe fails
   at the version assertion before generating or comparing schemas.
3. With Codex absent from `PATH`, the same probe records one skip and the fixture-only assertion
   passes.
4. Generating the 0.150.1 schema produces bundle SHA-256
   `e9bad0a20736e7d3aba18c0f04bef59856fb212ae21049fe17d786682203cfae` and 364 v2 files, while
   the frozen 0.147.0 fixture records bundle SHA-256
   `babfd5c98cd978dd858b4762cdfbc9fba941e1a0e4053de0050e4082ae1f075a` and seven selected
   files. The difference is expected version drift, not evidence that the fixture is corrupt.

## Root cause

The probe uses `shutil.which("codex")` as its only selection predicate. Availability proves
that some Codex executable exists, but the assertions that follow require the exact 0.147.0
executable used to create the fixture. The test therefore treats an environmental
non-applicability condition as a product regression.

The static test already owns fixture integrity. The live probe's distinct responsibility is
to re-observe the bound hashes when the exact generating version is available. Mixing those
responsibilities makes the full suite depend on whichever Codex release happens to be first on
`PATH`.

This is a test-harness bug in the cross-host prototype, not a `ticket-autopilot` runner bug and
not evidence that Codex 0.150.1 violates the 0.147.0 contract. Confidence is high because both
environment branches reproduce deterministically and the failure precedes schema comparison.

## Fix contract

Add one explicit version-bound selection seam for the optional installed-schema probe:

- no executable: skip with an unavailable reason;
- executable reports a version other than `generated_schema.installed_cli`: skip with expected
  and observed versions;
- exact version: generate the schema and retain every current bundle and per-file hash check;
- version-command or schema-generation failures for an exact selected executable remain test
  failures.

Add deterministic tests for absent, mismatched, and exact-version selection so the behavior
does not depend on the developer machine. Preserve the fixture-only assertions and do not
regenerate, weaken, or relabel the 0.147.0 evidence.

## Alternatives ruled out

- **Regenerate the fixture for every installed release.** Rejected because it destroys the
  frozen evidence boundary and turns an incidental local update into a semantic change.
- **Remove the live probe.** Rejected because exact-version schema regeneration is useful when
  the bound executable is available.
- **Accept any version whose generated schema happens to match.** Rejected because the artifact
  explicitly claims a version-bound source and must not infer cross-version equivalence.
- **Make every version mismatch fail.** Rejected because the repository does not provision
  Codex 0.147.0 as a mandatory test dependency; absence already means the probe is optional.

## Verification target

The regression is complete when an injected 0.150.1 observation yields a clear skip without
schema generation, an injected exact 0.147.0 observation retains the hash comparisons, the
real ambient 0.150.1 run skips, and the complete cross-host prototype suite passes with only
the declared optional probe skipped.
