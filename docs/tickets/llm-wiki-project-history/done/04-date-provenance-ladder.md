---
ticket_schema: 1
ticket_id: "LW-04"
execution_mode: AFK
blocked_by:
  - "LW-03"
---

# Resolve artefact dates through a recorded provenance ladder

## Artifact Graph
- Artifact ID: `artifact:lw-04-date-provenance-ladder`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
A resolver that answers "when did this happen" for an artefact, and always says how it
knows.

The ladder, strongest rung first:

1. `git-rename` — a rename-detected move into `done/`, `canceled/` or `hold/`. Verified on
   this repository: `git log --follow --diff-filter=R` reports
   `docs/tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md` moved on
   **2026-08-13** by `437b287` (*"chore(tickets): move WT-01, WT-02 and WT-03 to done"*),
   detected as `R100`; `canceled/07-decide-and-introduce-ci.md` likewise through `711e574`.
2. `git-commit` — first commit touching the file for creation, last for modification.
   Verified: `81c351f`, **2026-08-12**, for both the ticket above and
   `docs/specs/windows-text-fidelity-wayfinder.md`.
3. `frontmatter` — an explicit date already in the artefact.
4. `session-observed` — the earliest or latest dated mention of the artefact's identity key
   in a project transcript. Declared here, **populated by `LW-08`**.
5. `mtime` — filesystem timestamp, always flagged low confidence.
6. `unknown` — no rung produced an answer.

Two failure modes the ladder exists to survive, both of them real rather than hypothetical:

- **Rename detection is not guaranteed.** The three observed moves were `R100` because they
  were pure moves. A commit that moves a ticket into `done/` *and* edits it can surface as a
  delete plus an add, in which case rung 1 finds nothing and the completion date is lost
  unless the pair is reunited. The fix is to pair the delete and the add on the artefact's
  `identity_key` from `LW-10` — a ticket's `ticket_id` is in the front matter of both sides
  of the pair.
- **Git may be silent or absent.** `docs/` may be untracked and the host may not be a
  repository at all. Here `docs/` happens to be fully tracked — `git status --porcelain
  --ignored docs/` is empty and all 36 `*.completion.json` sidecars appear in
  `git ls-files` — but that is a local fact, not a contract.

With git silent, a **disposition move has no witness at all** except a transcript mention or
an explicit date. Some tickets will therefore legitimately have an unknown completion date,
and the resolver must return `unknown` rather than reach for `mtime` and present a
filesystem artefact as a completion. That substitution is the single worst outcome available
to this ticket: it is indistinguishable from a fact at the point of reading.

Note what cannot help: `*.completion.json` carries `run_id`, `implementation_status`,
`ticket_digest`, `base_tree_oid`, `candidate_tree_oid` and `ticket_source_mode` — and no
date field. It is a provenance edge, never a timestamp.

## Acceptance Criteria
- [ ] Every returned date carries the rung that produced it; a date without provenance is
      not representable in the return type.
- [ ] The three verified facts are reproduced exactly: `437b287` / 2026-08-13 / `R100`,
      `711e574` for the canceled ticket, and `81c351f` / 2026-08-12 for creation.
- [ ] The delete-plus-add fallback recovers a completion date on a fixture where the move and
      an edit share one commit, and the recovered date equals the pure-move case.
- [ ] On an untracked-`docs/` fixture, a disposition move resolves to `unknown` — asserted
      explicitly, because passing this by returning an `mtime` is the defect.
- [ ] On a non-git host, resolution completes without raising and every date is
      `frontmatter`, `mtime` or `unknown`.
- [ ] `mtime` results are flagged low confidence in the returned value, not only in a log.
- [ ] `session-observed` is a declared rung that returns nothing until `LW-08` supplies data,
      and its absence never changes another rung's result.
- [ ] Resolution works from a worktree, reusing `LW-03`'s resolver rather than re-deriving
      the project root.

## Frontier
Dependency-blocked on `LW-03` for the project binding. Everything else it needs is already
measured and recorded in the parent map.

## Step-by-Step Implementation Plan
1. Define the return type so provenance is mandatory. Checkpoint: no code path can build a
   date without a rung.
2. Implement rungs 1 and 2 over the real repository. Checkpoint: the three verified facts
   reproduce.
3. Implement the delete-plus-add pairing on `identity_key`. Checkpoint: the move-plus-edit
   fixture yields the same date as a pure move; verify it fails before the pairing is added,
   since a fallback that cannot fail proves nothing.
4. Implement rungs 3, 5 and 6, and stub rung 4 behind `LW-08`'s input. Checkpoint: the
   untracked fixture returns `unknown` for the disposition move.
5. Add the non-git host path. Checkpoint: no exception, no git invocation.

## Testing Plan
Automated, stdlib `unittest` per repository convention: fixtures built with real `git init`
in temporary directories for tracked, untracked, non-git, move-only and move-plus-edit
cases, plus assertions pinned to the three known-good facts against the actual repository.

Manual: resolve every artefact under `docs/tickets/` and eyeball the provenance distribution
— a run where everything comes back `mtime` means the git rungs are silently broken.

Unavailable boundary: only Windows is available. Git rename detection is
platform-independent, but line-ending handling in `--diff-filter=R` similarity scoring on a
CRLF checkout is unobserved on POSIX and stays a declared gap.

## Out of Scope
- Rendering any timeline. That is `LW-06`.
- Reading transcripts. That is `LW-08`; this ticket only declares the rung.
- Writing dates into `docs/` artefacts.
- Deciding which transitions emit events, which is `LW-10`.
