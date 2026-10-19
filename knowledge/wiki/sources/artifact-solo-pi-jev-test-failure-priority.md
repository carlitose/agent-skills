---
type: source
title: "Public failure has priority over review-format uncertainty"
identity_key: artifact:solo-pi-jev-test-failure-priority
identity_strength: stable
source_path: docs/specs/solo-pi-jev-test-failure-priority.md
source_digest: sha256:fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Public failure has priority over review-format uncertainty

Compiled from `docs/specs/solo-pi-jev-test-failure-priority.md`. Identity is `artifact:solo-pi-jev-test-failure-priority`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-12]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-test-failure-priority.md","payload_bytes":1967,"payload_sha256":"fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62"}],"payload_bytes":1967,"payload_sha256":"fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62","schema":1,"source_digest":"sha256:fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62","source_identity":"artifact:solo-pi-jev-test-failure-priority","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1967,"payload_sha256":"fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62","schema":1,"source_digest":"sha256:fe7a9818a66a39b0425df0e76952e07d09efd3e2e589b4961f1b32ba353a7e62","source_identity":"artifact:solo-pi-jev-test-failure-priority"} -->
```markdown
# Public failure has priority over review-format uncertainty

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-test-failure-priority`
- Role: `spec`
- Standalone: true

### Children
- [SPB-12](../tickets/solo-pi-jev-luna-pilot/12-fix-test-review-priority.md)

## Observed cause / mandate
SPB-11 real cell r4: public test exit2 with concrete TypeScript compilation failures; review
includes valid blocker and a directory-only `tests` finding, therefore state unparsed. Current
controller gates review-format before treating known failed tests as a quality failure: no fix
turn, failures0. This prevents evaluating repair behavior, not a missing human decision.
Covered by current explicit arm fix/retest mandate, original cumulative financial budget.

## Minimal contract change
Only unresolved-format + tests-passed continues to be a human gate. Known completed failed
public tests continue the ordinary bounded quality-failure/fix path even if review unparsed.
Capture/cleanup uncertainty and readonly mutation gates retain priority. Keep original prose,
partial findings and exact bound receipt; never relabel review clean or adjudicate test failure
with Jev/judge. No hidden feedback, auto-approval or quality cap changes.
Review role must request concrete relative file:line markers (directory-wide missing-test
finding anchors nearest existing file); no parser changes or synthetic findings. Normalization
is instruction clarity only; genuinely unparsed green-test review remains a gate.

## Causal validation
Same actual Git/test fixture: bad public code plus directory finding => failed3 with ordinary
fix turns and no external coverage calls; green code plus same malformed format => gate0.
Changed controller/repair shards and current frozen selected contrast; prior Budget unchanged,
no model calls in local tests. New live cell uses full prior account and distinct source;
valid model failures remain results, not grounds for repeated score hunting.

```
