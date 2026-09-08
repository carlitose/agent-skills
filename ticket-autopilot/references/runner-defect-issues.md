# Runner-defect issue publication

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

Runner-defect issue publication is also orthogonal. `runner-defect-issue-grant` registers one
repository-scoped, revocable authority for exactly `carlitose/agent-skills`; no run, gate, provider
access, AFK mode, or merge grant implies it. `runner-defect-issue-escalate <run> <record> --dry-run`
validates strict high-confidence diagnosis, redaction, stable fingerprint, exact run-ledger binding,
and fixed rendering without a provider call or sidecar write. Live escalation negotiates GitHub
issue capabilities, searches open and closed issues by the exact marker, creates only with the `bug`
label, and persists an integrity-wrapped Git-common outbox receipt. Exact matches never comment,
reopen, relabel, or edit. Revocation blocks new mutations; ambiguous sends permit read-only
exact-search reconciliation but never automatic recreation. Escalation holds the canonical run lock
and proves `ledger.json` byte identity before returning.

## Operator procedure

### Opt-in runner-defect issue publication

Runner-defect escalation is a separate, repository-scoped lifecycle. It cannot pass a
run gate, change a ticket, authorize merge, or inherit any of those authorities. It is
hard-bound to `carlitose/agent-skills`, GitHub, the `bug` label, and the accepted
[publication
decision](../../docs/specs/ticket-autopilot-runner-defect-issue-publication-decision.md).
No publication grant is created by a run or installation.

1. Prepare a schema-1 diagnosis record whose `run_binding` names the run and ticket,
   the current raw `ledger.json` SHA-256, and the ticket digest. It must attest the
   diagnose redaction contract and include both deterministic-reproduction and
   runner-source-trace evidence. Local paths, credentials, tokens, multiline fields,
   weak confidence, stale bindings, and unknown fields fail closed.
2. Register the separate durable authority, retaining the returned `authority_id`:

   ```bash
   python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
     runner-defect-issue-grant --repo . \
     --actor '<identity>' --evidence '<durable-decision-ref>'
   ```

3. Validate fingerprinting, redaction, rendering, run-ledger protection, and authority
   without a provider call or outbox write:

   ```bash
   python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
     runner-defect-issue-escalate <run-id> <diagnosis.json> --repo . --dry-run
   ```

4. Only under separate live-publication authority, omit `--dry-run`. The runner first
   negotiates GitHub issue capabilities, searches open and closed issues in the exact
   repository, and compares the full hidden fingerprint marker. One exact match writes
   only a local deduplication receipt: it never comments, reopens, labels, or edits the
   issue. No match reserves a crash-safe intent, creates one issue with only `bug`, reads
   it back, and writes an integrity-wrapped receipt binding issue, body hash, actor,
   grant, fingerprint, and provider evidence.
5. Revoke future mutation with the exact active grant:

   ```bash
   python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
     runner-defect-issue-revoke <authority-id> --repo . \
     --actor '<identity>' --evidence '<durable-revocation-ref>'
   ```

Use `runner-defect-issue-status --repo .` for local authority inspection. Revocation
blocks new mutations immediately. A known non-send may retry after a fresh exact search;
an ambiguous dispatch never creates again automatically. Replay performs read-only
exact-marker reconciliation, finalizes if the issue is found, and otherwise remains
`dispatch-ambiguous` for human investigation. Outbox receipts live outside the worktree
under the Git common directory and are retained indefinitely. Never delete one to force
a retry.
