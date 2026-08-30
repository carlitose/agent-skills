# Ticket Autopilot zero-to-autopilot private bootstrap

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-zero-to-autopilot-private-bootstrap`
- Role: spec
- Standalone: true

### Children

- [ZTA-01 — Add exact-inventory private zero-to-autopilot bootstrap](../tickets/ticket-autopilot-zero-to-autopilot-private-bootstrap/01-add-exact-inventory-private-zero-to-autopilot-bootstrap.md)

## Type

Feature specification.

## Decision

Ticket Autopilot will provide a separate, explicit `zero-to-autopilot` transaction that can
turn one existing local directory into a scheduler-ready private GitHub repository when Git
and/or `origin` is absent. The transaction binds one exact, complete initial filesystem
inventory before it initializes Git, creates a root commit, configures `origin`, or mutates
GitHub.

This capability is independent from repository-wide merge authority. It creates no run,
implements no ticket, and grants no PR, merge, conflict-resolution, source-publication,
wiki-sync, Pi-sync, cleanup, visibility-change, or future-bootstrap authority.

## Current behavior

`bootstrap-private-github` safely creates or adopts one private GitHub repository, configures
an absent/equivalent `origin`, publishes one exact existing base commit, and establishes the
default branch. It requires an already valid local Git repository, branch, and exact base
SHA. Ticket Autopilot cannot start when the project directory has no Git metadata because it
has no place to bind the base commit or persist the existing bootstrap intent.

Directly running `git init`, `git add -A`, and `gh repo create --push` is not acceptable:
that sequence has no pre-mutation authority record, may publish unreviewed secrets or
untracked files, cannot prove an exact initial tree, and is ambiguous after a crash.

## Target behavior

### Read-only inventory preparation

A provider-free command prepares a canonical inventory manifest for one absolute directory.
It performs no Git or provider mutation. The manifest binds:

- schema and inventory digest;
- canonical root path;
- every pre-existing non-Git filesystem entry as a normalized relative path;
- entry type, byte digest, size, and executable/non-executable Git mode for regular files;
- an explicit `publish` or `exclude` disposition for every regular file;
- the requested base branch and private GitHub target; and
- scanner findings that require exclusion or explicit human review.

The walk rejects path escape, duplicate/case-colliding paths, `.git` content, nested Git
repositories, symlinks, submodules, sockets, devices, FIFOs, unsupported modes, unreadable
entries, and inventory output placed inside the source directory. Empty directories have no
Git representation and are reported separately but never published implicitly.

Known credential-bearing names and private-key/token markers are never automatically marked
`publish`. Detection is a safety floor, not proof that content is non-secret. Application
requires an exact manifest digest in durable actor/evidence authority; files absent from the
manifest can never enter the initial commit.

### Apply transaction

An explicit apply command requires:

```text
zero-to-autopilot \
  --repo <absolute-directory> \
  --target <owner/repository> \
  --visibility private \
  --base <branch> \
  --inventory <absolute-manifest> \
  --inventory-sha256 <exact-digest> \
  --actor <identity> \
  --evidence <durable-ref>
