# LLM Wiki Docs-Only Auto-Sync Decision

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-decision`
- Role: `spec`
- Parent: [LLM Wiki Docs-Only Auto-Sync](llm-wiki-docs-only-autosync-wayfinder.md)

## Type

Decision spec

## Status

Accepted

## Source and authority

Produced by
[WS-03](../tickets/llm-wiki-docs-only-autosync/done/03-decide-sync-policy.md) after the
human interview required by that ticket. The user confirmed the complete decision set in
ticket-autopilot run `f74e8975ae4d49a5`.

The evidence is the
[current-contract report](../research/llm-wiki-docs-only-autosync-contract.md) and the
[docs-only sync prototype](../prototypes/llm-wiki-docs-only-autosync/NOTES.md).

## Context

Project-history compilation already ingests project documents, builds the temporal axis, and
lints a wiki. It has no single synchronization operation, no project-to-wiki locator, and no
delivery owner. Generic docs-only v1 cannot fill that gap: it accepts only `docs/**/*.md` and
binds its evidence to one active origin ticket.

This decision defines one `wiki-sync-v1` boundary. The wiki remains compiled documentation:
research may query it for context, but follows its provenance to project artifacts or raw
sources before treating a claim as primary evidence.

## Goals

- Keep an existing compatible project wiki current after ticket creation and integration.
- Treat generated wiki Markdown as docs-only work without widening generic docs-only v1.
- Give every tracked wiki mutation a fresh identity, complete validation, and an explicit
  delivery policy.
- Make absent, disabled, unchanged, direct, tracked, and failed outcomes deterministic.
- Preserve the origin ticket's CandidateRef, verification, integration, and run result.

## Non-goals

- Scaffold a missing wiki.
- Change `purpose.md`, `schema.md`, raw sources, audit records, assets, or binding files.
- Mix wiki output with application code, ticket-source changes, or configuration changes.
- Make an external wiki's Git repository part of the caller's delivery transaction.
- Treat wiki pages as primary research evidence.

## Vocabulary

| Term | Meaning |
|---|---|
| Compatible wiki | A root with readable `purpose.md`, `schema.md`, `wiki/index.md`, and a valid binding to the requested project. |
| Internal wiki | A compatible wiki inside the source project's Git worktree. |
| External wiki | A compatible wiki outside that Git worktree, whether or not another repository contains it. |
| Generated scope | Regular, non-executable Markdown under `wiki/**/*.md`. |
| AFK complete | A run created with an explicit autonomous merge grant, not merely a ticket whose execution mode is `AFK`. |
| Origin event | The completed ticket batch or durably integrated ticket that requested synchronization. |

## Decision

### D1 — Discovery is bounded and fail-closed

`sync-project` receives a canonical project root and zero or more explicitly configured wiki
roots. It also checks only bounded in-project candidates: the project root and direct child
directories that contain `llm-wiki-project.json`. It never searches a home directory, sibling
repositories, mounted volumes, or the network.

An external wiki is therefore eligible only through an explicit wiki-root input. Every found
root must resolve its binding back to the same canonical project root.

| Discovery state | Outcome |
|---|---|
| No compatible root | `skipped` with reason `absent`; create nothing. |
| One compatible root | Continue to scope and ownership classification. |
| More than one compatible root | `failed` with reason `ambiguous-root`; write nothing. |
| Missing, unreadable, or contradictory explicit binding | `failed` with reason `broken-binding`; write nothing. |
| Binding has `auto_sync: disabled` | `skipped` with reason `disabled`; do not compile or lint. |

`auto_sync` is an optional binding value with allowed values `enabled` and `disabled`.
Absence means `enabled`. The disabled value is a durable, reversible opt-out: future automatic
triggers report the skip instead of reopening the same error. Manual LLM Wiki operations and
queries remain available.

### D2 — External ownership precedes Git classification

An external wiki is always a direct-write target for this workflow. After successful staging
and validation, synchronization replaces only generated-scope files. It performs no Git
status, add, commit, push, pull-request, or merge operation in the external wiki, even when a
Git repository contains that root. This can deliberately leave external repository changes
uncommitted.

For an internal wiki, classify the complete pre-sync generated corpus in the source project's
Git repository:

- all existing generated files tracked: `tracked`; new generated paths inherit tracked
  delivery;
- no existing generated files tracked: `untracked`;
- any mixture: `failed` with reason `partial-tracking`.

Classification never asks whether project source documents are tracked. A compatible wiki has
at least `wiki/index.md`, so the empty-corpus case does not exist.

### D3 — The eligible candidate is exact

`wiki-sync-v1` permits only regular, non-executable UTF-8 Markdown at `wiki/**/*.md`, relative
to the compatible root. It includes `wiki/index.md`, `wiki/log.md`, source pages, concepts,
entities, queries, comparisons, synthesis pages, timelines, and future page types under
`wiki/`.

It excludes:

- `purpose.md`, `schema.md`, and `llm-wiki-project.json`;
- `audit/**`, `raw/**`, sources, references, assets, and binaries;
- symlinks, executable files, non-Markdown files, code, ticket sources, and paths outside
  `wiki/`.

The declared path set must equal the complete staged diff. A candidate containing both allowed
and forbidden paths fails as `forbidden-scope`; the validator never filters forbidden changes
and delivers the remainder.

### D4 — A separate request and fresh owner replace docs-only reuse

The public request is `wiki-sync-v1`, not a new profile inside generic docs-only. It reuses
the common regular-file, UTF-8, patch, Markdown-link, and graph-validation primitives but owns
its root, path policy, wiki lint, and result schema.

Every mutation receives a fresh `WikiSyncRef` derived from:

- contract version;
- canonical wiki identity;
- origin kind and stable origin identifier;
- pre-sync generated-tree identity;
- normalized trigger set.

Its CandidateRef belongs to the wiki-sync operation. The origin ticket or ticket batch appears
only as provenance and is never reused as the sync CandidateRef. Replaying the same origin and
same pre-sync tree resolves to the same operation; a changed tree creates a new CandidateRef
and invalidates prior sync evidence.

### D5 — Compile and validate before publishing

The operation stages project-doc ingest, timeline rebuild, index and log updates, and the full
wiki lint away from the protected wiki tree. It then freezes the complete generated diff and
checks:

1. compare-and-swap against the pre-sync tree;
2. the exact D3 path policy;
3. regular-file, executable-bit, UTF-8, patch, link, and graph invariants;
4. a full `llm-wiki lint` with zero errors;
5. a content-addressed receipt with claim ceiling `implementation-complete`.

Failure leaves the protected tree unchanged. An unchanged compile writes zero bytes and returns
`unchanged`.

Validated internal-untracked and external output is applied directly. Validated
internal-tracked output remains frozen as a separate candidate; `llm-wiki` never commits or
delivers it.

### D6 — There are exactly two automatic trigger seams

Ticket creation requests one synchronization after the complete ticket batch has been emitted,
parsed back, and linked reciprocally. It never synchronizes once per file or once per ticket in
that batch.

Ticket autopilot requests one synchronization only after the origin ticket is durably
`integrated`. Implementation completion, verification, PR creation, queued, pending, failed,
unknown, and other pre-integration states do not trigger it.

Both trigger owners persist the `WikiSyncRef` and normalized result. Resume is idempotent and
cannot create duplicate sync work.

### D7 — Delivery depends on location and explicit run policy

| Wiki state | Delivery |
|---|---|
| External | Apply the validated generated files directly; ignore external Git. |
| Internal and untracked | Apply the validated generated files directly. |
| Internal and tracked, manual run | Create a separate wiki-sync candidate and require exact-current-head human merge authorization. |
| Internal and tracked, AFK-complete run | Create, verify, deliver, read back, and merge the separate candidate automatically. |

Selecting AFK complete is an explicit, persisted autonomous grant scoped to `wiki-sync-v1`.
Ticket execution mode `AFK`, provider access, or silence does not create that grant. Automatic
merge still requires that the provider's observed PR head equals the fully verified candidate
head immediately before merge. It never authorizes a mixed candidate or an application ticket.

The current run `f74e8975ae4d49a5` has manual merge policy. This decision grants it no merge
authority and changes no already-open PR authorization.

### D8 — The sync operation owns retry and serialization

The origin event never reruns to repair wiki sync. The `WikiSyncRef` owns retry state.
Transient lock, compare-and-swap, and provider/network failures receive at most three automatic
attempts in AFK complete. Configuration, ambiguous discovery, partial tracking, forbidden
scope, and lint failures do not retry automatically.

Only one operation may mutate a canonical wiki root at a time. Callers coalesce pending origin
events by wiki identity. An event arriving during an active operation joins that operation when
it has not frozen input; otherwise it joins the next attempt. Compilation always reads the
latest complete project corpus, so coalescing cannot omit an earlier ticket.

### D9 — Every trigger returns one normalized result

The result envelope has one top-level status and one reason code:

| Status | Meaning | Typical reasons |
|---|---|---|
| `skipped` | Policy says no work is eligible. | `absent`, `disabled`, `coalesced` |
| `unchanged` | The compiled generated tree equals the current tree. | `no-diff` |
| `updated-directly` | Validated files were applied without Git delivery. | `external`, `internal-untracked` |
| `candidate-created` | A frozen internal tracked candidate awaits or enters delivery. | `manual-authorization`, `delivery-started` |
| `merged-automatically` | AFK complete delivered and merged the exact verified head. | `autonomous-grant` |
| `failed` | No wiki output was published. | `ambiguous-root`, `broken-binding`, `partial-tracking`, `forbidden-scope`, `lint`, `stale-tree`, `transient-exhausted` |

Every result records the `WikiSyncRef`, wiki identity when known, origin references, attempt
count, changed paths, validation receipt when one exists, and retry disposition. A skipped or
unchanged result is still durable.

Sync failure does not roll back created tickets or an integrated ticket. The enclosing report
continues and includes the failed sync result prominently; it never reports the sync as green
or silently drops it.

## Rejected alternatives

- **Widen generic docs-only v1.** Rejected because it would change every existing docs-only
  request and still would not provide a post-integration owner.
- **Caller-provided path allowlists.** Rejected because callers could admit configuration,
  raw inputs, or mixed candidates.
- **Reuse the origin CandidateRef.** Rejected because the origin is completed or integrated
  and its evidence and authorization are stale for a new tree.
- **Mutate the origin candidate.** Rejected because it invalidates application verification
  and exact-head authorization.
- **Silently filter a mixed diff.** Rejected because it publishes an incomplete projection.
- **Create a missing wiki.** Rejected because location, purpose, schema, and ownership require
  explicit human choices.
- **Operate Git in an external wiki.** Rejected by the user; the external root is a validated
  direct-write target only.

## Compatibility and migration

Generic docs-only contract v1, its `docs/**/*.md` root, existing receipts, CandidateRefs, and
tests remain unchanged. `wiki-sync-v1` is a separate request and result schema. No v1 receipt
is upgraded, rebound, or accepted as wiki-sync evidence.

Existing valid bindings remain readable because missing `auto_sync` means `enabled`. Operators
who need a permanent opt-out add `auto_sync: disabled`; enabling it again is reversible.

The changed behavior is additive at the two explicit trigger seams. Rollout must first ship
`sync-project`, then the ticket-creation caller, then the post-integration caller. Until a
caller adopts the seam, its current behavior remains unchanged.

## Implementation slices

1. `WS-04` owns discovery, classification, staging, validation, request/result schemas, and
   the idempotent `sync-project` command.
2. `WS-05` owns the single post-batch trigger and result reporting in ticket creation.
3. `WS-06` owns the post-integration effect, fresh tracked candidate, retry projection, and
   manual/autonomous delivery adapters.
4. `WS-07` owns the forward matrix across both triggers and every outcome.

## Verification strategy

- Unit tests cover discovery order, binding opt-out, scope validation, status/reason
  normalization, retry classification, and deterministic `WikiSyncRef` identity.
- Integration fixtures cover absent, internal-untracked, internal-tracked, external, partial,
  multiple, broken, mixed, lint-failed, stale, concurrent, unchanged, and replayed states.
- Existing docs-only v1 tests run unchanged as regression evidence.
- Git/provider tests prove the origin CandidateRef and protected worktree never change, manual
  authorization remains exact-head, and AFK complete merges only under its scoped grant.
- Live provider and production-wiki claims require separate evidence; local simulation cannot
  establish them.

## Unresolved implementation details

- The durable storage adapter used by callers to remember explicitly configured external roots.
  The public contract requires explicit input and forbids unbounded search; it does not require
  one host-specific configuration store.
- The concrete transport used to coalesce triggers across independent processes. It must obey
  D8 and remain outside the generated candidate.
