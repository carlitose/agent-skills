# Omicron Code Upstream Pi Baseline

## Artifact Graph

- Artifact ID: `research:omicron-code-upstream-pi-baseline`
- Role: `research`
- Parent: [OMC-01 — Map the upstream Pi baseline](../tickets/omicron-code/done/01-map-upstream-pi-baseline.md)

## Status

Complete for the OMC-01 research candidate. Ticket verification, delivery, and integration
remain separate lifecycle stages.

## Bounded Question

Which exact upstream Pi source, license, package, build, release, extension, settings,
session, update, CLI, and SDK contracts form the evidence baseline for a distinct,
coexisting Omicron Code fork?

## Answer in Brief

The official upstream is `https://github.com/earendil-works/pi`. The ticket's historical
compatibility reference is tag `v0.84.4`, commit
`b79e4cc834970cca69daebffab7df1da7d1e52c4`, but the current official release observed
for this report is `v0.85.0`, commit `107d79f11072bbc8a3a757ed7fd69596bee7d68c`.
The effective local executable also reports `0.85.0`, although Volta's package inventory
still labels its installation `0.84.4`. Omicron Code must therefore preserve both exact
references in compatibility evidence and must not call the stale Volta label the effective
runtime version.

Upstream already exposes useful distribution seams through coding-agent package metadata:
`piConfig.name` controls the application name, `piConfig.configDir` controls the global and
project configuration namespace, and the derived environment variables and most user-facing
labels follow those values. The public SDK and extension API provide a lower-divergence
composition seam. These facts make a distinct `omicron` command and state root feasible,
but they do not by themselves choose between a source fork, a downstream package, or a
profile distribution. Update discovery still targets `https://pi.dev/api/latest-version`,
some Pi-specific endpoints and strings remain, and extensions/packages run with full user
process authority. OMC-03 must exercise these boundaries rather than assume rebranding is
complete.

## Evidence Boundary and Method

Research was read-only. It did not install, update, execute, or modify upstream packages;
did not alter local Pi settings, sessions, caches, or extensions; and did not inspect
credential values. The upstream clone was an inspection-only partial clone below the
operating system's temporary directory (`${TMPDIR:-/tmp}/earendil-works-pi-omc01`).

The following primary evidence was observed on 2026-09-04:

| Evidence | Exact identity |
|---|---|
| Historical ticket baseline | `v0.84.4`; commit `b79e4cc834970cca69daebffab7df1da7d1e52c4`; tree `e036f454021bdaa07b53afb7ee7ed600b0dbc823` |
| Current official release | `v0.85.0`; commit `107d79f11072bbc8a3a757ed7fd69596bee7d68c`; tree `f5103239060686ea2983e18906857b3df54428f5` |
| Release publication | `v0.85.0`, non-draft, non-prerelease; published `2026-09-04T10:18:28Z` |
| Effective local executable | `$HOME/.volta/bin/pi`; `pi --version` returned `0.85.0` |
| Local package payload | `@earendil-works/pi-coding-agent` package metadata reports `0.85.0` under the Volta image |
| Volta inventory label | `@earendil-works/pi-coding-agent@0.84.4` with Node `24.16.0` |

The local package metadata, `docs/extensions.md`, and `docs/packages.md` SHA-256 values
matched the same three files at upstream `v0.85.0`:

| File | SHA-256 |
|---|---|
| `packages/coding-agent/package.json` | `1dba78e1dee92c7ea4d0997d815a390ad5bfaf47ea5ada6f71818d01e97a70dc` |
| `packages/coding-agent/docs/extensions.md` | `39c54b91faabd76a17ab07f7ae85b274e941f36aacfaa6fe304281f697671faf` |
| `packages/coding-agent/docs/packages.md` | `1067eae058c5ce980a21b04c51ce6d38e201e51197807037d0a063ac3c769b46` |

