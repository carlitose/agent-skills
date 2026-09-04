# Omicron Code Extension and Configuration Inventory

## Artifact Graph

- Artifact ID: `research:omicron-code-extension-config-inventory`
- Role: `research`
- Parent: [OMC-02 — Inventory active extensions and configuration](../tickets/omicron-code/done/02-inventory-active-extensions-and-config.md)

## Status

Complete for OMC-02's bounded research question. This report inventories the observed
loader declarations and tracked configuration sources without selecting an Omicron Code
packaging or migration policy.

## Bounded Question

Which active Pi package roots, extensions, prompts, skills, and tracked
`pi-personal-config` capabilities may be considered for Omicron Code; who owns them; where
do implementations overlap; and which material is a default candidate, optional,
development-only, duplicate, machine-local, or forbidden?

## Evidence Boundary

The inspection was read-only and allowlist-based. It read:

- only the package and extension declarations plus top-level value types from
  `$HOME/.pi/agent/settings.json`;
- only root dependency declarations from `$HOME/.pi/agent/npm/package.json` and its lock;
- directory entries, not file contents, under `$HOME/.pi/agent/extensions`;
- named manifests, source files, documentation, license files, and Git metadata under the
  clean `pi-personal-config` and local Agent Skills checkouts;
- public package manifests and documentation for the five dependency packages reached by
  the active personal package;
- `pi list`, which reports package sources without loading a model or changing settings.

It did **not** open or traverse provider credentials, `auth.json`, trust record contents,
sessions, caches, model stores, MCP server configuration, OAuth storage, saved code-tool
state, private audits, or shell/environment values. Presence of a forbidden file is recorded
only through a safe category or existing Git index metadata. No extension was executed for
this inventory, and no package install, update, reload, authentication, provider request, or
configuration write was performed.

The deterministic pre-inspection snapshot is stored in the Ticket Autopilot run artifact
`omc-02-safe-snapshot-before.json`, SHA-256
`403a2289f12b9c313c18acdc62439880f67c71221f1f99b027887a957e1877dd`.

## Exact Snapshot Bindings

| Surface | Exact identity | Observation |
|---|---|---|
| Live Pi settings | SHA-256 `a9de95dbf39b24f7f8a08a699e05a650584cdbfa64f93af9d949259e69c0c8f8` | Only package/extension declarations and top-level value types were selected. |
| Pi npm declaration | package SHA-256 `bf89287763e8d06607c4cf0f7b7cbff35b294bc34ecf97d9368a8d439423a9ff` | Installed-package inventory; it is not the active-source list. |
| Pi npm lock | SHA-256 `a9d68295d331fc5da30e60998d300c13585e5965d08f2fd880e94ad201384925`, lockfile v3 | Root declarations only; resolved URLs and transitive records were not copied. |
| `pi-personal-config` | commit `c0ba651dce6efc56684ed65f92698581432465b6`, tree `7ccec055212e5a39d2afb7c9c25aeece6c1a0b17` | Clean tracked checkout at `$HOME/Projects/pi-personal-config`. |
| `pi-personal-config/package.json` | Git blob `097cf57afa2dd4b963f3f203b454d42af045fccc` | Private package named `pi-personal-config`; no license field. |
| Tracked portable profile settings | SHA-256 `8c6ae89d065c1e6382be643033c1df3460c4f675661c01d6730a48f56292ad8e` | Package declarations and top-level value types only. |
| Tracked trust snapshot | Git index entry `100644 c9839eef8979ade13c5cb6ef73409cb76994c229` | Contents deliberately not inspected; forbidden for migration. |
| Local Agent Skills | commit `8e275136e5a4639bc340e887e4dc62ffaea3bc2e`, tree `5d633e149e5d3e25f0c14d320ed8cbe5125892f3` | Clean persistent checkout at `$HOME/.pi/agent/local/agent-skills`. |
| Agent Skills package manifest | SHA-256 `2380f8228ff471fb1aaf2e339d42e4d17b6beccd053f7b3e153a9fabd04b9e5c` | Package `carlitose-agent-skills-pi@0.1.0`; no license field. |
| Historical/current Pi semantics | [OMC-01 upstream baseline](omicron-code-upstream-pi-baseline.md) | Package-filter interpretation is tied to Pi `v0.85.0`, commit `107d79f11072bbc8a3a757ed7fd69596bee7d68c`. |

