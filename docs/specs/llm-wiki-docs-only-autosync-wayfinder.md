# LLM Wiki Docs-Only Auto-Sync

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [WS-01 map current sync boundary](../tickets/llm-wiki-docs-only-autosync/done/01-map-current-sync-boundary.md)
- [WS-02 prototype docs-only sync contract](../tickets/llm-wiki-docs-only-autosync/done/02-prototype-docs-only-sync-contract.md)
- [WS-03 decide sync policy](../tickets/llm-wiki-docs-only-autosync/done/03-decide-sync-policy.md)
- [WS-04 implement sync-project](../tickets/llm-wiki-docs-only-autosync/done/04-implement-sync-project.md)
- [WS-05 sync after ticket creation](../tickets/llm-wiki-docs-only-autosync/done/05-sync-after-ticket-creation.md)
- [WS-06 sync after ticket integration](../tickets/llm-wiki-docs-only-autosync/done/06-sync-after-ticket-integration.md)
- [WS-07 forward-test sync matrix](../tickets/llm-wiki-docs-only-autosync/done/07-forward-test-sync-matrix.md)
- [WS-08 preserve hand-written root catalog sections](../tickets/llm-wiki-docs-only-autosync/done/08-preserve-hand-written-root-catalog-sections.md)
- [Current auto-sync contract research](../research/llm-wiki-docs-only-autosync-contract.md)
- [Accepted auto-sync decision](llm-wiki-docs-only-autosync-decision.md)
- [Exact-source checkout sync diagnostic](llm-wiki-exact-source-checkout-sync.md)
- [Complete auto-sync forward test](../research/llm-wiki-docs-only-autosync-forward-test.md)

## Type

Wayfinding spec

## Prototype evidence

- [WS-02 docs-only sync prototype](../prototypes/llm-wiki-docs-only-autosync/NOTES.md)

## Status

Implemented and forward-tested through WS-07; reopened with the ready WS-08 catalog-ownership bug

## Destination

When a project already has an LLM wiki, ticket creation and ticket completion keep its
project-history projection current without turning wiki generation into application work.
The reachable behavior is:

- no existing wiki is a successful no-op and never scaffolds one;
- an existing untracked wiki is synchronized directly and receives truthful static
  validation;
- an existing internal tracked wiki is synchronized through a separate, evidence-backed
  `wiki-sync-v1` candidate, never mixed into an application or ticket-source candidate;
- an existing external wiki is validated and updated directly without Git operations;
- `to-tickets` requests one sync after a complete ticket batch, not once per file;
- `ticket-autopilot` requests one sync only after the originating ticket is durably
  `integrated`;
- wiki sync failure remains visible and retryable without rewriting the already-recorded
  outcome of ticket creation or integration;
- research continues to query an existing wiki first, while treating its pages as compiled
  context and source pointers rather than primary evidence;
- `sync-project` updates compiler-owned project/session/timeline catalog entries without
  deleting or rewriting hand-written concept, entity, query, open-work, or other non-owned
  sections in `wiki/index.md`.

Assumptions for this map: "tracked" refers to generated wiki content tracked by Git in its
own repository context; the wiki is compatible with `llm-wiki` and bound to the same project;
automatic scaffolding is not part of sync.

## Decisions So Far

- **There are three normal discovery outcomes.** The user fixed them as absent, present and
  tracked, or present and untracked. Broken bindings and multiple matching wikis are error
  or ambiguity states, not a fourth normal choice.
- **Wiki synchronization is docs-only work.** A tracked wiki update must use the docs-only
  quality and claim boundary rather than the application implementation loop.
- **A missing wiki is not created.** The research rule and the proposed sync both operate
  only on an existing compatible wiki.
- **The wiki is a compiled projection, not primary evidence.** `research/SKILL.md` now
  queries it before broader collection but follows provenance back to owning artifacts or
  raw sources.
- **Workflow ownership stays local.** `llm-wiki` owns discovery/sync policy and wiki
  validation; `to-tickets` owns the batch-created trigger; `ticket-autopilot` owns the
  post-integration trigger and any Git/provider delivery.
