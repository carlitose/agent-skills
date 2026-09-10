# Synchronize the local agent-skills Pi package after integrated tasks

## Artifact Graph

- Artifact ID: `spec:agent-skills-post-task-pi-sync`
- Role: spec
- Standalone: true

### Children

- [PIS-01 — Synchronize exact integrated agent-skills into Pi](../tickets/agent-skills-post-task-pi-sync/01-synchronize-exact-integrated-agent-skills-into-pi.md)
- [Resolve Pi-normalized local package source identities](ticket-autopilot-pi-local-package-source-identity.md)
- [Migrate the Pi owned-skill source explicitly](ticket-autopilot-pi-owned-skill-source-migration.md)
- [WPI-01 — Invoke installed Pi natively on Windows](../tickets/pi-sync-windows/done/01-native-windows-launcher.md)

## Type

Feature specification.

## Decision

After an `agent-skills` ticket reaches the durable Ticket Autopilot state `integrated`, the
workflow must synchronize the exact integrated revision into Pi. It must not trigger when
implementation, review, verification, PR creation, or an attempted merge merely finishes.

The synchronization has two ordered outputs:

1. update the `agent-skills`-owned directories under `~/.agents/skills`, preserving every
   external skill directory; then
2. invoke the installed Pi CLI through the platform-specific launcher, run
   `pi install <checkout-locale>`, and verify the installed local package with `pi list`.

POSIX keeps the normal zsh wrapper. The human-confirmed Windows exception invokes the
already-installed npm Pi entry point with native Node and literal arguments/environment;
it does not require zsh or execute a `.cmd` command string.

This is a local package refresh. It must never invoke `pi update`, `pi update --self`, or
otherwise update the Pi binary.

## Evidence and current state

Pi's package documentation says that local packages are referenced rather than copied, that
relative settings entries resolve against their settings file, and that `/reload` or a new
session is needed to reload active resources. Pi accepts an absolute install argument but may
persist the source relative to its settings root. The repository already declares its
extension and top-level skills in `package.json`.

The original POSIX deployment had:

- a pinned `git:github.com/carlitose/agent-skills@...` Pi package with `skills: []`;
- copied skills under `~/.agents/skills`;
- Pi-facing symlinks under `~/.pi/agent/skills` that resolve to those copied skills.

A later Windows observation found Pi 0.85.1 installed through npm, with `pi.cmd` pointing
to the package's declared `bin.pi` (`dist/bundle/cli.js`), native Node available, and no zsh.
The user explicitly selected native Windows support while retaining the transaction and
excluding binary updates or automatic reloads. The earlier zsh-only limitation is superseded
on Windows only; the separate ownership inventory must still be observed on each host.

Primary CLI references: Pi's [package documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)
and [Windows documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/windows.md).
Installed package metadata and shim contents determine the executable on the actual host,
not a guessed global install path or a hard-coded version layout.

Blindly adding a local package would duplicate the extension and could duplicate
skills. The first successful local synchronization must replace only the exact existing
`carlitose/agent-skills` package source, preserve its `skills: []` filter, and leave all
unrelated Pi package entries unchanged.

## Goals

- Make future Pi sessions consume the exact integrated `agent-skills` revision after each
  integrated task.
- Keep `~/.agents/skills` current because it remains the canonical cross-agent skill install.
- Preserve external skills, unrelated Pi packages, package filters, and user settings.
- Make retries, interruption recovery, and concurrent invocations deterministic and safe.
- Emit a receipt that binds the source repository, integrated commit/tree, local checkout,
  owned-skill manifest, settings before/after digests, actor, and durable evidence.

## Non-goals

- Updating the Pi executable, model catalogs, npm packages, or unrelated Pi packages.
- Reloading or controlling an already-running interactive Pi session.
- Treating `pr-open`, local tests, verification, or a merge attempt as completion.
- Installing from an uncommitted candidate, transient ticket worktree, dirty checkout, or
  branch name without an exact integrated commit.
- Deleting or rewriting skill directories not owned by the exact source manifest.
- Granting ticket start, merge, provider, wiki-sync, repository-bootstrap, or cleanup
  authority.

## Target workflow

### Exact integrated source

A synchronization request binds:

- the canonical `agent-skills` repository identity;
- an exact commit observed as durably integrated by Ticket Autopilot;
- its exact tree;
- actor and durable evidence;
- the dedicated persistent local checkout path;
- the agents skill root and Pi settings path.

