# LLM Wiki application compatibility at v0.5.4

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-app-compatibility`
- Role: `research`
- Parent: [LLM Wiki as a Project History Knowledge Base](../specs/llm-wiki-project-history-wayfinder.md)

Produced by `LW-02`. The owner edge is on the map rather than on the ticket because the
scheduler binds the ticket source by digest, and editing the ticket file mid-run is source
drift.

## Answer

The application is not a constraint to work around. All three questions the wayfinder map
raised come back permissive, and one of them comes back the opposite of what the map assumed:
**a custom directory under `wiki/` is a first-class page type, by design, in code.**

- An unknown directory under `wiki/` is **watched recursively**, not skipped and not rejected.
- An unknown `type:` value is **supported**: the application derives a page type from the
  directory name for any directory it does not recognise, and title-cases it for display.
- Extra front-matter keys are **preserved**, with one constraint: keep them flat, because
  nested values are read back as JSON strings.

So `wiki/timeline/` as designed in `LW-06` needs no accommodation. This is advisory only —
[the independence decision](../specs/llm-wiki-app-independence-decision.md) already removed
the application's power to gate the design — but where compatibility was expected to cost
something, it costs nothing.

Every claim below is scoped to **`nashsu/llm_wiki` v0.5.4**, read at the clone in
`../llm_wiki` (`package.json` version `0.5.4`, last commit `nash_su`, *"release: v0.5.4"*),
which is the version built into `~/Downloads/LLM-Wiki-0.5.4-windows-x64-portable/`. A later
release may differ.

## Q1 — An unknown directory under `wiki/`

**Included, recursively.** The watch predicate is a single line:

`src-tauri/src/commands/file_sync.rs:1115`

```rust
rel == "purpose.md" || rel == "schema.md" || (rel.starts_with("wiki/") && rel.ends_with(".md"))
```

Any `.md` file at any depth under `wiki/` qualifies. There is no directory allowlist inside
`wiki/`. The scan roots are hardcoded at `file_sync.rs:524` and `:647` as
`&["raw/sources", "wiki", "purpose.md", "schema.md"]`, and the walk over them is recursive —
`WalkDir::new(...)` at `:551`, `:617`, and `:678`.

Two consequences:

- `wiki/timeline/index.md` and `wiki/timeline/tickets/lw-01.md` are watched like any other
  page.
- `audit/` at the wiki root is **not** watched. It is neither `purpose.md` nor `schema.md`
  nor under `wiki/`, so it fails the predicate. This confirms from source what
  `.llm-wiki/file-snapshot.json` showed from data: the correction channel chosen in
  `LW-01` is invisible to the application, and therefore free.

## Q2 — An unknown `type:` value

**Supported as a custom type, derived from the directory.** `src/lib/wiki-page-types.ts:34`

```ts
const customDir = normalized.match(/(?:^|\/)wiki\/([^/.][^/]*)\/[^/]+\.md$/)?.[1]
if (customDir) return customDir
```

`inferWikiTypeFromPath` first tries a table of nine known directory-to-type pairs, then falls
through to this. `wiki/timeline/2026-08.md` therefore resolves to the type `timeline`, and
`wikiTypeLabel` (same file, `:39`) title-cases it to `Timeline` for the knowledge tree
(`src/components/layout/knowledge-tree.tsx:337`, defaulting to `"other"`) and the activity
panel (`src/components/layout/activity-panel.tsx:58`). The leading `[^/.]` in the pattern is
why `.llm-wiki/` never becomes a type.

Three corrections to the map's premise:

- **The closed set is not the application's.** The seven types enumerated in
  `../minnarone/wiki/minnarone-wiki/schema.md` are that wiki's own convention. The
  application's own list, `GENERATION_WIKI_TYPES` at `wiki-page-types.ts:1`, has **nine**
  entries and includes `thesis`, `methodology`, and `finding`, none of which that `schema.md`
  mentions.
- **The type comes from the path, not from the front matter.** Nothing reads a
  `type:` key to decide a page's type. So a page at `wiki/timeline/x.md` carrying
  `type: lifecycle` in its front matter still displays as `Timeline`. That is not an error,
  but it is a silent disagreement, and it argues for naming the directory whatever the type
  should be rather than carrying a second answer in front matter.
- **The application's lint does not police types.** Its `LintItem` union is exactly
  `"orphan" | "broken-link" | "no-outlinks" | "semantic"` (`src/lib/lint.ts:10`). No pass
  looks at page types or unknown directories.

### Indexing sub-question

The vector indexer walks the tree recursively and takes any `.md` file, excluding by
**filename stem** rather than by directory (`src/lib/embedding.ts:644`):

```ts
if (node.is_dir && node.children) { /* recurse */ }
else if (!node.is_dir && node.name.endsWith(".md")) {
  const id = node.name.replace(/\.md$/, "")
  if (!["index", "log", "overview", "purpose", "schema"].includes(id)) { /* index it */ }
```

So pages in a custom directory **are** indexed. One detail worth knowing for `LW-06`: a
timeline landing page named `index.md` is excluded from semantic search by that stem list,
exactly as `wiki/index.md` is. Per-period pages named `2026-08.md` are indexed.

## Q3 — Extra front-matter keys

**Preserved.** `normalize()` in `src/lib/frontmatter.ts:180` iterates every key with
`Object.entries` and copies it through. There is no allowlist and nothing is dropped. The
parser also exposes the literal block and documents the contract at `frontmatter.ts:5`:

> Callers that edit only the body — e.g. the read-mode renderers or body-only transforms —
> write back `rawBlock + body` so user-managed YAML survives untouched.

**The one constraint: keep added keys flat.** `FrontmatterValue` is `string | string[]`
(`frontmatter.ts:3`), and `stringifyScalar` (`:193`) JSON-encodes anything it cannot reduce to
a scalar. A nested map such as

```yaml
date_provenance:
  created: git-commit
  completed: git-rename
```

survives on disk untouched, but the application reads it as the single string
`{"created":"git-commit","completed":"git-rename"}`.

Advice, not constraint, for the two tickets that need somewhere to put fields:

- `LW-10` may put `identity_key` and `source_digest` in front matter as plain scalars. A
  sidecar is not required on the application's account.
- `LW-04` should flatten date provenance — `created_provenance: git-commit` and
  `completed_provenance: git-rename` as sibling scalars, rather than one nested map.

## What remains unobserved

- **The GUI was never launched.** Every claim here is read from source at a named version.
  Nothing asserts what the application displays on screen.
- **No behaviour was confirmed by running the application against a wiki containing
  `wiki/timeline/`.** The code paths above are unambiguous, but they are read, not executed.
- **Version-scoped.** These are facts about v0.5.4 only. `nashsu/llm_wiki` is third-party and
  under active development; the last commit in the local clone is 2026-06-30.
- Neither `../llm_wiki` nor `../minnarone/wiki/minnarone-wiki` was modified while producing
  this finding.