A final readback returned the same three package hashes and the effective/manager version
values. The local Pi settings file was not parsed; its SHA-256 remained
`a9de95dbf39b24f7f8a08a699e05a650584cdbfa64f93af9d949259e69c0c8f8`, the
same exact digest recorded before this research began. Sessions, package caches, trust
records, and credentials were not traversed. This is evidence for the observed files only,
not a claim that every installed byte equals the upstream release. The Volta/payload
version disagreement is observed; its cause was not established and must not be inferred.

### Reproducible inspection commands

These are the read-only command shapes used. Variables deliberately replace the inspecting
machine's user-specific path. The GitHub API call targets public release metadata and no
credential value was supplied or printed.

```bash
UPSTREAM="${TMPDIR:-/tmp}/earendil-works-pi-omc01"
git clone --filter=blob:none https://github.com/earendil-works/pi.git "$UPSTREAM"
git -C "$UPSTREAM" fetch origin refs/tags/v0.84.4 refs/tags/v0.85.0
git -C "$UPSTREAM" checkout --detach v0.85.0
git -C "$UPSTREAM" rev-parse HEAD^{commit} HEAD^{tree}
git -C "$UPSTREAM" rev-parse v0.84.4^{commit} v0.84.4^{tree}
git -C "$UPSTREAM" diff --shortstat v0.84.4..v0.85.0
git -C "$UPSTREAM" diff --name-only v0.84.4..v0.85.0 -- packages/coding-agent
gh api repos/earendil-works/pi/releases/latest

type -a pi
command -v pi
pi --version
volta list pi
volta list @earendil-works/pi-coding-agent
volta which pi

LOCAL_PACKAGE="$HOME/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent"
node -p "require('$LOCAL_PACKAGE/package.json').version"
shasum -a 256 \
  "$LOCAL_PACKAGE/package.json" \
  "$LOCAL_PACKAGE/docs/extensions.md" \
  "$LOCAL_PACKAGE/docs/packages.md"
shasum -a 256 \
  "$UPSTREAM/packages/coding-agent/package.json" \
  "$UPSTREAM/packages/coding-agent/docs/extensions.md" \
  "$UPSTREAM/packages/coding-agent/docs/packages.md"
```

The report also used `git show`, `git diff`, `rg`, and read-only file inspection inside the
same pinned clone to trace the cited manifests, source symbols, workflow, and tests. No
upstream test suite was executed: source and representative test contracts were inspected,
while runtime behavior requiring installation, a model/provider, or user state remains
unobserved.

## Repository, License, and Attribution

### Observed

- The official repository is `earendil-works/pi`.
- The root `LICENSE` is the MIT License, copyright 2025 Mario Zechner.
- `packages/coding-agent/package.json` declares `license: "MIT"`, identifies the same
  repository and package directory, and names Mario Zechner as author.
- The root is a workspace monorepo. Public packages at `v0.85.0` are:
  `@earendil-works/chord`, `@earendil-works/pi-agent-core`,
  `@earendil-works/pi-ai`, `@earendil-works/pi-client`,
  `@earendil-works/pi-coding-agent`, `@earendil-works/pi-protocol`,
  `@earendil-works/pi-server`, `@earendil-works/pi-session-backend-sqlite-node`,
  `@earendil-works/pi-telemetry`, and `@earendil-works/pi-tui`.
- Example packages and `@earendil-works/pi-evals` are private workspace packages.

The public workspace dependency edges declared by package manifests are:

| Package | Declared role | Internal dependencies |
|---|---|---|
| `chord` | application composition runtime | none |
| `pi-telemetry` | vendor-neutral telemetry contracts | none |
| `pi-tui` | terminal UI library | none |
| `pi-ai` | model/provider API | `pi-telemetry` |
| `pi-agent-core` | general agent runtime | `chord`, `pi-ai`, `pi-telemetry` |
| `pi-protocol` | transport-neutral remote-session protocol | `chord` |
| `pi-client` | transport-neutral remote-session client | `chord`, `pi-protocol` |
| `pi-server` | experimental server | `chord`, `pi-agent-core`, `pi-protocol` |
| `pi-session-backend-sqlite-node` | Node SQLite session backend | `pi-agent-core`, `pi-ai` |
| `pi-coding-agent` | CLI, TUI host, tools, and session management | `chord`, `pi-agent-core`, `pi-ai`, `pi-client`, `pi-protocol`, `pi-tui` |

