# LLM Wiki Semantic Coverage Recovery

## Artifact Graph
- Artifact ID: `artifact:llm-wiki-semantic-coverage-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [Semantic coverage gap diagnostic](llm-wiki-semantic-coverage-gap-diagnostic.md)
- [SW-01 measure semantic projection options](../tickets/llm-wiki-semantic-coverage/01-measure-semantic-projection-options.md)
- [SW-02 confirm semantic projection policy](../tickets/llm-wiki-semantic-coverage/02-confirm-semantic-projection-policy.md)
- [SW-03 compile structured semantic content](../tickets/llm-wiki-semantic-coverage/03-compile-structured-semantic-content.md)
- [SW-04 enforce semantic coverage lint](../tickets/llm-wiki-semantic-coverage/04-enforce-semantic-coverage-lint.md)
- [SW-05 require visible stage-gate causes](../tickets/llm-wiki-semantic-coverage/05-require-visible-stage-gate-causes.md)
- [SW-06 repair evidence-backed gate causes](../tickets/llm-wiki-semantic-coverage/06-repair-evidence-backed-gate-causes.md)

## Type
Wayfinding spec

## Status
Active

## Destination

The project-history wiki is a source-grounded knowledge base rather than only a provenance catalog:
every discovered spec, ticket, research note, prototype, or guide has an identity-stable page with a
confirmed semantic projection; lint detects missing semantic coverage; and every Ticket Autopilot
stage gate records and exposes the concrete reason that blocks progress.

The source documents remain authoritative. Existing identity, digest, graph, lifecycle, temporal,
and idempotence guarantees remain intact. Local ignored documents are treated as a separate source
durability risk, not as content the wiki can make durable by itself.

Assumptions:

- the supplied diagnosis describes the affected wiki and ledger corpus accurately where this checkout
  cannot reproduce the external data;
- semantic interrogability requires visible source-grounded content, not merely a digest or a pointer;
- backward compatibility is not required for an obsolete semantic projection format because none
  exists, but active durable ledgers must remain readable and must never receive invented gate causes;
- no wiki run, ticket run, source publication, or historical gate mutation is authorized by this map.

## Decisions So Far

- **The defect is systemic.** A one-off page for NightDAX ticket 25 would leave the compiler and all
  other pages metadata-only.
- **The current behavior was intentional but no longer satisfies the destination.** The completed
  [project-history map](llm-wiki-project-history-wayfinder.md) delivered provenance, graph, timeline,
  and idempotence. Its `LW-05` and `LW-11` contracts explicitly excluded semantic summarization and
  semantic lint. The new work changes that boundary rather than treating the old implementation as
  an accidental partial failure.
- **No source content is known to be destroyed.** The reported 201 pages omit semantic content, while
  their source documents remain available. The eight ignored/untracked Markdown files are different:
  they carry a real durability risk because they reportedly have no copy on `origin/main`.
- **Preserve the proven compiler invariants.** Identity-keyed page names, canonical ticket parsing,
  universal-newline digests, set-based move detection, tombstones, provenance, graph links, and
  zero-write unchanged runs remain requirements.
- **Semantic compilation and semantic lint are distinct contracts.** The compiler must materialize
  meaning; lint must independently prove required coverage rather than infer it from page existence or
  digest freshness.
- **Gate cause belongs at both write and read boundaries.** A gated stage transition requires a
  specific reason, and `status` exposes structured gate records rather than only gate IDs.
- **Historical facts cannot be manufactured.** Generic historical gate reasons remain explicitly
  unknown unless durable evidence supports a precise refresh.
- **The durable diagnosis is**
  [llm-wiki-semantic-coverage-gap-diagnostic.md](llm-wiki-semantic-coverage-gap-diagnostic.md).

## Not Yet Specified

- The exact semantic projection: preserved source sections, concise generated summaries and derived
  pages, or a layered combination.
- Per-kind required coverage for tickets, specs, research, prototypes, and guides.
- Freshness and audit rules if any semantic text is agent-authored rather than deterministically
  extracted.
- The representation of legacy gates whose specific reason cannot be recovered.
- The owning repository, exact paths, and publication intent for the eight reported local documents.

## Out of Scope

- Creating only a wiki page for ticket 25.
- Copying every source body verbatim before the projection contract is confirmed.
- Replacing source documents with wiki pages or weakening source provenance.
- Adding semantic fields to Ticket Envelope v1 or parsing ticket metadata outside `ticket-parse`.
- Fabricating a reason for a historical gate from nearby narrative evidence.
- Mutating NightDAX, `C:\el`, an external wiki, or any ledger from this repository without an exact
  repository identity and a separately authorized delivery request.
- Executing or scheduling the planned tickets in this wayfinding pass.

## Frontier / Blocking Edges

| Edge | Why it blocks | Unblock condition | Owning ticket |
|---|---|---|---|
| Semantic projection contract is undefined | Compiler and lint could agree on a new but still non-interrogable shape, or copy excessive content | A representative prototype measures projection completeness, page size, determinism, and query usefulness | `SW-01` |
| Projection policy needs human confirmation | Extraction versus authored synthesis changes freshness, audit, cost, and source-fidelity guarantees | `grilling` confirms a decision spec using `SW-01` evidence | `SW-02` |
| Compiler has no semantic source model | `Artefact` and `render_page()` cannot emit confirmed content | Implement the confirmed projection while preserving current identity/re-ingest invariants | `SW-03` |
| Lint equates current metadata with sufficient coverage | Metadata-only pages remain green | Add a seeded-defect semantic-coverage pass against the confirmed per-kind contract | `SW-04` |
| Stage gates accept no cause and status returns IDs only | Operators cannot understand or safely resolve a gate from status | Require reason on gated stage events and expose structured open-gate records | `SW-05` |
| Old generic gate reasons lack evidence | Automatic migration would invent historical facts | Supply durable evidence per open gate, or retain an explicit legacy/unknown marker | `SW-06` |
| Eight local documents reportedly lack durable ownership | Wiki compilation cannot ingest or preserve sources absent from its configured durable corpus | Identify the owning repository and explicitly publish, retain, or discard each document | External follow-up; no local ticket yet |

## Ticket Plan

Canonical Ticket Envelopes are emitted under
`docs/tickets/llm-wiki-semantic-coverage/`. Their normalized dependency graph is the executable
projection of this plan.

| ID | Type | Mode | Blockers | Title | Expected output |
|---|---|---|---|---|---|
| `SW-01` | Prototype/research | AFK | — | Measure semantic projection options | Disposable compiler over representative tickets/specs/other docs plus a durable comparison of coverage, size, determinism, and query utility |
| `SW-02` | Decision | HITL | `SW-01` | Confirm semantic projection and lint policy | Decision spec produced through `to-spec` after `grilling`, defining per-kind required content, authored-text policy, freshness, and audit semantics |
| `SW-03` | Task | AFK | `SW-02` | Compile structured semantic content | Updated ingest model/renderer and tests proving body changes alter visible content while identity, moves, and no-op re-ingest remain correct |
| `SW-04` | Task | AFK | `SW-02`, `SW-03` | Enforce semantic coverage in lint | Named lint pass with metadata-only, empty, malformed, stale, and clean fixtures plus documented severity and repair guidance |
| `SW-05` | Task | AFK | — | Require and display concrete stage-gate causes | Versioned event validation, kernel transition, structured status records, ledger compatibility handling, and causal CLI/kernel tests |
| `SW-06` | Data repair | HITL | `SW-05` | Repair evidence-backed open generic gates | Exact refreshes only where a human supplies durable evidence; irrecoverable historical records remain explicitly unknown |

Ready now: `SW-01` and `SW-05`. Blocked: `SW-02` on `SW-01`; `SW-03` on `SW-02`; `SW-04`
on `SW-02` and `SW-03`; `SW-06` on `SW-05` plus human evidence. The external source-durability
follow-up is blocked on repository identity and publication intent.

## Next Review

Review the outputs of `SW-01` and `SW-05` before opening the implementation frontier:

1. Does the proposed projection let a query recover a ticket's build intent, acceptance criteria,
   testing plan, frontier, and exclusions without reading the source file separately?
2. Does the projection preserve source fidelity and idempotence without turning a 121,726-word corpus
   into an indiscriminate duplicate?
3. Can semantic lint fail on a page whose digest is current but whose required projection is absent?
4. Does a newly gated stage fail closed without a reason, and does `status` expose enough structured
   context to act without opening the ledger manually?
5. Are old ledgers still readable while unknown historical causes remain visibly unknown rather than
   inferred?

Recommended next step: route the validated folder to `ticket-autopilot`. Execute ready AFK work,
keep `SW-02` and `SW-06` behind their exact human/evidence gates, and never infer the external
NightDAX repository or historical causes.
