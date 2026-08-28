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
- [WS-05 sync after ticket creation](../tickets/llm-wiki-docs-only-autosync/05-sync-after-ticket-creation.md)
- [WS-06 sync after ticket integration](../tickets/llm-wiki-docs-only-autosync/06-sync-after-ticket-integration.md)
- [WS-07 forward-test sync matrix](../tickets/llm-wiki-docs-only-autosync/07-forward-test-sync-matrix.md)
- [Current auto-sync contract research](../research/llm-wiki-docs-only-autosync-contract.md)
- [Accepted auto-sync decision](llm-wiki-docs-only-autosync-decision.md)

## Type

Wayfinding spec

## Prototype evidence

- [WS-02 docs-only sync prototype](../prototypes/llm-wiki-docs-only-autosync/NOTES.md)

## Status

Policy accepted; implementation active

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
- **The policy is accepted.**
  [The WS-03 decision](llm-wiki-docs-only-autosync-decision.md) fixes discovery, scope,
  ownership, triggers, result states, retry, concurrency, direct-write behavior, and
  manual versus AFK-complete delivery.

## Not Yet Specified

- **External-root configuration adapter.** The contract requires explicit external roots but
  leaves each host's durable configuration transport to implementation.
- **Cross-process coalescing adapter.** The contract fixes per-wiki serialization and
  coalescing semantics but does not require one host-specific queue format.
- **Live provider evidence.** AFK-complete delivery is specified but remains unobserved until
  an authorized provider test produces live receipts.

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

Ready after WS-03 delivery: `WS-04`. `WS-05` and `WS-06` remain blocked by `WS-04`; `WS-07`
remains blocked by both caller integrations. The WS-03 interview is confirmed and recorded in
the accepted decision spec.

## Next Review

Review the WS-03 decision with `WS-01` and `WS-02`, then start `WS-04`. Implementation must
answer three falsifiable questions:

1. Can a caller starting from the project root resolve exactly one compatible bound wiki
   without application-private state?
2. Can one docs-only validator accept generated wiki Markdown while rejecting configuration,
   raw/binary, agent-instruction, ticket-source, and mixed candidates?
3. Can a post-integration tracked sync receive a fresh owning identity without reusing or
   mutating the integrated ticket's CandidateRef?

If any answer is no, `WS-04` must fail closed and return to the recorded decision rather than
widening scope or reusing origin evidence.
