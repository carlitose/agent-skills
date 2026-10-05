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
- [Contratto implementativo e tracer bullet](solo-pi-jev-implementation.md)

### Related
- [SPJ-01: trasporto e lifecycle offline](../research/solo-pi-jev-session-transport.md)
- [SPJ-02: fallback confermato](solo-pi-jev-uncertainty-decision.md)
- [SPJ-03: rilettura e correzione](solo-pi-jev-review-decision.md)
- [SPJ-04: gestione e ripresa](solo-pi-jev-script-ownership-decision.md)
- [SPJ-05: prova con fake](../research/solo-pi-jev-chain-prototype.md)
- [Contratto storico del driver](ticket-driver.md)
- [DBH-09: regime difficile](../research/delivery-bench-hard-results.md)
- [DBH-16: driver corretti](../research/delivery-bench-hard-drivers.md)
- [DBH-20: Opus 5.5](../research/delivery-bench-hard-opus.md)
- [TJV-02: c3a corretto nel regime precedente](../research/delivery-bench-c3a-corrected.md)

## Type
Wayfinding spec — ricerca, decisioni e prototipo; non specifica implementativa approvata.

## Status
Active — chart pubblicato nella PR #406, merge `001d362`; SPJ-01 ha un rapporto offline locale, non ancora consegnato al provider. SPJ-02 ha decisione e handoff locali validati. SPJ-03 ha decisione e handoff locali validati; SPJ-04 ha decisione e handoff locali validati. SPJ-05 ha prova offline, rapporto e handoff locali validati. Contratto implementativo e ticket SPC-01/02/03 emessi; prima tracer bullet ready, refactoring non ancora implementato.

## Destination

Un candidato del ticket-driver nel quale **lo script manda i turni a una sola sessione Pi
lungo tutta la catena**, con un solo processo Pi principale. Jev valuta il rischio per
funzione e le domande semantiche dove può rispondere. La [decisione SPJ-02](solo-pi-jev-uncertainty-decision.md)
consente un judge mediante completion **in-process**, con prompt distinto, senza strumenti,
cronologia del builder, nuova sessione agente o processo Pi figlio. Non si usa il loop
`/goal`: si riusa il suo meccanismo di completion, con prove e contratto dedicati.

Pi genera codice e analisi; Jev non genera patch o review. Chiamate judge aggiuntive sono
esplicite e contabilizzate: un processo non significa una sola chiamata al modello né costo
zero. La meta non trasforma incertezza in approvazione e conserva l'identità del candidato;
non promette qualità, costo, velocità o autonomia pari ai candidati misurati.

