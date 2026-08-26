---
ticket_schema: 1
ticket_id: "LW-12"
execution_mode: AFK
blocked_by: []
---

# Fold the completed evidence back into the map

## Artifact Graph
- Artifact ID: `artifact:lw-12-fold-evidence-into-the-map`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
A map that describes the work as it stands rather than as it was planned. Eleven tickets are
complete and merged; the map still reads as though none of them had started, which makes it
worse than no map — a stale plan is followed.

Six sections are wrong, each in a different way.

**`## Status`** says `Active`. Every ticket in the plan is `completed`.

**`### Children`** links `LW-05` through `LW-11` at their pre-completion paths, for example
`../tickets/llm-wiki-project-history/05-ingest-repository-docs.md`, while every one of those
files now sits under `done/`. `artifact-audit` does not report this because `AG-03` made its
link resolution disposition-tolerant, but the second resolver — the docs-only link check at
`ticket-autopilot/scripts/autopilot/docs_only.py` — is still literal, so the links are wrong
in a way that one checker forgives and the other does not.

**`## Not Yet Specified`** lists six unknowns. Four are answered and must move into
`## Decisions So Far` carrying their answers, not simply be deleted:

- *Where the log lives* — `LW-09` decided one `wiki/log.md`, newest first, and the reason: the
  operations that append to it are serialized, so the concurrent-write problem a per-day
  directory solves does not arise.
- *What the timeline may claim when `docs/` is untracked* — `LW-04` and `LW-06` render the word
  `unknown` with its reason, and never a date-shaped value.
- *Whether a worktree counts as the same project* — `LW-07` decided it, through
  `git rev-parse --git-common-dir`.
- *How a continued session is re-digested* — `LW-08` decided the staleness signal.

Two are genuinely still open and stay: repairing the eight weak-key artefacts, and where this
repository's own wiki instance lives.

**`## Frontier / Blocking Edges`** lists three edges, all of them now unblocked. A frontier with
no open edge must say so in a sentence rather than list resolved work.

**`## Ticket Plan`** marks four rows `**Done.**` and eleven are done. `LW-11`'s row is also
substantively wrong: it promised "eight new passes" including `index drift` beside the existing
index pass. What shipped was **seven** new passes plus a replacement — `index-drift` subsumed
`index-coverage` because two passes asking the same question in one direction each is worse than
one asking both — for **fifteen** passes in total.

**`## Next Review`** is entirely about work that is finished, including a note that "this ticket
folder is itself untracked right now", which has not been true since `a956aa1`.

Two findings from the completed work belong in `## Decisions So Far`, because they were learned
rather than planned and the next reader needs them:

- **A graph edge must link a page, never an identity key.** `ingest_docs.py` rendered
  `blocked_by` as `[[ticket:family/TK-01]]` where the page is named `ticket-family-tk-01`: 41
  dead links from one cause. Fixed in `LW-11`.
- **A catalog entry is not a citation, and catalogs nest.** Fixed in `LW-09` and `LW-11`.

## Acceptance Criteria
- [ ] `## Status` states that the plan is complete.
- [ ] Every `### Children` link resolves literally, with no reliance on disposition tolerance.
- [ ] The four answered unknowns appear in `## Decisions So Far` with their answers and are gone
      from `## Not Yet Specified`; the two open ones remain, each naming what it needs.
- [ ] `## Frontier / Blocking Edges` states in one sentence that no edge is open.
- [ ] Every `## Ticket Plan` row is marked done, and `LW-11`'s row says seven new passes plus one
      replacement, fifteen in total.
- [ ] `## Next Review` names what a reader should actually do next, or states that nothing is
      pending.
- [ ] The two learned findings appear in `## Decisions So Far`.
- [ ] `artifact-audit` reports no error for this folder, and its error and unreferenced totals
      are unchanged from before this ticket.
- [ ] No claim is added that was not observed. Where a number is stated, it comes from a
      recorded run rather than from memory.

## Frontier
Ready. It depends on no ticket: every input is already merged.

## Step-by-Step Implementation Plan
1. Record the current `artifact-audit` error and unreferenced totals. Checkpoint: a baseline, so
   a regression is measurable rather than argued.
2. Repoint the `### Children` links at the paths the files occupy now. Checkpoint: each target
   exists at the literal path.
3. Move the four answered unknowns into `## Decisions So Far`, each with its answer and the
   ticket that decided it. Checkpoint: `## Not Yet Specified` holds exactly the two open items.
4. Rewrite `## Frontier / Blocking Edges`, `## Ticket Plan`, `## Status` and `## Next Review`.
   Checkpoint: no sentence in the map describes work as pending that is merged.
5. Add the two learned findings. Checkpoint: each names the defect and the ticket that fixed it.
6. Re-run `artifact-audit`. Checkpoint: totals match step 1.

## Testing Plan
Automated: `artifact-audit --json` before and after, compared on error and unreferenced counts;
`ticket-list --json` to confirm no diagnostic appears; and a literal existence check on every
link target in the map.

Manual: read the map start to finish as a newcomer and confirm that nothing reads as pending.

Unavailable boundary: none. This is a documentation change with no runtime behaviour.

## Out of Scope
- Any change under `llm-wiki/`. The skill is finished; this is only its map.
- Repairing the eight weak-key artefacts. That is the open item this ticket keeps, not resolves.
- Making `docs_only.py`'s link resolution disposition-tolerant. That is a code change in
  `ticket-autopilot/` and deserves its own ticket.
- Any new ticket in this folder beyond this one.
