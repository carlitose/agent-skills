---
ticket_schema: 1
ticket_id: "EG-01"
execution_mode: AFK
blocked_by: []
---

# EG-01 — `## Gates` chiesti e scritti in spec e ticket

## Artifact Graph
- Artifact ID: `ticket:explicit-gates:01`
- Role: `ticket`
- Parent: [explicit-gates.md](../../specs/explicit-gates.md)

## Parent Spec
[explicit-gates.md](../../specs/explicit-gates.md), Decisione 1.

## What to Build
`to-spec` e `to-tickets` chiedono all'utente, in un solo giro e mentre scrivono, i gate del
lavoro, e li scrivono in una sezione `## Gates` della spec e di ogni ticket:
- tentativo;
- budget e tempo per tentativo;
- tentativi massimi;
- approvazioni;
- eventuale versione esatta;
- blocchi già nel codice, cercati prima.

Un gate senza risposta resta `open` e il ticket ha la frontiera "decisione umana richiesta".

## Acceptance Criteria
- [ ] `to-spec/SKILL.md` richiede la sezione `## Gates` in ogni spec, con i sei elementi, la
      ricerca dei blocchi esistenti e la domanda all'utente in un solo giro.
- [ ] Il modello del corpo ticket in `to-tickets/SKILL.md` contiene `## Gates`, che riprende i
      gate della spec applicabili più quelli propri del ticket. Un gate aperto rende la frontiera
      una decisione umana.
- [ ] `to-tickets/SKILL.md` resta entro il suo limite di 115 righe; `test_skill_graph.py` passa.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa esterna, nessun limite di tempo o di tentativi, nessuna versione
esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`. Blocco esistente: limite di 115
righe di `to-tickets/SKILL.md`.

## Step-by-Step Implementation Plan
1. `to-spec`: aggiungere la regola `## Gates` ai Defaults e una voce nei Quality checks.
2. `to-tickets`: aggiungere `## Gates` al corpo del ticket e una frase sul gate aperto, poi
   compattare altrove per restare entro le 115 righe.

## Testing Plan
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`
- `npm run -s lint`

## Out of Scope
- Budget per tentativo e legami di versione nelle altre skill (EG-02).