**Flusso confermato in parole semplici:** Autopilot semplificato con Jev. Lo script gestisce
ticket e prove; lo stesso Pi scrive, corregge e rilegge; Jev controlla rischi e decisioni.
Se Jev non decide, un secondo parere AI in-process come `/goal`; se non basta, richiesta
umana. Nessuna nuova autorità per benchmark, installazioni o merge. La [review SPJ-03](solo-pi-jev-review-decision.md)
usa le parti rischiose/incerte e conserva il controllo della richiesta completa; al terzo
fallimento finale il ticket si ferma, come il limite Autopilot verificato. La [gestione SPJ-04](solo-pi-jev-script-ownership-decision.md) conferma gli owner,
la copia separata, le prove reali, la continuazione degli indipendenti e la ripresa sicura.

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
| Richiesta iniziale | Una sessione Pi per la catena; Jev quando possibile; niente Pi aggiuntivi per i ruoli. | Richiesta utente del 2026-10-01; la conferma SPJ-02 sotto distingue processo, sessione agente e chiamata al modello. |
| Confermata SPJ-02 | Soglie Jev invariate; fallback semantico con un judge in-process, poi analisi condivisa e gate umano se indecidibile; rischio incerto verso review condivisa obbligatoria. | [Decisione e conferme reali](solo-pi-jev-uncertainty-decision.md). Il subagent inizialmente richiesto è sostituito esplicitamente dal meccanismo in-process dopo verifica di `/goal`. SPJ-03/04 non sono approvati per inferenza. |
| Confermata SPJ-03 | Review nello stesso Pi, solo findings prima dei fix, parti rischiose/incerte e verifica della richiesta intera; limite Autopilot di 3 fallimenti finali per ticket. | [Spiegazione, esempi e conferma reale](solo-pi-jev-review-decision.md); la proposta iniziale di una correzione è sostituita. SPJ-04 non è risolto da questa decisione. |
| Confermata SPJ-04 | Script responsabile di copia, sessione, prove, avanzamento locale e stop; indipendenti dalla versione valida, ripresa sicura contata, drift riconciliato. | [Matrice e conferme reali](solo-pi-jev-script-ownership-decision.md); completamento locale distinto da applicazione e delivery. Nessuna nuova autorità live/merge. |
| Richiesta iniziale | Usare Wayfinder per chart e frontier, senza eseguire il refactoring durante il chart. | Richiesta utente del 2026-10-01; il batch iniziale è documentale. |
| Mandato successivo | Pubblicare il chart e proseguire i ticket per terminare il lavoro; le scelte HITL richiedono comunque conferme reali. | Correzione utente del 2026-10-01: il solo trasferimento ai ticket e il Wayfinder locale non terminano i lavori. Non è una risposta ai trade-off né un budget per benchmark. |
| Vincolo operativo | Consegna skills-only, inline e seriale; nessun Autopilot, scheduler o delega implicita. | Richiesta esplicita dell'estensione subagent limitata al tentativo descritto in SPJ-02, senza giudizio prodotto; non autorizza worker o review delegati ulteriori. Funzioni pure dei contratti riutilizzabili; il candidato progettato non guida questa consegna. |
| Vincolo di integrità | Non cambiare copie misurate, ledger, ricevute, sessioni o risultati dei lotti. Sonnet interrotto è VOID, escluso dai confronti. | Disposizione locale del lotto annullato; la mappa non pubblica dati privati. |
| Limite esplicito | Review e giudizi nel contesto del builder non sono indipendenti. | Separazione di contesto oggi visibile in `Cascade.judge` e `directed_review`; SPJ-02/03 devono registrare il compromesso, non rinominarlo indipendenza. |

Il [contratto storico](ticket-driver.md) prescrive Jev → LLM fresco → umano e vieta
l'autoapprovazione del builder. SPJ-02 conferma un prompt judge separato in-process e
l'analisi condivisa prima del gate, senza autoapprovazione. Permessi, limiti e prove restano
espliciti nella decisione; la completion non ha strumenti. SPJ-03 conferma la review
condivisa, **non indipendente**, e il limite di qualità spiegato con esempi. SPJ-04 conferma ownership e
avanzamento dopo failure con prove osservate e limiti espliciti; nessuna garanzia è rimossa
per inferenza. Ripresa dopo crash conta come nuova apertura, non nuova istanza per ruolo.

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

1. **Trasporto e lifecycle (SPJ-01, ricerca offline disponibile):** il
   [rapporto](../research/solo-pi-jev-session-transport.md), attraverso il ticket proprietario,
   verifica documentalmente Pi 0.99.1 e raccomanda RPC per Python; SDK è alternativa
   supportata. `agent_settled`, delte per entry e resume sono documentati, non provati live.
   `--continue` conserva cronologia, non un singolo processo. Commit upstream Pi ignoto;
   crash reale, risorse installate e piattaforme non osservate restano limiti. Nessuna scelta
   di fallback/review/owners è approvata da questa raccomandazione.
2. **Incertezza (SPJ-02, confermata localmente):** [decision table](solo-pi-jev-uncertainty-decision.md)
   e conferme distinguono semantica/rischio, negativo deciso, indisponibilità, divieto,
   sotto soglia, fuori bound e malformato. Un judge in-process può decidere solo prove
   sufficienti e consentite; altrimenti analisi/gate. Non esiste ancora l'adapter reale.
   Il handoff documentale locale è validato; non è implementazione o prova live.
3. **Review (SPJ-03, confermata localmente):** [contratto e conferme](solo-pi-jev-review-decision.md)
   definiscono ruolo condiviso, solo findings, input/lettura, gate, correzioni e limite di
   3 fallimenti finali. Non si finge indipendenza; codice cambiato richiede nuove prove.
   Handoff documentale locale validato; non prova un reviewer runtime.
