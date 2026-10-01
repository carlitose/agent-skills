---
ticket_schema: 1
ticket_id: "SPJ-04"
execution_mode: HITL
blocked_by:
  - "SPJ-01"
  - "SPJ-03"
---

# SPJ-04 — Confermare gli owner di worktree, prove e integrazione

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-04`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Destination, Not Yet Specified 4, Frontier / Blocking Edges.

## Question / Outcome
Quali attività e garanzie restano nello script che guida il Pi condiviso, e quali passano a Pi, Jev o umano? Una sessione unica non decide da sola isolamento, prove e integrazione.

## Evidence
Leggere `driver.py` (`preflight`, `create_worktree`, `_record_candidate`, `integrate_candidate`, `execute`), i contratti puri CandidateRef/Ticket Envelope e gli esiti attribuibili di SPJ-01 e SPJ-03. Il contratto storico distingue integrazione locale da PR/merge remoto; `c4` non integra automaticamente e può ancora invocare un reviewer separato.

## Produces
Decisione confermata tramite `to-spec` in `docs/specs/solo-pi-jev-script-ownership-decision.md`, Artifact ID `artifact:solo-pi-jev-script-ownership-decision`, Role `spec`, Parent a questo ticket e link Children reciproco qui, aggiunti alla creazione. Matrice di ownership nella decisione e aggiornamento della edge della mappa.

## Acceptance Criteria
- [ ] Esiti SPJ-01 e SPJ-03 verificati con fonti e conferme reali; nessuna dipendenza completata per sola emissione.
- [ ] Invocata `grilling`, una domanda per volta, e ottenuta conferma reale della matrice script/Pi/Jev/umano per lifecycle, worktree, test, freeze, artefatti, gate, integrazione locale e stop.
- [ ] Per ogni garanzia attuale: preservata, modificata o rimossa, con osservatore, prova e limite dichiarati. CandidateRef usa alberi Git e digest canonico; dichiarazioni del modello non diventano ricevute osservate.
- [ ] Confermati comportamento su drift della base/candidato, test che scrivono, richieste fallite, crash/ripresa e handoff umano; costo/consumo cumulativo e credenziali Jev non si azzerano né si ereditano nel Pi.
- [ ] Distinte fine del turno, candidato verificato, `completed-local`, integrazione locale e delivery remoto; stop/gate non sono successo. Spec tramite `to-spec`, prova di conferma, grafo e mappa aggiornati senza implementazione.

## Frontier
Dependency-blocked da SPJ-01 e SPJ-03, HITL per la matrice di ownership. Nessuna integrazione o rimozione di garanzie è già approvata. Per cambi materiali alla destinazione ritornare al destination gate Wayfinder prima di aggiornare gli artefatti.

## Step-by-Step Implementation Plan
1. Verificare le dipendenze e confrontare ownership attuale con il trasporto raccomandato e la review confermata.
2. Usare `grilling` per confermare la matrice e la gestione dei failure paths; dichiarare garanzie e autonomia eventualmente perse. Completion criterion: ogni attività ha owner e prova confermati, o il ticket resta aperto.
3. Salvare attraverso `to-spec` la decisione, le alternative e le conferme; collegare il grafo e aggiornare la frontier.

## Testing Plan
Walkthrough documentale di catena buona, test rossi, base avanzata, candidato cambiato, crash e tentativo di integrare senza autorità. Verificare che le prove appartengano all'albero corretto e che il consumo sia cumulativo. Controlli di link/grafo, nessuna esecuzione live.

## Out of Scope
Scheduler, provider delivery, nuove soglie o policy Jev, codice di produzione, credenziali/spesa, lotti/copie misurati, CLI Autopilot, installazione/reload e wiki impliciti. Consegna skills-only inline; nessuna delega.
