---
ticket_schema: 1
ticket_id: "SPJ-02"
execution_mode: HITL
blocked_by: []
---

# SPJ-02 — Confermare il fallback quando Jev non decide

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-02`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Decisions So Far, Not Yet Specified 2, Frontier / Blocking Edges.

## Question / Outcome
Chi decide quando Jev è incerto o indisponibile senza introdurre un altro Pi? Il fallback delle domande semantiche e quello del rischio per funzione possono essere diversi. Non scegliere una policy per convenienza tecnica.

## Evidence
`cascade.py` (`Cascade.batch`, `judge`) oggi può aprire un judge fresco; `risk.py` (`assess`, `directed_review`) instrada incertezza/hunk fuori bound verso review. Il contratto storico `docs/specs/ticket-driver.md` prescrive Jev → LLM fresco → umano e vieta l'autoapprovazione: il target nuovo richiede una decisione esplicita sulle eventuali variazioni.

## Produces
Decisione confermata tramite `to-spec` in `docs/specs/solo-pi-jev-uncertainty-decision.md`, Artifact ID `artifact:solo-pi-jev-uncertainty-decision`, Role `spec`, Parent a questo ticket e link Children reciproco qui, aggiunti soltanto quando esiste. Aggiornamento della relativa edge nella mappa; nessun output è già prodotto.

## Acceptance Criteria
- [ ] Invocata la skill canonica `grilling`: una domanda per volta, attendendo la risposta; ottenuta conferma reale della policy e conservato il riferimento alla risposta, senza inventare evidenza o trattare il silenzio come consenso.
- [ ] Confrontate almeno gate umano, analisi nel Pi condiviso con successivo giudizio Jev e mantenimento di un giudice fresco solo come variazione esplicita della destinazione; nessuna opzione è preapprovata.
- [ ] Decision table distingue domande semantiche da rischio; copre confident positivo/negativo, sotto soglia, servizio indisponibile, invio vietato dal repository, input fuori bound e risposta malformata.
- [ ] Esplicitati retry/stop/handoff umano, consumo cumulativo e chi può approvare; un risultato incerto non equivale a PASS, rischio basso o nuova autorità di spesa.
- [ ] Spec di decisione e grafo reciproco salvati attraverso `to-spec`; mappa aggiornata solo per risposte confermate. Una scelta che cambia materialmente Destination/scope ritorna al destination gate Wayfinder prima di aggiornare gli artefatti.

## Frontier
Ready HITL per intervista; non confermato. Nessun blocker canonico. SPJ-01 può informare l'intervista ma non è una precondizione tecnica per chiedere chi decide. Se manca l'utente, lasciare la edge aperta.

## Step-by-Step Implementation Plan
1. Leggere mappa, contratto storico e la skill `grilling`; presentare il trade-off tra zero Pi aggiuntivi, indipendenza e autonomia.
2. Intervistare una domanda alla volta e fermarsi alla conferma della policy; le soglie numeriche nuove non si inventano. Completion criterion: tutte le condizioni della decision table hanno un owner e un esito confermati, o il ticket resta aperto.
3. Registrare tramite `to-spec` opzioni, decisione, conseguenze e prova della conferma; aggiornare la edge senza implementare il fallback.

## Testing Plan
Ripassare la decision table con casi sintetici e controllare che nessun ramo approvi l'incertezza o nasconda un nuovo Pi. Verificare link/grafo e attribuzione della conferma. Nessun test del provider o benchmark.

## Out of Scope
Intervista sulla review o sulla proprietà dello script, implementazione, chiamate live, nuove spese, modifica dei lotti/copie storici, calibrazione, CLI/scheduler Autopilot, delivery/wiki impliciti. Consegna skills-only inline; nessuna delega.
