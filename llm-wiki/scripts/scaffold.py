#!/usr/bin/env python3
"""Create a new wiki tree, ready for the operations.

The layout below is the skill's **single** layout. The shape this skill once documented —
``CLAUDE.md``, ``log/YYYYMMDD.md``, ``raw/{articles,papers,notes}``, ``wiki/summaries``,
``outputs/queries`` — is gone. There is no second profile to choose between.

    <wiki-root>/
    ├── llm-wiki-project.json   the binding: which project this wiki is the history of
    ├── purpose.md              scope, goal, key questions, thesis
    ├── schema.md               page types, naming, front matter, index and log format
    ├── audit/                  human corrections, the one channel running human to agent
    │   └── resolved/
    ├── raw/
    │   ├── sources/            ingested material, including repository docs
    │   ├── refs/               pointers to what is too large to copy
    │   └── assets/
    └── wiki/
        ├── index.md            every page, exactly once
        ├── log.md              operation log, newest first
        ├── concepts/  entities/  sources/
        ├── queries/   comparisons/  synthesis/
        └── timeline/           the temporal axis, with tickets/ beneath it

Two placements are deliberate rather than incidental:

``audit/`` sits at the root, outside ``wiki/``
    The LLM Wiki application watches only ``raw/sources``, ``wiki``, ``purpose.md`` and
    ``schema.md``, so a root directory outside that set is invisible to it. The correction
    channel therefore costs nothing in compatibility, and it has to exist because both of that
    application's own channels run the other way, agent to human.

``wiki/log.md`` is one file, not one per day
    It lives inside ``wiki/`` so the log is part of the browsable wiki rather than a sidecar,
    and the application's vector indexer skips the ``log`` stem so it never pollutes semantic
    search. The operations that append to it are agent-driven and serialized, so the
    concurrent-append problem a per-day directory solves does not arise here.

Usage:
    python3 scaffold.py <wiki-root> "<Topic Title>" [--project-root <path>]

On Windows ``python3`` may resolve to a Microsoft Store alias that does not run Python. Use
``python`` there.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from console import utf8_stdout
from root_catalog import PROJECT_SOURCES, SESSION_SOURCES, TIMELINE, catalog_block

sys.path.insert(0, str(Path(__file__).resolve().parent))

DIRECTORIES = (
    "audit",
    "audit/resolved",
    "raw/sources",
    "raw/refs",
    "raw/assets",
    "wiki/concepts",
    "wiki/entities",
    "wiki/sources",
    "wiki/queries",
    "wiki/comparisons",
    "wiki/synthesis",
    "wiki/timeline",
    "wiki/timeline/tickets",
)

PURPOSE = """# Project Purpose

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
"""

SCHEMA = """# Wiki Schema

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

- Files: `kebab-case.md`
- Entities: the official name where one exists
- Concepts: descriptive noun phrases
- A page compiled from a project artefact is named from the artefact's **identity**, never from
  its path, so moving the artefact updates the page instead of creating a second one

## Frontmatter

Every page carries YAML front matter. **Values are flat scalars or lists of scalars.** A nested
map survives on disk but is read back by the LLM Wiki application as a single JSON string, so
compound information travels as sibling keys.

```yaml
---
type: entity | concept | source | query | comparison | synthesis | lifecycle | period
title: Human-readable title
tags: []
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

A page compiled from a project artefact also carries:

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

**Every date carries the rung that produced it.** A date without provenance is not a date this
wiki will state, and an unresolved date is written as unknown rather than as a plausible value.

## Index Format

`wiki/index.md` lists every page grouped by type, each exactly once:

```
- [[sources/<page-slug>]] — one-line description
```

The root catalog has mixed ownership. Exact HTML-comment boundaries identify the generated
`project-sources`, `session-sources`, and `timeline` blocks. Compilers replace only those
blocks; headings, links, and prose outside them are human-owned and remain byte-identical.
Missing or ambiguous boundaries fail closed and are never inferred from heading text.

## Log Format

`wiki/log.md` records operations newest first:

```
## YYYY-MM-DD

- HH:MM <op> — <one line: what changed, and how many pages>
```

## Cross-referencing Rules

- Link with `[[page-slug]]`.
- Every page appears in `wiki/index.md` exactly once; lint enforces it.
- A lifecycle record links the sessions that named its ticket, and each links back.

## Contradiction Handling

When sources disagree:

1. Note the contradiction on the relevant concept or entity page.
2. Open or update a query page to track it.
3. Link both sources from the query page.
4. Resolve in a synthesis page once the evidence supports one reading.

A **human correction** is a different thing from a contradiction between sources. It goes in
`audit/`, where the audit operation applies it and archives the file to `audit/resolved/`.
"""

INDEX = """# Index — {title}

> {title}: one-sentence scope.

## Navigation

[[#Concepts]] · [[#Entities]] · [[#Sources]] · [[#Queries]] · [[#Synthesis]] · [[#Timeline]]

## Concepts

## Entities

## Sources

{project_catalog}
{session_catalog}
## Queries

## Comparisons

## Synthesis

{timeline_catalog}
## Open Questions
"""

LOG = """# Log — {title}

Newest first. One entry per operation, as `- HH:MM <op> <description>`.

## {today}

- {now} scaffold — created the wiki tree
"""

AUDIT_README = """# Audit

One file per human correction. This is the only channel that runs **human to agent**: the agent
writes the wiki, and this is where a human says it got something wrong.

A correction is one Markdown file with front matter locating it and a body saying what is wrong
and what is right. The audit operation applies it, appends a `# Resolution` section, and moves
the file to `resolved/`. Nothing here is ever deleted, a rejected correction included: the
rejection and its reason are the valuable part.

See `references/audit-guide.md` for the file format and the anchor strategy.
"""


def scaffold(wiki_root: Path, title: str, project_root: Path | None = None) -> list[str]:
    """Create the tree. Returns the relative paths written, sorted."""

    for relative in DIRECTORIES:
        (wiki_root / relative).mkdir(parents=True, exist_ok=True)

    stamp = datetime.now()
    written: list[str] = []
    files = {
        "purpose.md": PURPOSE,
        "schema.md": SCHEMA,
        "wiki/index.md": INDEX.format(
            title=title,
            project_catalog=catalog_block(
                PROJECT_SOURCES,
                "> Project history compiled from the repository's own `docs/`.\n",
            ),
            session_catalog=catalog_block(SESSION_SOURCES, "## Session sources\n"),
            timeline_catalog=catalog_block(TIMELINE, "## Timeline\n"),
        ),
        "wiki/log.md": LOG.format(
            title=title, today=stamp.date().isoformat(), now=stamp.strftime("%H:%M")
        ),
        "audit/README.md": AUDIT_README,
    }
    for relative, content in files.items():
        target = wiki_root / relative
        if not target.exists():
            target.write_text(content, encoding="utf-8")
            written.append(relative)

    if project_root is not None:
        from project_binding import write_binding

        write_binding(wiki_root, project_root)
        written.append("llm-wiki-project.json")
    return sorted(written)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    wiki_root = Path(argv[0])
    title = argv[1]
    project_root = None
    if "--project-root" in argv:
        project_root = Path(argv[argv.index("--project-root") + 1])
    written = scaffold(wiki_root, title, project_root)
    print(f"scaffolded {wiki_root}")
    for relative in written:
        print(f"  + {relative}")
    if project_root is None:
        print()
        print("No binding written. Pass --project-root <path> to record which project this")
        print("wiki is the history of; every operation needs it.")
    return 0


if __name__ == "__main__":
    utf8_stdout()
    raise SystemExit(main(sys.argv[1:]))
