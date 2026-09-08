---
ticket_schema: 1
ticket_id: "OMC-02"
execution_mode: AFK
blocked_by: []
---

# Inventory active extensions and configuration

## Artifact Graph

- Artifact ID: `ticket:omicron-code:OMC-02`
- Role: `ticket`
- Parent: [Omicron Code](../../specs/omicron-code-wayfinder.md)

### Produces

- [Omicron Code extension and configuration inventory](../../research/omicron-code-extension-config-inventory.md)

## Parent Spec

[Omicron Code](../../specs/omicron-code-wayfinder.md)

## What to Build

Produce a secret-safe, exact-source inventory and ownership matrix for the active local Pi
packages/extensions and the tracked capabilities in `pi-personal-config`. Classify each
surface as product-default candidate, optional integration, development-only tool,
duplicate implementation, machine-local binding, or forbidden material. Record ownership,
source/version identity, portability, license evidence, overlap, and the intended decision
owner without copying live credentials, trust state, sessions, caches, or private content.

The report is evidence for OMC-03 and OMC-04; it must not preselect packaging or migration
policy and must not change local Pi or personal configuration.

## Acceptance Criteria

- [ ] The report binds exact snapshots for Pi settings/package declarations, the installed/local Agent Skills package, and the inspected `pi-personal-config` commit and tree.
- [ ] Every active package and extension is represented once with source, version or digest, current loader path, capability family, and ownership source.
- [ ] Overlapping implementations across installed Pi, Agent Skills, and `pi-personal-config` are identified without assuming which copy wins in Omicron.
- [ ] Each row is classified as default candidate, optional, development-only, duplicate, machine-local, or forbidden, with evidence and unresolved decision owner.
- [ ] Secrets, OAuth material, tokens, credentials, trust records, sessions, caches, private audits, and machine-specific values are excluded or represented only by safe category and digest metadata.
- [ ] License and redistribution status is cited where observable and marked unresolved rather than guessed where absent.
- [ ] Portability constraints cover macOS, Linux, Windows, interactive/print/JSON/RPC/SDK use where the source exposes relevant behavior.
- [ ] Readback proves that inspected local settings, package declarations, extensions, and `pi-personal-config` tracked files were not mutated.

## Frontier

Ready. It runs in parallel with OMC-01. Both reports must be terminal before OMC-03 may
materialize a disposable composition prototype.

## Step-by-Step Implementation Plan

1. Freeze safe identities for the active Pi package/extension declarations, local Agent Skills source, and `pi-personal-config` repository.
2. Enumerate capability families and ownership without reading or recording secret values or private runtime content.
3. Build the classification, overlap, portability, license, and decision-owner matrices.
4. Record forbidden and machine-local boundaries explicitly, including any data that could not be safely inspected.
5. Recompute source digests/readbacks and validate that the inventory is complete, deduplicated, and non-mutating.

## Testing Plan

- Compare enumerated package/extension rows against sanitized loader declarations and tracked manifests.
- Recompute repository commit/tree and safe file digests before and after inspection.
- Run redaction checks that reject credential-like values, raw trust/session/cache content, and unapproved absolute machine paths from the report.
- Resolve all repository citations and Artifact Graph links; report unavailable license or runtime evidence explicitly.

## Out of Scope

- Copying extensions or configuration into a fork.
- Selecting product defaults, package scope, migration behavior, or repository visibility.
- Editing Pi settings, installing/uninstalling packages, updating Pi, or changing `pi-personal-config`.
- Reading or preserving secret values, session bodies, trust decisions, caches, or private audit data.
