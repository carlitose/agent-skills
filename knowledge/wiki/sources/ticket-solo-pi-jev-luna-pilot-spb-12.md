---
type: source
title: "SPB-12 — Test fallito non bloccato da review-format"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-12
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/12-fix-test-review-priority.md
source_digest: sha256:5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-12 — Test fallito non bloccato da review-format

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/12-fix-test-review-priority.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-12`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-test-failure-priority]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-10]] — `ticket:solo-pi-jev-luna-pilot/SPB-10`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-12.md","payload_bytes":2047,"payload_sha256":"5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb"}],"payload_bytes":2047,"payload_sha256":"5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb","schema":1,"source_digest":"sha256:5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-12","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2047,"payload_sha256":"5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb","schema":1,"source_digest":"sha256:5be7ddb4302dd833dfb68828db8d834e54b9f48c525e25186ec2723cdec76bcb","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-12"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-12"
execution_mode: AFK
blocked_by:
  - "SPB-10"
---

# SPB-12 — Test fallito non bloccato da review-format

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-12`
- Role: `ticket`
- Parent: [Test failure priority](../../specs/solo-pi-jev-test-failure-priority.md)

## Parent Spec
[Test failure priority](../../specs/solo-pi-jev-test-failure-priority.md).

## What to Build
Minimal precedence repair: known public failure reaches bounded fix even with unparsed review;
green-test unparsed review still gates. Clarify concrete-file review format without parser change.

## Acceptance Criteria
- [ ] Known failed public test + unparsed review reaches quality failure/fix, preserves receipts/prose/partial findings and no external approval.
- [ ] Green tests + unparsed review still gates0; capture/readonly and ordinary blocker/NO/uncertainty/quality3 remain unchanged.
- [ ] Role instructions require concrete relative file marker; no parser, threshold, hidden/product intervention or historical mutations.
- [ ] Causal RED/GREEN and frozen controller/repair contrasts with substituted ports, inline review/QA/audit and handoff; no live calls in repair.

## Frontier
Ready: SPB-10 complete; SPB-11 real gated cell r4 is causal evidence, not completed dependency.
Current explicit repair-loop mandate covers local repair/retest.

## Step-by-Step Implementation Plan
1. Canonical admission and causal failing test.
2. Minimal conditional/prompt change, targeted regression and frozen quality/handoff.
3. Subsequent distinct live trial retains all prior budget/history.

## Testing Plan
Actual Git/public process and fake peer/semantic ports; failed-versus-green review-format contrast,
controller/repair regressions. No Budget or model suite replay.

## Out of Scope
Parser expansion, review relabel/auto-approval, question/policy/quality limit changes, product
intervention, historical/source/ledger reset, live launches inside repair, delegation/runner,
commit/push/PR/merge/install/reload/wiki sync.

```
