# Solo Pi + Jev — come si rilegge e corregge il codice

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-review-decision`
- Role: `spec`
- Parent: [SPJ-03](../tickets/solo-pi-jev/03-decide-shared-context-review.md)

## Type
Decision spec confermata; non implementazione o prova di qualità del modello.

## Status
Decisione locale SPJ-03 confermata il 2026-10-01, dopo spiegazione in italiano semplice
ed esempi. Pubblicazione separata. SPJ-04 deve ancora confermare file, prove e avanzamento;
SPJ-05 deve provare il flusso con fake prima del contratto produttivo.

## In parole semplici

Il comportamento richiesto è **Autopilot semplificato con Jev**, non una nuova collezione
di regole da scegliere una per una. Lo script gestisce ticket e prove; un solo Pi scrive,
corregge e rilegge; Jev controlla rischi e decisioni. Quando Jev non decide, un secondo
parere AI come `/goal` lavora nello stesso processo, senza un altro Pi. Se non basta,
si chiede all'utente. Questo è il flusso confermato, non autorità per nuovi benchmark,
installazioni o merge.

**Esempio:** Pi aggiunge un pulsante Salva. Jev segnala che la gestione del file merita
attenzione. Pi la rilegge e descrive «manca la gestione dell'errore». In un passaggio
successivo può correggerla; lo script riprova il codice nuovo. Test verdi e «non vedo
problemi» non sostituiscono il controllo che il pulsante faccia davvero quanto richiesto.

Se un ticket cambia dieci parti e Jev ne considera due rischiose e una incerta, Pi rilegge
quelle tre. Nessuna parte non classificabile si considera innocua per comodità; la verifica
della richiesta completa resta distinta e deve ricevere prove sufficienti.

La rilettura è fatta dallo stesso Pi che ha scritto: **non è un secondo programmatore
indipendente**. Separare il turno e le scritture permette di identificare il codice
controllato, non di eliminare l'influenza del contesto precedente.

## Confirmation Evidence

Conferme reali della conversazione del 2026-10-01, non dedotte dal goal «termina i todos»:

- SPJ-02 ha confermato [fallback e limiti](solo-pi-jev-uncertainty-decision.md), con handoff
  locale validato in `C:/dbench/tmp/spj02-handoff.json` sul tree `65a7df8d...`.
- Prime risposte SPJ-03: «Solo findings», «Gate tipati separati», «Review diretta e coverage
  globale». L'utente ha poi avvertito che le domande erano incomprensibili; non si è
  passati all'implementazione contando quelle risposte come comprensione di altri dettagli.
- Richiesta esplicita: «Cerca di farmi le domande in cristiano che non capisco. Con esempi»
  e «Deve essere Como autopilot ma semplificato con Jev».
- Dopo spiegazione semplice, selezione «Sì, questo è il flusso» e conferma Telegram esplicita:
  «Confermo il flusso spiegato: Autopilot semplificato, script che gestisce ticket e prove,
  un Pi condiviso per scrivere/correggere/rileggere, Jev per rischi e decisioni, controllo
  AI in-process come /goal se Jev non decide, poi richiesta umana se resta incerto.
  Non è autorizzazione aggiuntiva a benchmark, installazioni o merge».
- Sull'esempio di dieci parti cambiate: «I pezzi rischiosi o incerti», mantenendo elenco
  completo delle modifiche e controllo della richiesta intera; nessuna omissione silenziosa.
- L'iniziale proposta «una correzione» proveniva dal vecchio driver, non da Autopilot.
  Alla domanda «Skill only e autopilot come funzionano ora?» sono stati verificati skill
  e codice installati. Dopo spiegazione, scelta **«Come Autopilot: limite 3»**, che
  sostituisce la proposta precedente di una sola correzione automatica.
- Conferma finale «Confermo la review spiegata» dopo riepilogo con esempio Salva: segnalare
  prima dei fix, rileggere parti rischiose/incerte, verificare la richiesta intera,
  fermarsi al terzo fallimento finale e non fingere indipendenza o controllo completo.

Le etichette sono riportate senza emoji. Source message IDs non forniti dal tool: non sono
inventati. La conferma del flusso non sceglie per inferenza gli owner definitivi di SPJ-04.

## Review Contract

1. **Quando:** dopo il turno di costruzione e la freeze osservata del candidato. Jev
   seleziona funzioni ad alto rischio secondo le soglie conservate in SPJ-02. Incerto,
   indisponibile, vietato, fuori bound o malformato allargano la review, non abbassano il
   rischio. Se non vi è alcuna parte selezionata, non occorre inventare una review diretta;
   i controlli globali non si omettono.
2. **Input:** richiesta/ticket canonico, CandidateRef osservato, inventario completo delle
   modifiche, parti selezionate con path/funzione/hunk e ricevute pertinenti. Modifiche non
   classificabili non spariscono dall'inventario. Se una review obbligatoria non può essere
   completata entro i limiti, resta una mancanza esplicita, non un risultato clean.
3. **Ruolo:** un turno dedicato dello stesso Pi; conserva il contesto del builder e non
   è indipendente. Non si apre un nuovo Pi o un subagent reviewer. Il judge separato di
   SPJ-02 riguarda le domande semantiche, non è implicitamente un nuovo reviewer con tools.
4. **Scritture:** durante la rilettura Pi produce soltanto findings; il controller salva
   quell'output in un artefatto distinto. Non cambia prodotto o test. Se il prodotto muta,
   il risultato non vale per il candidato precedente e non viene usato per approvarlo.
   Il controllo delle scritture non è una promessa di sandbox OS; SPJ-04 ne definisce
   owner e prove osservate. I fix tornano a un successivo turno builder.
5. **Formato:** conservare la prosa canonica `blocker|should-fix|nit`, posizione e spiegazione,
   e una dichiarazione clean esplicita quando appropriata. Lo script legge i risultati,
   non il PASS autoattribuito dal Pi. Mancanti, incoerenti o non leggibili restano un
   problema di controllo. Non introdurre un protocollo JSON inventato dal modello.
6. **Giudizio:** findings sono authored-by-model, non test osservati. Blocking, copertura
   della richiesta e claims passano alle domande tipate e alla cascata SPJ-02 con le prove
   del candidato. Un blocker esplicito non si ignora. Un nit non diventa automaticamente
   blocker; classificazioni ambigue non approvano. «No findings» non è prova di copertura.
7. **Correzione:** se il difetto è recuperabile e l'autorità/budget lo consentono, ritorno
   al builder. Nuova freeze; prove interessate invalidate e controlli causali necessari
   ripetuti. Findings e ricevute vecchi restano sul loro candidato, senza essere relabelati.
8. **Esaurimento:** al limite di qualità il ticket si ferma senza successo. Il comportamento
   verso altri ticket, crash e ripresa è da confermare in SPJ-04, non dedotto dalla review.

## Limite come Autopilot, non un tentativo per ogni modifica

Il valore iniziale richiesto è **3 fallimenti di qualità finale complessivi per ticket**,
configurabile come il comportamento Autopilot verificato. Comprende fallimenti delle fasi
review, QA eseguita e verifica finale; non concede tre retry distinti a ciascuna fase o
funzione. Non si azzera tornando al builder, cambiando candidato, ruolo o riprendendo.

Esempio: prima verifica finale negativa -> correzione; seconda negativa -> correzione;
terza negativa -> fermare il ticket. Il primo fallimento è compreso nei tre: non significa
prima esecuzione più tre ulteriori correzioni. Le piccole modifiche e i normali test durante
la costruzione non sono automaticamente eventi di fallimento finale. Restano comunque
entro i limiti di consumo/strumenti/tempo applicabili, mai lavoro gratuito o illimitato.

Una sospensione per mancanza di permesso o ambiente non è automaticamente un difetto del
codice da correggere. Conservare causa, tentativi, consumo e classificazione; niente PASS
per esaurimento o timeout. Il limite Jev e il singolo judge per domanda/candidato di SPJ-02
sono distinti da questo contatore di qualità e non lo resettano.

## Evidence and Compatibility

- `risk.py`: `assess` seleziona alto rischio/incerto e hunk fuori bound; `directed_review`
  oggi usa scratch e contesto nuovi, controlla scritture e legge findings. Quella separazione
  di contesto è modificata esplicitamente, non mantenuta per etichetta.
- `driver.py`: `risk_phase` osserva fingerprint e tree, ma oggi ha un loop di due review
  e un solo retry condiviso col builder. Il nuovo limite 3 è una decisione confermata,
  non una descrizione di quel driver storico o delle copie misurate.
- `findings.py`: `parse_findings` e `parse_directed_findings` distinguono clean esplicito,
  prosa strutturata e unparsed. Il regex path attuale riconosce `.py`: un futuro adapter
  non può trattare findings di altri linguaggi come assenza di difetti. La copertura di
  path/formati resta da implementare oppure deve dare controllo incompleto/gate.
- Nelle skill **installate**, `execute-ticket/SKILL.md` richiede un limite fornito dal
  caller e compone implement/simplify/review/QA/verify. Skills-only non fissa da sola
  «una correzione». `ticket-autopilot/scripts/autopilot/cli.py` imposta
  `--max-quality-failures` a 3; `kernel.py` (`record_stage`) incrementa sui fallimenti
  di qualità e ferma quando raggiunge quel limite; `ledger.py` valida le transizioni.
  Autopilot gestisce anche ordine/stato/delivery, non implementa il ticket al posto della skill.

Non cambiano copie driver, protocolli o ricevute storici. Nessuna compatibilità/shim
implicita tra vecchio e nuovo candidato. La consegna di questi ticket resta skills-only
inline e seriale: voler progettare un prodotto simile ad Autopilot non avvia il runner.

## Verification Strategy

Walkthrough documentale: review clean, blocker, severity ambigua, output mancante o
malformato, controllo incompleto, modifiche non classificabili, prodotto cambiato durante
review, test verdi ma richiesta non provata, due recovery e terzo fallimento finale.
Controllare il nuovo candidato dopo ogni fix e conservare le prove vecchie sotto la loro
identità. Risposte umane sono prove della decisione, non del funzionamento del prodotto.

SPJ-05 dovrà eseguire casi causali con fake dopo gli owner confermati in SPJ-04. Review reale,
modello/provider, auth, qualità, costi e trasporto non sono testati da questa decisione.
Non autorizza produzione, benchmark, PR/merge, installazione, reload, GC o wiki sync.
