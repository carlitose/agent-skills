# Omicron Code

## Artifact Graph

- Artifact ID: `artifact:omicron-code-wayfinder`
- Role: `wayfinder`
- Standalone: true

## Type

Wayfinding spec.

## Status

Deferred until the Agent Skills wiki adoption and tracked wiki update are complete.

## Destination

Create and maintain a fork of the Pi coding agent named **Omicron Code**. The fork must provide a coherent, installable coding-agent distribution that includes Agent Skills, the currently used Pi extensions/packages, and the extensions and profile capabilities maintained in `pi-personal-config`.

The starting assumptions are:

- upstream is the official `earendil-works/pi` repository and the currently installed Pi `0.84.4` behavior is the first compatibility baseline;
- `agent-skills` remains independently testable and its mandatory routing/authority rules are preserved;
- `pi-personal-config` at `/Users/carlogiuseppesergi/Projects/pi-personal-config` is a primary source to inventory, not content to copy blindly;
- Omicron Code initially coexists with Pi under distinct command, package, settings, cache, and session identities until migration is explicitly accepted;
- this map becomes active only after the preceding wiki update has an exact terminal receipt.

## Decisions So Far

- Product name: **Omicron Code**.
- Delivery shape: an actual Pi coding-agent fork, not a wrapper around `pi-code-tool` and not merely another personal-config package.
- Included capability families: Agent Skills; currently installed Pi extensions/packages; `pi-personal-config` extensions and profile behavior.
- Order: wiki repair and wiki update first; Omicron work afterward.
- Planning mode: wayfinding before implementation because upstream divergence, inventory ownership, distribution, migration, and security boundaries remain broad.
- Existing OpenAI service outages are operational evidence, not fork requirements.

## Known Source Inventory

Current Pi configuration includes package sources for `pi-web-access`, `pi-mcp-adapter`, local filtered `agent-skills`, `@narumitw/pi-btw`, `@upstash/context7-pi`, the configured relays package, and `pi-code-tool`, plus the local `update-plan` extension.

`pi-personal-config` currently contains extension families for mandatory Agent Skills routing, `pi-code-tool` runtime/timeout configuration, and `update-plan`, together with install scripts, profile settings/trust material, and remote-TUI support. Exact ownership, duplication, portability, secrets, and license treatment still require research.

## Not Yet Specified

- Exact upstream commit/tag and long-term rebase/cherry-pick policy.
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

1. **Wiki update receipt** — blocks all Omicron execution. Unblocked when the legacy catalog repair is integrated and its separate tracked wiki candidate is terminally resolved.
2. **Upstream fork contract** — exact source revision, license, build, release, and update seams are not yet mapped. Owned by OMC-01.
3. **Extension/config inventory** — current Pi and `pi-personal-config` contain overlapping and machine-local surfaces. Owned by OMC-02.
4. **Composition architecture** — cannot choose vendor/dependency/profile boundaries until OMC-01 and OMC-02 report. Owned by OMC-03.
5. **Product decisions** — visibility, package scope, compatibility, telemetry, and migration may require user confirmation after evidence. Owned by OMC-04.
6. **Executable fork plan** — implementation tickets wait for the accepted architecture decision. Owned by OMC-05.

## Ticket Plan

- **OMC-01 — research, AFK, blocked by wiki update:** map upstream Pi `0.84.4` source, license, package graph, build/release, extension loader, settings/session identities, and update seams. Output: primary-source research report.
- **OMC-02 — research, AFK, blocked by wiki update:** produce a secret-safe exact inventory and ownership matrix for active Pi packages/extensions and `pi-personal-config`; classify default, optional, development-only, duplicate, machine-local, and forbidden material. Output: inventory report.
- **OMC-03 — prototype, AFK, blocked by OMC-01 and OMC-02:** compare vendored, dependency-composed, and profile-distributed architectures in a disposable fork; prove distinct `omicron` identity and one representative extension from each source. Output: prototype and measurements.
- **OMC-04 — decision, HITL if evidence leaves material alternatives, blocked by OMC-03:** select repository visibility, distribution, compatibility, telemetry, update, extension ownership, and migration policy. Use `grilling` only for unresolved product choices.
- **OMC-05 — task decomposition, AFK, blocked by OMC-04:** create the versioned implementation spec and tracer-bullet tickets for the fork, CI, packaging, migration, documentation, and rollout.

Tickets are intentionally not emitted until the wiki-update blocking edge is resolved.

## Next Review

After the wiki candidate is terminal, verify the latest upstream Pi release and inspect `pi-personal-config` through the secret-redaction boundary. Then emit OMC-01 and OMC-02 as the first parallel frontier; do not start fork implementation yet.
