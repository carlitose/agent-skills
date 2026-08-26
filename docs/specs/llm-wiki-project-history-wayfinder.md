# LLM Wiki as a Project History Knowledge Base

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-project-history-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [App independence decision](llm-wiki-app-independence-decision.md)
- [App compatibility finding](../research/llm-wiki-app-compatibility.md)
- [Re-ingest identity decision](llm-wiki-reingest-identity-decision.md)
- [LW-01 decide-audit-surface](../tickets/llm-wiki-project-history/done/01-decide-audit-surface.md)
- [LW-02 measure-app-tolerance](../tickets/llm-wiki-project-history/done/02-measure-app-tolerance.md)
- [LW-03 bind-wiki-to-project](../tickets/llm-wiki-project-history/done/03-bind-wiki-to-project.md)
- [LW-04 date-provenance-ladder](../tickets/llm-wiki-project-history/done/04-date-provenance-ladder.md)
- [LW-05 ingest-repository-docs](../tickets/llm-wiki-project-history/05-ingest-repository-docs.md)
- [LW-06 temporal-axis](../tickets/llm-wiki-project-history/06-temporal-axis.md)
- [LW-07 session-discovery-contract](../tickets/llm-wiki-project-history/07-session-discovery-contract.md)
- [LW-08 ingest-agent-sessions](../tickets/llm-wiki-project-history/08-ingest-agent-sessions.md)
- [LW-09 retarget-scaffold-and-lint](../tickets/llm-wiki-project-history/09-retarget-scaffold-and-lint.md)
- [LW-10 reingest-identity-contract](../tickets/llm-wiki-project-history/10-reingest-identity-contract.md)
- [LW-11 drift-and-coverage-lint](../tickets/llm-wiki-project-history/11-drift-and-coverage-lint.md)
- [LW-12 fold-evidence-into-the-map](../tickets/llm-wiki-project-history/12-fold-evidence-into-the-map.md)

Lineage (evidence, not owner edges): the `llm-wiki` skill was copied into this repository at
`llm-wiki/` from `../ai-agent-python-api/.claude/skills/llm-wiki`. It is not installed in
`~/.agents/skills/`, so nothing consumes it yet. A second, older copy exists at
`~/Downloads/llm-wiki-skill-main/` and carries the Obsidian plugin and web viewer that this
repository's copy does not.

## Type

Wayfinding spec

## Status

Active

## Destination

A wiki that compiles **this project's own history** — not just external reading material —
and can answer questions with time as a first-class axis:

- every artefact under `docs/` (specs, tickets in every disposition, research, prototypes)
  has a wiki page carrying its provenance back to the repository path;
- the artefact graph that already exists in those files (`Artifact ID`, `Parent`,
  `blocked_by`) is materialised as wikilinks, so the wiki graph is the project graph rather
  than a hand-maintained parallel copy;
- a `wiki/timeline/` axis answers *when*: when a spec was charted, when each ticket was
  created, when it reached `done/` or `canceled/`, and which agent sessions were running
  while that happened;
- Claude Code and Codex transcripts **for the same project** are discoverable, distilled,
  and linked to the tickets they worked on — without copying ~47 MB of JSONL into the wiki;
- every date the wiki states carries its own provenance, so a filesystem guess can never be
  read as a recorded fact, and a date that cannot be established is stated as unknown rather
  than inferred;
- re-running ingest after `docs/` has grown, been amended, or had tickets move is **cheap and
  idempotent**: unchanged artefacts are skipped, changed ones update in place, moved ones keep
  their page, and lint reports the drift the wiki cannot repair on its own.

The wiki requires nothing but a filesystem. That the tree also opens in Obsidian and in
the LLM Wiki application is a property worth keeping, not a constraint on the design.

## Decisions So Far

