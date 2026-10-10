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
- Parent: [grilling-before-spec.md](../../specs/grilling-before-spec.md)

## Parent Spec
[grilling-before-spec.md](../../specs/grilling-before-spec.md), Correzione (GBS-02).

## What to Build
`ask-skills`: «se puoi chiedere all'utente e la richiesta non dice il comportamento esatto,
`grilling -> to-spec`: una lettura naturale è un'ipotesi». `grilling`, *Before a spec*: un
comportamento non scritto è aperto anche se una lettura sembra naturale, con un esempio.

## Acceptance Criteria
- [ ] Le due frasi sono nei file installati; `ask-skills/SKILL.md` resta entro 94 righe; test e CI verdi.
- [ ] Pin in `pi-personal-config` e `update:personal` verificato.
- [ ] Nuovo lotto vago per pi-full lanciato con queste skill.

## Frontier
Pronto.

## Gates
Come la spec: merge con CI verde, pin, `update:personal` e reload da parte dell'agente; il lotto
vago è autorizzato dall'utente («fallo», «2»), 5 celle alla volta a priorità bassa.

## Step-by-Step Implementation Plan
1. Frasi e test. 2. PR, merge, pin, installazione. 3. Lotto.

## Testing Plan
- `test_skill_graph.py`, limiti di righe; suite completa alla CI.

## Out of Scope
- Cambiare `to-spec` o il simulatore.
