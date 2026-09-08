---
ticket_schema: 1
ticket_id: "OMC-01"
execution_mode: AFK
blocked_by: []
---

# Map the upstream Pi baseline

## Artifact Graph

- Artifact ID: `ticket:omicron-code:OMC-01`
- Role: `ticket`
- Parent: [Omicron Code](../../specs/omicron-code-wayfinder.md)

### Produces

- [Omicron Code upstream Pi baseline](../../research/omicron-code-upstream-pi-baseline.md)

## Parent Spec

[Omicron Code](../../specs/omicron-code-wayfinder.md)

## What to Build

Produce a primary-source research report that maps the official Pi coding-agent baseline
needed to design Omicron Code. Bind both the installed compatibility baseline (`0.84.4`)
and the current official release observed at execution time. Map source identity, license
and notice obligations, package/workspace graph, build and test entry points, publication
and update mechanisms, extension loading, settings/cache/session identities, CLI and SDK
surfaces, and the seams required for a distinct coexisting fork.

Separate observed facts from assumptions and unresolved product choices. Do not select the
fork architecture or modify, install, publish, or fork upstream software.

## Acceptance Criteria

- [ ] The report binds the official repository, exact inspected revision or tag, installed `0.84.4` baseline, current official release, and observation date.
- [ ] License, copyright, notice, package-name, binary-name, and redistribution obligations cite owning upstream files or official release metadata.
- [ ] A package/workspace map identifies production packages, internal dependencies, build outputs, tests, release commands, and version propagation.
- [ ] Extension discovery/loading and package installation are traced through owning source and tests rather than inferred from documentation alone.
- [ ] Settings, cache, sessions, environment variables, CLI binary, RPC/JSON/print modes, SDK entry points, and update behavior are mapped with exact paths or symbols.
- [ ] A coexistence table identifies which identities Omicron must separate and which formats might be shared only after an explicit compatibility decision.
- [ ] Unsupported, unavailable, or live-only behavior is recorded as unobserved; no local Pi setting, package, cache, or session is mutated.
- [ ] Every material claim cites a primary source, and commands used for reproducible inspection are recorded without credentials or machine-private data.

## Frontier

Ready. It runs in parallel with OMC-02. Both reports must be terminal before OMC-03 may
compare composition architectures.

## Step-by-Step Implementation Plan

1. Resolve the official upstream repository and record exact installed and current-release identities.
2. Inspect license, package manifests, workspace graph, build/test/release automation, and update seams at the bound revisions.
3. Trace extension loading, settings, session/cache/config identities, CLI modes, and SDK entry points through source and representative tests.
4. Build the coexistence and unresolved-question matrices without choosing an architecture.
5. Validate citations, revision bindings, reproducible commands, and the no-mutation boundary; finalize the report.

## Testing Plan

- Resolve every cited repository path and symbol against the exact inspected revisions.
- Run only read-only metadata, build-graph, or focused upstream test commands in disposable clones when needed.
- Cross-check release/version claims against both official release metadata and source manifests.
- Verify local Pi settings, package rows, sessions, caches, and installed files remain byte-identical wherever they are observed.

## Out of Scope

- Choosing vendor, dependency-composed, or profile-distributed architecture.
- Creating or publishing the Omicron repository, package, binary, or release.
- Modifying the installed Pi distribution or migrating user data.
- Copying upstream source into the Agent Skills repository.