Git commit/tree identities apply to tracked content only. Dependency directories under
`pi-personal-config/node_modules` are bound below by package version, manifest digest, entry
file digest, and observable license evidence rather than by the parent Git tree.

## Reproducible Secret-Safe Inspection

These examples expose no credential values. They intentionally select only approved fields.

```bash
PI_AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
PERSONAL="$HOME/Projects/pi-personal-config"
AGENT_SKILLS="$PI_AGENT_DIR/local/agent-skills"

shasum -a 256 \
  "$PI_AGENT_DIR/settings.json" \
  "$PI_AGENT_DIR/npm/package.json" \
  "$PI_AGENT_DIR/npm/package-lock.json"

git -C "$PERSONAL" status --porcelain=v1
git -C "$PERSONAL" rev-parse HEAD 'HEAD^{tree}'
git -C "$AGENT_SKILLS" status --porcelain=v1
git -C "$AGENT_SKILLS" rev-parse HEAD 'HEAD^{tree}'

pi list
find "$PI_AGENT_DIR/extensions" -mindepth 1 -maxdepth 1 -print
```

A safe selector for live settings reads package declarations while discarding all other
values:

```bash
python3 - <<'PY'
import hashlib, json, os
from pathlib import Path

home = str(Path.home())
path = Path(os.environ.get("PI_CODING_AGENT_DIR", Path.home() / ".pi/agent")) / "settings.json"
raw = path.read_bytes()
value = json.loads(raw)

def portable(item):
    if isinstance(item, str):
        return item.replace(home, "$HOME")
    if isinstance(item, list):
        return [portable(child) for child in item]
    if isinstance(item, dict):
        return {key: portable(item[key]) for key in sorted(item)}
    return item

print(json.dumps({
    "sha256": hashlib.sha256(raw).hexdigest(),
    "top_level_shape": {key: type(item).__name__ for key, item in sorted(value.items())},
    "packages": portable(value.get("packages", [])),
    "extensions": portable(value.get("extensions", [])),
}, sort_keys=True))
PY
```

Do not replace that selector with a dump of the complete settings object. Do not inspect
`auth.json`, `trust.json`, MCP configuration, sessions, caches, or environment values to
reproduce this report.

## Active Loader Roots

`pi list` reported exactly two filtered user package roots:

1. `$HOME/Projects/pi-personal-config`, stored in settings relative to the Pi agent
   directory;
2. `$HOME/.pi/agent/local/agent-skills`, stored as `local/agent-skills`.

The top-level `$HOME/.pi/agent/extensions` directory was empty. The live settings contained
no independent top-level `extensions` entries. Consequently, the six extension rows below
come from the two package roots, not from standalone copies.

The settings filter on `pi-personal-config` force-excludes its nested
`node_modules/carlitose-agent-skills-pi/extensions/mandatory-agent-skills.ts`. The settings
filter on the local Agent Skills package sets `skills: []`, which Pi `v0.85.0` defines as an
explicit disable-all filter for that resource type while leaving its manifest-declared
extension enabled. This produces one loader-selected mandatory extension and avoids loading
the package's 34 `SKILL.md` files as a second Pi package skill source.

This describes the current on-disk declarations. It is not evidence that an already-running
session has reloaded them.

## Active Extension and Resource Matrix

Each loader-selected extension appears exactly once here. Supporting modules imported by an
entry point remain part of that row rather than becoming duplicate extensions.