All ten public package manifests report `0.85.0` at the current release. Root version scripts
apply npm workspace versioning, run `scripts/sync-versions.js`, and regenerate the lock;
the release script then validates and publishes the public workspace set rather than only
the coding-agent package.

### Required fork treatment

The MIT copyright and permission notice must remain in copies or substantial portions of
the upstream software. Omicron Code must add its own downstream attribution without
misrepresenting upstream authorship. Third-party dependency and bundled-extension licenses
require their own inventory; the upstream root license does not prove that separately
incorporated packages may be redistributed under identical terms. OMC-02 owns the latter
inventory for current extensions.

## Package and Build Contract

### Observed upstream graph

`@earendil-works/pi-coding-agent@0.85.0` is the CLI/library distribution. It:

- exposes the `pi` executable at `dist/bundle/cli.js`;
- exports the public library at `dist/index.js` with declarations at `dist/index.d.ts`;
- exports `./rpc-entry`, `./client`, and an experimental plugin entry point;
- requires Node `>=22.19.0`;
- depends on the core agent, AI, client, protocol, TUI, and Chord workspace packages;
- ships `dist`, docs, examples, changelog, containerization material, and an npm
  shrinkwrap.

The root build orders workspace builds and finishes with the coding-agent package. The
coding-agent build has two relevant outputs:

1. `build`: an unbundled TypeScript build plus a bundled Node CLI.
2. `build:binary`: prerequisite package builds followed by a compiled Bun executable and
   copied runtime assets.

The root quality path includes formatting/static checks, pinned-dependency and entry-graph
checks, shrinkwrap/install-lock checks, type checking, a browser smoke check, script tests,
and workspace tests. Upstream development documentation names Node 22+, npm 10.9+, and
Bun 1.3.5+ for binary work; release CI currently selects Node 22 and Bun 1.3.14.

### Fork implications

- A source fork can retain upstream's workspace build and binary pipeline, but package
  names, release assets, update endpoints, and provenance must be downstream-owned.
- A downstream coding-agent package can reuse public APIs with less source divergence, but
  it still must prove that all required CLI/TUI modes and resource loading are exposed.
- Omicron's CI must test the same published artifact shape it releases; a successful source
  build alone is insufficient.
- The package's `bin`, `name`, `version`, `repository`, `author`/contributors, `license`, and
  `piConfig` metadata form one reviewable distribution identity boundary.

## Release and Artifact Contract

### Observed

Pushing a `v*` tag triggers `.github/workflows/build-binaries.yml`. The workflow:

- checks out the exact release source;
- creates a versioned source archive;
- builds binaries from that archive;
- produces macOS arm64/x64, Linux arm64/x64, and Windows arm64/x64 archives;
- includes installer package and lock files;
- generates `SHA256SUMS`;
- smoke-tests `--help` and `--version` on Ubuntu, macOS, and Windows;
- stages a draft GitHub release before npm publication;
- publishes public workspace packages to npm with provenance; and
- publishes the GitHub release only after preceding release stages succeed.

The observed `v0.85.0` GitHub release contains ten assets: the source archive, six platform
archives, two installer lock artifacts, and `SHA256SUMS`.

The release preparation script checks package registration, synchronizes workspace
versions, updates changelogs, regenerates model/shrinkwrap/install-lock artifacts, runs
checks and an offline build, commits and tags, then pushes `main` and the tag to trigger CI.
Between `v0.84.4` and `v0.85.0`, upstream changed 688 files with 95,441 insertions and
25,115 deletions; 214 changed paths are under `packages/coding-agent`. The current release
cannot be treated as a trivial patch over the historical ticket baseline.

