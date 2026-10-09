---
ticket_schema: 1
ticket_id: "GQ-01"
execution_mode: AFK
blocked_by: []
---

# GQ-01 — Gate di default, senza domande

## Artifact Graph
- Artifact ID: `ticket:gates-without-questions:01`
- Role: `ticket`
- Parent: [gates-without-questions.md](../../../specs/gates-without-questions.md)

## Parent Spec
[gates-without-questions.md](../../../specs/gates-without-questions.md), Decision 1-4 e Verification.

## What to Build
In `to-spec/SKILL.md` la sezione su `## Gates` riempie ogni gate con un default invece di
chiederla. Chiede solo un'approvazione `open` che il lavoro richiede o un blocco in contrasto, e
dice che un limite scelto dall'agente non è una gate. In `to-tickets/SKILL.md` il passo 3 copia
le gate senza chiedere quelle mancanti. Un test di testo lo fissa.

## Acceptance Criteria
- [x] `to-spec` elenca i default e non chiede più tutte le gate in un giro.
- [x] `to-spec` vieta di fermarsi su un limite scelto dall'agente o di chiedere di estenderlo.
- [x] `to-tickets` non chiede più le gate mancanti prima di emettere i ticket.
- [x] Il test delle skill e il controllo dei limiti di righe passano; CI verde.

## Evidence
- `to-spec/SKILL.md`: default per ogni gate, domanda solo per un'approvazione `open` necessaria o un
  blocco in contrasto, «A limit the agent chose itself is not a gate».
- `to-tickets/SKILL.md` passo 3: copia le gate e riempie le mancanti con i default di `to-spec`.
- `test_gates_take_defaults_instead_of_questions` falliva prima della modifica; ora
  `test_skill_graph.py` 30 passati; limiti di righe ok (to-spec 80/150, to-tickets 114/115).
- CI sulla head esatta verificata prima della merge.

## Frontier
Fatto.

## Gates
Come la spec: il lavoro fino alla merge, nessun budget, tempo o tentativo massimo fissato; merge
con CI verde da parte dell'agente, poi pin, `update:personal` e reload.

## Step-by-Step Implementation Plan
1. Test che fallisce in `ticket-autopilot/tests/test_skill_graph.py`.
2. Testo di `to-spec` e `to-tickets`.
3. Test delle skill, limiti di righe.

## Testing Plan
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py`; `scripts/check_file_limits.py`.

## Out of Scope
- Runner, `/goal`, banco.
