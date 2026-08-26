# Log Guide — `wiki/log.md`

The operation log is **one file, newest first**: `wiki/log.md`.

Two things about that placement are deliberate.

**One file, not one per day.** A per-day directory exists to keep concurrent writers off each
other. The operations that append here are agent-driven and serialized — one operation finishes
before the next begins — so that problem does not arise, and a single file is the one you can
read top to bottom without opening thirty of them.

**Inside `wiki/`, not beside it.** The log is part of the browsable wiki rather than a sidecar.
`lint` treats it as machinery rather than as a page: it is neither indexed nor expected to have
inbound links.

## Format

```markdown
# Log — <Topic>

Newest first. One entry per operation, as `- HH:MM <op> <description>`.

## 2026-04-10

- 15:05 lint — 2 dead links found, 2 fixed
- 14:30 audit — resolved 20260409-143022-a1b2, corrected the file count
- 09:15 ingest — google-gemma-4, Gemma 4 release notes (5 pages)

## 2026-04-09

- 16:02 scaffold — created the wiki tree
```

Rules `lint` enforces:

- One H1 at the top: the log's title.
- Every H2 is one ISO date, `## YYYY-MM-DD`, and a real date.
- **Dates run newest first.** A date that is not older than the one above it is an error, not a
  style preference: the whole value of the file is that the top is the present.
- Every entry is `- HH:MM <op> <description>`, with a real 24-hour local time.
- `<op>` is one of the operations below. An unrecognised op is an error.

## Operations

| Op | When it appears | Example |
|---|---|---|
| `compile` | Structural edits, splits, merges, index rebuild | `- 10:00 compile — split claude-code into 7 sub-pages` |
| `ingest` | New source added to `raw/sources/`, wiki updated | `- 09:15 ingest — google-gemma-4 (5 pages)` |
| `query` | Question answered, page written to `wiki/queries/` | `- 11:20 query — rag-vs-llm-wiki-tradeoffs` |
| `promote` | A query answer promoted to `comparisons/` or `synthesis/` | `- 11:35 promote — rag-vs-llm-wiki, from the query` |
| `lint` | Lint run, issues fixed | `- 15:05 lint — 2 dead links found, 2 fixed` |
| `audit` | Correction applied and moved to `audit/resolved/` | `- 14:30 audit — resolved 20260409-143022-a1b2` |
| `split` | One page split into a folder | `- 10:00 split — claude-code into claude-code/` |
| `scaffold` | Initial wiki setup | `- 08:00 scaffold — created the wiki tree` |
| `ingest-docs` | A project's specs and tickets compiled | `- 12:40 ingest-docs — 84 artefacts, 3 changed` |
| `timeline` | The temporal axis rebuilt | `- 12:45 timeline — 130 events, 6 dates unknown` |
| `sessions` | Session digests and pointers written | `- 12:50 sessions — 11 sessions, 2 unresolved` |

The last three are the project-history operations. They report counts because the counts are the
signal: `6 dates unknown` in a `timeline` entry is the line that tells you the axis has gaps.

## Quick reads

```bash
# The twenty most recent entries
grep -m 20 '^- ' wiki/log.md

# Every audit resolution
grep '^- .* audit ' wiki/log.md

# Everything that happened on one day
sed -n '/^## 2026-04-09$/,/^## 2026-04-08$/p' wiki/log.md
```

## Migrating an existing `log/` directory

A wiki built on the retired layout has `log/YYYYMMDD.md`, one file per day, with entries as
`## [HH:MM] <op> | <description>`. To convert:

1. Read `log/*.md` in **descending** filename order.
2. For each file, emit `## YYYY-MM-DD` from its filename.
3. For each `## [HH:MM] <op> | <description>` inside it, emit `- HH:MM <op> — <description>`.
   Sort the entries within a day newest first as well.
4. Fold the body bullets under an entry into its description, or drop them: the log is a
   pointer, not a diary, and the page it names holds the detail.
5. Write the result to `wiki/log.md` and delete `log/`.

This is a one-time manual conversion. The skill does not automate it, and `lint` will tell you
when you are done: the `layout` pass wants `wiki/log.md` to exist and the `log-shape` pass wants
it in order.

## What not to put in the log

- **Content.** Never paste a chunk of the page you just wrote. The log is a pointer.
- **Long rationale.** A design decision belongs on a page, or in `purpose.md` — not in a log line.
- **Secrets or credentials.** Never.
- **Correction bodies.** The audit ID and one line. The file in `audit/` already has the rest.