### Fork implications

Omicron needs its own release namespace, signing/provenance policy, checksum ownership,
artifact names, npm scope, and update manifest. Reusing the workflow mechanically without
renaming assets and endpoints risks replacing or confusing Pi installations. OMC-03 should
prototype artifact identity without publishing anything.

## Runtime Identity and Coexistence Seams

### Observed source contract

`packages/coding-agent/src/config.ts` derives distribution identity from the installed
coding-agent `package.json`:

- `PACKAGE_NAME` comes from `package.json.name`;
- `APP_NAME` comes from `piConfig.name`, defaulting to `pi`;
- `APP_TITLE` follows the custom name, otherwise `π`;
- `CONFIG_DIR_NAME` comes from `piConfig.configDir`, defaulting to `.pi`;
- the global agent directory defaults to `~/<configDir>/agent`;
- project resources and settings use `<cwd>/<configDir>`;
- environment variables derive from the application name as
  `<APP_NAME>_CODING_AGENT_DIR` and `<APP_NAME>_CODING_AGENT_SESSION_DIR`;
- settings, auth, models, packages, extensions, skills, prompts, themes, managed tools,
  sessions, trust state, and debug logs live below the chosen agent/config roots.

The current upstream package only sets `piConfig.configDir: ".pi"`; the name field is an
available but unset seam. Source code also explicitly recognizes the official distribution
as the exact tuple `@earendil-works/pi-coding-agent`, `pi`, and `.pi`, and suppresses the
experimental official first-time setup for a differently identified distribution.

### Required Omicron invariant

The prototype must use all of the following at once:

- command `omicron`, not `pi`;
- a downstream package name, not `@earendil-works/pi-coding-agent`;
- `piConfig.name: "omicron"`;
- a distinct config directory such as `.omicron`;
- a distinct default global agent directory and project resource root;
- a distinct session directory, package cache, trust store, debug log, and managed-tool
  directory;
- no writes into `~/.pi`, project `.pi`, or the installed Pi package during smoke tests.

The exact downstream config-directory spelling remains a product decision, but sharing
`.pi` would violate the accepted coexistence requirement.

### Residual identity risks

Not every endpoint follows `piConfig` automatically. At `v0.85.0`:

- release discovery is hard-coded to `https://pi.dev/api/latest-version`;
- the default shared-session viewer is `https://pi.dev/session/`, with
  `PI_SHARE_VIEWER_URL` as an override;
- telemetry/update behavior and provider attribution are Pi-defined;
- documentation, examples, archive names, and some user-facing prose remain Pi-branded.

A metadata-only rename is therefore not a complete fork. These surfaces need explicit
replacement, disablement, or documented inheritance.

### Coexistence identity matrix

| Identity or format | Pi baseline | Omicron requirement | Sharing rule |
|---|---|---|---|
| Executable | `pi` | `omicron` | Never alias or replace Pi during coexistence |
| npm package | `@earendil-works/pi-coding-agent` | downstream-owned name | Never self-update one into the other implicitly |
| Application name | `pi` | `omicron` | Separate process title, help, labels, and derived env names |
| Global state root | `~/.pi/agent` | distinct Omicron root | Never shared writable state |
| Project state root | `.pi` | distinct Omicron directory | Never load Pi project resources implicitly |
| Environment namespace | `PI_CODING_AGENT_*` | `OMICRON_CODING_AGENT_*` when `APP_NAME=omicron` | Values are not imported automatically |
| Settings schema | upstream JSON settings | initially compatible subset | Copy/transform only after an explicit migration decision |
| Auth/models | `auth.json`, `models.json` under Pi root | separate files under Omicron root | Credentials are never bundled; future opt-in copy requires separate security design |
| Package/cache roots | Pi `npm`, `git`, `bin` directories | separate Omicron directories | Package specs may be shared as data only after OMC-02 classification |
| Trust decisions | Pi `trust.json` | separate Omicron trust store | Never import implicitly |
| Sessions | Pi JSONL v3 | separate Omicron session tree | Read copied fixtures only until compatibility is accepted |
| Extension/package API | upstream public module contracts | version-pinned compatibility layer | Share code/package inputs, not mutable installation directories |
| Update/release service | Pi-owned endpoint and package | Omicron-owned or disabled | Never use Pi response as Omicron authority |
| Shared-session viewer | `pi.dev` default | undecided/disabled in prototype | No inherited publication without OMC-04 policy |