| ID | Loader-selected entry | Package/version or owner | Capability family | Classification | Decision owner |
|---|---|---|---|---|---|
| E1 | `$HOME/Projects/pi-personal-config/extensions/update-plan/index.ts` | `pi-personal-config` at `c0ba651…` | Model-callable `update_plan`, `/todos`, branch-aware plan state, and optional TUI widget | **Default candidate** for non-trivial coding workflow; UI surfaces remain mode-dependent | OMC-03 composition; OMC-04 product policy |
| E2 | `$HOME/Projects/pi-personal-config/node_modules/@narumitw/pi-btw/dist/index.ts` | `@narumitw/pi-btw@0.56.2` | Temporary side-question threads and explicit bring-back to the main editor | **Optional integration**; TUI-only and model/credential dependent | OMC-04 |
| E3 | `$HOME/Projects/pi-personal-config/node_modules/@upstash/context7-pi/extensions/context7.ts` | `@upstash/context7-pi@0.1.2` | Documentation lookup tools and `/c7-docs` | **Optional integration**; network service with optional credential | OMC-03 adapter test; OMC-04 default/network policy |
| E4 | `$HOME/Projects/pi-personal-config/extensions/pi-code-tool/index.ts` | Local wrapper over `pi-code-tool@0.6.1` | Sandboxed Python code mode, bridged Pi tools, saved helper tools, and model-aware limits | **Development-only tool** until mutation approval and duration policy are decided | OMC-03 security prototype; OMC-04 policy |
| E5 | `$HOME/Projects/pi-personal-config/node_modules/pi-mcp-adapter/index.ts` | `pi-mcp-adapter@2.32.1` | Lazy MCP discovery/proxy, optional direct tools, resources, transport, and auth flows | **Optional integration**; server/config/credential material remains external | OMC-03 adapter test; OMC-04 network/auth policy |
| E6 | `$HOME/.pi/agent/local/agent-skills/extensions/mandatory-agent-skills.ts` | Agent Skills commit `8e275136…` | Mandatory skill routing, delivery-lane policy, `/agent-skills-flow`, and bounded `/break-glass` lifecycle | **Default candidate** for the requested workflow, but not yet a redistribution decision | OMC-03 composition; OMC-04 licensing/release policy |

Additional enabled resources are:

| ID | Resource | Source | Classification | Notes |
|---|---|---|---|---|
| R1 | `context7-docs` skill | `@upstash/context7-pi@0.1.2` | Optional integration | Teaches library-specific documentation routing; network lookup remains evidence, not repository authority. |
| R2 | `c7-docs.md` prompt | `@upstash/context7-pi@0.1.2` | Optional integration | Manual documentation workflow prompt. |

The personal package lists `pi-mcp-adapter` only under its `extensions` resources, so the
adapter's package-owned `skills` directory is not selected by this composition. Likewise,
the local Agent Skills package's skill files are disabled by its explicit empty filter. No
other prompt, skill, or theme source was selected by the inspected package declarations.

## Exact Active Entry Identities

| ID | SHA-256 | Bytes | Supporting identity |
|---|---|---:|---|
| E1 | `da2b0acfb97a106f973cda90db5af9ae6672c913b267d973cec0b5f857161918` | 4,695 | State module SHA-256 `3d3aea3258c6a536441408e5f1acb7398f93410eb073a6b8a5cf57d29d1c0a54` |
| E2 | `551a0cf95ee0020853bcffed99ac326ccdcb6c140b68297e2cd6aed3b3b22c84` | 113,189 | Package manifest SHA-256 `d10fcaccb9fad8c6137fe71a7ddfda395a2464a26d4c40601acc67cb7096c368` |
| E3 | `b8b3ae539981a1469678e19771c061e692838e8c1fde6a5a3990962a8671c8e7` | 346 | Package manifest SHA-256 `367f6565087be5e89315d3cb171d9f391017124b598b744662c3500705adcb11` |
| E4 | `370f20e4c861a116f4a27abb8b04866b96c4faabfafab045db9ee8f8cb707014` | 460 | Runtime SHA-256 `63e8e222283ae1e56a14e97564c5047624ecba1b5458a06d1e3e49d7b8b3a367`; timeout config `31f7ec1dbdcaca0bb43b8c94f5ca6f58421382cfaeeaceac9442c9181af0b89a` |
| E5 | `4d463f957d0613da8254b20dffe0b982e57a9d7cc484e6db556501abd3a140b8` | 55,886 | Package manifest SHA-256 `43c22297f4e9d28c9e77438eaf3f757c57c46be6214bc96df4b1db6cd0555f8e` |
| E6 | `e1e4c7a550677df7aa94bf1652219f68256f87aa2a7204b764786a38503ac44a` | 22,705 | Break-glass module SHA-256 `9c08e20bdc9971b815e2a9a609970c987c59e731eb711d5a69038914a04343ef` |

