---
ticket_schema: 1
ticket_id: "EG-02"
execution_mode: AFK
blocked_by: []
---

# EG-02 — Budget e tempo per tentativo, nessun legame di versione

## Artifact Graph
- Artifact ID: `ticket:explicit-gates:02`
- Role: `ticket`
- Parent: [explicit-gates.md](../../specs/explicit-gates.md)

## Parent Spec
[explicit-gates.md](../../specs/explicit-gates.md), Decisioni 2 e 3.

## What to Build
Le skill trattano budget e tempo per tentativo, come li definisce `## Gates`:
- un nuovo tentativo parte con budget e tempo pieni;
- i tentativi precedenti restano registrati, ma non lo consumano.

Un'autorizzazione copre il lavoro, non una versione. Un nuovo candidato, release, head o
sorgente non è mai, da solo, un motivo per fermarsi o richiedere il consenso. È un limite solo
una versione nominata dall'utente.

## Acceptance Criteria
- [ ] Nessuna di queste skill richiede più un consumo cumulativo tra i tentativi né un limite di
      versione non chiesto: `execute-ticket/references/verification-cost.md`,
      `execute-ticket/references/skills-only.md`, `ticket-autopilot/references/technical-gates.md`,
      `execute-ticket/SKILL.md`, `qa-test-plan/SKILL.md`.
- [ ] Le voci 8 e 11 della policy obbligatoria (`extensions/mandatory-agent-skills.ts`) dicono lo
      stesso; `extensions/mandatory-agent-skills.test.ts` controlla il testo nuovo.
- [ ] Restano invariate:
  - la selezione causale delle verifiche;
  - la CI sulla head esatta;
  - la conservazione dei tentativi falliti;
  - lo stop su scope cambiato, revoca, budget del tentativo esaurito o tentativi massimi
    raggiunti.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa esterna, nessun limite di tempo o di tentativi, nessuna versione
esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`. Blocco esistente: le asserzioni
sul testo attuale in `extensions/mandatory-agent-skills.test.ts`.

## Step-by-Step Implementation Plan
1. `verification-cost.md`: sostituire il conto cumulativo con un conto per tentativo.
2. `skills-only.md`, passo 4: i gate della spec, un nuovo tentativo con budget pieno, nessun
   legame di versione.
3. `technical-gates.md`: la riga del mandato, il paragrafo sul limite di versione, i passi 2 e 4.
4. `execute-ticket/SKILL.md` e `qa-test-plan/SKILL.md`: allineare le diciture.
5. Le voci 8 e 11 di `mandatory-agent-skills.ts`, più i test.

## Testing Plan
- `node --test extensions/mandatory-agent-skills.test.ts`
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`
- `npm run -s lint`

## Out of Scope
- Il codice Python del runner, `goal.ts`, `to-spec` e `to-tickets` (EG-01).