The tool maintains a dedicated checkout, defaulting to
`~/.pi/agent/local/agent-skills`. It must never repoint Pi at a transient Ticket Autopilot
worktree or at a dirty developer checkout. Under a lock, it fetches or materializes only the
bound commit, verifies `HEAD` and tree readback, and fails closed on divergence.

### Owned skill synchronization

The source package manifest and regular `*/SKILL.md` roots determine the exact owned skill
set. Before mutation the tool validates that every owned root stays inside the source,
contains no escaping symlink or submodule, and has deterministic regular-file content.

The tool stages complete replacement directories next to the destination, records the
previous owned-install manifest, and atomically replaces only names owned by the current or
previous manifest. Names absent from both manifests are external and untouchable. Removed
owned names may be deleted only when the previous manifest proves ownership. The manifest
records the integrated commit/tree and per-directory digest.

### Pi package installation and filtering

After the skill replacement succeeds, invoke the installed Pi CLI through a narrow
package-command boundary that accepts the operation, literal arguments, checkout cwd and
approved settings root. The transaction does not construct or parse shell programs.

On POSIX retain the normal zsh wrapper, passing the checkout as a positional argument
without shell interpolation:

```text
zsh -lic 'PI_CODING_AGENT_DIR="$1" pi install "$2"' agent-skills-pi-sync <absolute-pi-config-dir> <absolute-checkout>
```

On Windows, resolve the PATH-selected npm `pi.cmd` to its installed package's declared
`bin.pi` and resolve native Node as that npm launcher would (adjacent `node.exe`, otherwise
PATH). Invoke Node and the entry point directly with an argument vector and a copied child
environment containing the exact `PI_CODING_AGENT_DIR`. Never execute or interpolate the
`.cmd` shim, use `shell=True`, download a runtime, search unrelated package installations,
or silently select a different Pi. Require an unambiguous supported npm launcher layout,
matching package identity/bin declaration and existing executable/entry-point files; fail
closed for missing, contradictory or unsupported layouts. Supporting custom launchers,
other package managers and standalone Pi distributions is not part of WPI-01.

Both commands preserve spaces, Unicode and shell metacharacters in legal Windows paths,
including percent/exclamation sequences, as literal data. Decode native Pi output strictly
as UTF-8 on the caller thread after binary capture: Windows subprocess text reader errors
must not become missing streams or ignored stderr. Git path readback also uses UTF-8 so a
Unicode checkout is not mistaken for a different repository root. Inspect Git symlink modes
under owned skills even when `core.symlinks=false` materializes links as ordinary files;
filesystem appearance cannot erase the existing source safety rule.
A launch, decoding, command or readback failure goes through existing transaction
recovery with no success receipt. Do not mutate the parent environment or add launcher
selection/authority fields to persisted transaction history.

The first migration may replace only the exact installed
`git:github.com/carlitose/agent-skills@...` entry. The resulting local package entry keeps
`skills: []`, because those skills are already loaded through `~/.agents/skills`; the local
package supplies the extension. All unrelated settings bytes and package entries remain
semantically unchanged.

Pin `PI_CODING_AGENT_DIR` to the parent of the actor-approved `settings.json` for both
commands. Resolve Pi's absolute or relative configured package row against that exact settings
root and require exactly one effective `agent-skills` identity at the dedicated local checkout.
Preserve Pi's source spelling when retaining `skills: []`; never count the separately indented
installed-path display as package evidence. A partial or contradictory readback is failure, not
success.

### Transaction and recovery

Use one process lock for the dedicated checkout, owned skill roots, install manifest, and Pi
settings transaction. Persist intent before filesystem or settings mutation. Persist phase
receipts after checkout materialization, skill replacement, `pi install`, filter migration,
and `pi list` readback.

An exact replay is idempotent. A crash resumes from readback and never assumes the prior
command succeeded. If settings or skill replacement cannot be proven exact, restore from
the transaction backup when safe; otherwise leave a prominent recovery gate with the backup
and observed state paths. Never delete an unknown directory or rewrite unrelated settings to
force recovery.

## Invocation policy

The mandatory agent-skills policy must require this synchronization only after a durable
`integrated` result for the `agent-skills` repository and only when an actor/evidence-bound
local sync configuration exists. Failure is reported as an open post-integration local-sync
gate; it cannot roll back or conceal the already-recorded Git integration.

