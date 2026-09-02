# Migrate the Pi owned-skill source explicitly

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-pi-owned-skill-source-migration`
- Role: spec
- Parent: [Synchronize the local agent-skills Pi package after integrated tasks](agent-skills-post-task-pi-sync.md)

### Children

- [PSM-01 — Migrate an exact owned-skill source](../tickets/ticket-autopilot-pi-owned-skill-source-migration/01-migrate-an-exact-owned-skill-source.md)

## Type

Bug-analysis specification.

## Observed behavior

RDR-05 integrated head `cc0cb94685921ae49e5f7a61105692a73addc542` and tree
`4e9929ef48ad65b0f04e1e716783c5efe35a8d1a` were materialized into the clean dedicated
Pi checkout. The post-integration transaction then stopped before skill replacement and Pi
installation with:

```text
Pi sync owned-skill manifest source drifted
```

The valid installed manifest names
`/Users/carlogiuseppesergi/Projects/.agent-skills-runner-latest` as its source repository,
while the independently delivered RDR run is durably bound to
`/Users/carlogiuseppesergi/Projects/.agent-skills-rdr-remediation-20260901`. Both checkouts
represent `carlitose/agent-skills`, but source paths are authority-bearing literals and the
current command has no explicit migration input. Cleanup of ignored bytecode made the
checkout clean but correctly supplied no source-migration authority.

The failed RDR-05 sync state is itself immutable and records only `intent-persisted` and
`checkout-materialized`. Reusing its fixed state path with a new implicit intent would either
contradict replay or rewrite historical failure.

A subsequent read-only ownership preflight found exactly three drifted prior-owned roots:
`llm-wiki`, `ticket-autopilot`, and `verification-audit`. The user explicitly authorized
replacing those three roots in
`pi-session://01a04e2a-0b7a-70fd-be3b-06500686244a/message/3ca3dada`. That decision does not
authorize any other name or any bytes differing from the observed digests bound at invocation.

## Root cause

`PiSyncRequest` has explicit first-adoption and package-source replacement flags, but no
field for an exact prior owned-manifest source. `_sync_skills` therefore has only two states:
identical source, or unconditional rejection. The CLI also maps every sync for one ticket head
to one state path, leaving no append-only successor for an explicitly authorized migration.

## Target behavior

Add `sync-local-pi --migrate-owned-source-from <absolute-repository-root>` as a narrow,
actor/evidence-bound authority.

When the option is absent, behavior remains unchanged. When present, the transaction may
replace the manifest's `source_repository` only if all of these are true:

1. a valid prior owned-skill manifest exists;
2. its source equals the exact canonical path named by the option;
3. that path differs from the current source repository;
4. every previously owned installed skill still matches its recorded digest;
5. the current source checkout is the exact durably integrated head/tree; and
6. normal package, settings, owned-root, rollback, and `pi list` checks pass.

Previously owned digest drift remains rejected by default. A caller may additionally repeat
`--replace-drifted-owned <name>=<observed-sha256>` only during an explicit source migration.
The complete sorted authorization set must equal the complete observed drift set, and every
supplied digest must equal the bytes observed immediately before backup. Missing, extra,
duplicate, stale, malformed, unowned, or non-migration replacement authority fails before
replacement. This makes the destructive decision exact rather than turning source migration
into blanket overwrite permission.

A migration request uses a deterministic successor state path derived from the exact old/new
source paths and exact drift-replacement set. It never edits, deletes, or recasts the ordinary
failed state. Exact replay uses the same successor and issues no second install after
completion. Historical states whose intent predates the optional migration fields remain
readable and replayable without rewrite.

The completed manifest records the new source. The persisted intent records the exact prior
source plus actor and evidence. A downstream failure restores the previous skills, previous
manifest bytes, and settings through the existing transaction backup.

## Semantic invariants

- Source migration is opt-in and exact; basename, remote similarity, symlink aliases, or a
  caller's new source path alone never authorize it.
- `--adopt-existing-owned` does not imply source migration, and
  `--replace-package-source` remains limited to the Pi package entry.
