# LLM Wiki App Independence and the Correction Channel

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-app-independence-decision`
- Role: `spec`
- Parent: [LLM Wiki as a Project History Knowledge Base](llm-wiki-project-history-wayfinder.md)

## Type

Decision spec

## Status

Accepted

## Source

`LW-01` in `docs/tickets/llm-wiki-project-history/01-decide-audit-surface.md`. Confirmed
through `grilling`, one question at a time, on 2026-08-26.

## Context

The parent map selected a target layout for the `llm-wiki` skill by copying the shape of a
wiki already in live use at `../minnarone/wiki/minnarone-wiki`. That wiki was produced by a
desktop application, and the application's presence in the design was never made explicit —
which left three coupled questions unanswered: how much the skill may depend on that
application, where a human files a correction, and whether the skill supports one layout or
two.

### What the application actually is

Established by inspection, after the identification was initially asserted without evidence:

- **`LLM Wiki` by `nashsu`** — `github.com/nashsu/llm_wiki`, version **0.5.4**, a Tauri plus
  React/TypeScript desktop application. Third-party open source; not authored here.
- A clone sits at `../llm_wiki` (last commit `nash_su`, *"release: v0.5.4"*, 2026-06-30) and
  a Windows portable build of the same version at
  `~/Downloads/LLM-Wiki-0.5.4-windows-x64-portable/`.
- The shipped executable is a 75.6 MB packed binary, but **the source of exactly that version
  is on disk and readable** — `src/lib/{ingest.ts,ingest-cache.ts,lint.ts,persist.ts}`,
  `src/components/review/review-view.tsx`, and their tests.

### What the application offers, and in which direction

- `.llm-wiki/review.json` holds **74 items** with `type` ∈ {`missing-page` 39,
  `suggestion` 31, `contradiction` 4}, and fields `title`, `description`, `sourcePath`,
  `affectedPages`, `createdAt`, `resolved`. **All 74 are `resolved: false`.**
- Those items are **written by the ingest LLM**, via a `---REVIEW: <type> | <title>---`
  marker in its output (`src/lib/ingest-source-path-collision.test.ts:434,467`).
- The review UI calls `resolveItem` and `dismissItem`. It **consumes** items; it does not
  create them. `createReviewPageDrafts` builds wiki pages *from* an item.
- `src/lib/graph-insights.ts` emits a second suggestion channel over orphan pages and
  disconnected areas.
- The bundled MCP server exposes `llm_wiki_files`, `llm_wiki_graph`, `llm_wiki_projects`,
  `llm_wiki_read_file`, `llm_wiki_rescan_sources`, `llm_wiki_reviews`, `llm_wiki_search`,
  `llm_wiki_status` — all read or rescan. **No write tool.**
- No `audit`, `annotation`, `comment` or `feedback` concept exists in the application source
  as a human-to-agent path.

Both application channels therefore run **agent to human**. A human can resolve or dismiss
what the agent raised; a human cannot file *"this is wrong"*.

## Decision

### D1 — The skill is independent of the application, at runtime and in its data

No behaviour of the skill may require the application to be installed, running, or ever to
have run. Specifically:

- No file under `.llm-wiki/` is an input. This explicitly forgoes
  `.llm-wiki/ingest-cache.json`, whose `entries` map a repository-relative source path to a
  `hash` (sha256), a `timestamp`, and **`filesWritten`** — very nearly the contract `LW-10`
  has to define. `LW-10` implements its own instead.
- The application's local HTTP API (`/api/v1`) and its MCP server are not used, for reading
  or for writing.
- Layout compatibility with the application is a **non-binding property**, not a requirement.
  The layout is owned by this skill; that the application can also open the tree is a
  consequence, not a constraint.

### D2 — `audit/` at the wiki root is the human-to-agent correction channel

A correction is filed as one Markdown file under `audit/`, processed by the skill's `audit`
operation, and archived to `audit/resolved/` with a resolution section. The existing format in
`llm-wiki/references/audit-guide.md`, including the
`anchor_before`/`anchor_text`/`anchor_after` triple, is unchanged.

Two facts make this cheap and necessary:

- **Structurally free.** `.llm-wiki/file-snapshot.json` tracks 275 files under exactly four
  prefixes — `raw/` (194), `wiki/` (79), `purpose.md`, `schema.md`. A directory at the wiki
  root outside those four is invisible to the application: not tracked, not ingested, not
  indexed. `audit/` also sits outside `wiki/`, so the open question about unknown page types
  under `wiki/` does not apply to it.
- **Necessary because this wiki's errors are the invisible kind.** Its subject is project
  history: dates, which ticket reached `done/` when, which session touched which ticket. A
  wrong attribution contradicts nothing visible. `LW-04`'s provenance ladder prevents
  *invented* dates; it cannot prevent a wrong attribution, and neither application channel
  can receive the correction.

### D3 — One layout, not two named profiles

The skill targets a single layout. `SKILL.md`, the five documents under
`llm-wiki/references/`, and the three scripts under `llm-wiki/scripts/` are retargeted to it.
`scripts/audit_review.py` and the two `audit/` passes in `scripts/lint_wiki.py` are **kept
unconditionally** — they are part of the one layout, not profile-conditional code.

Nothing depends on the layout being abandoned: no file in this repository references
`llm-wiki` outside the skill directory itself, and the skill is not installed
(`~/.agents/skills/llm-wiki` does not exist), so no runner executes it.

### Target layout

```
<wiki-root>/
├── purpose.md              ← scope, goal, key questions, thesis
├── schema.md               ← page types, naming, front matter, index and log format
├── audit/                  ← human corrections (D2)
│   └── resolved/
├── raw/
│   ├── sources/            ← ingested repository docs
│   ├── refs/               ← pointer files for what is too large to copy (LW-08)
│   └── assets/
└── wiki/
    ├── index.md
    ├── concepts/  entities/  sources/
    ├── queries/   comparisons/  synthesis/
    └── timeline/           ← shape owned by LW-06
