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
- [LW-05 ingest-repository-docs](../tickets/llm-wiki-project-history/done/05-ingest-repository-docs.md)
- [LW-06 temporal-axis](../tickets/llm-wiki-project-history/done/06-temporal-axis.md)
- [LW-07 session-discovery-contract](../tickets/llm-wiki-project-history/done/07-session-discovery-contract.md)
- [LW-08 ingest-agent-sessions](../tickets/llm-wiki-project-history/done/08-ingest-agent-sessions.md)
- [LW-09 retarget-scaffold-and-lint](../tickets/llm-wiki-project-history/done/09-retarget-scaffold-and-lint.md)
- [LW-10 reingest-identity-contract](../tickets/llm-wiki-project-history/done/10-reingest-identity-contract.md)
- [LW-11 drift-and-coverage-lint](../tickets/llm-wiki-project-history/done/11-drift-and-coverage-lint.md)
- [LW-12 fold-evidence-into-the-map](../tickets/llm-wiki-project-history/12-fold-evidence-into-the-map.md)

Lineage (evidence, not owner edges): the `llm-wiki` skill was copied into this repository at
`llm-wiki/` from `../ai-agent-python-api/.claude/skills/llm-wiki`. It is not installed in
`~/.agents/skills/`, so nothing consumes it yet. A second, older copy exists at
`~/Downloads/llm-wiki-skill-main/` and carries the Obsidian plugin and web viewer that this
repository's copy does not.

## Type

Wayfinding spec

## Status

**Complete.** Every ticket in the plan is `completed` and merged. The trail, since a
contiguous range would be wrong: `LW-01` in #87 alongside this map, `LW-02` in #88, then
`LW-03` #95, `LW-04` #96, `LW-10` #97, `LW-07` #98, `LW-08` #99, `LW-05` #100, `LW-06` #101,
`LW-09` #102, `LW-11` #103, and `LW-12` — this fold-back — in #104 and #105. Pull requests
#89 through #94 belong to the `artifact-graph-disposition-drift` family, not to this plan.
The skill at `llm-wiki/` implements the Destination below. Two items remain open and are
listed under *Not Yet Specified*; neither blocks anything.

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
- **The log is one `wiki/log.md`, newest first.** Decided by `LW-09`, which owned the question.
  A per-day directory exists to keep concurrent writers off each other; the operations that
  append here are agent-driven and serialized, so that problem does not arise. It sits inside
  `wiki/` so the log is part of the browsable wiki rather than a sidecar, and `lint_wiki.py`
  treats it as machinery: neither catalogued nor expected to carry inbound links.
- **An unresolvable date renders as the word `unknown` with its reason.** Decided by `LW-04` and
  implemented by `LW-06`: never a gap, never a range, never a plausible value. A low-confidence
  `mtime` date reads *"low confidence, from a filesystem timestamp"* while a rename reads
  *"from a rename recorded in Git"*, so the two are distinguishable in prose rather than by
  inspecting a field. Against this repository the axis carries 84 `git-commit` and 48
  `git-rename` events, **no `mtime` at all**, and lists the 6 dates it could not establish.
- **A linked worktree of the same repository is the same project.** Decided by `LW-07`.
  Sameness is settled by `git rev-parse --git-common-dir`, not by string prefix, because a
  worktree lives outside the project tree — this repository's autopilot worktrees sit in
  `Projects/.agent-skills-ticket-autopilot-worktrees/<id>/`. Excluding them would lose exactly
  the sessions in which the project was changed.
- **A session digest is stale when size, record count, or last timestamp changes.** Decided by
  `LW-08`. All three are written into the pointer, and `claude --resume` appending to the same
  JSONL moves at least one of them, so the file identity staying constant is not mistaken for
  the content staying constant.
- **A graph edge must link a page, never an identity key.** Learned rather than planned.
  `ingest_docs.py` rendered `blocked_by` as `[[ticket:family/TK-01]]` while the page it names
  is `ticket-family-tk-01`: **41 dead links from one cause**, invisible until `LW-11`'s lint
  looked. It also compiled only the *upward* half of the Artifact Graph, so every decision spec
  had no inbound link. Both fixed in `LW-11`.
- **A catalog entry is not a citation, and catalogs nest.** `wiki/index.md` lists
  `[[timeline/index]]`, and `wiki/timeline/index.md` lists the pages beneath it. Demanding that
  the top catalog name all 61 lifecycle records reported 63 findings against a wiki that was
  correctly organised. Being listed also does not clear the orphan pass: the two ask different
  questions. Settled across `LW-09` and `LW-11`.

## Not Yet Specified

- **Repairing the eight weak-key artefacts.** Five specs, one research note, and two prototype
  notes carry no `## Artifact Graph`, so they key on a path and lose their page identity if they
  move. Adding those sections would fix it, but they are files this plan does not own. Needs its
  own ticket; until then the limitation is declared rather than hidden. Measured, not estimated:
  `lint_wiki.py`'s `orphan-pages` pass reports exactly these eight against this repository, and
  they are the only findings on an otherwise error-free ingest.
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

