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
- Parent: [delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md)

## Parent Spec
[delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md), Decisions 2–5 e Target behavior 1.

## What to Build
Una skill `crew-delivery` in `agent-skills` per il coordinatore e per i worker di una Crew:
worktree e branch per worker, al più 2 compiti interi per worker con file disgiunti, compito =
ticket portato a termine con `execute-ticket` inline (corsia skills-only), integrazione in `main`
e test sul risultato integrato a carico del coordinatore, compito bloccato ripreso dal
coordinatore. `ask-skills` la instrada quando c'è una Crew o più Pi sullo stesso progetto.

## Acceptance Criteria
- [ ] `crew-delivery/SKILL.md` con i ruoli di coordinatore e worker, entro il limite di righe.
- [ ] `ask-skills` la instrada senza superare il suo limite di righe.
- [ ] Test del grafo delle skill aggiornati e verdi; CI verde.

## Frontier
Pronto.

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
