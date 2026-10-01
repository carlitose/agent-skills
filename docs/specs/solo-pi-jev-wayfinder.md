# Solo Pi + Jev: una sessione per la catena

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [SPJ-01](../tickets/solo-pi-jev/01-research-session-transport.md)
- [SPJ-02](../tickets/solo-pi-jev/02-decide-uncertainty-fallback.md)
- [SPJ-03](../tickets/solo-pi-jev/03-decide-shared-context-review.md)
- [SPJ-04](../tickets/solo-pi-jev/04-decide-script-ownership.md)
- [SPJ-05](../tickets/solo-pi-jev/05-prototype-two-request-chain.md)

### Related
- [Contratto storico del driver](ticket-driver.md)
- [DBH-09: regime difficile](../research/delivery-bench-hard-results.md)
- [DBH-16: driver corretti](../research/delivery-bench-hard-drivers.md)
- [DBH-20: Opus 5.5](../research/delivery-bench-hard-opus.md)
- [TJV-02: c3a corretto nel regime precedente](../research/delivery-bench-c3a-corrected.md)

## Type
Wayfinding spec — ricerca, decisioni e prototipo; non specifica implementativa approvata.

## Status
Active — cinque ticket emessi, nessuno eseguito. Tre decisioni HITL restano aperte.

## Destination

Un candidato del ticket-driver nel quale **lo script manda i turni a una sola sessione Pi
lungo tutta la catena**, invece di avviare builder, judge e reviewer separati. Jev valuta
il rischio per funzione e le domande semantiche dove può rispondere. Pi genera il codice e
l'eventuale analisi testuale; Jev non è un generatore di patch o review.

La meta è ridurre le istanze Pi senza trasformare un esito incerto in un'approvazione e
senza perdere l'identità del candidato osservato. Non è una promessa di qualità, costo,
velocità o autonomia pari ai candidati misurati.

**Assunzioni di pianificazione, non decisioni approvate:**

- Una catena è una sequenza ordinata di richieste sullo stesso prodotto. Non significa
  una sessione per richiesta, per funzione o per ruolo.
- Si cerca un trasporto persistente controllato dallo script. SPJ-01 deve distinguere
  processo, sessione logica e cronologia: riaprire lo stesso JSONL non prova un solo processo
  persistente. Nessun trasporto Pi è già scelto.
- Il nuovo candidato si realizzerà dopo ricerca, decisioni e prototipo. La compatibilità
  non è implicita; le copie storiche restano però immutabili per provenienza, non come shim.

## Decisions So Far

| Stato | Decisione o vincolo | Evidenza e record |
| --- | --- | --- |
| Richiesta esplicita | Una sessione Pi per la catena; Jev quando possibile; niente Pi aggiuntivi per i ruoli. | Richiesta utente del 2026-10-01, ricostruita nel checkpoint della sessione; questa mappa ne conserva il perimetro, non presume confermate le scelte sotto. |
| Richiesta iniziale | Usare Wayfinder per chart e frontier, senza eseguire il refactoring durante il chart. | Richiesta utente del 2026-10-01; il batch iniziale è documentale. |
| Mandato successivo | Pubblicare il chart e proseguire i ticket per terminare il lavoro; le scelte HITL richiedono comunque conferme reali. | Correzione utente del 2026-10-01: il solo trasferimento ai ticket e il Wayfinder locale non terminano i lavori. Non è una risposta ai trade-off né un budget per benchmark. |
| Vincolo operativo | Consegna skills-only, inline e seriale; nessun Autopilot, scheduler o delega. | Mandato corrente; le funzioni pure dei contratti restano riutilizzabili. Il candidato progettato non diventa il driver della consegna di questi ticket. |
| Vincolo di integrità | Non cambiare copie misurate, ledger, ricevute, sessioni o risultati dei lotti. Sonnet interrotto è VOID, escluso dai confronti. | Disposizione locale del lotto annullato; la mappa non pubblica dati privati. |
| Limite esplicito | Review e giudizi nel contesto del builder non sono indipendenti. | Separazione di contesto oggi visibile in `Cascade.judge` e `directed_review`; SPJ-02/03 devono registrare il compromesso, non rinominarlo indipendenza. |

