---
type: source
title: "Omicron Code"
identity_key: artifact:omicron-code-wayfinder
identity_strength: stable
source_path: docs/specs/omicron-code-wayfinder.md
source_digest: sha256:eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-03
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Omicron Code

Compiled from `docs/specs/omicron-code-wayfinder.md`. Identity is `artifact:omicron-code-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-03** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-omicron-code-omc-01]]
- Child source: [[sources/ticket-omicron-code-omc-02]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-omicron-code-wayfinder.md","payload_bytes":9311,"payload_sha256":"eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148"}],"payload_bytes":9311,"payload_sha256":"eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148","schema":1,"source_digest":"sha256:eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148","source_identity":"artifact:omicron-code-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | 10: Out of Scope |
| decisions | 6: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":9311,"payload_sha256":"eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148","schema":1,"source_digest":"sha256:eb662cd6c219c1f60fa7e7d5f9f01dbcd5055bd45f6a3bc377f329a91b8c4148","source_identity":"artifact:omicron-code-wayfinder"} -->
```markdown
# Omicron Code

## Artifact Graph

- Artifact ID: `artifact:omicron-code-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [Map the upstream Pi baseline](../tickets/omicron-code/done/01-map-upstream-pi-baseline.md)
- [Inventory active extensions and configuration](../tickets/omicron-code/done/02-inventory-active-extensions-and-config.md)

## Type

Wayfinding spec.

## Status

Active. The Agent Skills repair sequence, tracked wiki update, exact-source no-diff replay,
local Pi synchronization, and user reload are terminal. OMC-01 has mapped and verified the
exact upstream baseline and is PR-open under manual merge policy. OMC-02 now has a secret-safe
inventory candidate awaiting its own quality and delivery cycle; fork implementation remains
deferred until both tickets are terminal.

## Destination

Create and maintain a fork of the Pi coding agent named **Omicron Code**. The fork must provide a coherent, installable coding-agent distribution that includes Agent Skills, the currently used Pi extensions/packages, and the extensions and profile capabilities maintained in `pi-personal-config`.

The starting assumptions are:

- upstream is the official `earendil-works/pi` repository; `v0.84.4` is the exact historical compatibility reference, while the effective local runtime and current official release observed by OMC-01 are `v0.85.0` despite Volta still labeling the installation `0.84.4`;
- `agent-skills` remains independently testable and its mandatory routing/authority rules are preserved;
- `pi-personal-config` at `$HOME/Projects/pi-personal-config` is a primary source to inventory, not content to copy blindly;
- Omicron Code initially coexists with Pi under distinct command, package, settings, cache, and session identities until migration is explicitly accepted;
- this map becomes active only after the preceding wiki update has an exact terminal receipt.

## Decisions So Far

- Product name: **Omicron Code**.
- Delivery shape: an actual Pi coding-agent fork, not a wrapper around `pi-code-tool` and not merely another personal-config package.
- Included capability families: Agent Skills; currently installed Pi extensions/packages; `pi-personal-config` extensions and profile behavior.
- Order: wiki repair and wiki update first; Omicron work afterward.
- Planning mode: wayfinding before implementation because upstream divergence, inventory ownership, distribution, migration, and security boundaries remain broad.
- Existing OpenAI service outages are operational evidence, not fork requirements.

## Evidence Acquired

OMC-01 binds the historical upstream baseline to `v0.84.4` commit
`b79e4cc834970cca69daebffab7df1da7d1e52c4` and the current official release to
`v0.85.0` commit `107d79f11072bbc8a3a757ed7fd69596bee7d68c`. Its report records the
MIT obligations, workspace package graph, build and release pipeline, public CLI/SDK and
extension seams, settings/session identities, trust and telemetry defaults, and update
boundaries. It also records the local manager/payload version disagreement without inferring
its cause.

Upstream package metadata provides deliberate rebranding seams through `piConfig.name` and
`piConfig.configDir`, but release discovery and some service/branding surfaces remain
Pi-specific. OMC-03 must therefore test a distinct `omicron` command and state root rather
than treating metadata changes as a complete fork.

OMC-02 binds live settings, `pi-personal-config`, and local Agent Skills to exact clean
snapshots. It identifies two filtered active package roots and six extension entries:
`update-plan`, Pi BTW, Context7, the local Pi Code Tool wrapper, Pi MCP Adapter, and the local
mandatory Agent Skills extension. It separates those active declarations from dormant npm
copies, records the explicit duplicate filters, marks trust/auth/session/cache/MCP-secret
material forbidden, and defers packaging, license, migration, and default-policy decisions.

## Known Source Inventory

Live `pi list` reports only `$HOME/Projects/pi-personal-config` and
`$HOME/.pi/agent/local/agent-skills` as filtered user package roots. The standalone Pi
extension directory is empty. `pi-personal-config` composes `update-plan`, Pi BTW, Context7,
the Pi Code Tool wrapper, and Pi MCP Adapter; local Agent Skills supplies the one active
mandatory routing extension while its package skill resources are disabled by filter.

The Pi npm installation inventory still contains separate copies of Pi BTW, Context7, Pi
Code Tool, Pi MCP Adapter, and inactive `pi-web-access`; absence from `pi list` makes these
unselected, not safe to delete. The tracked personal profile is not equal to live settings,
and its trust snapshot is forbidden migration material. Exact identities, ownership,
classification, license evidence, portability constraints, and open decisions are recorded
in the OMC-02 research report.

## Not Yet Specified

- Long-term rebase, cherry-pick, or dependency-update policy after the exact `v0.84.4` and `v0.85.0` baselines mapped by OMC-01.
- GitHub fork owner, repository visibility, license notices, package names, release channel, and update mechanism.
- Whether bundled third-party extensions are vendored, pinned dependencies, optional first-party modules, or an install profile.
- Which “current extensions” are product defaults versus machine-local optional integrations.
- Stable CLI binary name, npm package scope, config directory, environment variables, session format, telemetry defaults, and coexistence/migration behavior.
- How secrets, OAuth tokens, trust records, machine paths, and provider credentials are excluded from `pi-personal-config` ingestion.
- Upgrade compatibility with upstream Pi and the support window for imported sessions/settings.
- Test/release matrix across macOS, Linux, Windows, interactive, print, JSON, RPC, and SDK modes.
- Governance for syncing Agent Skills and personal extensions into the fork without creating three divergent copies.

## Out of Scope

- Fork creation before the wiki update terminal receipt.
- Copying live credentials, trust decisions, sessions, caches, machine-specific paths, or private audit data.
- Replacing the installed `pi` binary in place during discovery.
- Claiming full upstream compatibility before a versioned matrix exists.
- Treating every currently installed package as a mandatory default without classification.

## Frontier / Blocking Edges

1. **Wiki update receipt — resolved:** the cumulative tracked wiki candidate merged as commit `7230019b3475656ea7d409470a05ff22fbb26b59`, and exact-source replay reported unchanged with no changed paths.
2. **Upstream fork contract — mapped in candidate:** OMC-01 records the exact `v0.84.4` historical and `v0.85.0` current baselines, license, build, release, runtime identity, compatibility, and update seams. Its ticket lifecycle remains subject to verification and delivery.
3. **Extension/config inventory — candidate produced:** OMC-02 maps exact active roots, six extension entries, duplicate installed copies, machine-local surfaces, forbidden material, portability, licenses, and unresolved owners. Quality and delivery remain.
4. **Composition architecture** — cannot choose vendor/dependency/profile boundaries until OMC-01 and OMC-02 report. Owned by OMC-03.
5. **Product decisions** — visibility, package scope, compatibility, telemetry, and migration may require user confirmation after evidence. Owned by OMC-04.
6. **Executable fork plan** — implementation tickets wait for the accepted architecture decision. Owned by OMC-05.

## Ticket Plan

- **OMC-01 — research, AFK, candidate produced:** maps upstream Pi `v0.84.4` and current official `v0.85.0`, license, package graph, build/release, extension loader, settings/session identities, compatibility, and update seams. Output: exact primary-source research report.
- **OMC-02 — research, AFK, candidate produced:** secret-safe exact inventory and ownership matrix for active Pi packages/extensions and `pi-personal-config`, including default-candidate, optional, development-only, duplicate, machine-local, and forbidden classifications. Output: inventory report.
- **OMC-03 — prototype, AFK, blocked by OMC-01 and OMC-02:** compare vendored, dependency-composed, and profile-distributed architectures in a disposable fork; prove distinct `omicron` identity and one representative extension from each source. Output: prototype and measurements.
- **OMC-04 — decision, HITL if evidence leaves material alternatives, blocked by OMC-03:** select repository visibility, distribution, compatibility, telemetry, update, extension ownership, and migration policy. Use `grilling` only for unresolved product choices.
- **OMC-05 — task decomposition, AFK, blocked by OMC-04:** create the versioned implementation spec and tracer-bullet tickets for the fork, CI, packaging, migration, documentation, and rollout.

OMC-01 and OMC-02 are emitted at activation as the first parallel frontier. OMC-03 through
OMC-05 remain planned but un-emitted until their declared predecessors are terminal.

## Next Review

Integrate OMC-01 only under its exact-head manual authority, verify and deliver OMC-02, then
confirm both reports are terminal before activating OMC-03. Do not start production fork
implementation yet.

```
