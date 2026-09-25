---
type: source
title: "Ticket-driver judge identity: one name per actual run invocation"
identity_key: artifact:ticket-driver-judge-identity
identity_strength: stable
source_path: docs/specs/ticket-driver-judge-identity.md
source_digest: sha256:242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-24
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket-driver judge identity: one name per actual run invocation

Compiled from `docs/specs/ticket-driver-judge-identity.md`. Identity is `artifact:ticket-driver-judge-identity`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-24** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-judge-identity-jci-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-driver-judge-identity.md","payload_bytes":2281,"payload_sha256":"242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e"}],"payload_bytes":2281,"payload_sha256":"242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e","schema":1,"source_digest":"sha256:242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e","source_identity":"artifact:ticket-driver-judge-identity","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2281,"payload_sha256":"242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e","schema":1,"source_digest":"sha256:242c805107fa669c5e941114c836682708cc78e0df70c1917962f954c089bb4e","source_identity":"artifact:ticket-driver-judge-identity"} -->
```markdown
# Ticket-driver judge identity: one name per actual run invocation

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-identity`
- Role: `spec`
- Standalone: true

### Children
- [JCI-01 — give fallback judges run-scoped IDs](../tickets/ticket-driver-judge-identity/01-give-fallback-judges-run-scoped-ids.md)

## Problem and evidence
In c3b-r4 post-fix (old skill HEAD `0d3df0f...`), a directed blocker triggered builder-2 and another `semantic_gates()` invocation. The first `semantic_gates()` had already used `sessions/judge-1`; a fresh `Cascade` instance reset its counter to zero and reused `judge-1`. The run had passed its candidate tests and several Jev decisions, then failed on `[WinError 183] ... sessions/judge-1` (ledger event 32, `failure=driver`). This was not a model/verification gate; the label consumed one start and remains failed. Direct evidence: `C:/bench38/driver-c3b-r4/project/.git/ticket-driver/runs/tdr-1790214450-ee84a564b4/ledger.jsonl` and `bench38-driver-c3b-r4.json`.

## JCI-01 invariant
Within one run, every fresh fallback judge has a unique receipt ID and session directory across all `Cascade` instances, including when `semantic_gates()` is entered again after a directed builder retry. Failed/partially-created session directories cannot be overwritten. The first judge retains `judge-1`; later judges use the next available monotonically increasing suffix. Do not change Jev confidence thresholds, question content, cascade order, decision parsing, key isolation, prompt or benchmark hidden tests. No guessed `yes` on uncertain results; gate as before when fresh judge is unavailable.

## Scope and verification
Change `ticket-driver/scripts/cascade.py` at the identity allocator, add causal test in `ticket-driver/tests/test_c3.py` and fake leaf support if required. Test RED on baseline by returning Jev uncertainty in both initial and retry semantic gates, causing two fresh judges in one run; GREEN demonstrates unique IDs and no FileExistsError while original c3/c4, c2, c1b and local quick profile remain green. Graph audit, inline review, canonical verification bundle, PR exact-head CI/merge/sync. Post-fix live benchmark labels must bind the *new* installed identity; old c3b-r4 must never be rerun or counted valid.

```