Il [contratto storico](ticket-driver.md) prescrive Jev → LLM fresco → umano e vieta
l'autoapprovazione del builder. La nuova destinazione entra in tensione con quelle garanzie:
questa mappa **non le modifica né le dichiara superate**. SPJ-02/03/04 registreranno attraverso
`to-spec` soltanto le variazioni confermate, con rimandi reciproci ai ticket proprietari.

## Current Evidence

Ricognizione sul commit `b7c5f5d03ff04e67a00cb37c96682e01894684bd`. Il target della
consegna del chart è `e002773395bf2c392736b6c1faeafe3a14f65b40`: aggiunge solo il report
DBH-20 e i relativi documenti, senza cambiare quei confini di codice. I riferimenti
nominano funzioni, non righe fragili. Sono letture, non nuove esecuzioni né misure.

| Confine osservato | Comportamento attuale | Conseguenza per la ricerca |
| --- | --- | --- |
| [leaf.py](../../ticket-driver/scripts/leaf.py): `invoke`, `leaf_argv` | Ogni invocazione crea una nuova directory sessione e lancia Pi in print mode tramite cattura del processo. `--session-dir` da solo non stabilisce il riuso. | Serve un confine di sessione più lungo di una foglia e di una richiesta. |
| [driver.py](../../ticket-driver/scripts/driver.py): `execute` | Il controllo di una richiesta apre un run, seleziona il builder, osserva il candidato e termina. Non possiede una sessione che attraversi più richieste. | La proprietà della sessione va al livello catena, senza inventare un scheduler di ticket. |
| [cascade.py](../../ticket-driver/scripts/cascade.py): `Cascade.batch`, `judge` | Jev risponde su stato e domande tipate; un esito incerto o indisponibile può lanciare una foglia judge distinta, poi aprire un gate umano. | Quel fallback non rispetta automaticamente il target zero Pi aggiuntivi. SPJ-02 ne decide la sostituzione. |
| [risk.py](../../ticket-driver/scripts/risk.py): `assess`, `directed_review` | Il rischio è già per funzione. Incertezza e hunk fuori dal bound selezionano review diretta, che oggi invoca una nuova foglia in scratch separata. | Jev non sostituisce la generazione dei findings. SPJ-03 decide ruolo, contesto e scritture della review. |
| [driver.py](../../ticket-driver/scripts/driver.py): `execute`, `risk_phase` | `c4` usa il checkout corrente e termina `completed-local`, ma `risk_phase` può ancora invocare il revisore separato. | `c4` non è già il candidato «solo Pi»; non basta cambiare un'etichetta. |
| [runner.py](../../benchmarks/delivery-bench/runner.py): `arm_argv` | I bracci Pi continuano la cronologia dopo la prima richiesta; i driver vengono lanciati nuovamente per ogni task. | Sessione logica, processo e contabilizzazione vanno distinti anche al confine del benchmark. L'harness storico non va riscritto retroattivamente. |
| [arbiter.py](../../ticket-driver/scripts/arbiter.py): `isolated_key`, `ask`, `classify` | Chiave Jev isolata nel driver; risposte tipate e soglie esplicite. | Il trasporto persistente non deve reintrodurre credenziali Jev nei figli Pi. Ricerca e prototipo usano soltanto fake. |

## Benchmark Evidence → Refactoring Frontier

Questi risultati motivano domande e prove, **non dimostrano il nuovo candidato**. Nessun
braccio misurato ha il contratto «una sessione Pi + Jev, zero Pi aggiuntivi». Continuità del
contesto, modello, prompt, garanzie e policy non sono stati variati uno alla volta: attribuire
il risultato alla sola topologia delle sessioni sarebbe una conclusione causale non misurata.

