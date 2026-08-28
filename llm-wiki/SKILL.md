---
name: llm-wiki
description: Build and maintain a self-compiling markdown wiki — an Agent ingests raw sources and a project's own docs, compiles cross-linked concept/entity/source pages, builds a dated timeline from Git and session history, answers queries against the corpus, lints the graph for health, and applies human corrections filed in audit/. Use when (1) scaffolding a knowledge base for a research topic or a project's history, (2) ingesting articles/papers/notes into raw/sources/, (3) ingesting a repository's specs and tickets and building the temporal axis over them, (4) answering questions against the wiki and filing durable answers back, (5) running lint passes for dead links, orphan pages, index coverage, log and audit shape, (6) applying human feedback from audit/. Not for general note-taking, daily journals, or non-wiki Obsidian use.
---

# LLM Wiki — Karpathy Knowledge Base Pattern

> **Experimental skill — iterating.**
> Authored by Lewis Liu (lylewis@outlook.com) · Inspired by [Karpathy's llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## Core idea

Instead of RAG (re-retrieving raw docs on every query), the LLM **compiles** raw sources into a persistent, cross-linked wiki. Every ingest, query, lint, and audit pass makes the wiki richer. Knowledge compounds — and the human stays in the loop through a structured feedback channel instead of ad-hoc corrections that get lost.

- **You** own: sourcing raw material, asking good questions, steering direction, filing feedback on anything the AI got wrong.
- **LLM** owns: all writing, cross-referencing, filing, bookkeeping, and acting on your feedback.

Every session starts by reading `purpose.md`, `schema.md`, and `wiki/index.md`.

## One layout

There is one layout and no profile to pick. `docs/specs/llm-wiki-app-independence-decision.md` settled that, along with the rule underneath it: **nothing here depends on any application.** No install step, no daemon, no private state directory, no HTTP API, no third-party Python package. The scripts read and write plain Markdown with the standard library. A wiki produced here opens in Obsidian, in a text editor, and in anything else that reads Markdown, but requires none of them.

```
<wiki-root>/
├── llm-wiki-project.json  ← Binding: which project this wiki is the history of (optional)
├── purpose.md             ← Scope, goal, key questions, thesis
├── schema.md              ← Page types, naming, front matter, index and log format
├── audit/                 ← Human corrections, one file each — the human-to-agent channel
│   └── resolved/          ← Applied or rejected, with a resolution appended
├── raw/                   ← Source material (the LLM reads, never rewrites)
│   ├── sources/           ← Articles, papers, notes, ingested repository docs
│   ├── refs/              ← Pointer files for anything too large to copy
│   └── assets/            ← Images and binaries a page cites
└── wiki/                  ← LLM-generated knowledge (the LLM writes, you read)
    ├── index.md           ← Master catalog — every page, exactly once
    ├── log.md             ← Operation log, newest first
    ├── concepts/          ← Ideas, techniques, phenomena (split when >1200 words)
    ├── entities/          ← People, tools, papers, organisations
    ├── sources/           ← One page per ingested source
    ├── queries/           ← Answers to questions asked of the wiki
    ├── comparisons/       ← Side-by-side analysis of related entities
    ├── synthesis/         ← Cross-cutting conclusions
    └── timeline/          ← The temporal axis
        └── tickets/       ← One lifecycle record per ticket
```

`purpose.md` and `schema.md` are the two configuration files, and both are read at the start of every session. `purpose.md` says what the wiki is for; `schema.md` says how it is shaped. Read `references/schema-guide.md` for what goes in each.

`audit/` sits at the root, outside `wiki/`, because it is the one channel that runs **human to agent** — everything else in the tree runs the other way.

## Core principles

Four rules govern everything below. If a future instruction contradicts one, flag it to the user before acting.

### 1. Divide and conquer

A single concept page should **never** try to cover a complex topic end-to-end. Target: **400–1200 words per page**. When a topic would blow past that:

- Create a subfolder: `wiki/concepts/<topic>/`
- Put a short index page at `wiki/concepts/<topic>/index.md` — definition, list of sub-pages, one-line summaries
- Put each aspect in its own file: `wiki/concepts/<topic>/<aspect>.md`
- In `wiki/index.md`, show the hierarchy through indented bullets

Example layout (from a real wiki):
```
wiki/concepts/claude-code/
├── index.md                  (overview + links to sub-pages)
├── architecture.md
├── agent-framework.md
├── bridge-system.md
├── query-engine.md
├── skills-plugins.md
├── state-management.md
└── tool-system.md
```

One fat file covering all seven aspects would be unreadable and unlinkable. Seven focused files plus an index page give you navigation, selective reading, clean backlinks, and small audit targets.

### 2. Mermaid for diagrams, KaTeX for formulas

- **Any flow, sequence, hierarchy, or state diagram** must be written in mermaid — never ASCII art. ASCII boxes rot fast and are impossible to annotate.
  ````
  ```mermaid
  flowchart LR
      A[raw/sources/article] --> B[wiki/sources page]
      B --> C[concept page]
      C --> D[index.md]
  ```
  ````
- **Any formula** must be written in KaTeX: inline or block.

Both render in Obsidian with default settings.

### 3. Raw file policy

Small text-based sources (md, txt, small PDFs, small images) → copy into `raw/sources/`. Images and binaries a page cites → `raw/assets/`.

Large binaries (videos, model weights, installers, datasets, PDFs over 10 MB) → **do not copy**. Instead:

- Create a pointer file at `raw/refs/<slug>.md` with:
  ```yaml
  ---
  kind: ref
  external_path: /Volumes/external/models/llama-3-70b/
  size: ~140 GB
  ---
  ```
  followed by a short description of what it is and why it matters to this wiki.
- Wiki pages cite `[[raw/refs/<slug>]]` exactly like any other source.

This keeps the wiki portable, and keeps it small enough to be tracked in Git if you want it tracked. Whether the wiki or the project's `docs/` are tracked at all is a per-project choice, and no operation here assumes either way.

### 4. Audit is the human feedback surface

The wiki is AI-written; it will be wrong sometimes. The raw sources are human-written; they will contradict each other. `audit/` is how humans correct both without losing the corrections in chat history.

- One correction is one file in `audit/`, with YAML front matter (anchor, target, severity) and a Markdown body. A human writes it in any editor.
- The AI **must** periodically run the `audit` op — never silently ignore `audit/*.md`.
- When a correction is applied, the file moves to `audit/resolved/` with a `# Resolution` section appended and an entry recorded in `wiki/log.md`.
- Nothing in `audit/` is ever deleted. A rejected correction is archived with its rejection rationale, which is the valuable part.

See `references/audit-guide.md` for the file format and the anchor strategy.

---

## The five operations

Every action on the wiki is one of these six, and each mutation appends one entry to
`wiki/log.md`.

### 1. `compile`

(Re)structure wiki content from existing `raw/` material — splitting oversized pages, merging near-duplicates, rebuilding `index.md`.

**When to run**: after a big ingest batch, when a page has outgrown 1200 words, when `index.md` no longer reflects reality, or when the user says "clean up the wiki".

**Steps**:
1. Read `purpose.md`, `schema.md`, `wiki/index.md`, and every file in the target subtree.
2. For each page over ~1200 words: plan a split into `concepts/<topic>/` with an index plus sub-pages. Confirm the plan with the user before writing.
3. For each pair of near-duplicate pages: propose a merge. Confirm, then rewrite.
4. Regenerate `wiki/index.md` so every page is listed exactly once.
5. Log: `- HH:MM compile — <files touched, splits, merges>`

### 2. `ingest`

Add a new source. **One source typically touches 5–15 wiki pages.**

**Steps**:
1. Save the source to `raw/sources/<slug>.md` — or `raw/refs/<slug>.md` as a pointer if it is large (see the raw file policy).
2. Read the source in full.
3. Create `wiki/sources/<slug>.md` (200–400 words — key takeaways, not a rewrite; see `references/article-guide.md`).
4. Create or update the relevant pages in `wiki/concepts/`. Respect divide-and-conquer: split rather than cram.
5. Create or update pages in `wiki/entities/` for any new people, tools, papers, or organisations referenced.
6. Update `wiki/index.md` so the new pages appear under the right heading.
7. Log: `- HH:MM ingest — <slug>, <one line> (N pages)`

### 3. `query`

Answer a question **grounded in the wiki**, not in general knowledge.

**Steps**:
1. Read `wiki/index.md`. Scan for relevant pages by category.
2. Read the identified pages in full; follow one level of wikilinks.
3. If the wiki does not have enough material, say so and suggest what to ingest next instead of inventing an answer.
4. Synthesize the answer, citing pages inline with `[[page-slug]]`.
5. Save to `wiki/queries/<YYYY-MM-DD>-<question-slug>.md` and list it in `wiki/index.md`.
6. If the answer is durable — a comparison, an analysis, a new synthesis — promote a cleaned-up version to `wiki/comparisons/` or `wiki/synthesis/`.
7. Log: `- HH:MM query — <question-slug>`, plus a separate `- HH:MM promote — ...` line if promoted.

### 4. `lint`

Health check, fifteen passes:

```bash
python3 scripts/lint_wiki.py <wiki-root>
```

**Structural passes**, over the wiki alone:

| Pass | Severity | Reports |
|------|----------|---------|
| `layout` | error | A directory or file the layout declares is missing |
| `dead-wikilinks` | error | `[[Target]]` where `Target.md` does not exist |
| `index-drift` | error | A page in no catalog, a catalog nothing links, or a catalog entry with no page |
| `log-shape` | error | `wiki/log.md` out of order, or an entry that is not `- HH:MM <op> <description>` |
| `audit-shape` | error | A malformed correction in `audit/` |
| `audit-targets` | error | An open correction whose `target` file does not exist |
| `orphan-pages` | warning | A page no other page cites |
| `unlinked-concepts` | warning | `[[X]]` linked 3+ times with no page of its own |

**Drift passes**, over the relationship between a page and the artefact it came from. These need a project binding; without one they report that they do not apply rather than reporting green.

| Pass | Severity | Reports |
|------|----------|---------|
| `dangling-source` | error | A page's `source_path` is gone, or no longer matches the globs |
| `stale-page` | error | The artefact's content digest differs from the page's recorded one |
| `duplicate-identity` | error | Two pages carrying one `identity_key` |
| `provenance-validity` | error | A date whose rung is absent, unrecognised, or contradicts its value |
| `timeline-coverage` | warning | A ticket with no lifecycle record, or a dated page with no event |
| `stale-session-pointer` | warning | A transcript that grew, moved, or vanished since its digest |
| `un-ingested-artefact` | info | A file the globs match that has no page yet |

Three properties of this design are worth knowing before reading its output.

**Every pass reports rather than skips.** A missing directory is an issue in `layout`, not a silent success in the pass that would have read it. A pass that cannot fail is worse than no pass, because it reports green and is believed.

**Severity is not decoration.** An `error` is a corruption or a broken reference and sets the exit code. A `warning` is a real signal you may reasonably defer. `info` is the normal steady state — `un-ingested-artefact` fires on everything added since the last ingest. Reporting all three at one volume teaches the reader to skip the output, so `lint` exits `0` when there are no errors even if warnings remain.

**No pass assumes Git.** A project's `docs/` may be untracked and the host may not be a repository; both are supported. A missing history is not drift, so `provenance-validity` checks that a date's rung is *coherent* and never that it is a good one. An `mtime` date is a valid date.

Each pass prints the repair to propose. Propose it, confirm with the user, then apply. Log: `- HH:MM lint — N errors, M warnings, K fixed`.

### 5. `audit`

Apply human feedback from `audit/`.

**Steps**:
1. Run `python3 scripts/audit_review.py <wiki-root> --open` for a list grouped by target file.
2. For each open correction, read the file. Use the `anchor_before` / `anchor_text` / `anchor_after` window to locate the exact range in the target — line numbers drift.
3. Decide: **accept** (apply it), **partially accept** (apply what holds, note the rest), **reject** (say why — the feedback may rest on a misreading of scope or a contradictory source), or **defer** (add it to `purpose.md` under key questions and leave the correction in place).
4. Append a `# Resolution` section to the correction:
   ```markdown
   # Resolution

   2026-04-10 · accepted.
   Fixed the file count (was "~1,900", corrected to "~1,800" per commit abc123).
   Updated: concepts/claude-code/architecture.md lines 47–48.
   ```
5. Move the file from `audit/` to `audit/resolved/`. Filename unchanged.
6. Log per resolved correction: `- HH:MM audit — resolved 20260409-143022-a1b2, <one line>`
7. Never delete a correction. Rejected ones go to `resolved/` too.

See `references/audit-guide.md` for the full format.

### 6. `sync-project`

Compile one existing project-bound wiki through the fail-closed `wiki-sync-v1` boundary:

```bash
python3 scripts/sync_project.py <project-root> --wiki-root <wiki-root> --json
```

The explicit root is required for an external wiki. Without it, discovery checks only the
project root and its direct children. No compatible wiki returns `skipped/absent`; it never
scaffolds one. `auto_sync: disabled` in `llm-wiki-project.json` is a durable skip, while a
missing `auto_sync` value means `enabled` for backward compatibility.

Ingest, timeline rebuild, generated-scope validation, and the full lint run happen in a
staging copy. Only regular non-executable UTF-8 `wiki/**/*.md` may change. An external or
internal-untracked wiki is updated directly after compare-and-swap. An internal tracked wiki
returns a frozen `wiki-sync-v1` candidate; this skill does not commit, deliver, or merge it.
The result always carries one normalized status/reason, a fresh `WikiSyncRef`, origin
provenance, changed paths, and deterministic validation evidence capped at
`implementation-complete`.

The post-integration owner may pass `--source-root <detached-worktree>
--expected-source-head <sha>` so compilation reads the exact integrated docs while discovery,
tracking classification, and publication remain bound to the canonical project root. The
alternate checkout must belong to the same Git common directory and match the expected head;
otherwise synchronization fails closed without touching the wiki.

---

## Project history

A wiki bound to a project — through `llm-wiki-project.json` at its root — additionally compiles that project's own `docs/` and the agent sessions that worked on it. The scripts are self-documenting; run each with `--help`.

| Script | What it does |
|--------|--------------|
| `scripts/project_binding.py` | Reads and writes the binding, and reports whether the project is a Git repository and whether its docs are tracked |
| `scripts/date_provenance.py` | Resolves each artefact's dates, and the rung each date came from |
| `scripts/ingest_docs.py` | Compiles the project's specs and tickets into `wiki/sources/`, keyed on artefact identity rather than path |
| `scripts/build_timeline.py` | Builds `wiki/timeline/` from those pages: one period page per period, one lifecycle record per ticket |
| `scripts/lint_drift.py` | Reports where a page and its artefact have drifted apart |
| `scripts/session_discovery.py` | Finds the Claude Code and Codex transcripts belonging to this project |
| `scripts/session_ingest.py` | Writes a digest and a pointer per session — never the transcript verbatim |
| `scripts/sync_project.py` | Compiles and validates one existing bound wiki, then applies direct output or freezes a tracked candidate |

Two rules hold across all of them, and both are worth knowing before reading any page they produce:

- **A page is named from the artefact's identity, never from its path.** Moving a ticket into `done/` updates its page; it does not mint a second one.
- **Every date carries the rung that produced it**, from `git-rename` down to `unknown`. A date with no witness renders as the word `unknown` with its reason, never as a plausible value.

## `wiki/index.md` format

The LLM rebuilds `index.md` on every compile and touches it on every ingest.

```markdown
# Index — <Topic>

> One-sentence scope of the wiki.

## Navigation

[[#Concepts]] · [[#Entities]] · [[#Sources]] · [[#Queries]] · [[#Synthesis]] · [[#Timeline]]

## Concepts

### <Category A>
- [[concepts/foo]] — one-line summary
- [[concepts/bar/index|bar]] — (folder-split) one-line summary
    - [[concepts/bar/aspect-1]] — ...

## Entities
- [[entities/andrej-karpathy]] — AI researcher, author of the llm-wiki pattern

## Sources
- 2026-04-09 — [[sources/llm-wiki-gist]] — Karpathy's original Gist

## Timeline
- [[timeline/index]] — when things happened, and how each date is known

## Open Questions
- Q1: ...
```

Rules:
- Every wiki page appears exactly once in `index.md`. `lint` enforces it.
- Folder-split concepts show hierarchy through indented bullets.
- `index.md` is a catalog, not a citation. A page also needs a real inbound link from another page.
- **Catalogs nest.** `wiki/index.md` lists `[[timeline/index]]`, and `wiki/timeline/index.md` lists the pages beneath it. `index-drift` accepts a page catalogued at any level, and reports a catalog that no other catalog links — because everything under an unreachable catalog is unreachable too.
- Every `index.md`, at any depth, and `wiki/log.md` are machinery rather than pages: none is catalogued, and none is expected to have inbound links.

## `wiki/log.md` format

One file, newest first. See `references/log-guide.md` for the full convention.

```markdown
# Log — <Topic>

## 2026-04-10

- 14:30 audit — resolved 20260409-143022-a1b2, corrected the file count
- 09:15 ingest — llm-wiki-gist, Karpathy's original (7 pages)

## 2026-04-09

- 16:02 scaffold — created the wiki tree
```

- H1 is the title; each H2 is one ISO date; dates run newest first.
- Each entry is `- HH:MM <op> <description>`.
- Ops: `compile`, `ingest`, `query`, `lint`, `audit`, `promote`, `split`, `scaffold`, `ingest-docs`, `timeline`, `sessions`, `sync-project`.
- Quick scan of recent history: `grep -m 20 '^- ' wiki/log.md`.

The log is one file rather than one file per day because the operations that append to it are agent-driven and serialized, so the concurrent-write problem a per-day directory solves does not arise. It lives inside `wiki/` so it is part of the browsable wiki rather than a sidecar.

## Tooling

| Tool | Purpose |
|------|---------|
| [Obsidian](https://obsidian.md) | Optional IDE for browsing the wiki; graph view shows connections |
| `scripts/scaffold.py` | Create a new wiki tree |
| `scripts/lint_wiki.py` | The health check: eight structural passes, and the driver for the rest |
| `scripts/lint_drift.py` | The seven passes over a page and the artefact it came from |
| `scripts/sync_project.py` | The idempotent `wiki-sync-v1` compile and publication boundary |
| `scripts/audit_review.py` | Group open or resolved corrections by target file |
| project-history scripts | See the table above |

## Starting a new wiki

```bash
python3 scripts/scaffold.py <wiki-root> "<Topic Title>"
python3 scripts/scaffold.py <wiki-root> "<Topic Title>" --project-root <path-to-project>
```

Creates the tree above, with `purpose.md`, `schema.md`, `wiki/index.md`, `wiki/log.md` and `audit/README.md` filled from templates. Pass `--project-root` to record which project the wiki is the history of; every project-history operation needs that binding. A freshly scaffolded wiki passes `lint` with zero issues — if it does not, the scaffold and the lint have drifted apart, and that is a bug in this skill rather than in the wiki.

After scaffolding:
1. Fill in `purpose.md` — scope, key questions, thesis.
2. Adjust `schema.md` if this wiki needs page types the default set does not cover.
3. Start ingesting.
4. Run `lint` periodically.
5. Run `audit` whenever corrections accumulate.

**Interpreter.** The commands above say `python3`, which is the convention across this repository. On Windows `python3` may resolve to a Microsoft Store alias that prints an install prompt instead of running Python; use `python` there. The scripts need nothing beyond CPython 3.10 or later.

## Use cases

- **Research deep-dive** — reading papers and articles on a topic over weeks; the wiki evolves with your understanding, and the audit trail keeps AI mistakes from silently accumulating
- **Project history** — a repository's specs, tickets and agent sessions compiled into a dated account of what was decided and when, with every date carrying its provenance
- **Personal wiki** — notes and ideas compiled into a personal encyclopedia; comment on anything you disagree with later, the AI corrects it
- **Team knowledge base** — fed by threads, meeting notes and docs; corrections filed as files
- **Reading companion** — filing each chapter as you go builds a companion wiki by the end

## References

- `references/schema-guide.md` — What goes in `purpose.md` and `schema.md`
- `references/article-guide.md` — How to write a good page (length, wikilinks, mermaid, math, divide-and-conquer)
- `references/log-guide.md` — The `wiki/log.md` convention
- `references/audit-guide.md` — Correction format, anchor strategy, processing workflow
- `references/tooling-tips.md` — Obsidian setup, capturing sources, optional semantic search
