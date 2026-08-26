---
ticket_schema: 1
ticket_id: "LW-06"
execution_mode: AFK
blocked_by:
  - "LW-04"
  - "LW-05"
  - "LW-08"
---

# Build the temporal axis

## Artifact Graph
- Artifact ID: `artifact:lw-06-temporal-axis`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
The part that answers *when*, and the integration point where docs, dates and sessions meet.

Three artefact kinds:

1. **A lifecycle record per ticket** — one page carrying `identity_key`, parent spec,
   disposition (`completed`, `canceled`, `on-hold`, or open), the dates from `LW-04` with the
   rung that produced each, `run_id` where a `*.completion.json` exists, and links to the
   sessions from `LW-08` that mention it.
2. **Per-period pages** — one page per month, listing the events in it: specs charted,
   tickets created, tickets moved, sessions run.
3. **An index** tying them together.

Diagrams are mermaid, not ASCII. That is one of the skill's four core principles, and mermaid
renders in Obsidian with default settings.

**What this ticket must not do is invent a date.** The provenance ladder exists because some
answers are genuinely unavailable: with `docs/` untracked, a disposition move has no witness
except a transcript mention or an explicit date. The rendering for an unknown date is
therefore part of the design, not an afterthought — a gap, a range, or an explicit unknown
marker, but never a plausible-looking value. A timeline that reads as authoritative while
containing filesystem guesses is worse than no timeline, because a reader cannot tell the two
apart.

The same applies to amended artefacts. `LW-10` decides whether a `changed` spec appends an
event or rewrites in place; whichever it decided, this axis renders it, and if it appends,
the history of an amendment must remain visible after the amendment.

**The shape is ours to choose.** `LW-01` decided that the skill is independent of the LLM Wiki
application, so the application's closed page-type set no longer constrains this axis:
`wiki/timeline/` with `type: lifecycle` pages is available. `LW-02` reports whether the
application still opens such a tree, as advice — take compatibility where it is free, and
prefer correctness where it is not. That is why `LW-02` is no longer a blocker here.

Grounding facts available for verification, all measured: `windows-text-fidelity` was charted
2026-08-12 (`81c351f`), three of its tickets completed 2026-08-13 (`437b287`), one was
canceled 2026-08-13 (`711e574`), and 5 Codex plus 6 Claude sessions ran against this project
across 2026-07-27 to 2026-08-11.

## Acceptance Criteria
- [ ] One lifecycle record per ticket discovered by `LW-05`, keyed on `identity_key` so a
      disposition move updates rather than duplicates.
- [ ] Every date on every page displays its provenance rung.
- [ ] An unknown date renders as explicitly unknown. Asserted on the untracked-`docs/`
      fixture, since the failure mode is a page that looks complete and is not.
- [ ] A low-confidence `mtime` date is visually distinguishable from a `git-rename` date.
- [ ] Per-period pages exist for every month in which an event occurred, with no empty months
      fabricated and no month with events omitted.
- [ ] Diagrams are mermaid; no ASCII diagrams anywhere in the output.
- [ ] Sessions appear on the axis and link to the tickets they mention, and tickets link back.
- [ ] The known facts above are reproduced: the 2026-08-12 charting, the three 2026-08-13
      completions, the one cancellation, and the 11 sessions.
- [ ] No output depends on the LLM Wiki application. The axis is correct and readable with the
      application absent, per `LW-01`.

## Frontier
Dependency-blocked on `LW-04` for dates, `LW-05` for pages, and `LW-08` for sessions. It is
deliberately the last integration and the only ticket that consumes all three. `LW-02` was
removed from this set by `LW-01`: an application constraint can no longer dictate the shape.

## Step-by-Step Implementation Plan
1. Fix the shape: `wiki/timeline/` with `type: lifecycle` pages. Checkpoint: written down, with
   `LW-02`'s advice taken where it costs nothing and overridden where it costs correctness.
2. Emit lifecycle records from `LW-05`'s pages and `LW-04`'s dates. Checkpoint: the four known
   `windows-text-fidelity` facts appear correctly.
3. Add provenance rendering, including the unknown and low-confidence cases. Checkpoint: the
   untracked fixture shows an explicit unknown, not a date.
4. Emit per-period pages with a mermaid timeline. Checkpoint: renders in Obsidian.
5. Join sessions to tickets in both directions. Checkpoint: a ticket page names the sessions
   that touched it and vice versa.

## Testing Plan
Automated: assertions over a fixture with one completed, one canceled, one open and one
untracked ticket, checking rendered provenance per date and the absence of any invented value;
a mermaid-syntax check on generated blocks.

Manual: open the axis in Obsidian and confirm the diagrams render; read one month page against
`git log` for that month and confirm nothing is missing or invented. Opening it in the LLM Wiki
application is optional and its result cannot fail this ticket.

Unavailable boundary: the `session-observed` rung only carries data if `LW-08` produced
mentions; if it did not, that must show as unknown rather than as an absence of events.

## Out of Scope
- Changing how dates are resolved, which is `LW-04`.
- Changing how pages are ingested, which is `LW-05`.
- New lint passes over the axis, which are `LW-11`.
- Any write to `docs/`.