## Settings, Packages, and Resource Loading

### Settings identity

Upstream merges global `~/.pi/agent/settings.json` and project `.pi/settings.json`, with
project settings overriding global settings and nested objects merged. The setting schema
covers model selection, UI, trust, telemetry, network, compaction, retry, shell, tools,
sessions, and resources. Resource settings are `packages`, `extensions`, `skills`,
`prompts`, and `themes`.

For Omicron, the same code path can follow a changed `CONFIG_DIR_NAME`, but compatibility
must be verified for both global and project scopes. Pi settings must not be silently read,
merged, migrated, or rewritten. Import must be a future explicit copy/transform operation,
not shared mutable state.

### Package manager

Pi packages may provide extensions, skills, prompt templates, and themes through manifest
entries or conventional directories. Sources may be npm, Git, or local paths. Important
behavior includes:

- global npm/Git installs live under the global agent directory;
- project installs live below the project config directory;
- versioned npm and referenced Git sources are pinned;
- Git reconciliation can reset and clean the managed clone;
- package identity is deduplicated between global and project settings;
- package filters can include or exclude resource classes and paths;
- package installation executes dependency installation where applicable.

This is a viable extension-distribution seam, but it is also a mutation and supply-chain
boundary. Omicron must own its settings root, pin exact defaults, preserve local-package
semantics only for deliberate development use, and never point a production default at a
machine-specific path.

### Loader order and conflicts

The default resource loader composes built-in/global, project-local, settings-declared,
package, and explicit CLI resources; project resources are trust-gated. It exposes override
hooks for extensions, skills, prompts, and themes. Extension conflicts are diagnosed while
load order determines precedence. Explicit CLI resources remain available even when normal
discovery is disabled.

The owning tests confirm representative boundaries: `extensions-discovery.test.ts` covers
file, directory, manifest, explicit-path, import, tool, command, event, shortcut, and flag
loading; `resource-loader.test.ts` covers project-over-user precedence, symlink
deduplication, pre/post-trust loading, untrusted project exclusion, conflict diagnostics,
and explicit-CLI precedence. `package-manager.test.ts`, `package-manager-ssh.test.ts`, and
`git-update.test.ts` cover local/npm/Git resolution, normalized source identity, user versus
project roots, dependency installation, pinned-ref reconciliation, reset/clean behavior,
and rewritten Git history. Those tests were inspected at the bound commit; they were not
executed for this research ticket.

OMC-03 must record the exact loaded source list and prove there is only one effective copy
of each representative extension/skill. This matters for Agent Skills, where duplicate
extension loading could apply routing or authority behavior twice.

## Extension API Contract

### Observed

Extensions are TypeScript/JavaScript modules loaded through jiti and execute in-process
with the user's full authority. The public `ExtensionAPI` supports, among other surfaces:

- event handlers across project trust, resource discovery, sessions, context, provider
  requests/responses, agent/turn/message lifecycle, tool execution, `tool_call`,
  `tool_result`, user shell input, and terminal input;
- tool, command, shortcut, flag, provider, renderer, and UI registration;
- controlled tool-call blocking or argument mutation through `tool_call` handlers;
- custom session entries and messages;
- access to working directory, session state, loaded tools, system prompt options, and a
  subprocess execution facility;
- runtime reload and provider registration/removal.