- **The skill is independent of the application, and owns a single layout.** Recorded in
  [llm-wiki-app-independence-decision.md](llm-wiki-app-independence-decision.md), confirmed
  through `grilling`. The application is **`LLM Wiki` by `nashsu` v0.5.4**
  (`github.com/nashsu/llm_wiki`, Tauri plus React/TypeScript, third-party open source), cloned
  at `../llm_wiki` and built portable in `~/Downloads/`. Three decisions: nothing may require
  the application to be installed or running, and no file under `.llm-wiki/` and no
  `/api/v1` call is an input; `audit/` at the wiki root is the human-to-agent correction
  channel; and the skill targets one layout rather than two named profiles. Compatibility with
  the application is a consequence, not a constraint.
- **Target layout.** `purpose.md` + `schema.md` + `audit/` + `audit/resolved/` +
  `raw/{sources,refs,assets}/` + `wiki/index.md` +
  `wiki/{concepts,entities,sources,queries,comparisons,synthesis}/` + `wiki/timeline/`. Shaped
  after the wiki in live use at `../minnarone/wiki/minnarone-wiki`, with `audit/` added.
- **Both of the application's feedback channels run the wrong way for this purpose.**
  `.llm-wiki/review.json` holds 74 items (`missing-page` 39, `suggestion` 31,
  `contradiction` 4), **all `resolved: false`**, written by the ingest LLM through a
  `---REVIEW: <type> | <title>---` marker; the review UI only calls `resolveItem` and
  `dismissItem`; `src/lib/graph-insights.ts` emits a second such channel; and the MCP server
  exposes eight tools, all read or rescan, with **no write tool**. A human can resolve what the
  agent raised and cannot file a correction — which is why `audit/` has to exist here.
- **A directory at the wiki root outside four prefixes is invisible to the application.**
  `.llm-wiki/file-snapshot.json` tracks 275 files under exactly `raw/` (194), `wiki/` (79),
  `purpose.md`, and `schema.md`. `audit/` therefore costs nothing in compatibility, and sits
  outside `wiki/` so the unknown-page-type question does not reach it.
- **Re-ingest identity and change behaviour are decided.** Recorded in
  [llm-wiki-reingest-identity-decision.md](llm-wiki-reingest-identity-decision.md).
  `identity_key` is `ticket:<spec-slug>/<ticket_id>` for tickets, the `Artifact ID` for specs
  that have one, and a weak `path:` key otherwise. Measured on the corpus `LW-03`'s resolver
  reports: **61 files yield `ticket_id`, 14 an `Artifact ID`, and 8 neither**, 83 in total — and
  five of those eight are specs predating the convention, so the fallback covers about one file
  in ten rather than two prototype notes. `source_digest` reuses the house idiom `sha256` over
  universal-newline text (`ticket_contract.py:245`), so a CRLF checkout does not report every
  file as changed. All five transitions are fixed, with `changed` appending an `amended` event
  rather than rewriting history and `missing` tombstoning rather than deleting. Classification
  is set-based, which is what separates a `moved` artefact from a `missing` plus `new` pair.
- **The application turns out to support `wiki/timeline/` by design.** Read from v0.5.4 source
  and recorded in [llm-wiki-app-compatibility.md](../research/llm-wiki-app-compatibility.md).
  A custom directory under `wiki/` becomes a first-class page type
  (`src/lib/wiki-page-types.ts:34`), every `.md` under `wiki/` is watched recursively
  (`src-tauri/src/commands/file_sync.rs:1115`), and extra front-matter keys are preserved
  (`src/lib/frontmatter.ts:180`). Two premises in this map were wrong: the closed seven-type
  set belongs to the minnarone wiki's own `schema.md`, not to the application, whose list has
  nine entries; and page type is derived from the **path**, never from a `type:` key. One real
  constraint survives, as advice: added front-matter keys must be flat, because nested values
  read back as JSON strings — so `LW-04` flattens date provenance into sibling scalars.
- **The application's source is readable, and its version is pinned on disk.** `LLM Wiki.exe`
  is a 75.6 MB packed binary, but the v0.5.4 source is cloned locally —
  `src/lib/{ingest.ts,ingest-cache.ts,lint.ts,persist.ts}`,
  `src/components/review/review-view.tsx`, with tests. Its rules are established by reading,
  not by running the GUI.
