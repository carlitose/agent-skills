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