The API reports an extension mode of `tui`, `rpc`, `json`, or `print`, allowing terminal UI
behavior to be mode-gated. Public exports from `@earendil-works/pi-coding-agent` include the
extension types and loader/runtime functions.

### Compatibility boundary for Agent Skills

Omicron must preserve the event and registration semantics used by the mandatory Agent
Skills extension, especially:

- startup/resource discovery and reload behavior;
- exact interception order for `tool_call` and `tool_result`;
- command/shortcut registration and conflict behavior;
- current working-directory semantics of built-in tools;
- session lifecycle events used to bind durable evidence;
- mode-safe UI behavior;
- no implicit translation of local execution into provider or repository authority.

Because extensions have full process authority and `tool_call` handlers may mutate later
inputs, extension order is security-relevant. OMC-03 must test order and duplication, not
just successful import.

## CLI, Non-Interactive, and SDK Contracts

### CLI modes

The upstream CLI supports:

- interactive text/TUI operation;
- print mode (`-p`/`--print`);
- newline-delimited JSON events (`--mode json`);
- stdin/stdout RPC (`--mode rpc`);
- persistent, resumed, selected, custom-directory, and ephemeral sessions;
- explicit extension, skill, prompt-template, and theme paths plus discovery-disable flags;
- tool allow/deny selection;
- package install/remove/update/list/config operations.

The Omicron smoke matrix must cover all four extension modes (`tui`, `print`, `json`,
`rpc`) and demonstrate command/help/version branding without invoking a live model where it
is unnecessary.

### SDK

The public SDK exports `createAgentSession`, runtime/service factories, `AgentSession`,
`SessionManager`, `SettingsManager`, `DefaultResourceLoader`, built-in tool factories, and
custom tool/extension types. Callers can supply a custom `cwd`, `agentDir`, settings
manager, session manager, resource loader, model runtime, tool set, and inline extensions.
The SDK can run in-memory settings and sessions, which is a strong prototype seam because it
avoids writing either Pi or Omicron user state.

The public SDK also exposes utilities for interactive, print, and RPC hosts. This makes a
thin downstream host technically plausible, but only a prototype can determine whether it
retains the full CLI/product behavior with acceptable divergence.

## Session Contract

### Observed

Default sessions are JSONL under:

```text
~/.pi/agent/sessions/--<encoded-project-path>--/<timestamp>_<uuid>.jsonl
```

The current format is version 3. The first record is a session header containing type,
version, ID, timestamp, and working directory. Subsequent entries form a tree through
`id`/`parentId` and include messages, model/thinking changes, compactions, branch summaries,
custom extension entries/messages, labels, and session metadata. Version 1 and 2 sessions
are legacy formats; loading migrates older sessions to the current format. The SDK supports
file-backed and in-memory session managers, including restoration from externally supplied
entries.

### Fork implications

- New Omicron sessions must be written only to the Omicron state root.
- Read compatibility is not permission to mutate a Pi session in place.
- Any future Pi-session import must copy first, validate the header/version and extension
  custom-entry handling, then migrate only the copy.
- Session compatibility claims must identify direction (`Pi -> Omicron`, `Omicron -> Pi`),
  exact versions, and whether the test is read-only, copied migration, or round-trip.
- Share/export behavior may leak Pi branding or endpoints and needs explicit policy.

## Trust, Security, Telemetry, and Network Boundaries

### Observed upstream defaults

- Extensions execute arbitrary code with full system access. Skills can instruct the model
  to execute arbitrary actions. Upstream does not provide a general sandbox.
- Interactive startup prompts before trusting project-local settings/resources when no
  applicable decision exists. Non-interactive modes cannot prompt and apply the global
  `defaultProjectTrust`; `ask` and `never` ignore untrusted project resources, while
  `always` accepts them. One-run approve/no-approve flags exist.
- Trust decisions are stored separately from settings and require restart to affect the
  current session.
- `enableInstallTelemetry` defaults to `true` and controls the anonymous install/update ping
  plus selected provider attribution headers. `enableAnalytics` defaults to `false`.