- **The skill as copied documents a different layout.** `llm-wiki/SKILL.md`,
  `scripts/scaffold.py` and `scripts/lint_wiki.py` describe and enforce
  `CLAUDE.md` + `log/YYYYMMDD.md` + `audit/` + `raw/{articles,papers,notes,refs}/` +
  `wiki/{concepts,entities,summaries}/` + `outputs/queries/`. The live wiki has **no**
  `log/`, `audit/`, or `CLAUDE.md`. This divergence is the largest single cost in the plan
  and is not a detail to be papered over.
- **Repo-docs ingest already exists in practice, unspecified.** The minnarone wiki contains
  `wiki/sources/4-docs--4-adrs--43-2026-06-29-live-media-backpressure-boundary--1n8nezu.md`
  with frontmatter `sources: ["docs/adrs/2026-06-29-live-media-backpressure-boundary.md"]`
  and `created`/`updated` dates. The pattern to formalise is observed, not invented.
- **Sessions are ingested as pointer plus digest, never verbatim.** Confirmed by the user.
  Measured for this project: Claude Code
  `~/.claude/projects/C--Users-CGS03-Projects-agent-skills/` = 6 files, ~6.7 MB, 3757 JSONL
  records (`assistant` 1491, `user` 836, `attachment` 377, plus 11 other record types);
  Codex `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` = 5 files, ~40 MB. ~47 MB total. The
  skill's own raw-file policy already forbids copying sources of this size; a pointer in
  `raw/refs/` plus a 200–400 word page is the compliant shape.
- **Git is the strongest temporal oracle, and it works from inside a host project.** Verified
  on this repository. `git log --follow --diff-filter=R` recovers the disposition move
  exactly: `docs/tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md` was moved
  on **2026-08-13** by `437b287` *"chore(tickets): move WT-01, WT-02 and WT-03 to done"*,
  detected as `R100`; its creation is **2026-08-12** by `81c351f`. `canceled/07-...` resolves
  the same way through `711e574`. Queries run against the **host repository**, never against
  the wiki's own history. Verified that this also works from a worktree — this repository
  currently has 11.
- **Nothing in the design may assume that either side is tracked.** Stated by the user, in
  two steps: the wiki may or may not be git-ignored, and `docs/` itself may or may not be
  tracked. In minnarone the wiki is ignored (`.gitignore:48: wiki/`); in this repository
  `docs/` happens to be fully tracked (`git status --porcelain --ignored docs/` is empty, and
  all 36 `*.completion.json` sidecars appear in `git ls-files`). Both are local facts, not
  contracts. Git is therefore one rung of a ladder, never a prerequisite: an untracked
  artefact is an ordinary case that degrades to a weaker provenance, not an error.
- **Transcripts are a second temporal oracle, independent of git.** Every Claude and Codex
  JSONL record carries a timestamp (`timestamp` at the record root for Claude; `timestamp`
  plus `session_meta.payload.timestamp` for Codex), and sessions name the tickets they work
  on by ID. A dated mention of `WT-05` in a project transcript therefore establishes that the
  ticket was being worked on at that time even when `docs/` is untracked and git can say
  nothing. This is weaker than a recorded disposition move and stronger than a filesystem
  timestamp, and it earns its own rung on the ladder.
- **Ticket disposition is filesystem position, and the vocabulary is already fixed.**
  `docs/specs/ticket-lifecycle-disposition-decision.md` maps `done/` → `completed`,
  `canceled/` → `canceled`, `hold/` → `on-hold`. The wiki consumes this mapping; it does not
  define its own.
- **`completion.json` is provenance, not a timestamp.** 36 `*.completion.json` sidecars exist
  across 7 ticket families, carrying `run_id`, `implementation_status`, `ticket_digest`,
  `base_tree_oid`, `candidate_tree_oid`, `ticket_source_mode` — and **no date field**. They
  give the ticket-to-autopilot-run edge; they cannot give the completion time.
- **Ingest is incremental in the steady state, and the observed naming convention breaks
  under it.** `docs/` is not a fixed corpus: specs get amended, tickets get added, and every
  ticket eventually moves to `done/` or `canceled/`. The page name observed in the live wiki,
  `4-docs--4-adrs--43-2026-06-29-live-media-backpressure-boundary--1n8nezu.md`, encodes the
  **source path**. A ticket moving from `docs/tickets/x/05-foo.md` to
  `docs/tickets/x/done/05-foo.md` would therefore mint a *second* page for the same artefact
  rather than update the first. Any re-ingest design must key pages on something that
  survives a move.
