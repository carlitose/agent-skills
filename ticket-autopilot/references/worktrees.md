# Worktree ownership and cleanup

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

New runs persist immutable `worktree-owner-v1` manifests. `worktree-owner-adopt <run>
--expected-ledger-sha256 <sha> --actor <identity> --evidence <durable-ref>` is the only legacy
adoption path: it binds the exact valid ledger, repository, Git registration, managed path, base,
and ticket snapshot without granting cleanup. `worktree-gc-plan --repo <repository> [--protect
<absolute-path>]...` acquires run locks non-blockingly and writes a deterministic digest-addressed
local plan. It never contacts a provider or removes anything. Only manifest-proven, completed,
integrated, clean (including ignored state), unlocked, retained, operationally unreferenced entries
are eligible; ambiguity, open wiki delivery, incomplete Pi sync, interrupted Git, invalid ownership
inventory, and unmanaged paths remain protected. Eligibility is not cleanup authority.
`worktree-gc-apply <plan-path> --expected-plan-sha256 <sha> --actor <identity> --evidence
<durable-ref>` acquires the repository and complete eligible lock set, requires exact plan
revalidation plus all-entry preflight, persists intent first, removes only with ordinary `git
worktree remove`, reads back absence, records ledger cleanup, and writes immutable
per-entry/completion receipts. Exact replay verifies prior effects; stale input or contradiction
stops before another removal. It never uses force/prune, deletes branches/remotes/evidence, contacts
a provider, or grants merge, publication, Pi-sync, reload, or lifecycle authority.

`worktree-sweep --repo <repository>` is the convenience boundary for phase-end hygiene. Without
`--apply` it reports, but does not remove, the exact GC-eligible owned worktrees plus registered
`ticket-wiki-*` children of the operating-system temp directory. A live wiki temporary holds a
crash-releasing lease and appears transiently in its run ledger, so it stays protected; an absent
or unlocked lease identifies an orphan left after a killed process. `--apply` additionally requires
`--actor` and `--evidence`: owned worktrees still pass unchanged through `worktree-gc-apply`, while
only those narrowly identified wiki temporaries may use forced removal. Every removal has an
immutable path/reason/result receipt. Other unmanaged paths and every protected entry are inert.

## Operator procedure

Abort records who stopped the run and why. Cleanup removes only the safe
isolated worktree and preserves the ledger; it never deletes remote branches or
PRs. Aborted or failed runs require `--confirm`, waiting runs require `--force`,
and running runs cannot be cleaned:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  abort my-change --repo . --actor "alice@example.com" --reason "requirements changed"
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  cleanup my-change --repo . --confirm
```

After a normally completed run, use the same `cleanup` command without
`--confirm`.

Every new run also persists an immutable `worktree-owner-v1` manifest in its
Git-common run directory. A legacy worktree has no ownership merely because its
path looks runner-shaped; adopt one exact valid ledger explicitly before it can
appear in a garbage-collection plan:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  worktree-owner-adopt my-change --repo . \
  --expected-ledger-sha256 "$LEDGER_SHA256" \
  --actor "alice@example.com" --evidence "artifact://change-123/worktree-owner"
```

`worktree-gc-plan` then acquires run locks non-blockingly and writes one
digest-addressed, provider-free plan under the Git common directory. It lists
every valid owned worktree as `eligible` or `protected`, reports unmanaged Git
worktrees without claiming them, and accepts repeated explicit protected paths:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  worktree-gc-plan --repo . --protect /absolute/path/to/keep
```

Running, nonterminal, dirty (including ignored files), locked, interrupted,
unretained, cross-referenced, open-wiki, incomplete-Pi-sync, malformed, primary,
and invocation worktrees stay protected. Planning never contacts a provider or
removes a worktree. Adoption grants no cleanup or other repository authority;
an eligible plan is not deletion authority.

Apply only an exact reviewed plan with separate actor/evidence-bound local
authority:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  worktree-gc-apply "$PLAN_PATH" --repo . \
  --expected-plan-sha256 "$PLAN_SHA256" \
  --actor "alice@example.com" --evidence "artifact://change-123/worktree-gc"
```

Application takes the repository GC lock and every eligible run lock, rechecks
the complete plan before the first removal, persists intent, and uses ordinary
`git worktree remove` without `--force`. Filesystem and Git-registration absence,
ledger cleanup, per-entry receipts, and the completion receipt are read back and
preserved. Replay uses the same plan, actor, evidence, and intent; prior exact
effects are verified, while any stale input or post-intent contradiction stops
before another removal. It never prunes metadata, deletes branches/remotes, or
grants provider, merge, publication, Pi-sync, reload, or lifecycle authority.

At a phase end, inspect the combined sweep first. Apply only after reviewing its exact output:

```bash
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  worktree-sweep --repo .
"$TICKET_AUTOPILOT_PYTHON" -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  worktree-sweep --repo . --apply \
  --actor "alice@example.com" --evidence "artifact://change-123/worktree-sweep"
```

`--apply` is cleanup authority only for that invocation. It grants no disposition for a dirty or
protected worktree and no authority over another repository.
