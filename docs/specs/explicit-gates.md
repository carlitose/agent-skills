# Gate espliciti, per tentativo, senza legami di versione

## Artifact Graph
- Artifact ID: `artifact:explicit-gates`
- Role: `spec`
- Parent: [`artifact:explicit-gates-wayfinder`](explicit-gates-wayfinder.md)

### Children
- [EG-01](../tickets/explicit-gates/done/01-gates-in-specs-and-tickets.md)
- [EG-02](../tickets/explicit-gates/02-per-attempt-budget-no-version-binding.md)

## Type
Decision

## Problem
Il 2026-10-06 una sessione Pi su un altro progetto ha usato `/goal` per 65 turni e 17 ore,
ripetendo sempre lo stesso blocco, per tre motivi:
- una finestra autorizzata era legata alla versione della release, quindi la release corretta
  veniva rifiutata (`source_mismatch`);
- budget e scadenza erano cumulativi tra i tentativi;
- l'agente se n'è accorto solo dopo aver avviato la finestra, anche se l'utente aveva chiesto
  esplicitamente se c'erano altri vincoli.

Le skill di oggi lo prescrivono. In [verification-cost](../../execute-ticket/references/verification-cost.md):
«A fresh candidate does not reset consumption». In
[skills-only](../../execute-ticket/references/skills-only.md): «Moving from a run does not reset
consumption». In [technical-gates](../../ticket-autopilot/references/technical-gates.md): «A
user-imposed exact head or path is a mandate limit» e il rinnovo resta «within … remaining
budget». In nessuna skill si chiedono i gate mentre si scrivono spec e ticket.

## Decision
Decisioni dell'utente, 2026-10-06:

1. **Gate decisi a priori e chiesti.** Ogni spec e ogni ticket hanno una sezione `## Gates`,
   chiesta all'utente in un solo giro mentre si scrivono. Contiene:
   - cos'è un tentativo;
   - budget e tempo per tentativo;
   - tentativi massimi;
   - approvazioni (merge, deploy, pubblicazione, spesa esterna);
   - eventuale versione esatta;
   - blocchi già presenti nel codice, nella configurazione o nelle policy, cercati prima di
     scrivere, oppure "nessuno trovato" con cosa si è cercato.

   Un gate senza risposta resta `open` e blocca solo il lavoro che ne dipende.
2. **Per tentativo.** Un nuovo tentativo, come definito in `## Gates`, parte con budget e tempo
   pieni. I tentativi precedenti restano registrati e riportati, ma non consumano il nuovo.
   Dentro lo stesso tentativo, un timeout, una compattazione o un nuovo shard non azzerano nulla.
3. **Niente legami di versione.** Un'autorizzazione copre il lavoro, non una versione. Un nuovo
   candidato, release, head o sorgente non è mai, di per sé, un motivo per fermarsi o richiedere
   il consenso. Solo una versione nominata esplicitamente dall'utente e scritta in `## Gates` è
   un limite.
4. `/goal` non si tocca.

## Non-goals
- Codice Python del runner `ticket-autopilot` (Autopilot sospeso), `goal.ts`, gateway di
  nations-league.
- Le regole sulla scelta delle verifiche restano invariate. Si continua a non ripetere l'intera
  suite senza un motivo causale, e la CI sulla head esatta resta obbligatoria.

## Gates
- Tentativo: una PR per ticket; un push nuovo sulla stessa PR fa parte dello stesso tentativo.
- Budget per tentativo: nessuna spesa esterna; solo test locali e CI di GitHub.
- Tempo per tentativo: nessun limite fissato dall'utente.
- Tentativi massimi: illimitati, perché non c'è spesa.
- Approvazioni:
  - merge su `main` con CI 8/8 e `--match-head-commit`, confermato dall'utente ("Ok",
    2026-10-06);
  - pin di `pi-personal-config`, `update:personal` e reload solo a lotto `dbh-luna3e` finito.
- Versione esatta: nessuna.
- Blocchi esistenti trovati:
  - il limite di 115 righe per `to-tickets/SKILL.md` (`ticket-autopilot/tests/test_skill_graph.py`);
  - le asserzioni sul testo attuale in `extensions/mandatory-agent-skills.test.ts`.

## Implementation Slices
- EG-01: `## Gates` in `to-spec` e `to-tickets`.
- EG-02: tentativo e versione in `verification-cost`, `skills-only`, `technical-gates`,
  `execute-ticket`, `qa-test-plan` e nella policy obbligatoria
  (`extensions/mandatory-agent-skills.ts`).

## Verification
- Test unitari:
  - `ticket-autopilot/tests/test_skill_graph.py`;
  - `node --test extensions/mandatory-agent-skills.test.ts`;
  - `npm run -s lint`.
- CI 8/8 sulla head esatta.
- Nessun test live.
