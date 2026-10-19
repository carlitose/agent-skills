---
type: source
title: "GBS-02 — Condizione concreta per `grilling -> to-spec`"
identity_key: ticket:grilling-before-spec/GBS-02
identity_strength: stable
source_path: docs/tickets/grilling-before-spec/done/02-concrete-trigger.md
source_digest: sha256:9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-10
created_provenance: git-commit
disposition_changed: 2026-10-10
disposition_changed_provenance: git-rename
---

# GBS-02 — Condizione concreta per `grilling -> to-spec`

Compiled from `docs/tickets/grilling-before-spec/done/02-concrete-trigger.md`. Identity is `ticket:grilling-before-spec/GBS-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-10** via `git-commit`
- Disposition changed: **2026-10-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-grilling-before-spec]]
- Blocked by: [[sources/ticket-grilling-before-spec-gbs-01]] — `ticket:grilling-before-spec/GBS-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-grilling-before-spec-gbs-02.md","payload_bytes":1900,"payload_sha256":"9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26"}],"payload_bytes":1900,"payload_sha256":"9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26","schema":1,"source_digest":"sha256:9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26","source_identity":"ticket:grilling-before-spec/GBS-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1900,"payload_sha256":"9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26","schema":1,"source_digest":"sha256:9602cbc0192fa8e38bc35b705147e9f20ab118671c03271bdcf23afdf4d28d26","source_identity":"ticket:grilling-before-spec/GBS-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "GBS-02"
execution_mode: AFK
blocked_by:
  - "GBS-01"
---

# GBS-02 — Condizione concreta per `grilling -> to-spec`

## Artifact Graph
- Artifact ID: `ticket:grilling-before-spec:02`
- Role: `ticket`
- Parent: [grilling-before-spec.md](../../../specs/grilling-before-spec.md)

## Parent Spec
[grilling-before-spec.md](../../../specs/grilling-before-spec.md), Correzione (GBS-02).

## What to Build
`ask-skills`: «se puoi chiedere all'utente e la richiesta non dice il comportamento esatto,
`grilling -> to-spec`: una lettura naturale è un'ipotesi». `grilling`, *Before a spec*: un
comportamento non scritto è aperto anche se una lettura sembra naturale, con un esempio.

## Acceptance Criteria
- [x] Le due frasi sono nei file installati; `ask-skills/SKILL.md` resta entro 94 righe; test e CI verdi.
- [x] Pin in `pi-personal-config` e `update:personal` verificato.
- [x] Nuovo lotto vago per pi-full lanciato con queste skill.

## Evidence
- agent-skills #467 (`0d6955b`), CI 8/8; `pi-personal-config` #76 (`0fc46db`): test:package 6/6,
  updater 32/32; `update:personal` verificato.
- Lotto `dbh-vague3` (privato, 2026-10-10 16:15Z → 21:46Z, solo pi-full, 9 celle): `grilling` letto in 9 celle su 9;
  accettate **12/36** contro 5/36 di `dbh-vague`; richiesta 4 da 0/9 a 3/9; 50 domande, nessuna su gate o
  budget; 8.05 $ di listino. Le richieste precise restano a 29/36: una sola misura, 3 ripetizioni.

## Frontier
Fatto.

## Gates
Come la spec: merge con CI verde, pin, `update:personal` e reload da parte dell'agente; il lotto
vago è autorizzato dall'utente («fallo», «2»), 5 celle alla volta a priorità bassa.

## Step-by-Step Implementation Plan
1. Frasi e test. 2. PR, merge, pin, installazione. 3. Lotto.

## Testing Plan
- `test_skill_graph.py`, limiti di righe; suite completa alla CI.

## Out of Scope
- Cambiare `to-spec` o il simulatore.

```
