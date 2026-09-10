---
type: source
title: "Prototype the docs-only wiki sync contract"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-02
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/02-prototype-docs-only-sync-contract.md
source_digest: sha256:8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Prototype the docs-only wiki sync contract

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/02-prototype-docs-only-sync-contract.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-01]] — `ticket:llm-wiki-docs-only-autosync/WS-01`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-02.md","payload_bytes":2231,"payload_sha256":"8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c"}],"payload_bytes":2231,"payload_sha256":"8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c","schema":1,"source_digest":"sha256:8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2231,"payload_sha256":"8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c","schema":1,"source_digest":"sha256:8a2c34d0ec7ec4436eeba6a8bc4761ec9035ec15d7007d117adb4fa518ab349c","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WS-02"
execution_mode: AFK
blocked_by:
  - "WS-01"
---

# Prototype the docs-only wiki sync contract

## Artifact Graph
- Artifact ID: `artifact:ws-02-prototype-docs-only-sync-contract`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
A disposable prototype that answers whether the docs-only adoption boundary can validate a
generated wiki sync without widening generic documentation scope or reusing an integrated
application CandidateRef.

## Acceptance Criteria
- [ ] Fixtures cover absent, untracked, tracked, partially tracked, multiple-match, broken
      binding, mixed code/wiki, and configuration/wiki candidates.
- [ ] The prototype demonstrates a precise scope profile and normalized result states, or
      records the smallest counterexample showing why that interface fails.
- [ ] Generated wiki Markdown can pass applicable static checks and `llm-wiki lint` while
      code, ticket sources, raw/binary inputs, and ambiguous roots fail closed.
- [ ] At least two identity designs for the post-integration tracked candidate are exercised.
- [ ] The prototype is clearly marked non-production and records limitations.

## Frontier
Blocked by `WS-01`. Its measured result feeds the `WS-03` decision.

## Step-by-Step Implementation Plan
1. Build isolated project/wiki/Git fixtures from the research contract.
2. Exercise a versioned profile design, a separate request-type design, and a caller-owned
   allowlist design against the same matrix.
3. Compare failure modes, candidate binding, validation coverage, and caller complexity.
4. Save the result under `docs/prototypes/llm-wiki-docs-only-autosync/` with an Artifact
   Graph pointing back to this ticket.

## Testing Plan
Automated fixture tests must assert exact paths, result states, CandidateRefs, and unchanged
trees for rejected inputs. No live provider or production wiki is required.

## Out of Scope
- Production implementation or provider delivery.
- Selecting the final policy without the human gate in `WS-03`.

```