- A migration flag with no prior manifest, the wrong prior source, or no actual source change
  fails before replacing skills or invoking Pi.
- Previously owned skill drift remains a hard failure unless every drifted name and its exact
  observed SHA-256 are independently authorized; source migration alone never overwrites it.
- The old failed state, its integrity wrapper, phase list, error, and intent remain literal.
- Exact integrated head/tree, local checkout, agents root, settings path, actor, and evidence
  retain their existing meanings.
- Migration grants no merge, provider, wiki, cleanup, Pi self-update, active-session reload,
  or future migration authority.
- The tool still invokes only `pi install` and `pi list`; successful completion requires
  `/reload` in the active session.

## Failure modes

Reject relative or malformed prior-source input, equal old/new source paths, absent or
malformed manifests, wrong old source, unauthorized/stale/partial/extra owned-skill drift,
dirty checkouts, immutable successor-intent contradictions, duplicate package identities, Pi
command failure, settings contradictions, or readback failure. Preserve the existing
rollback/recovery behavior and do not report success without a completion receipt.

## Implementation slice

One AFK tracer bullet should:

- add and normalize the exact prior-source request field and CLI option;
- derive a deterministic migration successor state path from old/new sources and exact drift
  authority while retaining the ordinary path for non-migration calls;
- add backward-compatible historical-intent comparison without rewriting historical state;
- authorize only exact old-manifest-to-current-source replacement after digest checks, with a
  separate exact-name/current-digest capability for destructive owned-root replacement;
- test successful migration, absent/wrong/no-op authorization, owned drift, rollback, exact
  replay, legacy intent replay, and CLI state-path separation;
- document the flag in the Ticket Autopilot contract; and
- after integration, run the real RDR-05 post-integration sync with evidence
  `pi-session://01a04e2a-0b7a-70fd-be3b-06500686244a/message/29684c3f`.

## Acceptance outcomes

1. The live-shaped old-source manifest migrates to the exact current source only with the
   explicit old path and unchanged installed digests.
2. The ordinary failed RDR-05 state remains byte-identical; migration persists in a distinct
   deterministic state artifact.
3. Missing, wrong, relative, equal, or stale source authority fails before skill or Pi
   mutation.
4. Drift replacement succeeds only for a complete exact set; missing, extra, stale, duplicate,
   malformed, unowned, or non-migration entries fail before replacement.
5. Downstream failure restores the old manifest source and owned skill bytes, including roots
   whose drift replacement was explicitly authorized.
6. Successful replay observes one current local package and performs no second install.
7. Legacy non-migration state and receipt envelopes replay without mutation.
8. Focused and full Ticket Autopilot tests, extension tests, static checks, final-tree checks,
   and Artifact Graph audit pass.
9. After integration, the real local sync replaces exactly the three authorized observed roots
   (`llm-wiki`, `ticket-autopilot`, and `verification-audit`), completes at exact integrated
   head/tree, and reports `/reload` without claiming the running session changed.

## Verification strategy

- **Unit:** request normalization, intent compatibility, exact manifest-source selection,
  exact observed-drift parsing/matching, and deterministic successor path.
- **Integration:** two source repositories, one persistent checkout, an old owned manifest,
  authorized and rejected drift sets, fake Pi commands, rollback injection, completed replay,
  and untouched ordinary failure.
- **Regression:** all Ticket Autopilot and mandatory extension tests plus compilation, diff,
  clean tree/index, and Artifact Graph audit.
- **Live local boundary:** invoke only the integrated command against the existing dedicated
  checkout, agents root, and Pi settings; inspect receipt and `pi list`; require the user to
  run `/reload` afterward.

## Alternatives rejected

- **Edit the manifest manually:** bypasses immutable intent, ownership checks, rollback, and
  receipt evidence.
- **Treat cleanup or checkout materialization as migration authority:** conflates separate
  capabilities and leaves skills/settings unverified.
- **Rewrite the failed state with a new field:** destroys literal history and weakens replay.
- **Reuse `--adopt-existing-owned` or `--replace-package-source`:** broadens unrelated flags
  beyond their existing ownership and package-setting meanings.