```

Before mutation it revalidates the manifest digest, canonical root, target, branch, every
entry and disposition, and current full inventory. For a directory without `.git`, it then:

1. creates only `.git/ticket-autopilot/` and atomically persists an immutable,
   integrity-wrapped zero-bootstrap intent there;
2. initializes Git on the authorized branch without changing global configuration;
3. stages only `publish` entries by explicit path, never `git add -A`;
4. proves index modes/blobs and the resulting tree against the manifest;
5. creates one root commit with a fixed bootstrap message and records its exact SHA; and
6. delegates private repository creation/adoption, equivalent-origin configuration,
   non-force base publication, and default-branch readback to the existing audited
   repository-bootstrap transaction.

`git init` may populate the pre-created `.git` directory but must preserve the intent file.
A crash at any phase re-enters only the same immutable transaction. A partially initialized
repository is recoverable only when its zero-bootstrap state matches the exact request.

For an existing Git repository with no `origin`, the command requires an explicit exact
base SHA. It proves that the named branch and committed tree match the manifest's `publish`
entries exactly, leaves history and index untouched, and delegates to the existing private
bootstrap transaction. An existing equivalent `origin` is admissible; a different origin is
a contradiction.

### Completion

Completion requires live readback of the private repository identity, exact remote base SHA,
equivalent origin, and default branch. The immutable receipt also records the inventory
digest, initial tree, local mode (`initialized` or `existing`), root commit/base SHA, actor,
evidence, and the digest of the nested repository-bootstrap receipt.

Successful output is `repository-ready-for-ticket-autopilot`. Starting a run remains a
separate command using a canonical ticket folder.

## Goals

- Safely recover from missing Git and/or missing `origin` without operator shell steps.
- Publish only one explicitly authorized private repository and one exact initial tree.
- Make every local and remote mutation crash-replayable and provenance-bound.
- Reuse the existing private GitHub bootstrap instead of duplicating provider semantics.
- Leave the resulting repository ready for normal Ticket Autopilot planning and runs.

## Non-goals

- Public or internal repository creation.
- Initializing an arbitrary nonempty Git history, rewriting commits, rebasing, or force
  pushing.
- Automatically deciding that unknown content is safe to publish.
- Publishing symlinks, nested repositories, submodules, special files, or files outside the
  exact inventory.
- Creating a ticket run or inferring ticket, merge, repository-wide, wiki, Pi, cleanup, or
  conflict authority.
- Deleting, renaming, transferring, changing visibility, or repairing later remote drift.
- Updating the Pi binary or installed skill package.

## Semantic invariants

1. Exact inventory authority is persisted before `git init`, staging, commit, origin, push,
   or provider mutation.
2. The full preexisting filesystem inventory is complete; every regular file has exactly one
   explicit disposition.
3. Only exact `publish` paths with matching bytes and modes enter the initial Git tree.
4. Scanner output cannot silently upgrade a risky file to publishable authority.
5. No global Git configuration is read as authority or mutated by the transaction.
6. Existing Git history and index are never rewritten; existing mode requires one explicit
   branch/base SHA and exact tree equivalence.
7. Repository creation remains private-only and GitHub-host-pinned.
8. `origin` may be absent or exactly equivalent; every conflicting fetch or push URL fails.
9. The base is published only when absent or already exact and never with force.
10. Exact replay is idempotent; contradiction, corruption, symlinked state, inventory drift,
    or unexpected refs fail before further mutation.
11. A completion receipt verifies current state but never authorizes later repair.
12. Zero-bootstrap authority transfers to no run, delivery, merge, source, wiki, Pi, cleanup,
    visibility, or unrelated repository action.

## Failure modes

| Failure | Required result |
|---|---|
| Inventory changes after preparation | Fail before Git/provider mutation. |
| Risky or unreviewed file is marked `publish` | Fail with the exact path/finding. |
| New, deleted, byte-drifted, or mode-drifted entry appears | Fail; require a new manifest and authority. |
| `.git` already exists but is malformed or has unexpected refs | Fail unless it is an exact replay of this transaction. |
| Existing repository base SHA/tree differs | Fail without staging, committing, or rewriting. |
| Commit crashes after index/tree creation | Replay proves the exact tree and creates or adopts only the matching root commit. |
| Origin points elsewhere or has conflicting push URLs | Fail without editing it. |
| Remote repository is public, nonempty, or contradictory | Fail without push or visibility change. |
| Remote base exists at another SHA | Fail without force. |
| Crash after remote creation/push/default branch | Existing nested bootstrap replay performs live exact readback without duplicate mutation. |
| Completed local or remote state later drifts | Report contradiction; completion grants no repair authority. |

## Security and data concerns

- Inventory artifacts contain paths and hashes, never file contents, credentials, environment
  dumps, or provider tokens.
- State and manifests reject symbolic-link traversal and unsafe parent/state paths.
- Commands pass explicit path lists and `--` separators; paths are never shell-expanded.
- Provider output is normalized and secret-safe before persistence.
- Large inventories have deterministic file-count and byte-size bounds; exceeding a bound
  fails with no partial publication.
- GitHub API calls remain pinned to `github.com` and existing strict 404/409/private
  classifications.

## Compatibility

The existing `bootstrap-private-github` command and completed bootstrap receipts remain
unchanged. `zero-to-autopilot` composes that transaction after establishing or proving an
exact local base. No legacy repository is auto-migrated and no existing run is changed.

## Implementation slice

One tracer-bullet ticket owns:

- canonical inventory generation/validation and secret-risk fail-closed rules;
- pre-Git intent persistence, initialization, explicit staging, exact tree/root-commit
  creation, and crash replay;
- existing-Git/no-origin exact-tree mode;
- composition with the existing private repository bootstrap;
- CLI, status/receipt, documentation, context-budget, and artifact graph updates; and
- disposable filesystem/Git/fake-GitHub tests plus full regression and forward scenarios.

## Verification strategy

### Unit

- Manifest canonicalization, digest, path/mode/type constraints, collisions, bounds, and
  risky-file classifications.
- Immutable intent/receipt, hash chain, corruption, symlink, contradiction, and exact replay.
- Explicit index/tree mapping excludes every `exclude` entry.

### Integration

- Real temporary non-Git directories and Git repositories with bare local remotes plus the
  deterministic GitHub command boundary.
- Crash injection before/after state creation, Git init, add/tree, commit, origin, push,
  default branch, and final readback.
- Prove no global Git config mutation, no `git add -A`, no force push, and no provider call
  before persisted authority.
- Existing-Git/no-origin and equivalent-origin paths preserve history and index exactly.
- Full Ticket Autopilot suite, extension tests, forward scenarios, context measurement, and
  artifact-audit delta.

### Live boundary

A real directory and target repository require separate exact manifest, actor, and evidence
authority. Without that input, tests may claim only local behavior with simulated provider
transport. No test may manufacture live repository-creation authority.

## Acceptance outcomes

1. A non-Git directory can become one private GitHub repository whose first branch tree
   exactly matches the authorized `publish` inventory.
2. Excluded, risky, unlisted, drifted, symlinked, nested-repository, and special-file entries
   cannot be committed or published.
3. A Git repository without `origin` can publish one explicit exact base without changing
   history or index.
4. Intent exists before every Git/provider mutation and every crash boundary replays without
   duplicate initialization, commit, repository creation, origin edit, or push.
5. Existing remote identity, visibility, branch SHA, and default branch contradictions fail
   closed without force, deletion, transfer, rename, or visibility mutation.
6. Completion reports exact inventory/tree/base/private/default-branch readback and grants no
   adjacent authority.
7. Existing private-bootstrap, merge, queue, repository-authority, source, wiki, and Pi
   contracts remain unchanged.

## Open questions

None block implementation. Applying the capability to a real project remains a separate,
manifest-digest-bound authority decision.
