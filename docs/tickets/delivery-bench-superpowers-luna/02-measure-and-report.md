---
ticket_schema: 1
ticket_id: "SPL-02"
execution_mode: HITL
blocked_by:
  - "SPL-01"
---

# SPL-02 — Misurare Superpowers e controlli contemporanei con Luna medium

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-superpowers-luna:SPL-02`
- Role: `ticket`
- Parent: [delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md)

### Produces
- [Risultati del confronto](../../research/delivery-bench-superpowers-luna-results.md)

## Parent Spec
[delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md),
Goal and decisions, Implementation slices, Verification, Gates.

## What to Build
Nuovo lotto con bare, Pi-tools, Pi-full e Pi-superpowers: Luna medium, scenari lua-vm,
sql-engine e crdt-yjs, 4 richieste, 3 ripetizioni. Report separato dai lotti storici.

## Acceptance Criteria
- [ ] Scenari privati e provenienza recuperati, senza contaminare i contesti dei partecipanti.
- [ ] Snapshot locale Superpowers, strumenti e skill personali congelati prima del lotto.
- [ ] Accesso Luna e Docker verificati; preflight passato sui quattro bracci.
- [ ] Autorità del lotto attribuita alla conferma dell'utente, con scope e stima dei costi espliciti.
- [ ] 144 posizioni di richiesta giudicate oppure fallimenti/gate conservati senza inventare punteggi.
- [ ] Report per braccio/scenario con correttezza, robustezza, regressioni, costi e tempi; confronto appaiato contemporaneo.

## Frontier
Dependency-blocked da SPL-01; input live mancante: percorso/accesso agli scenari privati.
`C:/Users/CGS03/dbench-private` e `C:/Users/rdpuser/dbench-private` non sono presenti.
Non ricostruire l'oracolo dai report e non sostituire gli scenari con altri problemi.

## Gates
- Attempt: una misura nuova completa attraverso il report, distinta da SPL-01.
- Budget per attempt: nessun limite impostato dall'utente; costi correnti stimati prima del live,
  uso soltanto dell'accesso OpenAI richiesto; sconosciuto non significa zero.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato; nessun retry implicito dell'intero lotto.
- Approvals: conferma «si facciamo cosi» per il confronto Luna medium; non Anthropic/Jev,
  delegazione, installazione globale, push/merge o pubblicazione.
- Exact version: `openai-codex/gpt-6-luna`, thinking `medium`; congelare le risorse prima dell'avvio.
- Existing blocks searched: specifiche/report/runner e percorsi locali; scenari privati assenti.
  Accesso di generazione Luna e Docker non provati per il lotto. Servono dati/ambiente, non
  un nuovo consenso sul modello. Non iniziare il preflight a pagamento finché gli input mancano.

## Step-by-Step Implementation Plan
1. Ottenere il percorso esistente degli scenari e validare la provenienza, senza modificarli.
2. Preparare lo snapshot upstream e la stima; eseguire il preflight e legare l'autorità del lotto.
3. Eseguire soltanto il protocollo concordato con il runner di benchmark esistente.
4. Scrivere il report con evidenze attribuibili e limiti; nessuna pubblicazione implicita.

## Testing Plan
Controlli live esplicitamente separati dai test offline; mantenere fallimenti, retry,
compaction, costi mancanti e richieste non giudicate. Un giudice generativo Anthropic non fa
parte della misura. Per affermazioni live usare il contratto Verification Audit.

## Out of Scope
- Cambiare scenari, rigiocare lotti storici, estendere a catene da 12 o altri modelli.
- Dedurre accesso operativo da una voce nel registro locale.
