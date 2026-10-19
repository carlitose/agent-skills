---
type: source
title: "IB-04 — Senza remote il target è il ramo locale"
identity_key: ticket:invented-blocks-bench/IB-04
identity_strength: stable
source_path: docs/tickets/invented-blocks-bench/done/04-no-remote-is-not-a-block.md
source_digest: sha256:8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-11
created_provenance: git-commit
disposition_changed: 2026-10-12
disposition_changed_provenance: git-rename
---

# IB-04 — Senza remote il target è il ramo locale

Compiled from `docs/tickets/invented-blocks-bench/done/04-no-remote-is-not-a-block.md`. Identity is `ticket:invented-blocks-bench/IB-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-11** via `git-commit`
- Disposition changed: **2026-10-12** via `git-rename`

## Graph

- Parent source: [[sources/artifact-invented-blocks-bench]]
- Blocked by: [[sources/ticket-invented-blocks-bench-ib-01]] — `ticket:invented-blocks-bench/IB-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-invented-blocks-bench-ib-04.md","payload_bytes":1431,"payload_sha256":"8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a"}],"payload_bytes":1431,"payload_sha256":"8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a","schema":1,"source_digest":"sha256:8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a","source_identity":"ticket:invented-blocks-bench/IB-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1431,"payload_sha256":"8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a","schema":1,"source_digest":"sha256:8ea988e86251276168793ee610fe306c2e665179283a02999363aac1e297018a","source_identity":"ticket:invented-blocks-bench/IB-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "IB-04"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-04 — Senza remote il target è il ramo locale

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:04`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../../specs/invented-blocks-bench.md), Risultati della prima misura.

## What to Build
In `execute-ticket/references/skills-only.md`, passo 2 dell'ammissione: un repository senza remote
non ha un target remoto; il target è il ramo locale, e questo non è un blocco.

## Acceptance Criteria
- [x] La frase è nel contratto; un test in `test_skill_graph.py` la verifica.
- [x] Pin in `pi-personal-config` e `update:personal` verificato.

## Evidence
- agent-skills #470 (`2b2ab3b`): `skills-only.md` passo 2 e
  `test_skills_only_without_a_remote_targets_the_local_branch`; pin in pi-personal-config #77.
- `goal-prerequisite` nelle misure dopo IB-04: nessuno stop su «niente remote»; 3/3 in
  `after-final4`.

## Frontier
Fatto.

## Gates
Come la spec: merge con CI verde, pin, `update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Frase e test. 2. PR, merge, pin, installazione. 3. Rimisura con `block-bench`.

## Testing Plan
- `test_skill_graph.py`; rimisura di `goal-prerequisite`.

## Out of Scope
- Il resto dell'ammissione skills-only.

```