These hashes bind observed files, not upstream release provenance. A future dependency
policy must add lock/integrity or vendored-source evidence appropriate to the chosen
architecture.

## Package Ownership, Source, and License Evidence

| Package/source | Observed version/source | Owner evidence | License/redistribution evidence | Classification |
|---|---|---|---|---|
| `pi-personal-config` | Clean private package at commit `c0ba651…`, tree `7ccec05…` | User-owned configuration repository | No package license field and no root license file observed; redistribution unresolved | **Machine-local binding** and composition source, not a distributable default as-is |
| Local `carlitose-agent-skills-pi` | `0.1.0`, commit `8e275136…`, tree `5d633e1…` | User-owned Agent Skills repository | No package license field and no root license file observed; redistribution unresolved | **Default candidate** capability; publication form unresolved |
| `@narumitw/pi-btw` | `0.56.2`; repository manifest points to `narumiruna/pi-extensions` | Package author/repository metadata | SPDX `MIT`; observed `LICENSE` SHA-256 `5293e92f073f47012e723990a8605431b438757e9c6eb00c89868b1203e157da` | Optional integration |
| `@upstash/context7-pi` | `0.1.2`; repository manifest points to `upstash/context7`, `packages/pi` | Upstash package metadata | SPDX `MIT`; observed `LICENSE` SHA-256 `3ee0c2e6e298dfe4afaae0526ec1626eb6fadc918b0fa00331e525f19b7da7dd` | Optional integration |
| `pi-code-tool` | `0.6.1`; repository manifest points to `josephkern/pi-code-tool` | Joseph Kern package/repository metadata | SPDX `MIT`; observed `LICENSE` SHA-256 `249afaf39728e51aaa6cad2bb1a0c38d383a296d26423bab5a30274382f4c87f` | Development-only pending security policy |
| `pi-mcp-adapter` | `2.32.1`; repository manifest points to `nicobailon/pi-mcp-adapter` | Nico Bailon package/repository metadata | SPDX `MIT`; observed `LICENSE` SHA-256 `2d20dfacd9742706e564470dc77438608a1e54b0ed46959f080709389209093c` | Optional integration |

MIT status permits use subject to preserving the applicable notices. It does not decide
whether Omicron vendors, pins, wraps, or asks users to install a package. No redistribution
right is inferred for the two sources without observed license evidence; OMC-04 must resolve
that before any public bundle or fork release includes them.

## Capability and Configuration Classification

### Default candidates

- **Agent Skills mandatory routing (E6):** required to preserve route-first behavior,
  delivery-lane separation, explicit authority boundaries, and break-glass limits. The
  package form and license are unresolved even though the capability is a default candidate.
- **Plan state (E1):** `update_plan` enforces a complete ordered snapshot with at most one
  active step. `/todos` and the widget require an interactive UI; the model-callable tool can
  still represent plan state when UI rendering is absent.

“Default candidate” means a capability OMC-03 must exercise in a prototype. It is not an
OMC-04 product selection.

### Optional integrations

- **Context7 (E3/R1/R2):** external documentation lookup. It can operate under an IP-based
  quota or an optional environment credential; the credential name may be documented, but
  its value must never enter a repository, migration bundle, snapshot, or report.
- **MCP adapter (E5):** lazy server discovery and proxying reduce exposed tool definitions,
  but server definitions, headers, commands, OAuth state, bearer material, credential-store
  records, and metadata caches must remain outside the fork. Omicron needs its own config and
  credential namespace before this can be enabled by default.
- **Pi BTW (E2):** useful only in TUI mode and capable of making side-model calls with the
  current or separately configured model. Its side-thread state is memory-only; saved model
  choice is a separate user setting.

### Development-only tool

