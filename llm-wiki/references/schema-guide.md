# Schema Guide — `purpose.md` and `schema.md`

Two files configure a wiki, and both are read at the start of every session together with
`wiki/index.md`. They answer different questions and change on different rhythms.

| File | Answers | Changes |
|------|---------|---------|
| `purpose.md` | *What is this wiki for?* Scope, key questions, thesis | When the direction changes |
| `schema.md` | *How is this wiki shaped?* Page types, naming, front matter, formats | When a new page type is needed |

Neither holds the list of current pages. `wiki/index.md` is that list, it is regenerated on
every compile, and duplicating it in a configuration file guarantees the copy goes stale.

## Why they matter

Without a schema the LLM invents inconsistent page names, writes overlapping pages, and drifts
out of scope. With one it behaves like a disciplined maintainer. The most common failure a
schema prevents is a **duplicate page under a slightly different name** — and the rule that
prevents it is the identity rule below.

## `purpose.md`

```markdown
# Project Purpose

## Goal

<One paragraph. What is this wiki the history or the study of, and why does it exist?>

## Key Questions

1. <A question the wiki should be able to answer once it has material.>
2. <Another.>

## Scope

**In scope:**

- <What belongs.>

**Out of scope:**

- <What does not, and why.>

## Thesis

> <One claim the wiki is accumulating evidence for or against.>
```

**A good scope statement prevents sprawl.** A wiki about "LLM memory techniques" excludes "LLM
training" even though the two are related — and says so, so the exclusion survives the next
session.

**Key questions give the LLM direction.** Without them it ingests the most obvious sources and
misses what you actually wanted to know.

**Key questions are also where deferred corrections land.** When an `audit` correction is
deferred rather than accepted or rejected, the question it raises goes here.

## `schema.md`

The scaffold writes a complete default. Change it only where this wiki needs something the
default does not cover.

```markdown
# Wiki Schema

## Page Types

| Type | Directory | Purpose |
|------|-----------|---------|
| entity | wiki/entities/ | Named things: people, tools, organisations, datasets |
| concept | wiki/concepts/ | Ideas, techniques, phenomena, frameworks |
| source | wiki/sources/ | Ingested material: papers, articles, repository docs, sessions |
| query | wiki/queries/ | Open questions under active investigation |
| comparison | wiki/comparisons/ | Side-by-side analysis of related entities |
| synthesis | wiki/synthesis/ | Cross-cutting summaries and conclusions |
| lifecycle | wiki/timeline/tickets/ | One record per ticket: disposition, dates, provenance |
| period | wiki/timeline/ | One page per period in which something happened |

## Naming Conventions
## Frontmatter
## Index Format
## Log Format
## Cross-referencing Rules
## Contradiction Handling
```

### The naming rule that matters most

**A page compiled from a project artefact is named from the artefact's identity, never from its
path.** A ticket that moves from `docs/tickets/family/01.md` to
`docs/tickets/family/done/01.md` keeps its identity `ticket:family/01`, so the ingest updates
one page. Name it from the path instead and the move mints a second page beside the first, with
no signal that the two are the same thing.

Where an artefact has no stable identity the page records a weak `path:` key and says on its own
face that it is weak. A limitation stated on the page is a limitation a reader can act on.

For hand-written pages: files are `kebab-case.md`, entities take the official name where one
exists, and concepts take descriptive noun phrases.

### Front matter is flat

Values are scalars or lists of scalars. A nested map survives on disk but several Markdown
readers hand it back as one opaque string, so compound information travels as sibling keys:
`created` and `created_provenance`, not a `created` map with a `provenance` field inside it.

Keep every value on **one line**. A folded or literal block scalar is valid YAML that more than
one front-matter reader in this repository rejects outright, and the failure surfaces far from
its cause.

```yaml
---
type: concept
title: Human-readable title
tags: []
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [list of raw/sources slugs this page draws from]
---
```

A page compiled from a project artefact carries more:

```yaml
identity_key: ticket:<folder>/<ticket_id> | artifact:<id> | path:<repo-relative-path>
identity_strength: stable | weak
source_path: <repo-relative-path>
source_digest: sha256:<hex>
source_status: present | missing
disposition: open | completed | canceled | on-hold | not-applicable
created_provenance: git-rename | git-commit | frontmatter | session-observed | mtime | unknown
disposition_changed_provenance: <the same set>
```

**Every date carries the rung that produced it.** A date without provenance is not a date the
wiki will state, and an unresolved date is written as `unknown` rather than as a plausible
value.

### Wikilinks

- Link with `[[page-slug]]`, matching the path under `wiki/` without the extension.
- For a folder-split page, link the index: `[[concepts/foo/index|foo]]`.
- Link the first mention of every entity or concept. Do not link the same page more than twice
  in one page.
- Being listed in `wiki/index.md` is not a link. The index is a catalog; `lint` asks for both.

### Diagrams and formulas

All diagrams are **mermaid**; no ASCII art. All formulas are **KaTeX**.

### Contradiction handling

When sources disagree: note the contradiction on the relevant page, open or update a page in
`wiki/queries/`, link both sources from it, and resolve into `wiki/synthesis/` once the evidence
supports one reading.

A **human correction** is a different thing from a contradiction between sources. It goes in
`audit/`. See `audit-guide.md`.

## Update cadence

- After a compile: nothing here changes. `wiki/index.md` carries the page list.
- After an audit pass: any deferred question goes under key questions in `purpose.md`.
- When a page type is needed that the table does not name: add it to `schema.md`, create its
  directory, and add it to `LAYOUT_DIRECTORIES` in `scripts/lint_wiki.py` so lint knows the
  directory is meant to be there.
- Monthly: reread the scope and prune stale key questions.
