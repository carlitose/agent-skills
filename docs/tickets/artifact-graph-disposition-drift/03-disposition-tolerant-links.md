---
ticket_schema: 1
ticket_id: "AG-03"
execution_mode: AFK
blocked_by:
  - "AG-01"
---

# Resolve artifact links across a ticket disposition move

## Artifact Graph
- Artifact ID: `artifact:ag-03-disposition-tolerant-links`
- Role: `ticket`
- Parent: [artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## Parent Spec
[artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## What to Build
`artifact-audit` must stop reporting a false owner-edge break every time the runner completes a
ticket.

`artifact_audit._link_target` resolves a link as `(source.parent / value).resolve()` with no
notion of the disposition directory. When `transition_ticket_source` moves a completed ticket
into `done/`, both halves of its owner edge break at once:

- the ticket's own `Parent: ../../specs/<map>.md`, read from inside `done/`, resolves to
  `docs/tickets/specs/`, which does not exist;
- the owning map's `### Children` entry still names the folder-root path the ticket has left.

They are coupled: repairing only the map's link makes it resolve and then trips
`children target must point back to its owner` instead. Both observed on this repository at
`507d6a7`.

Repository-wide effect today: **16 `broken-link` and 5 `reciprocity-mismatch` errors**, every
one of them a ticket in a disposition subdirectory, across six ticket families. It also blocks
`docs-only-adopt`, which runs the canonical audit over changed managed artifacts — `LW-10` was
rejected twice by exactly this.

**The obvious fix is unavailable, and that is the crux.** `transition_ticket_source` verifies
`_digest(source) != expected_digest` before the move and, on replay of an applied receipt,
`_digest(target) != expected_digest` after it. A ticket's bytes are frozen by contract across
the move, because the snapshot manifest and the CandidateRef depend on that digest. Having the
mover rewrite links would break the integrity invariant the transition exists to hold. So the
ticket's outbound links cannot be corrected by anyone, and the mismatch can only be resolved in
the reader.

Resolve it on one principle, the same one `llm-wiki-reingest-identity-decision.md` fixes for
wiki pages — that spec is still in flight on `LW-10` and is referenced by name rather than
linked: **a ticket's identity is its folder plus its filename, independent of the
disposition directory that currently holds it.**

- Links **out of** a ticket resolve additionally from the ticket folder root, because the file
  is digest-frozen and its location is lifecycle state.
- Links **into** a ticket accept the disposition subdirectories, because such a link names an
  artifact whose identity does not depend on where it sits now.

Both fallbacks apply **only when the literal target is absent**. The disposition directory
names come from `ticket_lifecycle`, not duplicated as literals.

A hand-written candidate exists on branch `fix/artifact-audit-disposition-links` at `b436ca9`,
marked not for merge. It was produced outside this pipeline and is an implementation reference,
not a substitute for the ticket's own quality loop. Treat its measured figures as claims to
re-verify, not as evidence.

## Acceptance Criteria
- [ ] A fixture with one map and one ticket, the ticket placed in each of `done/`, `canceled/`
      and `hold/` while the map's `### Children` still names the folder-root path, produces
      zero audit errors.
- [ ] A fixture whose ticket parent link names a spec that exists nowhere still reports exactly
      one `broken-link`. The tolerance must not become blanket permissiveness.
- [ ] Each new test is demonstrated to fail without the change. A test that cannot fail proves
      nothing, which `WT-01` recorded for this repository.
- [ ] No managed ticket file is rewritten, and `ticket_lifecycle`'s digest checks are untouched.
- [ ] `artifact-audit` stays read-only and provider-free.
- [ ] Repository audit errors drop from 24 to 8, and the eight that remain are named: one
      `path-escape` in `autopilot-token-economics-wayfinder.md`, and seven
      `reciprocity-mismatch` on `windows-text-fidelity`, whose map uses the `- Children:` bullet
      form the parser does not read. Neither is in scope here.
- [ ] `docs-only-adopt` succeeds for a candidate whose changed artifacts include a map linking
      to a completed ticket. This is the pipeline-level symptom, and it must be observed, not
      inferred.
- [ ] The suite result is compared against `AG-01`'s baseline, and any new red is named.

## Frontier
Dependency-blocked on `AG-01`. Not because the code needs it, but because the claim does: a
change to `artifact_audit` — used by `docs_only`, the finalizer and the scheduler — cannot be
reported as regression-free against an unknown baseline.

## Step-by-Step Implementation Plan
1. Export the canonical disposition directory names from `ticket_lifecycle` rather than
   duplicating them. Checkpoint: one source of truth, derived from `_DIRECTORIES`.
2. Make `_link_target` try the two fallbacks, gated on the literal target being absent.
   Checkpoint: the six existing call sites are unchanged, since they all compare a resolved
   path against `nodes_by_path`.
3. Add the two fixtures. Checkpoint: both pass.
4. Revert the resolution change and re-run only those tests. Checkpoint: both fail. Restore.
5. Run the six directly affected modules — `artifact_audit`, `docs_only`, `ticket_lifecycle`,
   `ticket_inventory`, `platform_locks`, `skill_graph`. Checkpoint: green.
6. Run the full suite and diff against `AG-01`'s baseline. Checkpoint: no new red.
7. Exercise `docs-only-adopt` against a real candidate. Checkpoint: accepted where it was
   previously rejected.

## Testing Plan
Automated, stdlib `unittest` per repository convention: the two new fixtures in
`tests/test_artifact_audit.py`, then the six affected modules, then the full suite against the
baseline. The revert-and-fail step in the plan is itself a required check, not a formality.

Manual: run `artifact-audit` on this repository and read the residual eight findings to confirm
they are the named unrelated ones.

Unavailable boundaries: only Windows and CPython 3.12.10 are observed. Path resolution differs
across platforms in ways this change touches directly — it manipulates parent directories — so
POSIX behaviour stays a declared gap until the suite runs there. The full suite takes about 17
minutes, so step 6 is a deliberate cost rather than an afterthought.

## Out of Scope
- Rewriting historical ticket files, forbidden by the digest contract and ineffective against
  recurrence.
- Making the mover rewrite links, for the same reason.
- Migrating the five specs that use the `- Children:` bullet form, which accounts for the seven
  residual reciprocity findings.
- The `path-escape` finding in `autopilot-token-economics-wayfinder.md`.
- Adding `## Artifact Graph` sections to the eight weak-key artefacts.
- Any change to how `artifact-audit` reports, classifies, or repairs findings.
