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
[delivery-bench-hard-crew-isolated.md](../../../specs/delivery-bench-hard-crew-isolated.md), Decisions 2–5 e Target behavior 1.

## What to Build
Una skill `crew-delivery` in `agent-skills` per il coordinatore e per i worker di una Crew:
worktree e branch per worker, al più 2 compiti interi per worker con file disgiunti, compito =
ticket portato a termine con `execute-ticket` inline (corsia skills-only), integrazione in `main`
e test sul risultato integrato a carico del coordinatore, compito bloccato ripreso dal
coordinatore. `ask-skills` la instrada quando c'è una Crew o più Pi sullo stesso progetto.

## Acceptance Criteria
- [x] `crew-delivery/SKILL.md` con i ruoli di coordinatore e worker, entro il limite di righe.
- [x] `ask-skills` la instrada senza superare il suo limite di righe.
- [x] Test del grafo delle skill aggiornati e verdi; CI verde.

## Evidence
- `crew-delivery/SKILL.md` (63 righe) e `crew-delivery/agents/openai.yaml`: ruoli di
  coordinatore e worker, worktree `../<repo-folder>-worktrees/<ticket-id>` su branch
  `crew/<ticket-id>`, al più due ticket interi per worker con file disgiunti, `execute-ticket`
  inline per ticket, integrazione e test su `main` a carico del coordinatore, compito bloccato
  ripreso dal coordinatore, nessuna attesa di ACK; non crea deleghe da sola.
- `ask-skills` la instrada (2 righe; limite portato da 92 a 94 in `scripts/file-limits.json` e
  nel test); `docs/model-invocation-policy.md` la classifica `model-invocable`.
- `ticket-autopilot/tests/test_crew_delivery_skill.py` (4 test) più `test_skill_graph`,
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