- **Pi Code Tool wrapper (E4):** the wrapper enables `bridgePiTools: true` and
  `autoApprove: true`. Bridged mutating tools can therefore execute without a second
  per-call dialog. This setting grants no repository, provider, merge, publication, wiki,
  synchronization, migration, or release authority, but it is still a high-impact local
  execution choice and must not silently become an Omicron product default.
- The tracked wrapper currently declares a 5-second fallback and a 300-second override for
  one exact provider/model pair, with custom validation capped at 3,600 seconds. The
  inspected standalone extension directory is empty. Therefore no current on-disk loader
  declaration in this snapshot sets a 30,000-second code timeout. A previously instantiated
  session could differ until reload; that was not tested. The discrepancy must be resolved
  by the configuration owner in a separate change, not by this research ticket.

### Machine-local bindings

- The live package source spelling resolves through the current `$HOME/Projects` layout.
- Tracked profile startup fields and package paths encode one user's defaults. Their values
  are not Omicron defaults merely because they are tracked.
- `scripts/install.sh` manages an `update-plan` copy and a bounded zsh environment filter on
  macOS/Linux. Shell profile mutation is a user installation action, not application code.
- Remote-TUI scripts manage tmux prerequisites/configuration and rely on separately
  authorized macOS Remote Login and private-network policy. They are operational tooling,
  not a cross-platform Omicron runtime feature.
- The tracked trust snapshot is explicitly optional and machine-specific in the source
  documentation. Its contents are forbidden for import.

### Forbidden material

The following must not be ingested, copied, logged, hashed into public evidence, committed,
or used as fixtures from the live machine:

- provider credentials, tokens, authorization codes, client secrets, and credential-store
  records;
- `auth.json` and environment secret values;
- trust decision contents, including the tracked personal profile trust snapshot;
- session bodies, branches, transcripts, and side-thread content;
- MCP server definitions containing commands, endpoints, headers, environment mappings, or
  authentication configuration;
- caches, model stores, saved code-tool state, temporary approval state, and private audits;
- usernames, hostnames, private addresses, device identities, shell history, and absolute
  machine-local paths.

OMC-03 must use synthetic fixtures and temporary homes for these boundaries. OMC-04 must
specify any opt-in import as copy-based, versioned, redacted, rollback-capable, and separate
from live Pi state.

## Overlap and Duplicate Inventory

The active and installed sets are not the same.

| Observed overlap | Active winner under current declaration | Inactive/duplicate surface | Required treatment |
|---|---|---|---|
| Mandatory Agent Skills extension | E6 from local Agent Skills at commit `8e275136…` | `pi-personal-config/node_modules/carlitose-agent-skills-pi` is pinned to archive commit `e85b88fae1bea8d3780377704629c9cb89b44750`; its extension hash is `f360a8e7e23bfcf9cd44925003fb4d487baabe7492e2c351453dd7b625466c8b` and is explicitly excluded | Keep exactly one extension in any prototype; do not assume the newer or bundled copy wins without an exact policy. |
| Agent Skills skill files | No skill files selected through the local package because `skills: []` | The local package contains 34 skill files; the nested dependency also declares skill files but is not exposed by the personal manifest | OMC-03 must name one skill source and test duplicate prevention. |
| Pi Code Tool | E4 local wrapper over `pi-code-tool@0.6.1` | An unwrapped `pi-code-tool@0.6.1` copy remains under the Pi npm installation inventory | Preserve one `code` registration; wrapper security and timeout policy must be explicit. |
| Context7 | E3/R1/R2 through `pi-personal-config` dependencies | The same `@upstash/context7-pi@0.1.2` manifest also exists under the Pi npm installation inventory | Use one exact package source; do not duplicate tools, prompt, or skill. |
| MCP adapter | E5 through `pi-personal-config` dependencies | The same `pi-mcp-adapter@2.32.1` manifest also exists under the Pi npm installation inventory | Use one exact package source; keep runtime/server state outside packaging. |
| Pi BTW | E2 through `pi-personal-config` dependencies | The same `@narumitw/pi-btw@0.56.2` manifest also exists under the Pi npm installation inventory | Use one exact package source; retain optional/TUI-only status. |
| Web access | None | `pi-web-access@0.27.0` exists under the Pi npm installation inventory but is absent from `pi list` and intentionally absent from the personal package | **Duplicate/inactive residue**, not an Omicron requirement. Do not reactivate by inventory inference. |
| Update plan | E1 through the active personal package | `scripts/install.sh` can also place a standalone copy under the Pi extension directory; no such entry exists now | Package and standalone installation modes must be mutually exclusive. |