```

## Semantic invariants

- A run of any operation with the application absent produces the same result as a run with
  the application present. The application is never a participant.
- `audit/` is append-only in effect: a processed file moves to `audit/resolved/` carrying its
  resolution, including a rejection. Audit files are never deleted.
- A correction recorded in `audit/` survives a page rewrite. This is the property that makes
  the channel worth having: `LW-10` establishes that a changed source causes its page to be
  rewritten, so a correction living only in the page is lost at the next ingest.

## Rejected alternatives

- **Read `.llm-wiki/ingest-cache.json` as the change-detection input.** Rejected under D1.
  It is the closest thing to free work in this whole plan, and taking it would make every
  ingest depend on an application-owned file whose format is not ours and whose absence would
  be indistinguishable from a first run.
- **Add a write path to the application** (fork, or a patch upstream) so corrections land in
  `review.json`. Rejected: it inverts a channel the application designed to run one way, and
  it makes the skill depend on maintaining a fork of a third-party application.
- **Correct in chat only.** Rejected: the correction dies with the session, which is the
  failure the `audit/` directory was introduced to prevent.
- **Correct by hand-editing the wiki page.** Rejected: `LW-10` rewrites a changed page, so the
  edit is silently overwritten at the next ingest.
- **No correction channel at all.** Considered seriously, on the evidence that all 74
  application review items are unresolved — a precedent for an inbox that is never emptied.
  Rejected because `audit/` is processed by the agent on request rather than by hand, which is
  a materially different cost.
- **Two named profiles.** Rejected: profile-aware `scaffold.py` and `lint_wiki.py` would
  double `LW-09`, double `LW-11`'s eight new passes, and double every later change, for a
  second layout with no consumer.

## Consequences for the plan

- `LW-02` is **demoted from a blocking gate to an optional compatibility check**, and its
  method changes: the application's rules are established by reading the local v0.5.4 source,
  not by running the GUI and observing. It leaves `LW-06`'s blocker set, because under D1 an
  application constraint can no longer dictate the timeline's shape.
- `LW-09`'s scope is now determined: one layout, `audit/` retained, `audit_review.py` and both
  audit lint passes kept.
- `LW-10` implements its own digest and source-to-pages mapping, with
  `.llm-wiki/ingest-cache.json` as a design reference it may read while designing but never as
  a runtime input.
- The other copy of the skill at `~/Downloads/llm-wiki-skill-main/`, which carries the
  Obsidian plugin and the web viewer, diverges further from this one. Both writers stay
  compatible with D2, because the `audit/` file format and anchor algorithm are unchanged.

## Unresolved questions

- **Where the log lives.** The target layout's `schema.md` documents a single
  `wiki/log.md` in reverse chronological order; the layout being retired uses
  `log/YYYYMMDD.md`, one file per day, and `lint_wiki.py` has a pass over that filename shape.
  Under D3 exactly one survives. Owned by `LW-09`; out of scope for this decision.

## Verification strategy

Observable outcomes, none of them claimed as executed here:

- **D1**: a static check that no file under `llm-wiki/` references `.llm-wiki`, `/api/v1`, or
  the MCP tool names; and a functional run of scaffold plus lint on a machine where the
  application has never run.
- **D2**: an audit round trip — file a correction against a generated timeline page, run the
  `audit` operation, and confirm the target file changes, the audit moves to
  `audit/resolved/` with a resolution, and a later re-ingest of the same source does not
  revert the corrected fact.
- **D3**: scaffolding a fresh wiki and immediately linting it reports zero issues, which is
  not currently true and is the state `LW-09` has to reach.
