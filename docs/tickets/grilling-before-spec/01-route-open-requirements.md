---
ticket_schema: 1
ticket_id: "GBS-01"
execution_mode: AFK
blocked_by: []
---

# GBS-01 — Requisiti aperti: `grilling -> to-spec`

## Artifact Graph
- Artifact ID: `ticket:grilling-before-spec:01`
- Role: `ticket`
- Parent: [grilling-before-spec.md](../../specs/grilling-before-spec.md)

## Parent Spec
[grilling-before-spec.md](../../specs/grilling-before-spec.md), Decision e Verification.

## What to Build
In `ask-skills/SKILL.md`: una richiesta i cui requisiti aperti cambierebbero il risultato o i suoi
test, quando qualcuno può rispondere, passa per `grilling -> to-spec`. In `grilling/SKILL.md`: la
sezione *Before a spec* con le regole di stop della spec.

## Acceptance Criteria
- [ ] `ask-skills` ha la rotta `grilling -> to-spec`, e una richiesta completa resta `to-spec`.
- [ ] `grilling` ha *Before a spec*: solo requisiti; niente processo; niente domande già risolte o
      senza effetto; assunzione senza risposta; nessun giro di conferma separato.
- [ ] `ask-skills/SKILL.md` resta entro il limite di righe; test e CI verdi.
- [ ] Pin in `pi-personal-config` e `update:personal` verificato.

## Frontier
Pronto.

## Gates
Come la spec: il lavoro fino all'installazione; merge con CI verde, pin, `update:personal` e reload
da parte dell'agente; nessun lotto.

## Step-by-Step Implementation Plan
1. `ask-skills`, `grilling`, test.
2. PR e merge; pin e installazione.

## Testing Plan
- `test_skill_graph.py`, `test_change_status_skill.py`, limiti di righe; suite completa alla CI.

## Out of Scope
- Rifare il lotto vago.
