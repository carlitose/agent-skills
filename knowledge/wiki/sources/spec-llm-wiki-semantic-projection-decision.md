---
type: source
title: "Deterministic, complete semantic source projection"
identity_key: spec:llm-wiki-semantic-projection-decision
identity_strength: stable
source_path: docs/specs/llm-wiki-semantic-projection-decision.md
source_digest: sha256:eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-09
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Deterministic, complete semantic source projection

Compiled from `docs/specs/llm-wiki-semantic-projection-decision.md`. Identity is `spec:llm-wiki-semantic-projection-decision`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-09** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[3],"status":"present"},"exclusions":{"headings":[4],"status":"present"},"goals":{"headings":[4],"status":"present"},"invariants":{"headings":[9],"status":"present"},"verification":{"headings":[11],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/spec-llm-wiki-semantic-projection-decision.md","payload_bytes":12185,"payload_sha256":"eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314"}],"payload_bytes":12185,"payload_sha256":"eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314","schema":1,"source_digest":"sha256:eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314","source_identity":"spec:llm-wiki-semantic-projection-decision","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 4: Goals and non-goals |
| exclusions | 4: Goals and non-goals |
| decisions | 3: Decision and evidence |
| invariants | 9: Transitions and invariants |
| verification | 11: Implementation and verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":12185,"payload_sha256":"eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314","schema":1,"source_digest":"sha256:eaf348ec684bd6a66ca861fa0c62e309d04de717d3313d6e86cf62828c8d2314","source_identity":"spec:llm-wiki-semantic-projection-decision"} -->
```markdown
# Deterministic, complete semantic source projection

## Artifact Graph
- Artifact ID: `spec:llm-wiki-semantic-projection-decision`
- Role: `spec`
- Parent: [Semantic coverage recovery](llm-wiki-semantic-coverage-wayfinder.md)

Source ticket: [SW-02 — Confirm semantic projection policy](../tickets/llm-wiki-semantic-coverage/done/02-confirm-semantic-projection-policy.md). The map owns the reciprocal graph edge, following the SW-01 output convention; the runner-bound ticket remains unchanged.

## Type and status
Decision spec. Human-confirmed through the SW-02 `grilling` interview; implementation belongs to SW-03 and SW-04. This decision is not evidence that the compiler or lint already implements it.

## Decision and evidence

Use **deterministic preservation of the complete source text**, organized by source sections, without agent-authored summaries. Accept duplication in exchange for source fidelity. Split large generated pages rather than truncating their source content.

The [SW-01 comparison](../prototypes/llm-wiki-semantic-coverage/NOTES.md) and its [retained results](../prototypes/llm-wiki-semantic-coverage/results.json) measured six adapted fixtures, not the full corpus. Metadata-only pages exposed 0/36 available answer witnesses; complete preservation and the source layer of the layered variant exposed 36/36; bounded extraction exposed 34/36; authored summaries alone exposed 8/36. Preservation produced 10,724 bytes versus 9,664 for bounded extraction. These are local lexical recoverability/size measurements, not token counts, human-comprehension proof or production performance estimates.

The human explicitly selected deterministic content, complete preservation, truthful missing-section reporting and a 32 KiB generated-page limit, then confirmed the combined contract below. The runner retains the separate actor/evidence-bound SW-02 start approval. No historical gate repair, wiki merge or local installation migration is implied.

## Goals and non-goals

- A source page and its linked parts expose all information available in its source, not just metadata or a pointer.
- Preserve canonical identity, parsing, source grounding, graph, dates, lifecycle and repeatable no-op behavior.
- Let deterministic lint detect lost, changed, missing or stale source content independently of the renderer's success report.
- Do not generate prose, score subjective meaning, call a model, repair sources, widen discovery automatically, or change Ticket Envelope v1.

## Source and per-kind coverage

The preserved payload is the complete UTF-8 source text after the existing source reader's universal-newline normalization. Envelope text may be displayed literally; only the canonical ticket parser interprets Ticket Envelope metadata. Invalid ticket contracts and unreadable/invalid-UTF-8 sources retain their existing failure boundary.

Expose a section navigation/coverage table for each logical source kind:

| Kind | Required navigation/coverage topics |
|---|---|
| Ticket | Build intent, acceptance criteria, testing, frontier, exclusions |
| Spec, including wayfinding specs | Goals, exclusions, decisions, invariants/contracts, verification |
| Research | Question, method, findings, evidence/sources, limitations |
| Prototype | Question, assumptions, observed results, limitations, decision or next step |
| Guide | Purpose, prerequisites, procedure, limitations |

These topics do not authorize inventing missing source sections. Each topic is either `present`, bound to actual source heading occurrences, or `not-identified`, visibly described as “no matching section identified in the source; complete source retained.” This is a structural observation, not a claim that the underlying fact cannot appear elsewhere. It implements truthful “not specified” reporting without pretending deterministic heading matching understands arbitrary prose.

Recognize ATX and Setext headings, nesting and repeated sections; headings inside fenced examples are data. Preserve unheaded text and irregular or unclassified sections too. A finite, documented heading-alias map supports navigation, but must never select which text survives. Duplicate matching sections are all retained. Missing matching sections in a nonempty source do not block compilation or lint. An empty/whitespace-only source has no semantic payload and receives an explicit failure, not invented filler.

Projection kind is separate from the existing identity key and file naming. Derive it from source role and configured source category; do not silently classify research/prototypes/guides as specs merely because they have an Artifact ID. Guide support applies to configured paths only; this decision does not add source globs or import unrelated repositories. Unresolvable kind classification must be reported explicitly rather than claiming coverage for an invented kind.

## Literal rendering and page size

- Display the original text in literal Markdown source blocks. Choose safe fences around nested examples. Source-relative links and example wikilinks remain literal, not new wiki graph edges. Keep navigable provenance, canonical graph links and part links outside those blocks.
- Source sections determine navigation and preferred split points. A section larger than the budget may span parts; its remaining text must not disappear.
- Every generated source page and content-part page is at most **32,768 UTF-8 bytes**, including metadata, navigation, markers and fences. This is a byte bound, not a token estimate.
- Split on valid Unicode boundaries and retain all normalized source characters, including whitespace, in order. Reassembling payloads must reproduce the normalized source byte-for-byte. Part decoration is not source payload.
- Keep the identity-stable source page as the entry point. Give parts deterministic identity-based names and explicit ordered links; directory moves of an identity-stable source do not create a new source identity.
- Include navigation overhead in size accounting. If even required metadata/navigation cannot be represented within the bound, report a specific size failure before publishing rather than silently truncating it. No larger-page compatibility fallback is authorized.

## Machine-readable contract: semantic projection v1

SW-03 owns the serializer/parser boundary for a versioned projection manifest; SW-04 owns validation against the source. Reserve these marker names:

- `<!-- semantic-projection-v1: <one-line canonical JSON> -->` for the manifest on the identity-stable source page.
- `<!-- semantic-payload-v1: <one-line canonical JSON> -->` immediately before each literal source payload block.

Canonical JSON is UTF-8, sorted keys, compact separators and deterministic ordering. Payload text is never interpolated into a marker. The manifest contains exactly:

- `schema: 1`, canonical `source_identity`, existing `source_digest`, and the independently determined `source_kind`;
- `payload_sha256` and `payload_bytes` for the complete normalized source text;
- `coverage`, mapping every required topic of that kind to `status` (`present` or `not-identified`) and an ordered `headings` list of zero-based heading-occurrence indexes; the latter is empty for `not-identified`;
- ordered `parts`, each containing `index` (zero-based), `path` (wiki-root-relative), `payload_sha256`, and `payload_bytes`.

Every payload marker contains exactly `schema: 1`, `source_identity`, `source_digest`, `part_index`, `payload_sha256`, and `payload_bytes`. The following fenced block is the literal payload for that part. The manifest declares all payloads exactly once; a source page may itself contain a part. There are no missing, duplicate or undeclared content parts. No field claims that source freshness is an authored-text audit.

A renderer may use internal types/helpers, but not a second ticket-envelope parser. Do not let the serialized manifest alone attest its own correctness: lint must read the configured source and generated payloads and perform the comparisons below.

## Lint contract

Add the error-severity pass **`semantic-coverage`**. It applies to present generated project-history source pages under an active project binding, and reports not-applicable when that binding is absent.

For each applicable page, lint independently checks marker schema and field shape, canonical source identity/digest/kind, complete per-kind topic mapping and actual heading occurrences, declared part inventory and order, payload hashes/byte counts, full reconstructed text against the normalized source, and the 32 KiB page bounds. Arbitrary nonempty prose or a current metadata digest cannot substitute for these checks.

Required seeded failures: current-digest metadata-only page; missing or empty payload; malformed/duplicate marker; wrong kind or identity; missing required topic record; incorrect `not-identified` claim for a recognized section; stale digest; altered payload; missing/duplicate/reordered/extra part; oversized page. Each reports the affected path and repair guidance. A clean fixture for every supported kind must remain reachable.

A present legacy metadata-only page fails with guidance to regenerate through ingest. No silent legacy pass, compatibility renderer or subjective LLM judge is added. Missing-source tombstones retain their identity/provenance and a truthful missing-source state; semantic freshness/coverage is not claimed for an unavailable source. A source that exists but cannot be read is an error, not a tombstone or an absent-binding no-op.

Lint never regenerates content, modifies sources, refreshes gates, or grants delivery/merge authority.

## Transitions and invariants

- Initial upgrade materializes projection v1 even where the existing metadata digest is unchanged. This is a real generated-content update, not an unchanged success.
- Once projected, identical source, configuration and projection version produce byte-identical pages and zero writes, including unchanged mtimes.
- Semantic-only source changes update visible payload, source/part digests and coverage/navigation when relevant.
- Stable-identity moves, including ticket moves to `done/`, update one existing source identity. Remove only obsolete generated parts owned by that identity; preserve unrelated pages.
- Preserve canonical graph links, dates and provenance, run links, weak-identity warnings, set-based transitions and tombstones.
- Unknown historical gate causes remain unknown. SW-06 retains its separate exact repository/run/gate/evidence requirement.

## Alternatives and consequences

Rejected: metadata-only output, character-capped extraction as the authoritative content layer, and agent-authored/layered summaries. Selective extraction may make useful navigation, but cannot discard the source tail or unsupported headings. Whole-source preservation costs storage and duplicates source text; the page limit bounds individual reads, not total corpus size or model cost. Literal rendering favors faithful agent-readable content over a polished re-rendering of arbitrary source Markdown.

## Implementation and verification

1. **SW-03:** implement source-kind/section navigation, complete literal payload rendering, versioned manifests and deterministic size-aware splitting. Keep identity and canonical parsing deep in their existing owners. Test semantic changes, source absences, irregular headings, splitting/reassembly, moves, tombstones and zero-write replay.
2. **SW-04:** implement the independently source-checking `semantic-coverage` pass, seeded negatives, all-kind clean fixtures and public documentation of severity, pass count and repair guidance.
3. Run focused and full `llm-wiki` regressions and scratch-corpus ingest/lint without mutating a production wiki. Record skips, unavailable environments and timeouts honestly. No live-provider, GUI, vector-search, wiki-merge or global readiness claim follows from local fixtures.

The [semantic coverage map](llm-wiki-semantic-coverage-wayfinder.md) retains scheduling ownership and links both implementation tickets. This spec resolves SW-02 policy only; it does not erase delivery gates in other runs.

```
