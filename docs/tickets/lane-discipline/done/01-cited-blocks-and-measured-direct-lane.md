---
ticket_schema: 1
ticket_id: "LD-01"
execution_mode: AFK
blocked_by: []
---

# LD-01 — Blocchi citati e percorso diretto misurato

## Artifact Graph
- Artifact ID: `ticket:lane-discipline:01`
- Role: `ticket`
- Parent: [lane-discipline.md](../../../specs/lane-discipline.md)

## Parent Spec
[lane-discipline.md](../../../specs/lane-discipline.md), Decisioni 1 e 2.

## What to Build
La policy obbligatoria e la mappa di `ask-skills` dicono:
- prima di fermarsi per un blocco, l'agente ne cita la fonte; quello che non sa citare non è
  un gate; una decisione mancante si chiede una volta, senza ripeterla a un loop;
- il percorso diretto conta anche i test, si misura prima del commit, passa a skills-only
  quando sfora e non vale mai per soldi, autenticazione e permessi, cancellazione di dati.

## Acceptance Criteria
- [x] La voce 2 di `extensions/mandatory-agent-skills.ts` dice: test compresi, misura con
      `git diff --stat` prima del commit, nessun commit come diretto oltre i limiti, passaggio
      a `execute-ticket`, esclusione di soldi, autenticazione e permessi, cancellazione di dati.
- [x] La voce 8 contiene la regola del blocco citato.
- [x] `ask-skills/SKILL.md` e `README.md` descrivono il percorso diretto allo stesso modo.
- [x] `extensions/mandatory-agent-skills.test.ts` controlla le frasi nuove; le asserzioni
      esistenti restano vere.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa a pagamento, nessun limite di tempo o di tentativi, nessuna
versione esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`, poi pin,
`update:personal` e reload.

## Step-by-Step Implementation Plan
1. Voce 2 e voce 8 di `mandatory-agent-skills.ts`.
2. Le frasi nuove nei test.
3. `ask-skills/SKILL.md` e `README.md`.

## Testing Plan
- `node --test extensions/mandatory-agent-skills.test.ts`
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py ticket-autopilot/tests/test_context_budget.py -q`
- `npm run -s lint`

## Out of Scope
- `goal.ts`, Autopilot, `OPERATING-DEFAULTS.md`.
