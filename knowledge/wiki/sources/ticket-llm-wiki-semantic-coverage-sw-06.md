---
type: source
title: "Repair evidence-backed historical gate causes"
identity_key: ticket:llm-wiki-semantic-coverage/SW-06
identity_strength: stable
source_path: docs/tickets/llm-wiki-semantic-coverage/06-repair-evidence-backed-gate-causes.md
source_digest: sha256:0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Repair evidence-backed historical gate causes

Compiled from `docs/tickets/llm-wiki-semantic-coverage/06-repair-evidence-backed-gate-causes.md`. Identity is `ticket:llm-wiki-semantic-coverage/SW-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-semantic-coverage-sw-05]] — `ticket:llm-wiki-semantic-coverage/SW-05`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-semantic-coverage-sw-06.md","payload_bytes":3870,"payload_sha256":"0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a"}],"payload_bytes":3870,"payload_sha256":"0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a","schema":1,"source_digest":"sha256:0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a","source_identity":"ticket:llm-wiki-semantic-coverage/SW-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3870,"payload_sha256":"0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a","schema":1,"source_digest":"sha256:0b448aa1cde07338f2d5501481ce2070ce37f3b16989e867be6175dead78d46a","source_identity":"ticket:llm-wiki-semantic-coverage/SW-06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SW-06"
execution_mode: HITL
blocked_by:
  - "SW-05"
---

# Repair evidence-backed historical gate causes

## Artifact Graph
- Artifact ID: `artifact:sw-06-repair-evidence-backed-gate-causes`
- Role: `ticket`
- Parent: [LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Parent Spec
[LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## What to Build
Define and perform only evidence-backed repair for still-open historical stage gates whose persisted reason is generic. Before any external ledger mutation, require the human to identify the exact repository, run, gate ID, replacement reason, actor, and durable evidence. Validate the current gate record and ledger identity, preserve the predecessor reason and evidence in append-only history, and use the canonical gate-reason refresh boundary rather than editing JSON directly.

If the evidence cannot establish a precise current cause, retain the generic reason and record it as legacy/unknown; do not infer a cause from nearby specs, ticket prose, or the historical Delayed Shadow pivot. Closed historical gates need no mutation merely to improve prose.

The reported NightDAX ticket 25 and old compiler ticket 72 are candidates, not authorization or verified identities. This ticket must stop at its HITL gate until exact inputs are supplied.

## Acceptance Criteria
- [ ] Canonical `grilling` obtains one explicit decision at a time for repository identity, run, gate, replacement cause, actor, and durable evidence.
- [ ] The target ledger is read and validated before any mutation; repository/run/gate mismatches fail closed.
- [ ] Only an open stage gate with the exact observed predecessor reason is eligible for refresh.
- [ ] Repair uses the canonical command/API under the run lock and appends evidence-bound history; direct ledger-file edits are forbidden.
- [ ] The refreshed `status` output shows the exact new reason and preserves the old reason in audited history.
- [ ] Replay with identical evidence is idempotent; conflicting or stale evidence fails without another mutation.
- [ ] Gates lacking sufficient evidence remain explicitly legacy/unknown and are not resolved, approved, or closed.
- [ ] A durable repair report distinguishes repaired, unchanged-unknown, closed-historical, and unavailable targets without claiming access that was not observed.

## Frontier
HITL and dependency-blocked on `SW-05`. It additionally requires exact external repository/run/gate identity and durable human evidence. The current request authorizes starting the run and merging eligible repository work; it does not provide those missing historical facts.

## Step-by-Step Implementation Plan
1. After `SW-05` integrates, invoke `grilling` for the exact target identity and evidence, one question at a time.
2. Read status and the validated ledger through canonical commands; compare the observed open gate with the supplied predecessor.
3. Refresh only exact eligible records under lock, then read back status and append-only history.
4. Record a durable outcome report in the owning repository and update this map only with verified evidence.

## Testing Plan
Before a live repair, use a disposable ledger fixture to prove exact-match mutation, idempotent replay, stale predecessor rejection, wrong repository/run/gate rejection, closed-gate rejection, and status readback. Any live operation is limited to the exact supplied repository and evidence and must report unavailable boundaries.

## Out of Scope
- Inferring NightDAX paths, run IDs, gate IDs, or causes.
- Repairing closed historical gates for cosmetic consistency.
- Resolving, approving, or closing a gate.
- Publishing the eight untracked source documents.
- Treating repository-wide merge authority as ledger-repair authority.

```