The Pi npm manifest declares five packages: `@narumitw/pi-btw`, `@upstash/context7-pi`,
`pi-code-tool`, `pi-mcp-adapter`, and `pi-web-access`. Because `pi list` reports only the two
filtered local roots, this inventory treats those npm copies as installed but unselected.
It does not delete them or infer that they are safe to remove.

## `pi-personal-config` Tracked Capability Map

| Surface | Behavior | Classification | Portability/authority boundary |
|---|---|---|---|
| Root package manifest | Composes six extension entries plus Context7 prompt/skill resources; pins a reviewed Agent Skills archive; marks the package private | Machine-local composition source | Useful prototype input, not a publication manifest. `.npmrc` permits remote archives only for root declarations and disables lockfile generation. |
| `extensions/update-plan` | Registers `update_plan`, `/todos`, renderer, widget, and branch restoration | Default candidate | Core tool path is agent-mode capable; command/widget need UI. Uses Pi extension APIs. |
| `extensions/pi-code-tool` | Wraps `pi-code-tool`, prebuilds timeout-specific delegates, restores branch state before execution | Development-only | Depends on the Pi extension API and Monty platform package; local mutation approval differs from repository authority. |
| `profile/settings.json` | Stores startup field categories and five historical package declarations | Machine-local binding | It is not equal to live settings: live settings now use two filtered local roots. Values were excluded from this report. |
| `profile/trust.json` | Stores project trust decisions according to source documentation | Forbidden material | Never migrate from the live/tracked snapshot; use synthetic fixtures only. |
| `scripts/install.sh` | Installs standalone update-plan and manages one zsh environment-filter block | Machine-local installer | macOS/Linux shell behavior; mutating and outside OMC-02 authority. |
| Remote-TUI scripts/tests | Prepare tmux settings and validate prerequisites; human owns SSH and private-network setup | Machine-local/development-only | macOS-specific setup; no automatic SSH, tailnet, or public exposure authority. |
| Tests | Unit, package/profile, temporary-home installer, and remote-TUI fixture coverage | Development-only evidence source | Tests were inspected as ownership evidence but were not executed by OMC-02. |

The tracked profile settings still describe separate npm/Git package sources, while live
settings describe the local personal package plus local Agent Skills. The profile is
therefore a portable historical/template surface, not an exact backup of current live
configuration.

## Portability Matrix

| Surface | TUI | Print/text | JSON/RPC | SDK/embed | OS constraints observed |
|---|---|---|---|---|---|
| E1 Update Plan | Tool plus widget and `/todos` | Tool registration can exist; UI feedback absent | Tool contract may be exposed by the host | Uses public extension APIs | Source is platform-neutral TypeScript; installer is Unix-shell-specific. |
| E2 Pi BTW | **Required** for its full-screen side-thread workflow | Unsupported by package documentation | Unsupported by package documentation | No supported embedding claim observed | Terminal, clipboard, and model availability vary by host/OS. |
| E3 Context7 | Tool and slash command | Tool use is host/agent dependent | Tools can be surfaced by Pi modes | Extension package; no standalone SDK claim inspected | Requires network; optional credential handling remains external. |
| E4 Pi Code Tool | Tool with approval UI when auto-approval is off | Headless behavior exists; current wrapper auto-approves | Host tool availability governs bridging | Package exports code runner APIs, but wrapper is Pi-specific | Monty uses platform-specific native dependencies; target matrix requires prototype execution. |
| E5 MCP adapter | Full panels, commands, status, and auth flows | Proxy tool can run; interactive setup/auth may be unavailable | Proxy/direct tools depend on host exposure | Package documents a `createMcpAdapter` factory | Node `>=20`; credential store and transport support vary by OS/headless environment. |
| E6 Agent Skills router | Commands, status, and break-glass UI are available | Prompt policy and hooks may apply; command UX differs | Host event/tool support must be tested | Pi extension specific | TypeScript source is portable; canonical local tools and path rules need per-host fixtures. |
| Personal installer/remote TUI | Operational TUI preparation | Not an agent mode | Not applicable | Not applicable | zsh installer targets macOS/Linux; remote-TUI installer targets macOS; Windows has separate manual instructions. |