A successful command updates future sessions. The final report must state that an existing
interactive Pi session needs `/reload` to reload the extension and resource catalogue.

## Security and data invariants

- Canonicalize every source, checkout, destination, settings, and backup path before use.
- Reject path escape, symlinked owned roots, submodules, special files, executable ambiguity,
  malformed settings, duplicate package identities, and dirty or wrong-head checkouts.
- Never copy repository secrets, `.git`, ticket-autopilot ledgers, sessions, or ignored
  planning sources into skill destinations.
- Do not place actor/evidence or private source contents in command output beyond bounded
  receipt fields.
- POSIX retains the mandatory zsh wrapper. The confirmed Windows exception resolves the
  existing npm launcher to its native Node entry point, without executing a shell string.
  Arbitrary executable overrides, binary installation and ownership bypass remain out of scope.

## Acceptance outcomes

1. An exact integrated head creates or advances the dedicated local checkout, replaces only
   owned skill roots, runs `pi install <checkout-locale>`, preserves `skills: []`, and passes
   `pi list` readback.
2. Replaying the same request produces no content or settings drift and no duplicate package
   entry.
3. A second integrated head updates changed/added owned skills and removes a missing skill
   only when the previous manifest proves ownership.
4. An unrelated skill directory and unrelated Pi package/settings fields remain byte- or
   semantics-equivalent across success and recovery.
5. Wrong commit/tree, dirty checkout, malformed package manifest, path escape, symlink,
   submodule, special file, settings contradiction, duplicate package identity, failed Pi
   command, or failed readback stops safely with no success receipt.
6. The workflow never invokes Pi self-update commands and never treats pre-integration state
   as a synchronization trigger.
7. The status/final report exposes the bound head/tree, local checkout, owned-skill digest,
   installation/readback state, limitations, and `/reload` requirement without claiming the
   running session reloaded.
8. A supported Windows npm Pi installation without zsh completes disposable-home install,
   list and exact replay using the same transaction; shell-sensitive paths and the approved
   settings root arrive literally, with no real-user settings or resources changed by tests.
9. Missing Node/Pi, a mismatched or unsupported launcher, invalid UTF-8 output and failed
   install/list remain failures with preserved owned-state recovery. Existing POSIX command
   behavior and transaction tests continue to pass.

## Implementation slice

One tracer-bullet ticket should add:

- a lock-serialized, receipt-backed local synchronization module and CLI;
- exact integrated-head and owned-skill manifest validation;
- atomic owned-directory replacement and bounded recovery;
- platform-specific installed-Pi `pi install` plus `pi list` readback;
- exact migration from the existing filtered Git package to one filtered local package;
- the post-integration mandatory policy instruction and status reporting;
- disposable-home tests for success, replay, update/removal, external preservation, command
  failure, readback contradiction, path/mode hazards, crash phases, and pre-integration
  non-triggering;
- operator documentation stating that `/reload` is required for an active session.

WPI-01 is one follow-up vertical: replace the transaction's shell-string seam with a
package-command seam, implement the Windows npm resolver/native process adapter, preserve
POSIX semantics, exercise the complete disposable transaction and update operator guidance.
No new persistent schema, authority store or automatic gate resolution is needed.

## Verification strategy

- **Unit:** path containment, manifest ownership/digests, settings transformation, command
  construction, receipt replay, and trigger classification.
- **Integration:** disposable Git repositories and HOME directories with a fake Pi package
  command; assert exact files, settings, invocations, rollback/recovery, and idempotency.
- **Windows process boundary:** native Node runs a disposable package CLI fixture to observe
  literal argv/environment and UTF-8 output; additionally test the installed Pi CLI against
  disposable configuration only when available. Missing executables are skips/limits, not
  passes. Neither fixture nor disposable CLI evidence proves the real user install updated.
- **Regression:** package extension tests, Ticket Autopilot tests, forward scenarios, static
  checks, and controlled context-budget checks.
- **Live manual boundary:** after integration and separate local-sync authority, run against
  the real dedicated checkout and inspect `pi list`; do not claim an active session reloaded
  until the user executes `/reload`.

## Authority

The user selected synchronization of both `~/.agents/skills` and the local Pi package. This
specification is not merge authority and is not itself a durable actor/evidence-bound live
configuration grant. The implementation run remains manual unless separately authorized.