- **A stable identity key already exists for the two artefact kinds that matter.** Tickets
  carry `ticket_id` in the Envelope v1 front matter and specs carry `Artifact ID` in their
  `## Artifact Graph` section; both are stable across renames and disposition moves.
  `docs/research/` and `docs/prototypes/` have neither and need a recorded fallback.
- **Change detection can be git-independent.** A content digest recorded per page makes
  re-ingest a comparison rather than a re-read, and works when `docs/` is untracked, when the
  host is not a git repository, and when a file is touched without being changed. The
  repository already uses this shape: `ticket_digest` in every `completion.json`.
- **The application solves part of this already, and the design deliberately forgoes it.**
  `.llm-wiki/ingest-cache.json` holds `entries` keyed by a repository-relative source path —
  `docs/adrs/2026-06-29-live-media-backpressure-boundary.md` — with a `hash` (sha256), a
  `timestamp`, and **`filesWritten`**, the pages that source produced. That is very nearly
  `LW-10`'s contract, and the key being a repository path proves the application already
  ingests repository docs from outside the wiki. Under the independence decision it is a design
  reference and never a runtime input; `LW-10` implements its own.
- **The application also demonstrates the duplication hazard.** `.llm-wiki/file-snapshot.json`
  tracks both `raw/sources/SPECIFICATION.md` and `raw/sources/docs/SPECIFICATION.md` — the
  same logical file ingested twice under two paths. This is the failure `LW-10` exists to
  prevent, observed rather than hypothesised.

## Not Yet Specified

- **Where the log lives.** The target layout's `schema.md` documents a single `wiki/log.md` in
  reverse chronological order; the layout being retired uses `log/YYYYMMDD.md`, one file per
  day, and `lint_wiki.py` has a pass over that filename shape. Under a single layout exactly
  one survives. Owned by `LW-09`.
- **What the timeline may claim when `docs/` is untracked.** With git silent, creation and
  disposition dates fall to `frontmatter`, `session-observed`, or `mtime`. A disposition move
  in particular has *no* non-git witness except a transcript mention or an explicit date, so
  some tickets will legitimately have an unknown completion date. What the timeline renders
  for those — a gap, a range, or an explicitly unknown marker — is undecided, and guessing it
  would be exactly the failure this map exists to prevent. Owned by `LW-04`.
- **Repairing the eight weak-key artefacts.** Five specs, one research note, and two prototype
  notes carry no `## Artifact Graph`, so they key on a path and lose their page identity if they
  move. Adding those sections would fix it, but they are files this plan does not own. Needs its
  own ticket; until then the limitation is declared rather than hidden.
- **Whether a worktree counts as the same project.** Codex records `cwd` per session; the
  observed distribution includes `...\minnarone\.claude\worktrees\prompt-externalization` and
  `...\translate-lector\.claude\worktrees\ocr-layout-wayfinder`. This repository's autopilot
  worktrees live at `Projects/.agent-skills-ticket-autopilot-worktrees/<id>/` — outside the
  project directory. Whether sessions run there belong to this project's history is
  undecided, and it changes both what the session index contains and which tickets get a
  `session-observed` date. Owned by `LW-07`.
- **How a continued session is re-digested.** `claude --resume` appends to the same JSONL, so
  a digest written today can be stale tomorrow while the file identity is unchanged. The
  staleness signal (size, record count, last timestamp) and the re-digest trigger are
  unspecified. Owned by `LW-08`.
- **Where this repository's own wiki instance lives**, and whether it is tracked. Assumed
  `wiki/agent-skills-wiki/` by analogy with minnarone, but the user's per-instance choice
  governs, and no ticket depends on the answer.

## Out of Scope

