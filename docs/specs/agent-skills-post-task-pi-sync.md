# Synchronize the local agent-skills Pi package after integrated tasks

## Artifact Graph

- Artifact ID: `spec:agent-skills-post-task-pi-sync`
- Role: spec
- Standalone: true

### Children

- [PIS-01 — Synchronize exact integrated agent-skills into Pi](../tickets/agent-skills-post-task-pi-sync/01-synchronize-exact-integrated-agent-skills-into-pi.md)

## Type

Feature specification.

## Decision

After an `agent-skills` ticket reaches the durable Ticket Autopilot state `integrated`, the
workflow must synchronize the exact integrated revision into Pi. It must not trigger when
implementation, review, verification, PR creation, or an attempted merge merely finishes.

The synchronization has two ordered outputs:

1. update the `agent-skills`-owned directories under `~/.agents/skills`, preserving every
   external skill directory; then
2. invoke the normal zsh-resolved command `pi install <checkout-locale>` and verify the
   installed local package with `pi list`.

This is a local package refresh. It must never invoke `pi update`, `pi update --self`, or
otherwise update the Pi binary.

## Evidence and current state

Pi's package documentation says that an absolute local package path is referenced directly
from settings rather than copied, and that `/reload` or a new session is needed to reload
active resources. The repository already declares its extension and top-level skills in
`package.json`.

The current machine has:

- a pinned `git:github.com/carlitose/agent-skills@...` Pi package with `skills: []`;
- copied skills under `~/.agents/skills`;
- Pi-facing symlinks under `~/.pi/agent/skills` that resolve to those copied skills.

Blindly adding a local package would therefore duplicate the extension and could duplicate
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

After the skill replacement succeeds, invoke Pi through the normal zsh wrapper, passing the
checkout as a positional argument without shell interpolation:

```text
zsh -lic 'PI_CODING_AGENT_DIR="$1" pi install "$2"' agent-skills-pi-sync <absolute-pi-config-dir> <absolute-checkout>
```

The first migration may replace only the exact installed
`git:github.com/carlitose/agent-skills@...` entry. The resulting local package entry keeps
`skills: []`, because those skills are already loaded through `~/.agents/skills`; the local
package supplies the extension. All unrelated settings bytes and package entries remain
semantically unchanged.

Pin `PI_CODING_AGENT_DIR` to the parent of the actor-approved `settings.json` for both
commands. Read back `pi list` through the same zsh resolution and require exactly one effective
`agent-skills` package at the dedicated local checkout. A partial or contradictory readback
is failure, not success.

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
- The zsh wrapper is mandatory for Pi invocation; direct absolute Pi paths intentionally
  remain out of scope.

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

## Implementation slice

One tracer-bullet ticket should add:

- a lock-serialized, receipt-backed local synchronization module and CLI;
- exact integrated-head and owned-skill manifest validation;
- atomic owned-directory replacement and bounded recovery;
- normal-zsh `pi install` plus `pi list` readback;
- exact migration from the existing filtered Git package to one filtered local package;
- the post-integration mandatory policy instruction and status reporting;
- disposable-home tests for success, replay, update/removal, external preservation, command
  failure, readback contradiction, path/mode hazards, crash phases, and pre-integration
  non-triggering;
- operator documentation stating that `/reload` is required for an active session.

## Verification strategy

- **Unit:** path containment, manifest ownership/digests, settings transformation, command
  construction, receipt replay, and trigger classification.
- **Integration:** disposable Git repositories and HOME directories with a fake zsh-resolved
  Pi command; assert exact files, settings, invocations, rollback/recovery, and idempotency.
- **Regression:** package extension tests, Ticket Autopilot tests, forward scenarios, static
  checks, and controlled context-budget checks.
- **Live manual boundary:** after integration and separate local-sync authority, run against
  the real dedicated checkout and inspect `pi list`; do not claim an active session reloaded
  until the user executes `/reload`.

## Authority

The user selected synchronization of both `~/.agents/skills` and the local Pi package. This
specification is not merge authority and is not itself a durable actor/evidence-bound live
configuration grant. The implementation run remains manual unless separately authorized.