| Evidenza aggregata e fonte | Implicazione per il refactoring | Owner / prova richiesta |
| --- | --- | --- |
| [DBH-09](../research/delivery-bench-hard-results.md): alla richiesta 1 passa 1/45; a L4 skills-only 9/36 contro bare 1/36 (Holm 0,03125). A L12 skills-only 21/72, Autopilot 22/72, bare 13/72, senza differenza significativa nella famiglia originale (Holm 0,157). | Il regime è difficile e il beneficio osservato dipende dalla lunghezza; niente promessa universale di qualità. La continuità è un'ipotesi da esplorare, non la causa dimostrata del vantaggio. | SPJ-01: distinguere cronologia/processo; SPJ-05: provare solo lifecycle e stop con fake. La qualità resta fuori dalle prove offline. |
| [DBH-16](../research/delivery-bench-hard-drivers.md): c1a corretto 1/36 a L4 e 3/36 a L12; bare sulle stesse coppie L12 8/36. Dei 32 run integrati, 28 non sono accettati dall'oracolo. | Test del builder verdi e integrazione non bastano a dimostrare copertura della richiesta. Togliere review/gate per aumentare le consegne cambia la garanzia, non risolve questo divario. | SPJ-03/04: claims, ownership e identità delle prove; SPJ-05: caso sintetico test verdi ma evidenza insufficiente, secondo la policy confermata. |
| DBH-16: c3a 0 accettate, 28 run gated; 5 candidati gated accettati nel giudizio separato. Non sono consegne né una catena alternativa ricostruita. | L'incertezza può bloccare un candidato buono, ma non diventa PASS. Non basta sommare i controfattuali per stimare la nuova catena o approvare un fallback. | SPJ-02: distinguere indisponibilità, incertezza, input fuori bound e negativo deciso; SPJ-03: verificare le prove disponibili al giudizio. |
| DBH-16: nessuno stop per protocollo o suite uccisa dopo le correzioni; c1a passa da 9 a 32 run integrati su 60. Restano 16 e 19 rinunce senza modifiche per c1a/c3a; i driver ripartono con una sessione nuova. | Separare guasti d'osservazione già corretti da limiti del builder e del gate. Sessione lunga può conservare conoscenza, ma il report non ne isola l'effetto. | SPJ-01: lifecycle e contabilizzazione; SPJ-04: richieste fallite e base reale della successiva. Non modificare retroattivamente le copie misurate. |
| [DBH-20](../research/delivery-bench-hard-opus.md): con Opus medium a L4 bare, skills-only, Autopilot e c1a accettano 36/36; c3a 26/36 (Holm 0,0078125). A L12 i bracci non-driver accettano 63/72, 64/72 e 65/72; i driver 30/36 e 23/36. Undici dei dodici candidati gated superano il giudizio separato, non sono consegne. | Il modello e il regime cambiano il risultato; i difetti documentati rendono necessaria la sensibilità, non giustificano l'approvazione dell'incertezza. Non è una prova di una sessione Pi + Jev. | SPJ-01: osservare processo e turni; SPJ-02/03: decidere le garanzie e dichiarare la review condivisa; SPJ-05: provare gli stop con fake, non stimare qualità/costo da controfattuali. |
| [TJV-02](../research/delivery-bench-c3a-corrected.md): c3a corretto 9/9, 25/27 e 45/48 alle lunghezze 1/3/8, indistinguibile da bare; modello e scenari diversi da DBH. | Il cancello non è universalmente inefficace; trasferire percentuali tra regimi o modelli non è una prova del nuovo design. | SPJ-02/03: conservare decisioni attribuibili e limiti; nessuna soglia nuova ricavata da un confronto non controllato. |
| DBH-16: c1a/c3a costano meno e lavorano meno; a L12 nessuna compaction nei driver, contro 15 skills-only e 57 Autopilot. | Ridurre istanze non garantisce riduzione di costo o tempo: una sessione lunga accumula contesto e può compattare. Contare lavoro consegnato, non solo processi. | SPJ-01/04: delte per turno, consumi cumulativi, crash e compaction espliciti; SPJ-05: nessun benchmark di prestazioni dichiarato dai fake. |

