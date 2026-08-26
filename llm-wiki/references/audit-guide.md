# Audit Guide — human corrections on wiki content

`audit/` is the human feedback surface: one file per correction, YAML front matter plus a
Markdown body, written by a human in any editor and **consumed by the AI during the `audit`
operation**.

It is the only channel in the tree that runs human to agent. Everything else — pages, the index,
the log, the timeline — runs the other way.

## Why it exists

AI-written content is wrong sometimes. Raw sources contradict each other. A correction given in
chat is lost the moment the conversation ends. `audit/` gives a correction a permanent,
location-anchored home that the AI, `lint_wiki.py` and `audit_review.py` all understand, with no
tool to install and no application to run.

## Directory layout

```
<wiki-root>/audit/
├── README.md                              ← documents the directory; not a correction
├── 20260409-143022-claude-code-size.md    ← open
├── 20260409-150110-rag-definition.md      ← open
└── resolved/
    ├── 20260408-110505-typo-gemma.md      ← applied, with a resolution
    └── 20260407-180012-rejected-scope.md  ← rejected, with the rationale
```

- `audit/*.md` — open corrections, not yet processed.
- `audit/resolved/*.md` — processed. **Nothing is ever deleted**; a rejection stays with its
  reason, which is the part worth keeping.
- `README.md` is skipped by both scripts. It has no front matter and is not a correction.

## File format

Filename: `YYYYMMDD-HHMMSS-<short-slug>.md`. The prefix is the creation timestamp in local time;
the slug is a human-readable hint from the selected text or the comment.

```markdown
---
id: 20260409-143022-a1b2
target: concepts/claude-code/architecture.md
target_lines: [45, 52]
anchor_before: "| Dimension | Detail |\n|---|---|\n"
anchor_text: "| **Size** | ~1,900 files, 512,000+ lines |"
anchor_after: "\n| **Language** | TypeScript (strict) |"
severity: warn
author: lewis
source: manual
created: 2026-04-09T14:30:22+08:00
status: open
---

# Comment

Should be ~1,800 files, per the tree at commit abc123 on 2026-03-31.
`find . -type f | wc -l` gave 1817 at the time. The number feeds three estimates below it.

# Resolution

<!-- Filled in when the correction is processed and moved to resolved/ -->
```

### Front matter fields

Every field is required. `lint_wiki.py`'s `audit-shape` pass reports any that is missing or
invalid, so a malformed correction is never silently skipped.

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique: `YYYYMMDD-HHMMSS-<4hex>`. Matches the filename prefix. |
| `target` | string | Path relative to the wiki root, or to `wiki/`. Must exist — the `audit-targets` pass checks it. |
| `target_lines` | `[int, int]` | Best-effort 1-indexed inclusive range at the time of writing. Expected to drift. |
| `anchor_before` | string | Up to ~80 characters immediately before the selection. Verbatim, newlines escaped. |
| `anchor_text` | string | The exact selected text. Verbatim. |
| `anchor_after` | string | Up to ~80 characters immediately after the selection. Verbatim. |
| `severity` | enum | `info`, `suggest`, `warn`, `error`. |
| `author` | string | Free text. |
| `source` | enum | `manual`, `obsidian-plugin`, `web-viewer`. |
| `created` | ISO 8601 | Timestamp with timezone. |
| `status` | enum | `open` in `audit/`, `resolved` in `audit/resolved/`. Lint checks it against the directory. |

`source: manual` is the value for a correction a human wrote by hand, and it is the only value
anything in this skill produces. The other two are accepted so a wiki that was previously fed by
an external editor plugin still lints, but no tool here writes them.

### Severity semantics

- **info** — worth noting, not wrong. Extra context, alternate phrasing.
- **suggest** — consider this. Reword, reorganise.
- **warn** — something looks off. A stale number, an ambiguous sentence.
- **error** — this is wrong. A factual mistake, a broken link, a wrong attribution.

Process `error` and `warn` first, then `suggest`, then `info`.

## Anchor strategy

Line numbers alone are fragile: any edit earlier in the file invalidates them. So every
correction carries a **text anchor window** alongside the line numbers, and this guide is the
single source of truth for how to use it.

On write:

1. Record `target_lines` from the selection.
2. `anchor_text` = the exact selected characters.
3. `anchor_before` = up to 80 characters immediately before the selection start, clamped to the
   start of the file.
4. `anchor_after` = up to 80 characters immediately after the selection end, clamped to the end
   of the file.

On read, during the `audit` op:

1. Try `target_lines` — does the text in that range contain `anchor_text`?
2. If not, search the whole file for `anchor_text`. Exactly one match: use it.
3. Several matches: search for `anchor_before + anchor_text + anchor_after` as one key.
4. Still nothing: the anchor is **stale**. Raise it with the user. Do not silently drop it, and
   do not guess — ask whether to re-anchor, reject, or archive.

Step 4 is the one that matters. A stale anchor silently skipped is a correction the human
believes was applied.

## Processing workflow (the `audit` op)

`SKILL.md` → "The five operations" → `audit` is the canonical version. In short:

1. `python3 scripts/audit_review.py <wiki-root> --open` for a list grouped by target.
2. For each open correction:
   - Read the file; use the anchor to locate the range in the target.
   - Decide: accept, partial, reject, or defer.
   - Apply the **smallest** edit that fixes the issue.
   - Append a `# Resolution` section.
   - Change `status: open` to `status: resolved` in the front matter.
   - Move the file to `audit/resolved/`.
   - Append `- HH:MM audit — resolved <id>, <one line>` to `wiki/log.md`.
3. Deferred — an unresolvable contradiction, say — leaves the file in `audit/` and adds the
   question to `purpose.md` under key questions, with the correction's id.

## Resolution section format

```markdown
# Resolution

2026-04-10 · accepted.
Fixed the file count (was "~1,900", corrected to "~1,800" per commit abc123).
Updated: concepts/claude-code/architecture.md lines 47–48.
```

- Date · decision: `accepted`, `partial`, `rejected`, or `deferred`.
- One to three sentences on what you did and why.
- Which files were touched, for anything non-trivial.

For a **rejected** correction, say *why* — most often "out of scope per `purpose.md`" or
"contradicts the more authoritative source X". Rejected corrections still move to `resolved/` so
they are not reprocessed, and they stay readable in case the scope changes later.

## Tooling

- `scripts/lint_wiki.py` — validates correction shape and that every open `target` exists.
- `scripts/audit_review.py` — lists and groups corrections by target file, severity first.

Both are standard-library Python. There is nothing else to install, and nothing that has to be
running for a correction to be filed: a text editor and this format are the whole mechanism.
