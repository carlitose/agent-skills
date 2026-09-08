# Bootstrap a private repository

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

`prepare-zero-to-autopilot --repo <absolute-directory> --target <owner/repository> --visibility
private --base <branch> --output <absolute-external-path>` performs a provider-free bounded scan and
writes a canonical exact inventory outside the source tree. Entries bind regular-file path, digest,
size, mode, risk findings, and publish/exclude disposition; links, special files, nested Git
metadata, unsafe/colliding paths, unreadable content, or inventory drift fail closed.
`zero-to-autopilot` requires that manifest's exact SHA-256 plus separate actor/evidence authority.
It persists immutable intent before `git init`, explicit staging, commit, origin, push, or provider
mutation; new Git receives one exact root tree, while existing Git additionally requires
`--base-sha` and preserves history/index. The command composes only the audited private GitHub
bootstrap, rechecks tree/base/origin/default branch, and records an integrity-wrapped append-only
receipt. Replay re-observes without duplicate init/commit/create/push. `zero-to-autopilot-status` is
provider-free. This authority grants no run, implementation, PR, merge, conflict resolution, source,
wiki, Pi, cleanup, visibility change, or future bootstrap.

`bootstrap-private-github --repo <absolute-root> --target <owner/repository> --visibility private
--base <branch> --base-sha <sha> --actor <identity> --evidence <durable-ref>` persists one immutable
Git-common intent before creating/adopting the exact private repository, configuring only an
absent/equivalent `origin`, non-force publishing an absent exact base, and verifying live
default-branch readback. Replay re-observes and emits no duplicate mutation; contradictions fail
closed. Bootstrap grants no run, PR, merge, wiki-sync, cleanup, or future authority.

## Operator procedure

## Exact-inventory zero-to-autopilot bootstrap

A directory with no Git repository, or an existing local repository with no `origin`, can be
bound to one exact initial file inventory and one private GitHub target. Inventory preparation is
provider-free and must write outside the source directory:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  prepare-zero-to-autopilot --repo "$PWD" --target owner/repository \
  --visibility private --base main --output /absolute/private/inventory.json
```

Review the canonical manifest. Every regular file has a path, SHA-256, size, executable mode,
risk findings, and explicit `publish` or `exclude` disposition; symbolic links, special files,
nested Git metadata, unsafe paths, case collisions, unreadable content, and configured bounds fail
closed. Risky names or credential markers are excluded, never silently deemed safe. The manifest
does not confer authority. Apply it only with its exact digest and separate durable actor/evidence:

```bash
INVENTORY_SHA=$(shasum -a 256 /absolute/private/inventory.json | awk '{print $1}')
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  zero-to-autopilot --repo "$PWD" --target owner/repository \
  --visibility private --base main \
  --inventory /absolute/private/inventory.json --inventory-sha256 "$INVENTORY_SHA" \
  --actor "alice@example.com" --evidence "artifact://change-123/zero-bootstrap"
```

For existing Git, add `--base-sha <exact-branch-sha>`; the branch tree must equal the authorized
publish inventory, while history, refs, worktree, and index remain intact. For missing Git, the
command persists the immutable intent under the future `.git` directory before `git init`, builds
only the explicitly published paths (never `git add -A`), creates one root commit, and then
composes the audited private GitHub bootstrap. A lock, integrity-wrapped append-only events,
exact tree/base/remote/default-branch readback, and contradiction-safe replay cover every crash
boundary. `zero-to-autopilot-status --repo <absolute-root>` is provider-free.

This one-shot authority grants only the exact local/private bootstrap. It grants no Ticket
Autopilot run, implementation, source promotion, PR, merge, conflict resolution, wiki, Pi,
cleanup, visibility change, or future bootstrap, and never deletes or rewrites unrelated state.

## Private GitHub repository bootstrap

A new local repository can establish its private GitHub target and first base branch without
an operator-side `gh` or `git push` prerequisite. Supply one exact bootstrap authority before
starting a folder run:

```bash
BASE_SHA=$(git rev-parse refs/heads/main)
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  bootstrap-private-github --repo "$PWD" --target owner/repository \
  --visibility private --base main --base-sha "$BASE_SHA" \
  --actor "alice@example.com" --evidence "artifact://change-123/bootstrap"
```

`--repo` must be an absolute repository-root path. Before any create, remote edit, push, or
default-branch update, the command stores one immutable actor/evidence-, target-, branch-, and
SHA-bound intent under Git common state and holds its lock. It creates or adopts only the exact
private repository, accepts only an absent or equivalent `origin`, pushes a non-force exact-SHA
refspec only when the remote base is absent, and verifies live repository, visibility, branch,
SHA, URL, and default-branch readback. Exact replay is byte-stable and performs no second create
or push; crash recovery re-observes each boundary. Any contradiction fails without delete,
visibility change, remote rewrite, force, or overwrite.

This authority is a one-repository prerequisite transaction. It grants no delivery, PR, merge,
wiki-sync, cleanup, or future bootstrap authority. Public/internal creation, transfer, rename,
delete, visibility changes, and divergent-base adoption remain unsupported.