- Disabling install telemetry does not disable version checks. `PI_SKIP_VERSION_CHECK=1`
  disables the version check; offline mode disables startup network operations including
  update checks, package checks, and install/update telemetry.

### Required Omicron posture for prototype and design

- No inherited Pi telemetry or update endpoint may be contacted in OMC-03.
- Use offline/in-memory or explicit test roots and prove filesystem isolation.
- Treat every included extension/package as executable supply-chain input.
- Preserve project trust as a separate decision; do not import Pi trust records.
- Never bundle credentials, OAuth state, provider tokens, sessions, caches, trust records,
  machine paths, or private audit artifacts.
- Do not claim that Agent Skills policy is a sandbox. It is an authority/routing contract
  layered on a runtime whose extensions still have process access.

Telemetry defaults for the eventual product remain an OMC-04 decision. The safe prototype
default is no telemetry and no update/network check.

## Update Seams

### Observed

Pi supports self-update for recognized npm, pnpm, Yarn, Bun, and managed-install layouts;
managed installations stage, verify, and atomically activate a release. Package updates are
separate and can reconcile pinned Git refs. Self-update planning currently queries the
Pi-owned latest-version endpoint, which may return a package name and version. The updater
can replace one package name with another when instructed by that response.

### Constraints for Omicron

- Omicron must not query Pi's release service to decide its own package identity or update
  target.
- `omicron update` must never install, uninstall, or rewrite the Pi package.
- Omicron package updates and Agent Skills source synchronization are separate contracts;
  neither implies repository/provider authority.
- A source-fork update policy must bind an upstream tag/commit and a downstream commit; a
  package-composed policy must bind the upstream package version and all bundled/default
  extension versions.
- The observed Volta label/payload disagreement shows why one version string is
  insufficient. Future diagnostics should report command path, runtime-reported version,
  package metadata version, manager inventory, and release/source identity separately.

OMC-04 must choose the long-term policy: periodic upstream merge/rebase, cherry-pick with a
patch queue, dependency update, or another explicit mechanism. OMC-01 does not select one.

## Compatibility Matrix for OMC-03

| Surface | Historical reference | Current execution reference | Prototype obligation | Risk |
|---|---|---|---|---|
| Source/build | `v0.84.4` exact commit/tree | `v0.85.0` exact commit/tree | Build from a pinned input; report resulting tree/artifact | High: large upstream delta |
| CLI identity | `pi` | `pi` | `omicron --help` and `--version`; no `pi` shim mutation | High |
| Config/project roots | `.pi`, `~/.pi/agent` | Same | Distinct Omicron roots; filesystem no-write proof for Pi roots | Critical |
| Sessions | JSONL v3 | JSONL v3 | New Omicron session isolated; copied read-only Pi fixture compatibility | High |
| Extensions | Public in-process API | Public API plus current events/modes | One representative from upstream/current install, Agent Skills, and personal config; exact load list | Critical |
| Skills/resources | package/settings/standard directories | Same | Deduplication and precedence proof | High |
| TUI | interactive regular/fullscreen surfaces | Current `0.85.0` behavior | Startup/exit smoke, extension UI mode guard | Medium |
| Print/JSON/RPC | Supported | Supported | Offline smoke for each output contract | High |
| SDK | public factories/loaders/managers | Current `0.85.0` exports | In-memory host smoke with isolated `agentDir` | High |
| Packages | npm/Git/local sources | Current manager/reconciliation rules | Pinned, test-root-only install/list behavior; no live package mutation | Critical |
| Trust | project trust with non-interactive fallback | Same | Untrusted project resource remains unloaded; no trust import | Critical |
| Telemetry/update | Pi endpoints/defaults | Pi endpoints/defaults | Network-disabled prototype; enumerate attempted endpoints | Critical |
| Release | npm + checksummed six-platform binaries | `v0.85.0` release | Local disposable artifact only; no publication | Medium |

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
