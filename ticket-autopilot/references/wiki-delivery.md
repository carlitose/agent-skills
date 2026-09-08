# Post-integration wiki delivery and exact retry

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

After durable integration, run separate `wiki-sync-v1` against a detached exact-head source; the
ticket is provenance only and docs-only v1 never widens. Resolve the canonical project root from
that exact source. When it is another checkout, require exact provider and normalized-remote
agreement with the run repository, materialize the source through the canonical target repository,
freeze only under its Git common candidate store, and persist a content-addressed target receipt
before provider observation. Publication and approval use that target as their Git cwd;
cross-repository, unsafe-path, stale-source, candidate, manifest, receipt, or persisted-target
contradictions fail closed without touching either worktree. External or internal-untracked output
may apply directly. Internal-tracked output is a fresh `WikiSyncRef`/CandidateRef with no inherited
verification, PR, or authority. `llm-wiki` never commits or delivers; persist its result separately
and keep failure prominent/retryable without rewriting the ticket. Tracked PRs require exact-head
`approve <run> --wiki-sync --ticket <id> --head-sha <head> --actor <id> --evidence <ref>` or a
separate autonomous wiki grant; application grants never transfer. `wiki-delivery-retry-status` and
`retry-wiki-delivery` cover the exact eligible historical pre-provider failures described below:
bind record SHA-256 plus actor/evidence, persist intent and the full predecessor, restore
`delivery-pending`, and stop provider-free. Replay is exact and idempotent;
provider/PR/authorization evidence or drift is ineligible, and ordinary `resume` remains the only
publication path.

## Operator procedure

### Canonical tracked-wiki delivery and exact local retry

Internal wiki bindings are portable: `project_root` is relative to the directory
containing `llm-wiki-project.json`, never the command's working directory. Scaffold
writes `..` for `knowledge/`, `.` for a root-level wiki, and an absolute root for an
external wiki. The same committed binding therefore follows each clone or relocation.
Absolute bindings remain deliberately checkout-pinned; a missing target fails rather
than silently selecting another checkout. Other schema-1 settings are unchanged.

Exact-source sync validates the expected head and shared Git common directory, reads
the internal relative binding in that source layout, and projects it onto the explicit
canonical project root. Only disposable compile copies receive a temporary absolute
binding; original config bytes are restored before candidate comparison. Empty layout
directories omitted by Git are materialized only in that compile copy. Root-level
wikis still permit only generated `wiki/**/*.md` candidate changes. Missing local
session transcripts remain unavailable provenance warnings, not a project-doc gate.
Copying a wiki or matching remotes never copies runtime ledgers or authority.

A deliberately absolute post-integration binding may instead name a canonical project
checkout that is not the run clone. The runner derives that target only from the exact
integrated source, then requires both checkouts to have the configured provider and the
same normalized remote. It creates a detached exact-head source from the target repository,
freezes the candidate only under that target's Git common directory, and persists a
content-addressed delivery-target receipt before any provider observation or push.
Publication, exact-head approval, and merge execute with the canonical target as the
Git working directory. A different provider, remote, repository root, wiki-relative
path, candidate store, manifest, validation receipt, source head, or unsafe/symlinked
path fails closed; neither worktree is rewritten by target discovery.

Frozen wiki storage uses native Windows long-path I/O without changing its digest-addressed
layout, file names, bytes, manifests, or logical identities. Git receives POSIX-relative
index paths and hashes literal frozen bytes through bounded binary stdin, not long
filename arguments. Failed filesystem access is not evidence of a regular file; unsafe
file types, reparse links, executable files, invalid UTF-8 and digest drift still fail.
Drive and UNC spelling are supported at this I/O boundary; local fixtures do not prove
access to a live network share.

A historical run that terminated before provider activity with exactly
`delivery-invalid: tracked wiki candidate is outside the project repository` can use
one narrow provider-free transaction. It also accepts the exact historical
`delivery-invalid: tracked wiki candidate contains a non-regular path` only on Windows,
after revalidating the canonical target, every frozen file and both receipts, with an
actual long candidate path (at least 260 characters). Error text alone is insufficient;
short paths, truly invalid files, prior provider state and ambiguous outcomes are ineligible.
Inspect eligibility and copy the exact reported record digest:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  wiki-delivery-retry-status my-change --repo . --ticket "01"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  retry-wiki-delivery my-change --repo . --ticket "01" \
  --expected-record-sha256 "$RECORD_SHA256" \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/wiki-delivery-retry"
```

The retry requires the exact terminal record, intact frozen candidate and receipts,
no prior PR/provider/authorization state, and the same canonical target identity. It
persists intent before replacement, embeds the complete predecessor record, reads the
ledger back, and is idempotent for the same actor/evidence request. Long-path replay also
revalidates the unchanged candidate and target. It only restores
`delivery-pending`; it never contacts the provider, publishes, pushes, merges,
approves, cleans up, synchronizes Pi, or grants authority. Run ordinary `resume`
afterward so the existing wiki policy performs any publication, and use a separate
exact-head wiki approval when that policy is manual. The regular `status` output also
projects per-ticket `wiki_delivery_retry` eligibility and receipt state. An `applied`
receipt proves only local preparation; it is not evidence that a later resume published.
