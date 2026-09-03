# LLM Wiki legacy root-catalog adoption

## Artifact Graph

- Artifact ID: `spec:llm-wiki-legacy-root-catalog-adoption`
- Role: `spec`
- Standalone: true

### Children

- [WCA-01 — Adopt the Agent Skills legacy root catalog](../tickets/llm-wiki-legacy-root-catalog-adoption/done/01-adopt-agent-skills-legacy-root-catalog.md)

## Type

Bug-analysis and migration specification.

## Observed behavior

WS-08 introduced exact ownership markers for compiler-managed sections of `wiki/index.md`, but the tracked Agent Skills wiki predates those markers. `root_catalog.parse_catalog()` correctly rejects ambiguous catalogs, while `ingest_docs._catalog_text()` initializes only an absent index. The existing catalog therefore reaches `sync_project()` as a pre-existing legacy file, raises `CatalogOwnershipError`, is normalized to `reason: compile`, and makes Ticket Autopilot's post-integration wiki attempt terminal before a candidate can be produced.

At GitHub `main` commit `5158e0a4fe2bc7ffba8e24772d00c6913a961af9`, `knowledge/wiki/index.md` is 48,573 bytes and has no ownership markers. Its content is the output shape of the pre-WS-08 compiler: project source sections, one session-source section, and one timeline section. WS-08 explicitly excluded reconstruction or publication of the real Agent Skills index, so code rollout and data migration were not completed together.

The OpenAI outage that produced `no healthy upstream` and `Not Found` is unrelated.

## Target behavior

Provide a dedicated, explicit legacy-catalog adoption boundary and apply it once to the tracked Agent Skills wiki. Normal compilation remains strict: an arbitrary unmarked catalog still fails closed.

The migration accepts a regular UTF-8 catalog, its required SHA-256, and a complete ordered ownership map. It inserts canonical markers around caller-declared byte spans and then proves:

1. the input digest equals the expected digest;
2. spans are ordered, complete, non-overlapping, and belong to the three known owners;
3. `parse_catalog()` accepts exactly one block for `project-sources`, `session-sources`, and `timeline`;
4. deleting only the six inserted marker lines reconstructs the original bytes exactly; and
5. replay on an already adopted catalog is byte-idempotent.

For the concrete Agent Skills catalog, the explicit map assigns the project preface plus `Other`, `Spec`, `Ticket`, and `Removed` source sections to `project-sources`; the complete `Session sources` section to `session-sources`; and the complete `Timeline` section to `timeline`.

After adoption, the ordinary staged compiler owns updates inside those blocks. It ingests current specs, tickets, sessions, and timeline records, runs generated-scope validation and every lint pass, and returns a tracked `wiki-sync-v1` candidate. Candidate publication remains separate from the implementation candidate.

## Goals

- Repair the concrete Agent Skills post-integration wiki failure.
- Preserve every original catalog byte and ordering aside from inserted marker lines.
- Keep WS-08's strict behavior for arbitrary or ambiguous catalogs.
- Make adoption and subsequent sync deterministic and idempotent.
- Bring the real tracked wiki current through the normal candidate flow.

## Non-goals

- Automatic ownership inference from headings.
- Adoption of unrelated legacy wikis without their own exact digest and map.
- Hand-rewriting generated source, session, or timeline entries.
- Pi package or Pi executable changes.
- Applying unrelated audit corrections.
- Inferring merge, cleanup, or reload authority.

## Semantic invariants

- Ordinary ingest and sync never adopt missing boundaries automatically.
- The migration writes nothing before digest, map, path, mode, and UTF-8 validation succeeds.
- Human-owned bytes are never reconstructed or normalized.
- Generated project, session, and timeline content remains complete and deterministic after adoption.
- Protected wiki compilation stays staging-first; failure cannot partially update it.
- Tracked wiki output remains a separately authorized exact candidate.

## Failure modes

- Digest mismatch, path/type mismatch, non-UTF-8 content, unknown owner, missing owner, overlap, gap inside a declared span, or out-of-order span: stop before mutation.
- Marker parse or round-trip reconstruction mismatch: discard staged output and preserve the source.
- Compiler or lint failure after adoption: no successful sync claim and no protected-tree application.
- Replay with a contradictory map: reject rather than reinterpret existing ownership.

## Implementation slice

One tracer-bullet ticket adds the adoption API/CLI and its tests, applies it to the exact tracked Agent Skills catalog, validates normal staged compilation, and leaves the subsequent generated wiki update to the runner's separate post-integration candidate.

## Verification strategy

- **Unit:** exact digest, ownership-map validation, marker insertion/removal identity, replay, newline fidelity, unknown/missing/overlapping spans, and malformed existing markers.
- **Integration:** exact legacy fixture through adopt → ingest → timeline → generated-scope validation → full lint; tracked and untracked `sync_project` behavior; unchanged replay.
- **Regression:** complete LLM Wiki suite, Ticket Autopilot wiki-sync tests, context/token tests, compileall, diff check, and Artifact Graph comparison.
- **Live tracked boundary:** after code integration, require the post-integration wiki hook to produce a valid exact candidate or truthful unchanged result; authorize any tracked candidate only by its observed head.

## Acceptance outcomes

1. Removing the six markers from the migrated repository catalog reproduces the exact legacy bytes.
2. The migrated catalog parses into exactly three known owned blocks and a second adoption is unchanged.
3. Arbitrary unmarked catalogs remain rejected during ordinary synchronization.
4. The exact Agent Skills wiki completes staged compilation and lint without the missing-boundaries error.
5. The post-integration wiki flow reaches a candidate, unchanged result, or truthful later boundary outcome instead of the WS-08 migration gap.
6. The resulting tracked wiki is updated only through its separate candidate and exact-head authorization flow.

## Authority

The user requested the bug fix and wiki update. This authorizes specification and implementation, but does not pre-authorize an unknown code or wiki candidate head, cleanup, Pi mutation, or active-session reload.
