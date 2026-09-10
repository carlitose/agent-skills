---
type: source
title: "LLM Wiki Docs-Only Auto-Sync Forward Test"
identity_key: artifact:llm-wiki-docs-only-autosync-forward-test
identity_strength: stable
source_path: docs/research/llm-wiki-docs-only-autosync-forward-test.md
source_digest: sha256:fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# LLM Wiki Docs-Only Auto-Sync Forward Test

Compiled from `docs/research/llm-wiki-docs-only-autosync-forward-test.md`. Identity is `artifact:llm-wiki-docs-only-autosync-forward-test`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[],"status":"not-identified"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[4],"status":"present"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-llm-wiki-docs-only-autosync-forward-test.md","payload_bytes":1877,"payload_sha256":"fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a"}],"payload_bytes":1877,"payload_sha256":"fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a","schema":1,"source_digest":"sha256:fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a","source_identity":"artifact:llm-wiki-docs-only-autosync-forward-test","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | no matching section identified in the source; complete source retained |
| limitations | 4: Limitations |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1877,"payload_sha256":"fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a","schema":1,"source_digest":"sha256:fc444314f31b29836a0b4f348902a8feba1c9860e316655626d4ddae7c489c3a","source_identity":"artifact:llm-wiki-docs-only-autosync-forward-test"} -->
````markdown
# LLM Wiki Docs-Only Auto-Sync Forward Test

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-forward-test`
- Role: `research`
- Parent: [LLM Wiki Docs-Only Auto-Sync](../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Result

The deterministic forward matrix passes for both public trigger boundaries. The
[machine-readable report](llm-wiki-docs-only-autosync-forward-test.json) owns the raw
given/when/then scenarios, executable commands, expected test counts, invariants, and
limitations.

| Trigger | States exercised | Result |
| --- | --- | --- |
| After complete ticket batch | absent, untracked, tracked, ambiguous, partial, invalid graph | pass |
| After durable ticket integration | absent, external, untracked, tracked, retry, replay, policy pending | pass |
| Shared sync boundary | broken binding, multiple roots, partial tracking, mixed paths, lint failure, stale and concurrent change | pass |

The suite proves one sync per complete batch and one stable effect per durable integrated
ticket. Missing wikis are never scaffolded. External and internal-untracked output applies
directly only after validation. Internal tracked output remains a separate docs-only
candidate with exact-head authority and an `implementation-complete` claim ceiling.

## Reproduce

```bash
python3 -B -m unittest ticket-autopilot.tests.test_wiki_sync_forward_matrix
```

The test loads the report, rejects coverage or policy drift, and executes the listed public
boundary suites. The report intentionally does not treat wiki pages as primary evidence.

## Limitations

All cases use local temporary filesystems, disposable Git repositories, and deterministic
provider fakes. No production wiki, live provider mutation, or host-specific cross-process
queue is observed, so the result supports `implementation-complete`, not a live or
production-ready claim.

````
