# LLM Wiki Exact-Source Checkout Sync

## Artifact Graph

- Artifact ID: `spec:llm-wiki-exact-source-checkout-sync`
- Role: `spec`
- Parent: [LLM Wiki Docs-Only Auto-Sync](llm-wiki-docs-only-autosync-wayfinder.md)

### Children

- [WXS-01 — Discover and synchronize the tracked wiki from the exact source checkout](../tickets/llm-wiki-exact-source-checkout-sync/done/01-sync-tracked-wiki-from-exact-source.md)

## Type

Bug-analysis specification.

## Status

Accepted for implementation through the request to make the tracked Agent Skills repository
wiki work. This scope covers only the project-bound `knowledge/` wiki and its existing
`wiki-sync-v1` contract.

## Observed behavior

The canonical repository identity is
`/Users/carlogiuseppesergi/Projects/.agent-skills-runner-latest`. That persistent checkout is
intentionally stale and dirty; its current worktree does not materialize `knowledge/`. The
exact integrated source checkout at head `9f0e009238293d867cb8845b22bdb94c6db0a8ca` is clean and
does contain the tracked `knowledge/` tree, whose binding correctly names the canonical
repository identity.

A read-only production reproduction invoked `sync_project.py` with the canonical project root,
that exact `source_root`, and its expected head. The result was:

- `status: skipped`;
- `reason: absent`;
- no wiki identity or candidate;
- byte-identical project and source checkout status before and after.

`sync_project` validates and compiles from `source_root`, but `discover_wiki` still searches only
the canonical project root when no explicit wiki roots are supplied. Passing the source
checkout's `knowledge/` as an explicit root is not a valid workaround: current classification
would call it external and update tracked generated files directly rather than freeze a
separate candidate.

The first exact-source fixture exposed two additional projection defects. Git does not
materialize empty scaffold directories, so a tracked wiki checkout can be logically complete
while `layout` reports missing empty containers; a disposable compile copy needs to recreate
those containers before linting. Also, retained `source_status: missing` tombstone pages were
rendered as code-only identities under “Removed sources”, leaving the preserved pages outside
every catalog and causing `index-drift`.

## Expected behavior

For a post-integration invocation with an exact alternate source checkout:

1. bounded discovery finds the wiki at the source checkout root or a direct child;
2. the wiki binding is still validated against the canonical project root;
3. its stable logical identity is the canonical project root plus its safe relative path;
4. tracking is classified in the exact source checkout only after proving both checkouts share
   one Git common directory;
5. tracked generated output is frozen as the normal separate `wiki-sync-v1` candidate;
6. neither the canonical dirty checkout nor the exact source checkout is modified;
7. empty logical scaffold directories omitted by Git are materialized only in the disposable
   compile stage, while direct lint recognizes that absence only for a Git-tracked wiki;
8. retained tombstones remain linked from the root catalog and therefore remain browsable;
9. publication and merge remain separately authorized.

## Root cause

The implementation conflates three identities:

- **canonical project root**, which owns the binding and origin repository identity;
- **physical source checkout**, which supplies the exact integrated docs and tracked wiki tree;
- **logical wiki identity**, which must remain stable when a temporary detached checkout path
  changes.

`_source_checkout` already proves the canonical and source roots share a Git common directory
and binds the expected source head. Discovery and `_classify` do not consume that distinction:
discovery remains rooted at the canonical worktree and classification treats any root outside
that worktree as external. Layout validation also treats filesystem absence as semantic absence
without accounting for empty directories that a committed Git tree cannot represent. Index
rendering preserves missing-source pages but omits links to them, contradicting the invariant
that every retained page appears in exactly one catalog.

## Goals

- Discover an existing internal wiki from an exact alternate source checkout without widening
  the bounded locator.
- Preserve exact checkout-specific binding to the canonical project root.
- Derive a deterministic logical wiki identity independent of temporary checkout paths.
- Classify complete generated-path tracking in the source checkout and freeze tracked output.
- Synchronize the Agent Skills `knowledge/` projection from current integrated `docs/` and
  require zero wiki lint errors before candidate creation and from the tracked checkout.
- Retain the existing separate manual exact-head authorization for the generated wiki PR.

## Non-goals

- Rebinding the wiki to a ticket or temporary worktree.
- Making any mismatched worktree binding succeed.
- Treating an explicitly configured external wiki as internal because Git tracks it.
- Scaffolding a missing wiki or changing `purpose.md`, `schema.md`, `raw/`, `audit/`, or the
  binding file.
