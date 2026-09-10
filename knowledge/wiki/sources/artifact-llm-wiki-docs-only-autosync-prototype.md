---
type: source
title: "LLM Wiki Docs-Only Auto-Sync Prototype"
identity_key: artifact:llm-wiki-docs-only-autosync-prototype
identity_strength: stable
source_path: docs/prototypes/llm-wiki-docs-only-autosync/NOTES.md
source_digest: sha256:901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# LLM Wiki Docs-Only Auto-Sync Prototype

Compiled from `docs/prototypes/llm-wiki-docs-only-autosync/NOTES.md`. Identity is `artifact:llm-wiki-docs-only-autosync-prototype`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-llm-wiki-docs-only-autosync-ws-02]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"assumptions":{"headings":[2],"status":"present"},"decision":{"headings":[7],"status":"present"},"limitations":{"headings":[8],"status":"present"},"question":{"headings":[2],"status":"present"},"results":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-llm-wiki-docs-only-autosync-prototype.md","payload_bytes":4765,"payload_sha256":"901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4"}],"payload_bytes":4765,"payload_sha256":"901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4","schema":1,"source_digest":"sha256:901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4","source_identity":"artifact:llm-wiki-docs-only-autosync-prototype","source_kind":"prototype"} -->

| Topic | Source sections |
|---|---|
| question | 2: Prototype frame |
| assumptions | 2: Prototype frame |
| results | no matching section identified in the source; complete source retained |
| limitations | 8: Limits |
| decision | 7: Keep, discard, decide |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4765,"payload_sha256":"901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4","schema":1,"source_digest":"sha256:901f66667442870279ae77f1094f38c5c0abfa12420f60f6b899069f2b2be6d4","source_identity":"artifact:llm-wiki-docs-only-autosync-prototype"} -->
````markdown
# LLM Wiki Docs-Only Auto-Sync Prototype

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-prototype`
- Role: `prototype`
- Parent: [WS-02 prototype docs-only sync contract](../../tickets/llm-wiki-docs-only-autosync/done/02-prototype-docs-only-sync-contract.md)

The active ticket source is runner-bound by digest, so its reciprocal link lives in the
wayfinder's non-canonical prototype-evidence section rather than mutating the ticket mid-run.

## Prototype frame

- **Question:** Can generated wiki synchronization use a docs-only validation boundary
  without widening generic documentation scope or reusing an integrated application's
  CandidateRef?
- **Branch:** logic. The uncertainty is scope, normalized states, tracking, and identity.
- **Assumption:** paths are relative to one already-discovered compatible wiki root; reverse
  discovery itself returns zero, one, or multiple roots.
- **Useful result:** one runnable matrix that keeps every rejected protected tree unchanged,
  proves generated Markdown can pass the real wiki lint, and distinguishes viable request
  and identity designs.

This folder is deliberately disposable and is not production implementation.

## Run

```bash
python3 -B docs/prototypes/llm-wiki-docs-only-autosync/runner.py
```

The runner prints the state, request-design, and identity matrices, then executes the
assertions in `test_model.py`, including a temporary wiki created by the real scaffold and
validated by the real lint command.

## Result

The current `docs-only` v1 request cannot be reused literally: it is fixed to `docs/**/*.md`,
excludes ticket sources, and binds an active origin ticket. Two designs can remain
fail-closed while reusing the static validator primitives:

1. `docs-only-v2-profile` makes `llm-wiki-generated-v1` a versioned canonical profile.
2. `wiki-sync-v1-request` owns the wiki identity and scope separately, while delegating
   regular-file, UTF-8, patch, Markdown, graph, and link checks to shared validators.

The separate request is the safer prototype result because it does not widen the generic
documentation request and it can require a fresh post-integration identity. A caller-owned
allowlist fails: the caller can add binding configuration or raw inputs, so the validation
owner cannot prove one canonical scope.

The proposed generated scope is exact: regular, non-executable `wiki/**/*.md` only, relative
to one compatible bound root. It includes `wiki/index.md`, `wiki/log.md`, and compiled page
types. It excludes `purpose.md`, `schema.md`, `llm-wiki-project.json`, `audit/`, `raw/`,
assets, binaries, symlinks, executable files, ticket sources, code, and mixed candidates.
Whether purpose/schema should ever join the generated set remains a WS-03 decision.

## Normalized outcomes

| Situation | Result | Protected tree |
|---|---|---|
| no wiki | `noop-absent` | unchanged |
| one compatible wiki, no diff | `unchanged` | unchanged |
| wholly untracked generated Markdown | `direct-write-validated` | advances only after lint |
| wholly tracked generated Markdown | `tracked-candidate` | unchanged; fresh candidate owns diff |
| partially tracked | `error-partial-tracking` | unchanged |
| multiple roots | `error-ambiguous-root` | unchanged |
| broken binding | `error-broken-binding` | unchanged |
| forbidden/mixed paths | `error-forbidden-scope` | unchanged |
| failed wiki lint | `error-lint-failed` | unchanged |

## Identity comparison

- Reusing the integrated origin CandidateRef fails as `error-stale-identity`.
- A fresh synthetic sync-ticket CandidateRef works but couples sync to scheduler ticket
  lifecycle.
- A fresh runner completion-effect CandidateRef works and preserves the origin ticket as a
  provenance input rather than a mutable owner.

The latter two produce different deterministic ticket digests for the same generated tree.
WS-03 must choose the owner and retry lifecycle; the prototype does not make that policy
decision.

## Keep, discard, decide

- **Keep:** normalized result vocabulary, exact generated-path profile, partial-tracking
  rejection, separate tracked/untracked delivery, and fresh identity requirement.
- **Discard:** the Python model after the production contract and tests exist.
- **Decide in WS-03:** separate request versus versioned profile, synthetic ticket versus
  completion effect, purpose/schema/log eligibility, external root registration, lock/retry
  policy, and how sync failure affects the folder run summary.

## Limits

- Git and provider behavior are modeled with tree identities; no remote mutation occurs.
- The real lint integration uses a temporary scaffolded wiki, not a production wiki.
- Concurrency and crash recovery are represented as policy gaps, not proven behavior.

````
