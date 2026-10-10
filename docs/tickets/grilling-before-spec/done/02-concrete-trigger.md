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
