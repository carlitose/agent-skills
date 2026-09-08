# Legacy run recovery and budget repair

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

Explicit `migrate-run-lifecycle` validates schema-3 history, preserves its chain, and appends one
audited v4 event. `compact-run-ledger` alone compacts history; event hashes stay fixed.

For pre-epoch schema-4 runs, `revalidation-budget-repair` binds the exact tree, rebuilds matching
progress, preserves retries, and appends one idempotent audit event. Use it for legacy false
exhaustion; real exhaustion opens a durable `resource-budget` gate.

## Operator procedure

### Exact legacy-run recovery

Legacy recovery is a separate local authority boundary. `prepare-legacy-recovery`
reads an explicit JSON inventory (`schema` plus ordered `runs` with `run_id`,
`action`, `reason`, and nullable `successor_run_id`) and writes a canonical,
provider-free manifest outside the repository. It does not mutate run state.
After separately approving the reported digest, apply that exact file with:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  apply-legacy-recovery --repo "$PWD" --manifest /secure/recovery.json \
  --manifest-sha256 <reported-digest> --actor "alice@example.com" \
  --evidence "decision://change-123/exact-legacy-recovery"
```

Application persists immutable intent before effects, rechecks every input under
repository and run locks, migrates only schema 3, and retires schema 1/2 without
rewriting `ledger.json`. `legacy-recovery-status` distinguishes migrated, retired,
failed, and untouched entries. Only an exact active retirement lets `merge-all`
report `retired-legacy`; malformed, stale, absent, or revoked state fails closed.
Retirement grants no ticket completion, provider, source, cleanup, wiki, Pi, or
merge authority. `revoke-legacy-retirement` appends a revocation and an old manifest
cannot reactivate it.
