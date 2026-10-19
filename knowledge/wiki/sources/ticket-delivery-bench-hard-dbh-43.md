---
type: source
title: "DBH-43 — Condizione del `/goal` senza la premessa «TASK.md ha cambiado»"
identity_key: ticket:delivery-bench-hard/DBH-43
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/43-goal-condition-premise.md
source_digest: sha256:532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-08
created_provenance: git-commit
disposition_changed: 2026-10-10
disposition_changed_provenance: git-rename
---

# DBH-43 — Condizione del `/goal` senza la premessa «TASK.md ha cambiado»

Compiled from `docs/tickets/delivery-bench-hard/done/43-goal-condition-premise.md`. Identity is `ticket:delivery-bench-hard/DBH-43`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-08** via `git-commit`
- Disposition changed: **2026-10-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-chain-12]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-39]] — `ticket:delivery-bench-hard/DBH-39`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-43.md","payload_bytes":2997,"payload_sha256":"532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c"}],"payload_bytes":2997,"payload_sha256":"532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c","schema":1,"source_digest":"sha256:532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c","source_identity":"ticket:delivery-bench-hard/DBH-43","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2997,"payload_sha256":"532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c","schema":1,"source_digest":"sha256:532bb43e33f5185fa146ef9deac1b131b7978ab88cdbf60c9c4c9e523725c64c","source_identity":"ticket:delivery-bench-hard/DBH-43"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-43"
execution_mode: AFK
blocked_by:
  - "DBH-39"
---

# DBH-43 — Condizione del `/goal` senza la premessa «TASK.md ha cambiado»

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:43`
- Role: `ticket`
- Parent: [delivery-bench-hard-chain-12.md](../../../specs/delivery-bench-hard-chain-12.md)

## Parent Spec
[delivery-bench-hard-chain-12.md](../../../specs/delivery-bench-hard-chain-12.md), Failure modes e
Verification: difetto del banco trovato nel report di DBH-36.

## What to Build
Dalla richiesta 2 in poi, `NEXT_GOAL_CONDITION` in `runner.py` inizia con «TASK.md ha cambiado:
ahora contiene un encargo nuevo, distinto del anterior». Il valutatore la tratta come un requisito
da provare. Il modello rilegge TASK.md, trova il compito che ha appena finito e lo dice; il
valutatore lo rimanda indietro. In `dbh-chain12` succede in 1.118 dei 1.500 verdetti «not yet met»
(fino a 469 giri in un tentativo, poi timeout). Nelle catene da 4 succede meno (luna3d pi-full 40
su 55).

La premessa resta nel prompt (`NEXT_PROMPT`, che serve contro DBH-25); la condizione del goal dice
solo cosa deve essere vero alla fine: «Lo que pide ahora TASK.md … esta hecho por completo …».

## Acceptance Criteria
- [x] `NEXT_GOAL_CONDITION` non afferma che TASK.md è cambiato; `NEXT_PROMPT` resta com'è.
- [x] Un test in `test_runner.py` fissa che la condizione della richiesta 2+ non contiene
      «ha cambiado» né «distinto».
- [x] Il report del primo lotto dopo la correzione riporta la stessa misura (verdetti che
      incolpano un TASK.md non cambiato), attesa vicina a zero.

## Evidence
- `runner.py`: `NEXT_GOAL_CONDITION` = `GOAL_CONDITION` con «Lo que pide ahora»; la premessa resta
  solo in `NEXT_PROMPT`. `test_runner.py` lo fissa; suite `test_runner` 67 test OK.
- Fatto dopo la fine di `dbh-vague` (2026-10-08T23:54Z).
- Criterio 3, lotto `dbh-crew3` (2026-10-10, `results/dbh-crew3/report.md` nel repo privato): 49
  verdetti, 13 «not met», **0** che incolpano un TASK.md non cambiato (in `dbh-chain12` erano 1.118
  su 1.500).

## Frontier
Fatto.

## Gates
- **Attempt:** una PR su `agent-skills` con CI verde, fatta dopo la fine di `dbh-vague` e prima di
  `dbh-crew3` (DBH-42).
- **Budget:** nessuna spesa; solo test locali e CI. **Time:** 2 ore. **Maximum attempts:** 2.
- **Approvals:** l'agente fa il merge con CI verde (regola dei ticket DBH).
- **Exact version:** il commit di `main` che contiene la correzione; `dbh-crew3` lo registra in
  `lot.json`.
- **Existing blocks searched:** un solo lotto alla volta; il checkout principale non si aggiorna
  durante un lotto (memoria `dbh-chain12-gates`).

## Step-by-Step Implementation Plan
1. Test che fallisce sulla condizione attuale.
2. Nuova `NEXT_GOAL_CONDITION`.
3. Suite `test_runner`.

## Testing Plan
- `python -B -m unittest test_runner` in `benchmarks/delivery-bench`.

## Out of Scope
- Rifare i lotti già chiusi; i loro numeri restano con questa nota.

```