**Provenienza e limiti:** DBH-09 e DBH-16 sono lotti distinti; i driver corretti hanno una sola
ripetizione a L12 e un manifest delle skill diverso, documentato nei report. La rimisura cambia
anche la famiglia di Holm (a L12 skills-only/Autopilot 0,1875): non mescolare il p di una
famiglia con le decisioni dell'altra. Gli 0/60 dei driver originali includono guasti poi corretti
 e non sono una baseline pulita della sola architettura. Jev e giudice fresco sono ruoli
distinti: il dato gated non attribuisce da solo l'incertezza a Jev.

**Opus e Sonnet:** [DBH-20](../research/delivery-bench-hard-opus.md) è pubblicato nella
PR #405, merge `e002773`. La regola sceglie bare nel regime misurato; confronti fra
lotti, campioni piccoli e sensibilità ai difetti impediscono attribuzioni causali alla sola
topologia o al solo modello. Sonnet interrotto resta VOID: ricevute e spesa preservate,
nessun confronto o baseline completata. Future misure del nuovo candidato richiedono
prima decisioni/spec/prototipo e poi autorità, budget e protocollo separati.

## Not Yet Specified

1. **Trasporto e lifecycle (SPJ-01):** quale interfaccia supportata della versione Pi
   disponibile permette turni seriali, eventi terminali, interruzione e contabilizzazione?
   Cosa succede su crash, ripresa e compattazione? Una nuova istanza dopo un crash non va
   occultata dal medesimo session ID.
2. **Incertezza (SPJ-02, HITL):** gate umano immediato, analisi nel Pi condiviso seguita da
   nuovo giudizio Jev, oppure un'altra politica esplicitamente scelta? Jev indisponibile,
   vietato dal repository, sotto soglia e input fuori bound non sono PASS né rischio basso.
   Un eventuale LLM fresco contraddice il target corrente e richiede una variazione esplicita.
3. **Review (SPJ-03, HITL):** mantenere un turno di review nello stesso contesto, modificarlo
   o rinunciarvi? Chi decide sui findings e cosa può scrivere? Se la review cambia codice,
   il candidato cambia e i controlli interessati non valgono per il nuovo albero.
4. **Proprietà dello script (SPJ-04, HITL):** chi possiede worktree, test, freeze, ricevute e
   integrazione locale? Se una garanzia viene tolta, va dichiarata; non nasce una garanzia
   equivalente da una dichiarazione del modello.
5. **Fattibilità (SPJ-05):** un prototipo di due richieste con trasporti fake deve provare il
   flusso scelto e i suoi stop prima di scrivere la specifica implementativa.

## Out of Scope

- Eseguire il driver o nuovi benchmark durante la consegna di questo chart; chiamate
  Pi/Jev live, credenziali e spesa del provider. L'esecuzione dei ticket richiesta dopo
  il chart procede serialmente, nei loro scope e solo dopo i gate pertinenti.
- Toccare copie misurate o risultati precedenti; includere il lotto Sonnet VOID in una
  baseline, o confondere la sua cancellazione con il completamento del benchmark.
- Scheduler, parallelismo, altri agenti, sostituzione del giro di skills, nuovo protocollo
  JSON autoredatto dal modello, nuove funzioni Autopilot, aggiornamenti personali impliciti.
- PR, push, merge remoto, installazione, reload o wiki sync impliciti da questo batch.
- Scelta del vincitore, calibrazione delle soglie, qualità dimostrata o risparmio promesso.
- Ritirare i candidati storici o mantenere alias/shim senza richiesta esplicita.

