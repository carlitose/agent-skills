---
type: source
title: "Semantic projection comparison — NON-PRODUCTION"
identity_key: artifact:llm-wiki-semantic-coverage-prototype
identity_strength: stable
source_path: docs/prototypes/llm-wiki-semantic-coverage/NOTES.md
source_digest: sha256:b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-08
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Semantic projection comparison — NON-PRODUCTION

Compiled from `docs/prototypes/llm-wiki-semantic-coverage/NOTES.md`. Identity is `artifact:llm-wiki-semantic-coverage-prototype`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"assumptions":{"headings":[2],"status":"present"},"decision":{"headings":[9],"status":"present"},"limitations":{"headings":[],"status":"not-identified"},"question":{"headings":[2],"status":"present"},"results":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-llm-wiki-semantic-coverage-prototype.md","payload_bytes":11836,"payload_sha256":"b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e"}],"payload_bytes":11836,"payload_sha256":"b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e","schema":1,"source_digest":"sha256:b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e","source_identity":"artifact:llm-wiki-semantic-coverage-prototype","source_kind":"prototype"} -->

| Topic | Source sections |
|---|---|
| question | 2: Prototype frame |
| assumptions | 2: Prototype frame |
| results | no matching section identified in the source; complete source retained |
| limitations | no matching section identified in the source; complete source retained |
| decision | 9: Keep, discard, decide |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":11836,"payload_sha256":"b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e","schema":1,"source_digest":"sha256:b66d43d0adada46989a86c00cbf57b3e2dd65e4ad97f40e18b6aaf557171fb6e","source_identity":"artifact:llm-wiki-semantic-coverage-prototype"} -->
````markdown
# Semantic projection comparison — NON-PRODUCTION