- **Current docs-only v1 cannot be reused unchanged.** Its canonical scope is
  `docs/**/*.md`, it excludes `docs/tickets`, and its path validator rejects every root
  other than `docs` (`ticket-autopilot/scripts/autopilot/docs_only*.py`).
- **Current project-history compilation is already idempotent but fragmented.**
  `llm-wiki/scripts/ingest_docs.py` classifies new, changed, moved, missing, and unchanged
  artifacts; `build_timeline.py` owns lifecycle pages; `lint_wiki.py` owns graph health.
  There is no single public sync operation or caller hook.
- **The binding is one-way.** `llm-wiki-project.json` identifies the project from the wiki
  root. A caller starting at the project root has no canonical reverse locator today.
- **The policy is accepted.**
  [The WS-03 decision](llm-wiki-docs-only-autosync-decision.md) fixes discovery, scope,
  ownership, triggers, result states, retry, concurrency, direct-write behavior, and
  manual versus AFK-complete delivery.
- **The root catalog has mixed ownership.** Generated project/session/timeline navigation is
  compiler-owned; hand-written sections are durable human-authored wiki content. A compiler
  may replace only the content it can identify as its own. Ambiguous ownership fails closed
  rather than rebuilding the complete file.

## Reproduced Root-Catalog Ownership Bug

`llm-wiki/scripts/ingest_docs.py::_write_index()` currently creates `lines` from `# Index`,
the generated project corpus, retained tombstones, and the optional timeline, then calls
`render_session_catalog()` and writes that value with `index.write_text()`. It never reads the
existing root catalog. `sync_project.py` invokes this ingest in its disposable staging copy, so
any docs transition causes the generated candidate to omit all hand-written catalog sections.
Lint can still pass because it verifies that existing pages are catalogued; it cannot prove that
human-authored navigation or open-work entries which were deleted should still exist.

The user reported reconstructing the lost concepts, entities, and open-work catalog manually and
provided the audit reference `audit/20260901-160000-index-sobrescrito.md`. That file was not
present in the available repository, installed package, tracked `knowledge/`, or discovered audit
roots during this planning pass, so its contents are not claimed as inspected. The code-level
destructive writer above independently reproduces the reported cause.

Expected behavior is ownership-preserving synchronization: update the generated catalog projection,
preserve every non-owned block byte-for-byte and in order, reject missing/duplicated/ambiguous
ownership boundaries, then run full wiki lint. “Rebuild the manual index after every sync” is a
recovery note, not an acceptable steady-state contract.

## Not Yet Specified

- **External-root configuration adapter.** The contract requires explicit external roots but
  leaves each host's durable configuration transport to implementation.
- **Cross-process coalescing adapter.** The contract fixes per-wiki serialization and
  coalescing semantics but does not require one host-specific queue format.
- **Live provider evidence.** AFK-complete delivery is specified but remains unobserved until
  an authorized provider test produces live receipts.
- **Catalog ownership encoding.** WS-08 must choose the smallest deterministic representation
  that can identify generated blocks in existing and newly scaffolded indexes without claiming
  ownership of arbitrary headings. No marker syntax or migration mechanism is selected here.

## Out of Scope

- Automatically scaffolding a wiki when none exists.
- Treating wiki answers as primary evidence or weakening research provenance requirements.
- Ingesting arbitrary external reading material, applying `audit/` corrections, or changing
  `purpose.md` and `schema.md` as a side effect of ticket lifecycle sync.
- Using application-owned `.llm-wiki/` state, an HTTP API, or an Obsidian dependency.
- Weakening CandidateRef, exact-head provider readback, or the explicit manual/autonomous
  merge-policy boundary.
- Combining code, ticket-source, configuration, binary, and generated-wiki mutations into
  one docs-only candidate.

## Frontier / Blocking Edges