4. **Proprietà dello script (SPJ-04, confermata localmente):** [matrice e gestione](solo-pi-jev-script-ownership-decision.md)
   assegnano copia, lifecycle, test, freeze, prove, avanzamento e stop allo script, con
   giudizi separati e gate umano. Indipendenti dopo fallimento e resume sicuro non azzerano
   consumo né fanno diventare completed-local una consegna remota.
5. **Fattibilità (SPJ-05, prova offline):** [rapporto riproducibile](../research/solo-pi-jev-chain-prototype.md)
   con due richieste, una sola apertura normale, review/gate, tre fallimenti, indipendenti,
   resume e accounting. Due omissioni riprodotte/corrette; 20 test passati e ultimo delta
   cleanup verificato con due mirati. GO alla spec, non conformità RPC o qualità live.

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
| Trasporto ricercato, integrazione non provata | RPC/SDK documentati per Pi 0.99.1; resta da osservare il flusso confermato, non basta una cronologia riaperta. | Rapporto offline locale SPJ-01; poi fake SPJ-05 dopo le decisioni HITL. Nessuno smoke live implicito. | SPJ-01 → SPJ-05 |
| Fallback confermato, adapter non implementato | Judge in-process, non subagent; incertezza non è PASS e chiamate aggiuntive sono contate. | [Conferma e spec SPJ-02](solo-pi-jev-uncertainty-decision.md); handoff locale validato sulla propria identità, implementazione futura dopo gli altri gate. | SPJ-02 → SPJ-05 |
| Review confermata, non implementata | Contesto condiviso non è indipendenza; findings non sono prove eseguite. | [Spec e handoff SPJ-03 locali](solo-pi-jev-review-decision.md); fake SPJ-05 prima del runtime. | SPJ-03 → SPJ-05 |
| Owner confermati, adapter reale non provato | Le prove documentali/fake non sono esecuzione Pi/Jev reali. | [Matrice e handoff SPJ-04](solo-pi-jev-script-ownership-decision.md); limiti nominati nel rapporto SPJ-05. | SPJ-04 → implementazione |
| Flusso provato soltanto con fake | Peer sintetico non è RPC reale; fixture non prova qualità/auth. | [Rapporto SPJ-05](../research/solo-pi-jev-chain-prototype.md), handoff in corso; spec/ticket del primo tracer bullet, poi verifica reale separata. | SPJ-05 → implementazione |

## Ticket Plan

| ID | Tipo | Modo | Blockers canonici | Frontier corrente | Esito atteso |
| --- | --- | --- | --- | --- | --- |
| SPJ-01 | research | AFK | nessuno | Rapporto offline locale preparato; handoff/consegna separati | RPC/SDK, lifecycle e accounting documentati; prova fake definita, non eseguita. |
| SPJ-02 | grilling | HITL | nessuno | Decisione e handoff documentali locali validati | Fallback in-process, rischio condiviso e analisi/gate; permessi e consumo espliciti. |
| SPJ-03 | grilling | HITL | SPJ-02 | Decisione e handoff documentali locali validati | Review condivisa, solo findings e limite Autopilot 3; niente indipendenza finta. |
| SPJ-04 | grilling | HITL | SPJ-01, SPJ-03 | Decisione e handoff documentali locali validati | Matrice confermata script/Pi/Jev/umano per osservazione e integrazione. |
| SPJ-05 | prototype | AFK | SPJ-01, SPJ-02, SPJ-03, SPJ-04 | Prova fake, rapporto e handoff locali validati | Due richieste sintetiche nella stessa sessione fake, flusso e failure paths osservabili. |

Nessuna dipendenza è completata dalla sola emissione dei ticket. L'ordine consigliato è
SPJ-01 → SPJ-02 → SPJ-03 → SPJ-04 → SPJ-05, serialmente e con handoff attribuibile.

## Next Review

**Prossimo passo nella frontier:** eseguire SPC-01 del [contratto implementativo](solo-pi-jev-implementation.md),
poi SPC-02/03 serialmente dai loro handoff. SPJ-01–05 validati localmente, non live; nessuna
nuova intervista su scelte confermate. Delivery, binding live e benchmark restano separati.

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
