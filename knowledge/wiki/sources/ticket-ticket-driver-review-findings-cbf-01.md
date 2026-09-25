---
type: source
title: "CBF-01 — Recognize prose findings safely"
identity_key: ticket:ticket-driver-review-findings/CBF-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-review-findings/01-recognize-prose-findings-safely.md
source_digest: sha256:1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-24
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# CBF-01 — Recognize prose findings safely

Compiled from `docs/tickets/ticket-driver-review-findings/01-recognize-prose-findings-safely.md`. Identity is `ticket:ticket-driver-review-findings/CBF-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-24** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-review-findings]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-review-findings-cbf-01.md","payload_bytes":2562,"payload_sha256":"1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa"}],"payload_bytes":2562,"payload_sha256":"1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa","schema":1,"source_digest":"sha256:1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa","source_identity":"ticket:ticket-driver-review-findings/CBF-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2562,"payload_sha256":"1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa","schema":1,"source_digest":"sha256:1ba4e4f0a995372309b60077eb6bc4ef855126f2a0422b92d172057e51cda9fa","source_identity":"ticket:ticket-driver-review-findings/CBF-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CBF-01"
execution_mode: AFK
blocked_by: []
---

# CBF-01 — Recognize prose findings safely

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-review-findings-01`
- Role: `ticket`
- Parent: [ticket-driver-review-findings.md](../../specs/ticket-driver-review-findings.md)

## Parent Spec
[ticket-driver-review-findings.md](../../specs/ticket-driver-review-findings.md)

## What to Build
In `ticket-driver/scripts/findings.py` and the reviewer prompt, recognize explicit severity/path/explanation review lines in the three observed prose forms while keeping malformed or contradictory review text fail-closed. The parser is shared by c1b, c2 and risk-directed review; do not relax safety or alter the QA-command limit.

## Acceptance Criteria
- [ ] Canonical lines and structurally representative variants from c1b-r1/r2/r3 produce findings with original severity, first source path, original line or `None`, and nonempty text.
- [ ] A blocker found in a bold, multi-path line still triggers the existing blocker path. Multiple findings preserve order and no severity is silently dropped.
- [ ] Fenced examples and `No blockers` never become findings or `clean`; exact `No findings.` is clean only without any severity marker, and a malformed marked line remains `unparsed` even when a clean marker or another valid finding is present.
- [ ] Prompt allows normal prose but asks reviewers to use explicit severity/path/explanation lines or `No findings.`; it does not request JSON or a status schema.
- [ ] RED/GREEN causal tests, shared c1b/c2/c3 suites and the admitted local quick profile pass; no live c1b rerun is inferred from tests.

## Frontier
Ready. User explicitly requested fixing c1b. No benchmark retry is authorized by this ticket.

## Step-by-Step Implementation Plan
1. Freeze synthetic structural examples of the three review artifacts and ambiguous cases in unit tests; demonstrate RED.
2. Update parser and reviewer prompt minimally; preserve closed-on-uncertainty behavior and canonical output shape.
3. Run focused suites and admitted profile; review exact diff, QA and validate a standalone verification bundle.

## Testing Plan
Run focused parser/c1b/c2/c3 tests, graph audit and applicable local quick profile. No Jev or model network call is required. Retain failures and limitations in verification record.

## Out of Scope
- Rerunning c1b/c2b, changing old receipts, resolving c2b retry uncertainty or oversized QA plan, altering ticket-autopilot, Jev billing, authorization, or provider policy.

```