This matrix records source-exposed constraints. It is not cross-platform runtime proof.
OMC-03 must run disposable representatives in every mode it claims to support.

## Ownership Decisions Deferred to OMC-03 and OMC-04

OMC-03 must compare, without publication:

1. **Source-fork prototype:** place representative E1/E6 behavior inside a disposable
   Omicron source tree and measure upstream coupling and identity isolation.
2. **SDK/dependency-composed prototype:** depend on exact external packages and register
   representative local capabilities through explicit adapters.
3. **Profile-distributed prototype:** leave packages external and install only a distinct
   Omicron profile/configuration layer.

Every prototype must:

- expose one and only one implementation for each selected capability;
- use a distinct `omicron` command and Omicron-owned application/config, settings, session,
  cache, trust, log, managed-tool, update, telemetry, and release identities;
- avoid reading or writing live Pi state;
- use synthetic settings, trust, MCP, auth, and session fixtures;
- demonstrate rollback and no-cross-load behavior;
- preserve Agent Skills authority boundaries and avoid treating code-tool auto-approval as
  merge/provider/publication authority;
- record TUI versus print/JSON/RPC/SDK availability rather than assuming parity.

OMC-04 must decide:

- whether E1 and E6 are first-party defaults, separately packaged dependencies, or optional
  installation-profile components;
- whether E2, E3, E4, and E5 ship, remain opt-in, or remain development-only;
- the exact pin/update/notice strategy for MIT dependencies;
- licensing and release treatment for `pi-personal-config` and Agent Skills;
- code-tool approval and timeout policy, including the unresolved 30,000-second mismatch;
- whether any settings import exists, under what schema, and with what explicit consent and
  rollback;
- supported operating systems and agent modes;
- the replacement for Pi-specific update, telemetry, sharing, and service endpoints.

## Unknowns and Limitations

- The active session was not reloaded or introspected; this report proves on-disk declarations
  and source contracts, not the exact extension instances already resident in memory.
- Third-party package versions and observed files are exact local snapshots, but no registry
  provenance, signature, SBOM, or upstream Git tag was independently verified.
- Package and source tests were not run. Their documented behavior is not execution evidence.
- No MCP server inventory was attempted because its definitions may contain commands,
  endpoints, headers, environment names, and authentication policy.
- No trust, session, cache, auth, model-store, audit, or saved-tool contents were inspected.
- Absence from `pi list` means “not selected by the observed Pi package declaration,” not
  “safe to delete.”
- Lack of observed license evidence for user-owned packages remains unresolved rather than
  guessed.
- Portability beyond source/documented behavior remains unverified until OMC-03 uses
  disposable environments.

## Acceptance Readback

The final OMC-02 quality pass must rerun the deterministic safe snapshot after report edits
and require byte equality with `omc-02-safe-snapshot-before.json`. It must also verify:

- exact `pi-personal-config` and local Agent Skills heads, trees, and clean status;
- unchanged live settings and npm declaration digests;
- an empty standalone extension directory;
- exactly two `pi list` roots and exactly six active extension rows;
- one row per active resource, with no duplicate ID or loader path;
- no literal home directory, credential-like assignment, raw trust/session/cache material,
  placeholder status, or architecture selection in this report;
- all relative links and Artifact Graph reciprocity;
- exact delivery CandidateRef integrity.

Passing those checks demonstrates that the approved sources remained unchanged during this
inspection. It does not authorize or claim reload, install, update, migration, cleanup,
publication, merge, or Omicron architecture selection.
