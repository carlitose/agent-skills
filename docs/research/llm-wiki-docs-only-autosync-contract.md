# Current Contract for LLM Wiki Docs-Only Auto-Sync

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-contract`
- Role: `research`
- Parent: [LLM Wiki Docs-Only Auto-Sync](../specs/llm-wiki-docs-only-autosync-wayfinder.md)

Produced by `WS-01`. The owner edge is on the map rather than on the active ticket because
the runner binds that ticket source by digest; editing it during the run would create source
drift.

## Research Question

At repository commit `7c4f3c17f472702fb80bef9afa5ce284ae086f17`, what existing
contracts govern LLM wiki discovery, project-history compilation, docs-only validation,
ticket creation, and durable ticket integration, and what must be decided before an absent,
untracked, or tracked wiki can be synchronized automatically?

The question is repository-local. It supports the docs-only auto-sync decision and the
`WS-02` prototype; this report is the durable output required by `WS-01`.

## Answer

There is no auto-sync boundary today. The repository has three reusable parts, but no owner
composes them: `llm-wiki` resolves a caller-supplied wiki root and separately ingests project
documents, rebuilds the timeline, and lints the graph; `docs-only-adopt` validates one active
ticket candidate under a fixed `docs/**/*.md` policy; and the two requested callers stop at
ticket emission or durable integration without invoking wiki code.

The three normal user states therefore need one new classification contract:

| Requested state | Current observable evidence | Missing contract |
|---|---|---|
| Wiki absent | No compatible root has been resolved. This repository contains no `llm-wiki-project.json`, `purpose.md` + `schema.md` + `wiki/index.md` instance at the pinned commit. | A bounded project→wiki locator and a successful no-op result. |
| Wiki present, untracked | A supplied root can be validated and bound, but current helpers report tracking for project artifacts, not generated wiki output. | The Git owner of the wiki root, the generated path set, and direct-write validation/retry semantics. |
| Wiki present, tracked | Same binding evidence; per-path Git tracking can be measured only after selecting the wiki's containing repository. | A separate docs-only candidate identity, scope profile, delivery path, and authorization boundary. |

Partially tracked output, multiple matching roots, broken bindings, and concurrent changes
are not normal alternatives. They must fail or gate explicitly. Treating them as either
tracked or untracked would silently select a mutation and delivery policy.

## Evidence

### Discovery and project binding

- `llm-wiki/scripts/project_binding.py:46-54` derives the binding path from an already-known
  `wiki_root`; `read_binding` also accepts a wiki root rather than a project root
  (`83-113`). There is no reverse registry or project→wiki lookup in this module.
- The binding is schema 1 and records `project_root`, document globs, Git mode, and session
  providers (`57-80`). `resolve_project_root` deliberately fails on a moved project and never
  falls back to the current directory (`116-131`).
- `is_git_repository` and `is_tracked` correctly separate repository membership from
  per-artifact tracking (`145-168`). `describe` applies those predicates to source artifacts
  selected by `docs_globs`, not to generated files under the wiki root (`184-220`).
- `llm-wiki/tests/test_project_binding.py:83-139` proves that project repository state and
  project-document tracking are independent. `141-163` proves worktree-aware project
  resolution, and `165-194` proves broken and missing bindings fail loudly.
- A repository file inventory at the pinned commit found no compatible wiki instance, so the
  updated `research/SKILL.md:28-37` correctly did not query or scaffold one for this ticket.

**Inference for `WS-02`:** classification must first resolve exactly one compatible root,
then find that root's Git context and classify the complete generated change set. Reusing
`project_binding.is_tracked(project_root, source_path)` without that extra step can answer
the tracking status of the wrong repository.

### Project-history compilation and validation

- `ingest_docs.plan` resolves the entire source corpus before classifying `new`, `changed`,
  `moved`, `missing`, and `unchanged` transitions
  (`llm-wiki/scripts/ingest_docs.py:405-460`).
- `ingest_docs.ingest` writes new/changed/moved pages, tombstones missing pages, and rewrites
  the index only when output changed. Its stated idempotence bar is that unchanged input
  writes nothing (`463-507`).
- `build_timeline.build` independently rewrites period pages, ticket lifecycle records, its
  index, and the top-level catalog entry (`llm-wiki/scripts/build_timeline.py:385-466`).
- `lint_wiki.run_passes` composes structural and binding-dependent drift passes
  (`llm-wiki/scripts/lint_wiki.py:481-496`). Its CLI returns nonzero only for errors;
  warnings and informational findings remain visible but non-blocking (`502-533`).
- Neither `ingest_docs.py` nor `build_timeline.py` appends the operation log, and neither
  calls the other. The public skill documents them as separate project-history scripts.

**Observed boundary:** the available primitives are individually useful but do not provide
one atomic/idempotent result covering discovery, ingest, timeline, lint, logging, tracking,
or retry. Callers would have to know their order and failure policy.

### Docs-only v1

- Contract version 1 hard-codes `roots: ["docs"]`, Markdown only, and exclusion of
  `docs/tickets` (`ticket-autopilot/scripts/autopilot/docs_only_contract.py:21-27`). A request
  must equal that canonical policy literally (`76-151`).
- Each request is bound to the normalized run Ticket Envelope, ticket digest, source path,
  and active runner CandidateRef (`83-136`). It cannot represent an ownerless post-integration
  side effect.
- The path validator accepts only regular, non-executable Markdown rooted under `docs`,
  rejects agent/config/generated path markers, and rejects runner-owned ticket sources
  (`ticket-autopilot/scripts/autopilot/docs_only.py:28-57,129-153`).
- Validation freezes the whole staged diff, requires the declared path set to match it,
  runs patch, file-kind, UTF-8, Artifact Graph, and Markdown-link checks, and emits
  content-addressed evidence with claim ceiling `implementation-complete` (`241-330`).
- Tests prove canonical Ticket Envelope/base-tree binding, mixed code rejection,
  agent/config/generated/ticket-source rejection, regular-file constraints, evidence
  hashing, and the claim ceiling (`ticket-autopilot/tests/test_docs_only.py:107-217`).
- The kernel accepts docs-only adoption only for an active ticket at its `implement` stage
  with zero prior leaf interactions; success moves that ticket directly to `verified`
  (`ticket-autopilot/scripts/autopilot/kernel.py:775-847`). Delivery revalidates the same
  receipt before commit (`ticket-autopilot/scripts/autopilot/finalizer.py:972-988`).

**Required invariant:** wiki support must extend the versioned contract without making
arbitrary roots, configuration, raw/binary data, ticket sources, or mixed candidates eligible.
It must preserve a frozen complete diff, runner-owned identity, content-addressed checks,
revalidation, and the `implementation-complete` ceiling.

### Requested trigger points

- `to-tickets` finishes by emitting every canonical Ticket Envelope, parsing it back, and
  reporting the folder/frontier (`to-tickets/SKILL.md:20-34,79-91`). It has no wiki discovery
  or sync operation. A post-batch hook belongs after all tickets and reciprocal graph edges
  validate, not inside per-ticket serialization.
- `ticket-autopilot` activates and executes one ready ticket, delivers a frozen verified
  candidate, records `pr-open` separately, and reaches completion only after integration
  (`ticket-autopilot/SKILL.md:70-90`).
- The durable integration transaction requires an open PR, exact PR head, and current-head
  human authorization, then sets `state = "integrated"`, completes ticket lifecycle, and
  records `ticket-integrated` (`ticket-autopilot/scripts/autopilot/kernel.py:1817-1830`). It
  performs no wiki action.
- Status projects integrated tickets as completed while ticket completion effects remain a
  separate runner-owned concern (`kernel.py:2196-2218,2245-2274`). This is the narrow seam for
  a post-integration sync effect; firing earlier would observe a provisional outcome.

## Contract Gaps and Experiments

| Gap | Why inspection cannot decide it | `WS-02` experiment |
|---|---|---|
| Project→wiki discovery | The only binding points from wiki to project. | Compare explicit root, bounded in-project scan, and reverse registration across absent, external, multiple, and broken fixtures. |
| Wiki tracking | Existing tracking applies to project source artifacts. | Create ignored, wholly tracked, partially tracked, untracked, and separate-repository wiki roots; classify the exact generated diff. |
| Eligible wiki scope | Wiki content mixes generated pages with purpose/schema, audit, raw sources, assets, and binding configuration. | Exercise a versioned profile, separate request type, and caller allowlist; prove forbidden/mixed paths fail. |
| Post-integration owner | Docs-only v1 requires an active Ticket Envelope and CandidateRef. | Compare a fresh synthetic sync ticket, a runner-owned completion-effect identity, and reuse of the origin ticket; demonstrate why stale identity is rejected. |
| Failure and concurrency | Current scripts write separate sets of files without one lock or transaction. | Inject failure between ingest/timeline/lint and concurrent changes; measure rollback, retry, and compare-and-swap needs. |
| Tracked delivery | Integration authorization is exact-head and ticket-bound. | Produce a separate tracked docs-only candidate and prove no application CandidateRef or base worktree changes. |

## Unknowns

- Where a project records an external wiki root, if external roots are supported.
- Whether "tracked wiki" means every generated output is tracked, any output is tracked, or
  repository policy declares future generated files tracked. Partial tracking must remain
  explicit until decided.
- Which wiki surfaces qualify for docs-only. The user decided the wiki sync is docs-only,
  but not whether human/agent configuration and raw inputs share the fast path.
- The owning identity and branch/PR policy for a tracked sync created after its origin ticket
  is already integrated.
- Whether sync failure changes only a `wiki-sync` projection or the enclosing folder run's
  final state.

## Next Step

Run `WS-02` against isolated fixtures using this report as the baseline. The prototype must
return one normalized outcome for every state, preserve docs-only invariants, and produce a
counterexample for any identity or scope design that cannot remain fail-closed. `WS-03` then
uses those measurements for the human decision; production code should not begin before it.
