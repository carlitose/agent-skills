---
ticket_schema: 1
ticket_id: "LI-01"
execution_mode: AFK
blocked_by: []
---

# Repair the existing disposition drift once

## Artifact Graph
- Artifact ID: `artifact:li-01-repair-existing-drift`
- Role: `ticket`
- Parent: [artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## Parent Spec
[artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## What to Build
A one-time repair of the stock, and the script that performs it — kept, because the flow fix
(`LI-02`) lands separately and the stock can drift again in the meantime.

The measured state: **131 `.md` links under `docs/` do not resolve literally**. Three kinds,
and the repair treats each differently:

- **Disposition drift** — the target exists under exactly one of `done/`, `canceled/`, `hold/`
  relative to the written path, or the source itself sits in a disposition directory and the
  link resolves one level up. Repoint the link. This is the bulk.
- **Fenced examples** — 4 links inside fenced code blocks in
  `docs/specs/artifact-graph-decision.md` are teaching material, not references. The scanner
  must skip fenced code entirely, and those bytes must survive the repair identical.
- **Genuinely dead** — a target that exists nowhere. Report it with its source line; never
  guess a replacement.

One hard exclusion: **links whose source is a ticket are not rewritten.** A ticket's bytes are
digest-frozen across its lifecycle (`transition_ticket_source` verifies the digest on both
sides of a move), so rewriting one corrupts the contract. Those links — 27 of the 41 graph
edges — stay stale and are resolved by `artifact_audit`'s reader tolerance, which exists for
exactly them.

## Acceptance Criteria
- [ ] The script repoints every dead link in a **writable** `docs/**/*.md` whose target exists
      under exactly one disposition candidate, in both directions (into a disposition
      directory, and out of one for a source that lives there).
- [ ] A link with more than one existing candidate is reported, not repointed.
- [ ] Fenced code blocks are skipped, and `docs/specs/artifact-graph-decision.md` is
      byte-identical after the run.
- [ ] No file under any `docs/tickets/**` disposition tree or with a frozen digest is modified;
      concretely, no ticket file is touched at all.
- [ ] The run is idempotent: a second execution changes zero bytes.
- [ ] Before and after counts are recorded in the run's own output: total dead, repointed,
      skipped-as-fenced, reported-as-dead, reported-as-ambiguous.
- [ ] `artifact-audit` reports no new error and no new warning after the repair.
- [ ] The full repository suite stays green.
- [ ] The script lives at a recorded location with a `--dry-run` flag, so the next accumulation
      can be repaired the same way.

## Frontier
Ready. Independent of `LI-02` and `LI-03`.

## Step-by-Step Implementation Plan
1. Record the baseline: the 131 count reproduced by the script's own scanner in `--dry-run`,
   split by kind. Checkpoint: the scanner agrees with the ad-hoc measurement or explains the
   difference.
2. Implement resolution: literal first, then the disposition candidates, mirroring
   `artifact_links` semantics if `AG-05`'s worktree module is adopted, or reimplementing the
   two directions locally if not. Checkpoint: unit fixtures for both directions, ambiguity, and
   fenced skipping.
3. Run against `docs/`, commit the corrected documents and the report. Checkpoint: second run
   changes nothing.
4. Re-run `artifact-audit` and the full suite. Checkpoint: no regression.

## Testing Plan
Automated: stdlib `unittest` fixtures — a link repaired into `done/`, a link repaired out of a
disposition source, an ambiguous double candidate reported, a fenced link untouched, a ticket
source untouched, idempotence. Then the real run's before/after counts asserted in a
repository-level test only if a stable invariant exists; otherwise recorded in the report.

Manual: read the diff of the five known map files and confirm every repoint lands on the file
the link always meant.

Unavailable boundary: POSIX unobserved; path handling verified on Windows only.

## Out of Scope
- Any rewrite of ticket bodies.
- The mover change (`LI-02`).
- A standing checker or CI gate for prose links.
- Repairing links inside `llm-wiki/` or any non-`docs/` tree.
