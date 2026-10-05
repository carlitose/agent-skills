---
ticket_schema: 1
ticket_id: "SPJ-05"
execution_mode: AFK
blocked_by:
  - "SPJ-01"
  - "SPJ-02"
  - "SPJ-03"
  - "SPJ-04"
---

# SPJ-05 — Provare due richieste con una sessione e giudizi fake

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-05`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

### Produces
- [Rapporto della prova con fake](../../research/solo-pi-jev-chain-prototype.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Not Yet Specified 5, Frontier / Blocking Edges, Next Review.

## Question / Outcome
Il flusso confermato regge due richieste consecutive nella stessa sessione, inclusi review, rischio, incertezza e stop, senza altri Pi? Costruire un prototipo throwaway con fake per rispondere a questa domanda; non anticipare il driver di produzione.

## Evidence
Verificare rapporto SPJ-01 e decisioni/conferme SPJ-02/03/04. Usare come riferimento i confini del driver e i suoi test/fake esistenti, senza cambiare le copie misurate. Leggere la skill `prototype` prima di costruire e rispettarne lifecycle e limiti.

## Produces
Rapporto `docs/research/solo-pi-jev-chain-prototype.md`, Artifact ID `artifact:solo-pi-jev-chain-prototype`, Role `research` (rapporto del prototipo), Parent a questo ticket e link `### Produces` reciproco nel grafo qui alla creazione. Codice throwaway e log in una directory scratch separata dal repository/copie misurate; il rapporto ne conserva riferimenti, hash, comandi e risultati necessari a riprodurre la prova. Non asserire che il prototipo esista prima dell'esecuzione.

## Acceptance Criteria
- [x] Tutte e quattro le dipendenze verificate su esiti attribuibili e conferme umane; nessuna decisione aperta tradotta in un default del prototipo.
- [x] Due richieste sintetiche percorrono il lifecycle approvato, con session ID, contatore di aperture/istanze, storia dei turni e ricevute distinte; nessuna foglia judge/reviewer nascosta. Le eventuali riprese contano separatamente secondo SPJ-04.
- [x] Test locali causali coprono Jev confident positivo/negativo, incerto, indisponibile, vietato e input fuori bound; rischio per funzione e review seguono esattamente SPJ-02/03, senza autoapprovazione.
- [x] Provati stop/failure per test rossi, test verdi con evidenza insufficiente secondo la policy confermata, findings blocker, mutazione del candidato, drift della base, crash/interruzione e risposta fake malformata; le prove appartengono al candidato corrente e i consumi restano cumulativi.
- [x] Credenziale sentinel di Jev non osservabile dal figlio fake Pi; nessuna chiamata Pi/Jev live e nessun benchmark. Nessun PASS dedotto dalla sola assenza di errori di trasporto.
- [x] Rapporto riproducibile con comandi/esiti reali, limiti dei fake e grafo reciproco; mappa aggiornata con ciò che resta incerto. Raccomandazione go/rework per una futura spec, non approvazione o implementazione di produzione.

## Frontier
Dipendenze verificate e prova offline eseguita in C:/dbench/tmp/spj05-prototype. Venti test passati dopo due omissioni del prototipo riprodotte e corrette; ultimo cleanup verificato con due test mirati, senza rinominare il full PASS precedente. Rapporto locale e handoff in verifica; GO alla spec, non approvazione di produzione o trasporto reale. Scelte confermate conservate, nessuna ulteriore domanda richiesta.

## Step-by-Step Implementation Plan
1. Leggere le dipendenze e `prototype`; fissare una domanda, una prova di due richieste e una directory throwaway non sovrapposta a copie o worktree misurati.
2. Costruire una vertical slice sintetica completa con trasporto Pi e Jev fake, osservazione del candidato e stop secondo ownership confermata; nessun percorso speciale per approvare tutti i casi.
3. Eseguire un test causale alla volta; conservare failure e consumo del prototipo senza affermare un benchmark RED/GREEN o live che non è stato eseguito.
4. Scrivere rapporto, link e limiti; aggiornare la mappa. Completion criterion: domanda risolta o limite nominato con evidenza, scratch preservata o rimossa soltanto secondo l'autorità effettiva; nessun codice promosso implicitamente a produzione.

## Testing Plan
Test unitari/protocollo e integrazione locale solo tra fake e repository sintetico; controlli di lifecycle, identità e failure paths. Elencare come non eseguiti trasporto reale Pi, autenticazione/provider Jev, qualità del modello, prestazioni e benchmark. In produzione la futura prima tracer bullet richiederà test RED → GREEN con foglie sostitutive, in un nuovo ticket e non retroattribuiti al prototipo.

## Out of Scope
Driver di produzione, trasporto/provider live, benchmark o confronto con Sonnet VOID, nuove autorità/budget, modifica di copie/risultati storici, scheduler/Autopilot, PR/merge, installazione/reload e wiki impliciti. Consegna skills-only inline; nessuna delega.
