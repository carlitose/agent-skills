# LLM Wiki Docs-Only Auto-Sync

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [WS-01 map current sync boundary](../tickets/llm-wiki-docs-only-autosync/done/01-map-current-sync-boundary.md)
- [WS-02 prototype docs-only sync contract](../tickets/llm-wiki-docs-only-autosync/done/02-prototype-docs-only-sync-contract.md)
- [WS-03 decide sync policy](../tickets/llm-wiki-docs-only-autosync/03-decide-sync-policy.md)
- [WS-04 implement sync-project](../tickets/llm-wiki-docs-only-autosync/04-implement-sync-project.md)
- [WS-05 sync after ticket creation](../tickets/llm-wiki-docs-only-autosync/05-sync-after-ticket-creation.md)
- [WS-06 sync after ticket integration](../tickets/llm-wiki-docs-only-autosync/06-sync-after-ticket-integration.md)
- [WS-07 forward-test sync matrix](../tickets/llm-wiki-docs-only-autosync/07-forward-test-sync-matrix.md)
- [Current auto-sync contract research](../research/llm-wiki-docs-only-autosync-contract.md)

## Type

Wayfinding spec

## Prototype evidence

- [WS-02 docs-only sync prototype](../prototypes/llm-wiki-docs-only-autosync/NOTES.md)

## Status

Active

## Destination

When a project already has an LLM wiki, ticket creation and ticket completion keep its
project-history projection current without turning wiki generation into application work.
The reachable behavior is:

- no existing wiki is a successful no-op and never scaffolds one;
- an existing untracked wiki is synchronized directly and receives truthful static
  validation;
- an existing tracked wiki is synchronized through the same bounded, evidence-backed
  docs-only path used for documentation candidates, never mixed into an application or
  ticket-source candidate;
- `to-tickets` requests one sync after a complete ticket batch, not once per file;
- `ticket-autopilot` requests one sync only after the originating ticket is durably
  `integrated`;
- wiki sync failure remains visible and retryable without rewriting the already-recorded
  outcome of ticket creation or integration;
- research continues to query an existing wiki first, while treating its pages as compiled
  context and source pointers rather than primary evidence.

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

## Not Yet Specified

- **Discovery.** Whether an in-project wiki is found by a bounded scan, configured explicitly,
  or registered by a reverse pointer; how external wikis and multiple matches are handled.
- **Tracked classification.** Whether one tracked generated page makes the whole wiki tracked,
  how partially tracked trees fail, and which Git repository owns an external wiki.
- **Exact docs-only scope.** Whether only `wiki/**/*.md` qualifies, or whether
  `purpose.md`, `schema.md`, `audit/`, `raw/`, assets, and the JSON binding can ever enter
  the fast path. The auto-generated and human/configuration surfaces must not be conflated.
- **Contract shape.** Whether docs-only v2 uses a `scope_profile`, a resolved root plus
  allowlist, or a separate wiki request type while preserving one validator and claim ceiling.
- **Identity after integration.** Docs-only v1 binds one active Ticket Envelope, digest, and
  CandidateRef. A post-integration wiki candidate needs an explicit owning identity rather
  than silently reusing a completed application candidate.
- **Tracked delivery.** Whether an authorized run opens a separate docs-only PR automatically
  or records `sync-pending` for a later run; any merge still requires the existing exact-head
  authorization boundary.
- **Failure and retry.** Required result states, idempotency key, retry owner, and whether a
  tracked sync gate affects only the sync or also the folder run's final status.
- **Concurrency.** Two runs may target the same external or shared wiki. The synchronization
  boundary needs serialization or compare-and-swap behavior beyond per-folder mutation locks.
- **Validation.** Which common docs-only checks remain valid, which wiki-specific checks
  replace artifact-graph and Markdown-link checks, and when full `llm-wiki lint` is required.

## Out of Scope

- Automatically scaffolding a wiki when none exists.
- Treating wiki answers as primary evidence or weakening research provenance requirements.
- Ingesting arbitrary external reading material, applying `audit/` corrections, or changing
  `purpose.md` and `schema.md` as a side effect of ticket lifecycle sync.
- Using application-owned `.llm-wiki/` state, an HTTP API, or an Obsidian dependency.
- Weakening CandidateRef, exact-head merge, provider readback, or merge-authorization gates.
- Combining code, ticket-source, configuration, binary, and generated-wiki mutations into
  one docs-only candidate.

## Frontier / Blocking Edges

| Edge | Why it blocks | Unblock condition | Owner |
|---|---|---|---|
| No project-to-wiki locator | Callers cannot distinguish absent from undiscovered | Discovery contract covers in-project, external, multiple, and broken cases | `WS-01` |
| Docs-only v1 recognizes only `docs/**/*.md` | A tracked wiki candidate must currently take the standard path | Prototype proves a fail-closed profile without widening generic docs | `WS-02` |
| Policy choices remain implicit | Scope, identity, delivery, and failure semantics change the public contract | Human confirms a recorded decision after prototype evidence | `WS-03` |
| Sync is three commands and caller knowledge | Every caller would duplicate ordering and error policy | One idempotent `sync-project` operation returns normalized outcomes | `WS-04` |
| Ticket creation has no sync trigger | Newly emitted tickets remain absent from an existing wiki | One post-batch hook consumes `sync-project` result | `WS-05` |
| Integration has no sync trigger | Lifecycle pages can remain stale after the durable outcome | One post-`integrated` hook creates or records the docs-only sync | `WS-06` |
| No end-to-end matrix | Local unit behavior cannot prove trigger timing and Git isolation | Forward test covers every state and both caller events | `WS-07` |

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

Ready now: `WS-01`. Blocked: `WS-02` through `WS-07`. `WS-03` remains HITL and must
invoke `grilling`; the user has decided that wiki synchronization is docs-only, but not the
contract details needed to implement that requirement safely.

## Next Review

Review `WS-01` and `WS-02` together. The evidence must answer three falsifiable questions:

1. Can a caller starting from the project root resolve exactly one compatible bound wiki
   without application-private state?
2. Can one docs-only validator accept generated wiki Markdown while rejecting configuration,
   raw/binary, agent-instruction, ticket-source, and mixed candidates?
3. Can a post-integration tracked sync receive a fresh owning identity without reusing or
   mutating the integrated ticket's CandidateRef?

If any answer is no, `WS-03` must choose a different boundary before implementation begins.