- Changing generic docs-only v1, OHR retrieval architecture, external-note ingest, or Obsidian.
- Mutating unrelated run ledgers, ticket dispositions, local Pi, or Betsharemarket artifacts.

## Design

### Canonical and physical roots remain separate

When `source_root != project_root` and no explicit wiki roots were supplied, discovery uses the
source checkout as its bounded physical search root. A candidate at physical relative path `R`
is compatible only when:

- `R` is canonical, non-empty where required, and does not escape through aliases or symlinks;
- the binding resolves exactly to `project_root`, not `source_root`;
- both roots are Git worktrees with the same canonical Git common directory;
- the observed source head still equals `expected_source_head`.

The logical wiki identity is `(project_root / R)` even if that path is not materialized in the
canonical checkout. `WikiSyncRef` and result provenance use this stable logical identity; file
reads, locking, staging, source-state checks, and compare-and-swap use the physical root.

### Tracking belongs to the exact source checkout

For a source-materialized internal wiki, classify `wiki/**/*.md` against the source checkout's
index. All existing generated files tracked means `internal-tracked`; none means
`internal-untracked`; a mixture remains `partial-tracking`. A candidate-created result freezes
validated generated files under the shared Git common directory and never writes them back to
the source checkout.

Explicit `wiki_root` inputs keep existing semantics. Roots outside both the canonical and exact
source checkout remain external, including roots tracked by another repository.

### Binding mismatch remains literal

The ticket-batch hook invoked with a linked worktree as `project_root` must continue to report
`broken-binding` when the tracked binding names the canonical persistent checkout. Same Git
history does not make two checkout paths binding-equivalent.

## Semantic invariants

- Binding identity, source identity, logical wiki identity, tracking owner, candidate owner, and
  publication authority are distinct.
- Alternate-source discovery never searches siblings, home directories, mounts, or the network.
- Symlinks, path escapes, submodules, another Git common directory, partial tracking, stale
  heads, and compare-and-swap drift fail closed.
- Generated scope remains regular non-executable UTF-8 Markdown under `wiki/**/*.md` only.
- The origin ticket's CandidateRef, verification, integration, and merge authority never transfer
  to wiki output.
- A sync failure remains visible and cannot rewrite ticket integration.

## Failure modes

| Condition | Outcome |
|---|---|
| Exact source contains no compatible wiki | `skipped/absent` |
| Multiple source candidates | `failed/ambiguous-root` |
| Binding names source worktree or another path | `failed/broken-binding` |
| Different Git common directory | `failed/broken-binding` |
| Unsafe relative/logical path | `failed/broken-binding` |
| Partial generated tracking | `failed/partial-tracking` |
| Source head or corpus drifts | `failed/stale-tree` |
| Wiki lint has errors | `failed/lint` |
| Tracked compile changes pages | `candidate-created/manual-authorization` |
| Repeated exact compile has no diff | `unchanged/no-diff` |

## Implementation slice

`WXS-01` owns the complete tracer bullet: physical source discovery, canonical logical
identity, source-index tracking classification, frozen candidate behavior, ticket-autopilot
post-integration composition, regression tests, and one production Agent Skills wiki sync.

## Verification strategy

- **Unit:** safe relative identity derivation, binding equality, source/canonical Git identity,
  explicit-root preservation, and stable `WikiSyncRef` across two temporary source paths.
- **Integration:** a stale canonical checkout without a materialized wiki plus an exact linked
  checkout containing an internally tracked wiki whose empty scaffold directories are absent
  from Git; candidate creation and zero-error layout lint with both checkouts clean.
- **Negatives:** source-bound binding, other repository, symlink/escape, submodule, partial
  tracking, stale head, concurrent source/wiki change, external explicit root, and ticket-batch
  binding mismatch.
- **Regression:** full LLM Wiki tests, Ticket Autopilot wiki-sync tests, forward matrix, ticket
  contract/inventory, Artifact Graph, extensions, and context-budget checks.
- **Production:** compile the tracked Agent Skills `knowledge/` from the exact integrated head,
  record zero lint errors, open the separate wiki PR, and stop at its exact-head manual gate.

## Acceptance outcomes

- The production reproduction changes from `skipped/absent` to a deterministic tracked
  candidate or `unchanged`, never direct-write external behavior.
- Agent Skills `knowledge/` reflects current tracked specs, tickets, research, and lifecycle
  moves with zero wiki lint errors in the validation receipt.
- Canonical and exact source checkout status remain byte-identical.
- Repeating the same origin/pre-sync tree is idempotent.
- The generated wiki PR is not merged without separate exact-head authorization.