- **Changing Ticket Envelope v1.** `ticket-autopilot/scripts/autopilot/ticket_contract.py`
  owns envelope parsing and serialization. No wiki state, timestamp, or index field is added
  to ticket front matter; the wiki reads tickets, never rewrites them.
- **Editing existing tickets or specs to add dates.** Explicitly rejected in favour of the
  provenance ladder.
- **Requiring the host project to be a git repository**, or to track `docs/`, or to track the
  wiki. All three are optional inputs.
- **Modifying `../minnarone/wiki/minnarone-wiki`.** It is read-only evidence for the profile
  shape. A copy may be used for verification; the live wiki is not touched.
- **Populating or reading `.llm-wiki/lancedb`.** Semantic search is app-owned state.
- **The Obsidian plugin and web viewer sources.** They live in the other copy of the skill,
  not in this repository. Only `LW-01` may reference them, and only to decide the audit
  question.
- **Installing the skill into `~/.agents/skills/`.**
- **Ingesting sessions from other projects.** 84 Codex session files exist across 12 distinct
  `cwd` values; only this project's are in scope.
- **Reading Codex's sqlite state** (`thread_history_1.sqlite`, 14 MB; `logs_2.sqlite`, 60 MB).
  The rollout JSONL files are the transcript of record.
- **Retro-fitting the wiki with pre-existing external reading material.** This map is about
  project history.

## Frontier / Blocking Edges

- **Nothing binds a wiki to a project yet.** Every downstream op needs `project_root`, the git
  mode, the docs globs, and the session providers, resolved without assuming that the wiki,
  the project, or `docs/` is tracked. Unblocked by the config contract — `LW-03`.
- **Rename detection is not guaranteed, and git may be absent entirely.** The three observed
  moves were `R100` because they were pure moves; a commit that moves a ticket to `done/`
  *and* edits it may surface as delete-plus-add, silently losing the completion date. With
  `docs/` untracked there is no rename to detect at all. Unblocked by a ladder that pairs the
  delete and the add on `ticket_id`, degrades explicitly, and records which rung produced
  each date — `LW-04`.
- **Session identity rules are derived from one observation.** The Claude directory name
  `C--Users-CGS03-Projects-agent-skills` implies a mangling of
  `C:\Users\CGS03\Projects\agent-skills`, but the rule for the drive colon versus the
  separators cannot be inferred from a single sample. Hardcoding it would break on the next
  project, and it is now load-bearing for dates as well as for content. Unblocked by deriving
  and testing the transform against more than one project — `LW-07`.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
