---
type: source
title: "DBH-40 — Skill crew-delivery"
identity_key: ticket:delivery-bench-hard/DBH-40
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/40-crew-delivery-skill.md
source_digest: sha256:777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-08
created_provenance: git-commit
disposition_changed: 2026-10-08
disposition_changed_provenance: git-rename
---

# DBH-40 — Skill crew-delivery

Compiled from `docs/tickets/delivery-bench-hard/done/40-crew-delivery-skill.md`. Identity is `ticket:delivery-bench-hard/DBH-40`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-08** via `git-commit`
- Disposition changed: **2026-10-08** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-crew-isolated]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-40.md","payload_bytes":2752,"payload_sha256":"777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9"}],"payload_bytes":2752,"payload_sha256":"777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9","schema":1,"source_digest":"sha256:777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9","source_identity":"ticket:delivery-bench-hard/DBH-40","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2752,"payload_sha256":"777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9","schema":1,"source_digest":"sha256:777f2a6bc8af60d0dfe8dee1060ffed31995e1066b3f0a19309dd57d01eca0b9","source_identity":"ticket:delivery-bench-hard/DBH-40"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-40"
execution_mode: AFK
blocked_by: []
---

# DBH-40 — Skill crew-delivery

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:40`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-isolated.md](../../../specs/delivery-bench-hard-crew-isolated.md)

## Parent Spec
[delivery-bench-hard-crew-isolated.md](../../../specs/delivery-bench-hard-crew-isolated.md), Decisions 2–7 e Target behavior 1.

## What to Build
Una skill `crew-delivery` in `agent-skills` che fa lavorare una Crew come un team umano:
PM (spec, ticket, coda di merge), developer nel proprio worktree con `execute-ticket`
(skills-only), reviewer con `code-review` e QA del ciclo, principale toccato solo dalla coda di
merge fast-forward e protetto da un hook `pre-commit`. `ask-skills` la instrada quando c'è già
una Crew o più Pi sullo stesso progetto.

## Acceptance Criteria
- [x] `crew-delivery/SKILL.md` con i ruoli PM, developer e reviewer, entro il limite di righe.
- [x] `ask-skills` la instrada senza superare il suo limite di righe.
- [x] Test del grafo delle skill aggiornati e verdi; CI verde.

## Evidence
- `crew-delivery/SKILL.md` (67 righe) e `crew-delivery/agents/openai.yaml`:
  - tabella dei ruoli PM, developer e reviewer, ciascuno con le sue skill;
  - worktree `../<repo-folder>-worktrees/<ticket-id>` su branch `crew/<ticket-id>`;
  - hook `pre-commit` che rifiuta i commit su `main`;
  - coda di merge: rebase, test, `merge --ff-only`, rimozione del worktree; con un conflitto
    il ticket torna al developer;
  - review separata che non modifica; ticket bloccato riscritto dal PM, stop al secondo
    blocco;
  - QA del ciclo sul principale; nessuna attesa di ACK; non crea deleghe da sola.
- `ask-skills` la instrada (2 righe; limite portato da 92 a 94 in `scripts/file-limits.json` e
  nel test); `docs/model-invocation-policy.md` la classifica `model-invocable`.
- `ticket-autopilot/tests/test_crew_delivery_skill.py` (5 test) più `test_skill_graph`,
  `test_model_invocation_policy`, `test_readme_dependencies`, `test_skill_examples`,
  `test_progressive_references`: 54 test OK; `check_file_limits.py` 1087/1300 righe.

## Frontier
Fatto.

## Gates
Come la spec: una PR con CI verde e merge con `--match-head-commit`; nessun tetto di spesa;
24 ore per tentativo, al massimo 2 tentativi. L'installazione avviene solo tra due lotti.

## Step-by-Step Implementation Plan
1. Test del grafo rossi per la skill nuova e il suo instradamento.
2. Scrivere la skill; aggiornare `ask-skills`, il README e i limiti dei file.
3. Suite delle skill e lint.

## Testing Plan
- `ticket-autopilot/tests/test_skill_graph.py` e i test dei limiti; CI.

## Out of Scope
- Il braccio del banco (DBH-41) e il lotto (DBH-42).

```