**No edge is open.** All three that were listed here are resolved: the binding by `LW-03`, the
rename-detection ladder by `LW-04`, and the session identity transform by `LW-07`, each with
tests pinned to the facts recorded in this map.

## Ticket Plan

Every row is complete and merged. "Produced" is what landed, which is not always what the row
originally promised — where the two differ the row says so.

| ID | Type | Mode | Produced |
|----|------|------|----------|
| LW-01 | decision | HITL | [llm-wiki-app-independence-decision.md](llm-wiki-app-independence-decision.md): independence from the application at runtime and in data, `audit/` as the human-to-agent channel, one layout instead of two profiles |
| LW-02 | prototype | AFK | [llm-wiki-app-compatibility.md](../research/llm-wiki-app-compatibility.md), read from the v0.5.4 source rather than observed in the GUI. It corrected two premises of this map, which is why it is worth more than the gate it was not |
| LW-03 | task | AFK | `scripts/project_binding.py` — the binding at the wiki root, with three separable predicates. Reports tracking as unknown rather than as zero when the host is not a repository |
| LW-04 | task | AFK | `scripts/date_provenance.py` — the ladder `git-rename` → `git-commit` → `frontmatter` → `session-observed` → `mtime` → `unknown`, a frozen result type that refuses a value without a rung, and `mtime` deliberately absent from the disposition ladder |
| LW-05 | task | AFK | `scripts/ingest_docs.py` — identity-keyed pages, set-based classification, all five transitions. 84 artefacts; a second run writes zero bytes |
| LW-06 | task | AFK | `scripts/build_timeline.py` — 61 lifecycle records, per-period pages with a mermaid timeline, and an index naming every rung it used and every gap it could not fill |
| LW-07 | research | AFK | `scripts/session_discovery.py` — the Claude mangling rule tested on more than one path, the Codex `cwd` filter, and the worktree answer through `git rev-parse --git-common-dir` |
| LW-08 | task | AFK | `scripts/session_ingest.py` — a `raw/refs/` pointer plus an adaptive digest per session, never the transcript, and the three-signal staleness rule |
| LW-09 | task | AFK | One layout across `scaffold.py`, `lint_wiki.py`, `SKILL.md` and the five references; the log question decided; a static independence check. A fresh scaffold now passes its own lint, which it did not |
| LW-10 | task | AFK | [llm-wiki-reingest-identity-decision.md](llm-wiki-reingest-identity-decision.md) — `identity_key` per artefact kind, `source_digest` over universal-newline text, and the behaviour of all five transitions |
| LW-11 | task | AFK | `scripts/lint_drift.py`. **Corrected from the plan:** it promised eight new passes with `index drift` beside the existing index pass; what shipped is **seven** new plus a replacement, because `index-drift` subsumed `index-coverage` rather than duplicating it in one direction — **fifteen** passes in total, across three severities. It also had to fix the two link defects above to make a zero-error state reachable at all |
| LW-12 | task | AFK | This fold-back |

`LW-09` was split during ticket emission. As one row it mixed a retarget blocked only by
`LW-01` with lint passes blocked by ingest, the timeline and sessions — a horizontal batch
with two different frontier states. Splitting it moved the retarget from five blockers to
one, and it was the right call: `LW-09` landed six tickets before `LW-11` was reachable.

## Next Review

Nothing in this plan is pending. What a reader should do next, in order of value:

- **Run it.** `scaffold.py <root> "<Title>" --project-root <path>`, then `ingest_docs.py`, then
  `build_timeline.py`, then `lint_wiki.py`. Against this repository that is 84 artefacts, 65
  timeline pages, **zero errors and eight warnings** — the eight weak-key artefacts above.
  If those numbers have drifted, something regressed.
- **Decide where this repository's wiki instance lives**, and whether it is tracked. It is the
  only decision left, it belongs to the user, and no code waits on it.
- **Open a ticket for the eight weak-key artefacts** if their page identity starts to matter.
  Adding an `## Artifact Graph` to each is the whole repair; it is a write to `docs/` that no
  ticket in this plan owned.
- **Open a ticket for `docs_only.py`'s link resolution.** Two independent literal link
  resolvers exist: `artifact_audit._link_target`, made disposition-tolerant by `AG-03`, and
  `docs_only.py`, still literal. The second will report a stale link that the first forgives,
  which is how the `### Children` paths in this map went wrong unnoticed.
- **Note for anyone extending the lint.** A pass that inspects a directory the scaffold does
  not create reports green forever. `LW-09` found two such passes and `LW-11` found a third
  kind — a pass whose findings duplicated another's. Every pass now has a seeded-defect test,
  and `test_documents.py` asserts the documented pass table against the code, because the
  document said seven while the script ran eight and nothing caught it.