| Edge | Why it blocks | Unblock condition | Owner |
|---|---|---|---|
| No project-to-wiki locator | Callers cannot distinguish absent from undiscovered | Discovery contract covers in-project, external, multiple, and broken cases | `WS-01` |
| Docs-only v1 recognizes only `docs/**/*.md` | A tracked wiki candidate must currently take the standard path | Prototype proves a fail-closed profile without widening generic docs | `WS-02` |
| Policy choices remain implicit | Resolved by the accepted decision spec | Complete WS-03 quality and delivery | `WS-03` |
| Sync is three commands and caller knowledge | Every caller would duplicate ordering and error policy | One idempotent `sync-project` operation returns normalized outcomes | `WS-04` |
| Ticket creation has no sync trigger | Newly emitted tickets remain absent from an existing wiki | One post-batch hook consumes `sync-project` result | `WS-05` |
| Integration has no sync trigger | Lifecycle pages can remain stale after the durable outcome | One post-`integrated` hook creates or records the docs-only sync | `WS-06` |
| No end-to-end matrix | Local unit behavior cannot prove trigger timing and Git isolation | Forward test covers every state and both caller events | `WS-07` |
| Full-file root-index rewrite | A docs transition can silently erase hand-written catalog sections while lint remains green | Ownership-preserving generated-section update, byte-preservation regressions, ambiguity rejection, idempotent `sync-project`, and full lint | `WS-08` |

The WS-07 unblock condition is satisfied by the
[deterministic forward-test report](../research/llm-wiki-docs-only-autosync-forward-test.md).
Live provider evidence remains an explicit limitation. The production Agent Skills wiki also
exposed one exact-source discovery defect: post-integration compilation receives a detached
integrated checkout containing `knowledge/`, but discovery still searches only the stale
canonical checkout and reports `absent`. The linked diagnostic and WXS-01 own that repair;
checkout-specific binding remains unchanged.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
|---|---|---|---|---|---|
| `WS-01` | Research | AFK | — | Map the existing sync and ownership boundary | `docs/research/llm-wiki-docs-only-autosync-contract.md` with discovery, tracking, identity, and trigger evidence |
| `WS-02` | Prototype | AFK | `WS-01` | Prototype a docs-only wiki sync contract | Disposable fixture proving absent, untracked, tracked, mixed, and ambiguous outcomes |
| `WS-03` | Decision | **HITL** | `WS-02` | Decide scope, identity, delivery, and failure policy | Confirmed decision spec produced through `to-spec` after `grilling` |
| `WS-04` | Task | AFK | `WS-03` | Implement one idempotent `llm-wiki sync-project` boundary | Versioned result contract, docs-only wiki profile, validation, and unit tests |
| `WS-05` | Task | AFK | `WS-04` | Sync once after ticket creation | `to-tickets` composition hook and batch-level tests |
| `WS-06` | Task | AFK | `WS-04` | Sync once after ticket integration | post-`integrated` autopilot hook, separate candidate semantics, retry state, and tests |
| `WS-07` | Task | AFK | `WS-05`, `WS-06` | Forward-test the complete sync matrix | deterministic report covering both triggers and all normal/error states |
| `WS-08` | Bug fix | AFK | — | Preserve hand-written root catalog sections | ownership-preserving compiler update, destructive-regression fixtures, full lint, and idempotent sync proof |

WS-01 through WS-07 remain completed; their history is not reopened. `WS-08` is the only ready
frontier. It is independent of exact-source discovery, tracked-wiki publication, retrieval
architecture, and the active delivery-revalidation investigation.

## Next Review

The implementation answers the three original falsifiable questions locally:

1. Can a caller starting from the project root resolve exactly one compatible bound wiki
   without application-private state?
2. Can one docs-only validator accept generated wiki Markdown while rejecting configuration,
   raw/binary, agent-instruction, ticket-source, and mixed candidates?
3. Can a post-integration tracked sync receive a fresh owning identity without reusing or
   mutating the integrated ticket's CandidateRef?

WXS-01 has repaired exact-source discovery and production synchronization. The next review is
WS-08: run a fixture whose root index contains generated sections interleaved with hand-written
concept/entity/open-work sections; change project docs; execute `sync-project`; prove the manual
blocks are byte-identical, generated entries are current, full lint has zero errors, and an
unchanged replay produces no diff. Include missing, duplicate, and malformed ownership-boundary
negatives.

Optional live-provider evidence and host-specific external-root or cross-process coalescing
adapters remain separate. WS-08 must not reconstruct or publish the tracked Agent Skills wiki,
resolve an unavailable audit note, widen sync scope, reuse origin evidence, or change the accepted
absent/untracked/tracked ownership rules.