|----|------|------|-----------|-------|-----------------|
| LW-01 | decision | HITL | — | **Done.** Decide the audit surface and profile model | [llm-wiki-app-independence-decision.md](llm-wiki-app-independence-decision.md) — independence from the application at runtime and in data, `audit/` as the human-to-agent channel, one layout instead of two profiles |
| LW-02 | prototype | AFK | — | Check that the application still opens the tree | A compatibility finding, no longer a gate: whether v0.5.4 ignores, warns on, or rejects `wiki/timeline/`, unknown `type:` values, and extra front-matter keys. Established by **reading the v0.5.4 source cloned at `../llm_wiki`** (`src/lib/{ingest,lint,persist}.ts`), not by running the GUI. Its answer cannot change the timeline's shape |
| LW-03 | task | AFK | — | **Done.** Bind a wiki to its host project | A config contract at the wiki root (`project_root`, git mode, docs globs, session providers) and a resolver that works from a worktree, tolerates a non-git host, and makes no assumption about what is tracked |
| LW-04 | task | AFK | LW-03 | **Done.** Resolve dates with recorded provenance | A dated-event resolver with the ladder `git-rename` → `git-commit` → `frontmatter` → `session-observed` → `mtime` → `unknown`, a per-date provenance field, a delete-plus-add fallback paired on `ticket_id`, a defined rendering for unknown dates, and tests pinned to the verified facts (`437b287`/2026-08-13/`R100`, `81c351f`/2026-08-12, `711e574`) plus an untracked-`docs/` fixture. Declares all six provenance values; the `session-observed` rung is populated by `LW-08` |
| LW-05 | task | AFK | LW-03, LW-04, LW-10 | Ingest repository docs as wiki sources | An `ingest-docs` op producing `wiki/sources/` pages with `sources:` provenance, `Artifact ID`/`Parent`/`blocked_by` materialised as wikilinks, and idempotent re-ingest implementing `LW-10`'s contract. Verified by ingesting twice with no change (no writes), then moving a fixture ticket into `done/` and re-ingesting (one page updated, zero pages created) |
| LW-06 | task | AFK | LW-04, LW-05, LW-08 | Build the temporal axis | `wiki/timeline/` — an index, per-month pages with a mermaid timeline, and one lifecycle record per ticket carrying disposition, dates, date provenance, `run_id` where a `completion.json` exists, and the sessions that touched it |
| LW-07 | research | AFK | — | Derive the session discovery contract | The Claude project-directory mangling rule tested on more than one path, the Codex `session_meta.payload.cwd` filter, and a recorded answer on whether worktree `cwd`s belong to the project |
| LW-08 | task | AFK | LW-03, LW-07 | Ingest agent sessions as pointer plus digest | An `ingest-sessions` op writing a `raw/refs/` pointer (`external_path`, size, provider, span) and a 200–400 word page per session listing tickets touched, files touched, and decisions; emits dated ticket mentions to feed `LW-04`'s `session-observed` rung; defines the staleness rule for resumed sessions |
| LW-09 | task | AFK | LW-01 | Retarget scaffold and lint to the decided profile | `scaffold.py`, `lint_wiki.py`, `SKILL.md` and the five references describing and enforcing the same layout, with every existing pass firing on the profile's real directories and no dead pass reporting green. Includes the 18 `python3` invocations in the docs, which do not resolve on this machine |
| LW-10 | task | AFK | — | **Done.** Decide the re-ingest identity and change contract | A recorded contract: `identity_key` per artefact kind (`ticket_id` for tickets, `Artifact ID` for specs, decided fallback for research and prototypes), a `source_digest` definition including the CRLF normalization question, the behaviour for all five transitions (`new`, `changed`, `moved`, `missing`, `unchanged`), and whether an amended spec appends a timeline event or rewrites in place |
| LW-11 | task | AFK | LW-05, LW-06, LW-08, LW-09, LW-10 | Add the drift and coverage lint passes | Eight new passes — dangling `sources:`, stale page, un-ingested artefact, duplicate identity, index drift, timeline coverage, date-provenance validity, stale session pointer — each with a seeded-defect test proving it can fail, a severity split so a normal steady state is not reported as breakage, and correct behaviour on a non-git host |

Ready now: `LW-01` (needs the user), `LW-02`, `LW-03`, `LW-07`, `LW-10`.

`LW-09` was split during ticket emission. As one row it mixed a retarget blocked only by
`LW-01` with lint passes blocked by ingest, the timeline and sessions — a horizontal batch
with two different frontier states. Splitting it moves the retarget from five blockers to
one.

## Next Review

- `LW-10` first, and before any line of `LW-05`. It is the cheapest ticket on the frontier and
  the one whose absence corrupts the wiki quietly rather than loudly. The application's own
  `ingest-cache.json` and its duplicate `SPECIFICATION.md` pair are the design reference to
  read while doing it — and never a runtime input.
- `LW-09` is now unblocked and is the largest single piece of work. It also owns the one
  question `LW-01` left open: whether the log is `wiki/log.md` or `log/YYYYMMDD.md`.
- `LW-03` and `LW-07` in parallel; neither blocks on anything.
- `LW-02` whenever convenient. It no longer gates anything, and it is now a source-reading
  task against `../llm_wiki` at v0.5.4 rather than a GUI observation.
- On completion of `LW-04`, check that the resolver reproduces the three verified dates in
  this map, **and** that it reports `unknown` rather than an `mtime` guess for a disposition
  move on an untracked fixture. If it silently produces a date there, the ladder is wrong and
  the whole timeline is untrustworthy.
- Note for whoever runs `LW-04`: this ticket folder is itself **untracked** right now, so the
  `git-rename` rung would find nothing for `done/01-decide-audit-surface.md`. It is a free
  fixture for the untracked case.
