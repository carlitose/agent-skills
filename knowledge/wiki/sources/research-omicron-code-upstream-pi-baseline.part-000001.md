---
type: source-part
source_identity: research:omicron-code-upstream-pi-baseline
source_digest: sha256:d7e21939d36eba147c774049d493a3506d340e9c5b0075a9c5942d202d79f313
source_entry: wiki/sources/research-omicron-code-upstream-pi-baseline.md
---

# Preserved source — Part 2

Entry and provenance: [[sources/research-omicron-code-upstream-pi-baseline]]

<!-- semantic-payload-v1: {"part_index":1,"payload_bytes":5816,"payload_sha256":"e6a7ff9ace5af55a607eb1bf5a4e5eeea195fd24aa66ab5eb9a61a04d97b78b4","schema":1,"source_digest":"sha256:d7e21939d36eba147c774049d493a3506d340e9c5b0075a9c5942d202d79f313","source_identity":"research:omicron-code-upstream-pi-baseline"} -->
```markdown
## Primary Sources

All repository links below are pinned to commit
`107d79f11072bbc8a3a757ed7fd69596bee7d68c` unless they name `v0.84.4` explicitly.

- [Official repository](https://github.com/earendil-works/pi)
- [Release v0.85.0](https://github.com/earendil-works/pi/releases/tag/v0.85.0)
- [Historical tag v0.84.4](https://github.com/earendil-works/pi/tree/b79e4cc834970cca69daebffab7df1da7d1e52c4)
- [MIT license](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/LICENSE)
- [Root workspace and scripts](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/package.json)
- [Coding-agent package metadata](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/package.json)
- [Distribution configuration source](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/src/config.ts)
- [Startup distribution check](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/src/cli/startup-ui.ts)
- [Resource loader](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/src/core/resource-loader.ts)
- [Extension discovery tests](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/test/extensions-discovery.test.ts)
- [Resource loader tests](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/test/resource-loader.test.ts)
- [Package manager tests](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/test/package-manager.test.ts)
- [Git package update tests](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/test/git-update.test.ts)
- [Extension API types](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/src/core/extensions/types.ts)
- [SDK implementation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/src/core/sdk.ts)
- [Extension documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/extensions.md)
- [Package documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/packages.md)
- [Settings documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/settings.md)
- [Usage and trust documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/usage.md)
- [Session format](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/session-format.md)
- [SDK documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/sdk.md)
- [Security documentation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/packages/coding-agent/docs/security.md)
- [Release preparation](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/scripts/release.mjs)
- [Binary/release workflow](https://github.com/earendil-works/pi/blob/107d79f11072bbc8a3a757ed7fd69596bee7d68c/.github/workflows/build-binaries.yml)

Context7 was used only as a secondary documentation locator for the package; every material
claim above was checked against the pinned official repository, release metadata, or local
read-only observations.

## Observations Versus Inferences

### Directly observed

- Exact `v0.84.4` and `v0.85.0` commit/tree identities.
- Current GitHub release state and asset names.
- MIT text and coding-agent package metadata.
- Build/release scripts and workflow behavior.
- Public CLI, SDK, extension, settings, package, trust, and session contracts.
- Effective local `pi --version` of `0.85.0`.
- Volta inventory label of `0.84.4` and the three-file equality check against upstream
  `v0.85.0`.

### Bounded inferences to test

- `piConfig.name` plus `piConfig.configDir` should provide most of the required product and
  state separation, because key paths and labels derive from them.
- SDK/package composition should create less long-lived source divergence than maintaining
  edits across the complete monorepo.
- A source fork should give the strongest control over release/update/branding behavior at
  the cost of a larger upstream synchronization surface.

These are prototype hypotheses, not architecture decisions.

## Unknowns and Handoff

OMC-02 must still determine which installed and personal-config capabilities are eligible,
portable, licensed, duplicated, optional, or forbidden. After both reports are terminal,
OMC-03 should compare at least:

1. a full source-fork build;
2. a downstream coding-agent package/host using public seams; and
3. a profile-distributed composition using packages and a distinct Omicron state root.

Each prototype must be disposable and offline, use exact pinned inputs, include one
representative upstream/current extension, Agent Skills, and personal-config capability,
and report identity isolation, extension order, compatibility behavior, artifact size/build
cost, and upstream-delta burden. It must not publish a package, create a provider repository,
replace Pi, or migrate live state.

OMC-04 remains responsible for package scope, repository visibility, telemetry, update
service, supported compatibility window, migration direction, and final distribution
choice. OMC-01 supplies evidence and does not grant those decisions.

```