## Frontier / Blocking Edges

| Edge | Perché blocca | Condizione di sblocco | Owner |
| --- | --- | --- | --- |
| Trasporto non verificato | Il lifecycle «una sessione» non ha ancora un confine implementabile. | Rapporto con documentazione primaria corrente, opzioni e prova riproducibile senza provider, oppure limite dichiarato. | SPJ-01 |
| Fallback non scelto | Non si possono approvare esiti incerti né avviare un Pi nascosto. | Grilling, una domanda per volta, conferma reale e decision spec; nessuna scelta per silenzio. | SPJ-02 |
| Review non scelta | Contesto condiviso e reviewer indipendente non sono la stessa proprietà. | Dopo SPJ-02, conferma di ruolo, claims e confine delle scritture; decision spec. | SPJ-03 |
| Owner non scelti | Riusare il contesto non decide chi osserva e integra il candidato. | Dopo SPJ-01/03, matrice confermata di owners, prove e garanzie cambiate; decision spec. | SPJ-04 |
| Flusso non provato | Un diagramma non prova continuità o stop corretti. | Dopo tutte le decisioni, prototipo isolato con fake e rapporto che separa ciò che prova da ciò che resta live. | SPJ-05 |

## Ticket Plan

| ID | Tipo | Modo | Blockers canonici | Frontier corrente | Esito atteso |
| --- | --- | --- | --- | --- | --- |
| SPJ-01 | research | AFK | nessuno | Ready, non avviato | Rapporto su trasporto Pi e lifecycle di catena. |
| SPJ-02 | grilling | HITL | nessuno | Ready per intervista; decisione aperta | Politica confermata per incertezza Jev, distinta tra rischio e gate. |
| SPJ-03 | grilling | HITL | SPJ-02 | Dependency-blocked e decisione aperta | Contratto confermato della review condivisa e limite d'indipendenza. |
| SPJ-04 | grilling | HITL | SPJ-01, SPJ-03 | Dependency-blocked e decisione aperta | Matrice confermata script/Pi/Jev/umano per osservazione e integrazione. |
| SPJ-05 | prototype | AFK | SPJ-01, SPJ-02, SPJ-03, SPJ-04 | Dependency-blocked | Due richieste sintetiche nella stessa sessione fake, flusso e failure paths osservabili. |

Nessuna dipendenza è completata dalla sola emissione dei ticket. L'ordine consigliato è
SPJ-01 → SPJ-02 → SPJ-03 → SPJ-04 → SPJ-05, serialmente e con handoff attribuibile.

## Next Review

**Prossimo passo nella frontier:** SPJ-01, richiesto ma non ancora avviato; leggere Pi dalla
versione risolta, raccogliere il rapporto offline e aggiornare questa mappa. SPJ-02 resta
pronto per grilling, non approvato dal rapporto tecnico.

Dopo SPJ-05, tornare a `to-spec` per il contratto implementativo confermato e a `to-tickets`
per la prima tracer bullet di produzione con test RED → GREEN e foglie sostitutive. Non
anticipare quei ticket mentre la scelta di fallback e delle garanzie è ancora aperta.

Eventuali misure Luna/Sonnet sono una fase successiva, con lotto nuovo, autorità e budget
nuovi, manifest/copie congelati e baseline valida. Sonnet VOID non è una baseline. `--arm-from`
è un riferimento al protocollo storico, non un'autorizzazione a usarlo adesso.

## Handoff Boundaries

Chart documentale, corsia skills-only: parser/serializer e CandidateRef canonici,
nessun CLI del runner né ledger sintetico. La pubblicazione è autorizzata separatamente;
CandidateRef e riferimenti hash nel handoff non approvano le decisioni o i ticket.
L'integrazione Git richiede readback del provider e CI sull'head esatto. Wiki synchronization
**deferred**, senza hook post-batch implicito. Il chart pubblicato non termina il refactoring.