## Artifact Graph
- Artifact ID: `artifact:llm-wiki-semantic-coverage-prototype`
- Role: `prototype`
- Parent: [Semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Prototype frame

- **Question:** Which projection lets a reader recover source-grounded answers while
  preserving identity, digest, graph, lifecycle, and zero-write replay guarantees?
- **Branch:** logic. This measures compilation and lexical query recoverability, not UI
  layout, retrieval ranking, or a human comprehension study.
- **Assumptions:** six small, adapted fixtures are sufficient to expose counterexamples,
  not to predict a full corpus. Guide discovery is enabled only in the temporary binding.
- **Useful result:** comparable generated pages, explicit coverage gaps and costs, and
  reproducible transition probes that inform—but do not select—production policy.

Source ticket: [SW-01](../../tickets/llm-wiki-semantic-coverage/done/01-measure-semantic-projection-options.md).
The ticket is runner-bound by digest; the reciprocal graph edge is in the parent map.
**SW-02 remains the human policy decision.** This directory is disposable, not production
compiler or lint implementation. Keep this report and its evidence when discarding the model.

## Run and inspect

From the repository root:

```bash
python3 -B docs/prototypes/llm-wiki-semantic-coverage/prototype.py
python3 -B -m unittest discover -s docs/prototypes/llm-wiki-semantic-coverage -p 'test_*.py' -v
python3 -B -m unittest discover -s llm-wiki/tests -p test_ingest_docs.py -v
```

The first command prints all measurements and transitions. To reproduce the retained
[complete comparison](results.json), add `--output /tmp/SW01-results.json`. Each variant's
`pages` object contains directly comparable source pages and, for `layered`, summary pages.
For example, print the same ticket under all four variants without opening its source:

```bash
python3 -B - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('docs/prototypes/llm-wiki-semantic-coverage/results.json').read_text())
for name, variant in result['variants'].items():
    print('\n===', name, '===\n', variant['pages']['wiki/sources/ticket-family-fx-01.md'])
PY
```

Observed development checks: **10 prototype tests and 20 existing ingest tests passed**.
The first prototype attempt correctly rejected a noncanonical inline dependency list;
fixtures were corrected to canonical block-list syntax without weakening `ticket-parse`.
These observations are local, not a globally green suite or release-readiness claim.

## Corpus and measurement method

[fixtures.py](fixtures.py) names the six grounding documents at baseline
`6b8ea103d4e5bb0e188116984a64882c5d77e53e`. Wording, IDs and dependencies are adapted
synthetic examples, not verbatim historical observations or new executable tickets.
Two canonical tickets join one spec, research note, prototype and guide. The cases include
nested/irregular headings, a Setext heading, repeated/empty/fenced headings in boundary
tests, missing information, an over-budget exclusion, and a path-derived weak identity.

The existing/default binding covers specs, tickets, research and prototypes; it does not
include this repository's root-level context guide. The experiment adds `docs/guides/*.md`
only to its own temporary binding. Production still classifies the ID-bearing research and
prototype fixtures as `spec`, and the weak-ID guide as `other`; logical corpus roles are
reported separately. No real binding or `llm-wiki/scripts/` file is changed.

The harness invokes the actual canonical parser and ingest planner/writer. Only the renderer
is temporarily wrapped in-process. Dates use fixed filesystem mtimes, Git history is disabled,
and all state is inside temporary `PROTOTYPE-wipe-me` directories. No provider, external
NightDAX source, real wiki, or LLM service participates.

Answer witnesses are explicitly annotated independently of the extraction heading aliases.
A witness must occur in the visible page body, not merely metadata or a source pointer.
This is **lexical recoverability**, not independent proof of human comprehension or absence
of every possible misleading statement. Six of 42 question/document combinations lack a
source answer; they are reported as absent, never credited as recovered.

## Options and measured cost

- **metadata-control:** the unchanged production renderer; provenance and graph only.
- **preserve:** deterministic preservation of the entire normalized fixture, including its
  envelope, in a literal Markdown block. The fence safely contains nested examples;
  original relative links stay literal while canonical graph links remain navigable.
  This intentionally measures a high-fidelity, high-duplication extreme, not a policy to
  copy the diagnosed corpus.
- **bounded:** fixed heading aliases, duplicate-section concatenation and a 220-Unicode-
  character cap per question. Missing sections and truncation are explicit. Setext
  headings are unsupported; this is not a general Markdown parser or semantic model.
- **layered:** the same preserved source plus separately indexed, agent-authored fixture
  summaries. The authored text is fixed input, not a newly invoked or audited LLM output.

| Option | Generated bytes | Words | Bytes/source | Words/source | Available answers |
| --- | ---: | ---: | ---: | ---: | ---: |
| metadata-control | 6,080 | 617 | 1.550× | 1.143× | 0/36 |
| preserve | 10,724 | 1,235 | 2.734× | 2.287× | 36/36 |
| bounded | 9,664 | 1,092 | 2.464× | 2.022× | 34/36 |
| layered | 13,856 | 1,519 | 3.533× | 2.813× | 36/36 |

Totals include generated source pages and catalogs; `layered` also includes summaries and
its catalog. The common input is 3,922 UTF-8 bytes / 540 whitespace-separated words.
Per-source page bytes, words and ratios are retained in `results.json`. Counts are not model
tokens, reader effort, or estimates for the full diagnosed corpus. Metadata overhead dominates
these deliberately small fixtures; even the metadata-only control exceeds source size.

## Which questions can a page answer?

Order: **I** intent, **A** acceptance, **T** testing, **F** frontier, **X** exclusions,
**D** decisions, **E** evidence. `Y` = witness present; `M` = source witness missing from page;
`–` = answer absent from source. The two tickets are shown separately.

| Document | metadata-control | preserve | bounded | layered source |
| --- | --- | --- | --- | --- |
| FX-01 ticket | M M M M M M M | Y Y Y Y Y Y Y | Y Y Y Y M Y Y | Y Y Y Y Y Y Y |
| FX-02 ticket | M M M M M M M | Y Y Y Y Y Y Y | Y Y Y Y Y Y Y | Y Y Y Y Y Y Y |
| Spec | M M M M M M M | Y Y Y Y Y Y Y | Y Y Y Y Y Y Y | Y Y Y Y Y Y Y |
| Research | – – M – M M M | – – Y – Y Y Y | – – Y – Y Y Y | – – Y – Y Y Y |
| Prototype | M – M M M M M | Y – Y Y Y Y Y | Y – Y Y Y Y Y | Y – Y Y Y Y Y |
| Guide | M – M – M M M | Y – Y – Y Y Y | M – Y – Y Y Y | Y – Y – Y Y Y |

`preserve` and the source side of `layered` recover all 36 available witnesses. This is not
42/42 completeness: neither invents the six absent answers. `bounded` misses the late
exclusion in FX-01 and the guide's Setext purpose. `metadata-control` recovers none.
The authored summaries alone recover only **8/36** available witnesses; they must not be
presented as equivalent to their source layer.

Concrete FX-01 comparison: metadata alone cannot answer what to build. Both preserved
options display “Reject blank reasons before a ledger mutation.” Bounded extraction retains
that intent but truncates “Do not infer historical gate causes.” The corresponding scope
question is therefore not answerable from its page alone.

## Update behavior and invariant probes

| Probe | Observation |
| --- | --- |
| Fresh compile | Six `new` source transitions for every option |
| Unchanged second run | Six `unchanged` transitions, zero source/summary writes, zero changed-file bytes, unchanged Markdown mtimes |
| Replay in a fresh directory | All generated Markdown byte-identical with the same fixed authored inputs |
| Semantic-only edit after the cap | All digests change; only `preserve` and `layered` expose the new fact and change semantic body |
| Ticket move into `done/` | One `moved` transition, no new source page, same canonical identity/name and parent link |
| Research source removal | One `missing` transition; tombstone retained rather than deleted |
| Replay after move/removal | Zero changed-file bytes |
| Weak-ID guide rename | New path identity plus old tombstone, not a falsely stable identity; new authored summary unavailable |
| Canonical parser rejection | Unsupported ticket schema fails before wiki writes |
| Newline normalization | Actual source reader gives identical digest for UTF-8 LF and CRLF text |
| Graph | Parent, child and blocker links checked; no broken generated source/summary wikilinks |
| Section boundaries | Empty sections unavailable, duplicate sections retained, fenced fake headings ignored |

The edited fact changes from “Do not infer historical gate causes.” to “Do not install
packages from this fixture.” A fresh digest does **not** make the bounded projection sensitive
to that semantic change: both the old and new fact are beyond its cap. Truncation is visible,
but coverage remains missing. This supplies a concrete negative case for SW-02/SW-04.

Identity, digest, source-page layout, canonical graph, move detection and tombstone behavior
come from the unchanged production owner. Added payload blocks and the layered summary
namespace are experimental layout additions. Literal preservation is not a polished rendered
section view, and arbitrary Markdown, full wiki lint, concurrency, Git-date provenance,
provider behavior and new summary-regeneration policy are not established by this model.

## Authored text: freshness is not audit

Each handwritten summary binds its original normalized source digest and is explicitly
`unreviewed`. Digest equality only reports `digest-match`; it does not approve accuracy or
coverage. After the semantic edit the old authored text remains visible but is marked `stale`
with a “do not treat as current” warning. A missing source is marked `source-missing`; a new
weak identity has `unavailable` authoring. No automatic repair or invented approval occurs.

Determinism for this layer means **same fixed authored text plus same source**, not deterministic
LLM generation. Choosing audit responsibility, regeneration triggers, missing-source handling,
and whether stale summaries may remain visible is production work for SW-02, not an outcome
silently selected by this prototype.

## Keep, discard, decide

- **Keep:** source-independent answer witnesses, metadata-only and truncated-tail negative
  controls, zero-write/fresh-directory replay tests, and explicit digest-versus-audit separation.
- **Discard after a confirmed contract exists:** the monkeypatched renderer, synthetic corpus,
  simplistic alias parser and handwritten demonstration summaries.
- **Recommendation for the decision:** reject page existence or digest freshness as sufficient
  semantic coverage. Compare explicit loss reporting against the cost of preservation before
  deciding; summaries alone are not supported as complete by these observations.
- **SW-02 must decide:** required questions per logical kind, guide discovery, preserved versus
  structured versus layered representation, truncation/unsupported-heading policy, source
  rendering/link behavior, authored freshness/audit ownership, and independent lint semantics.

No production projection, administrative disposition, historical repair or later HITL approval
is selected here. SW-02 and SW-06 remain behind their existing gates.

````
