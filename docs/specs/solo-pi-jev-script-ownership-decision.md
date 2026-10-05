# Solo Pi + Jev — chi gestisce lavoro, prove e ripresa

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-script-ownership-decision`
- Role: `spec`
- Parent: [SPJ-04](../tickets/solo-pi-jev/04-decide-script-ownership.md)

## Type
Decision spec confermata; non implementazione o autorizzazione a esecuzioni live.

## Status
Confermata localmente il 2026-10-01. Dipendenze: [ricerca SPJ-01](../research/solo-pi-jev-session-transport.md)
e [review SPJ-03](solo-pi-jev-review-decision.md), con handoff canonici locali
`C:/dbench/tmp/spj01-handoff.json` e `C:/dbench/tmp/spj03-handoff.json` sulle proprie
identità. SPJ-03: tree `d96224aa...`, limite di qualità 3, non una sola correzione.
Non sono prove del futuro adapter. Pubblicazione separata; fake SPJ-05 ancora da eseguire.

## In parole semplici
Lo script fa da capocantiere: prepara una copia separata, manda i turni a Pi, esegue
controlli reali e salva risultati e consumo. Pi scrive, rilegge e corregge; Jev e il
secondo parere AI valutano le domande. Per dubbi irrisolti o permessi mancanti decide
l'utente. «Tutto verde» detto da Pi non sostituisce il risultato del comando di test.

Esempio: Salva supera i controlli nella copia; il ticket seguente può usarne il risultato
locale verificato. Se Salva fallisce definitivamente, cambia-colore può continuare dalla
versione valida precedente; leggi-file-salvato aspetta. Il lavoro fallito resta conservato.
Né questo avanzamento né la fine di un turno pubblicano o applicano codice all'originale.

## Confirmation Evidence
Domande singole, esempi e selezioni reali della conversazione; etichette senza emoji:

1. «Copia separata e prove reali»: script responsabile di copia, versione, test e risultati,
   non certificazione del Pi né sovrascrittura del progetto originale.
2. «Continua quelli indipendenti»: dopo tre fallimenti finali, preservare il lavoro fallito;
   indipendenti dalla versione valida precedente, dipendenti in attesa. Recupero dubbio: stop.
3. «Ripresa automatica sicura»: stato integro, vecchio processo terminato, permesso e budget
   validi. Contare la riapertura e conservare storia, errori e spesa. Stato dubbio: umano.
4. «Conserva e ricontrolla»: mutazioni dopo il controllo richiedono riconciliazione e nuove
   prove necessarie; dubbi o decisioni nuove verso umano. Cache normali non sono prodotto.
5. «Confermo la gestione spiegata»: riepilogo di script/Pi/Jev/AI/umano e dell'esempio Salva,
   avanzamento nella copia locale, progetto originale intatto e autorità di delivery distinta.

Gli ID dei messaggi non sono forniti: non inventati. Non si deduce consenso dalla richiesta
«termina i todos», dalla frustrazione per le domande, dal silenzio o dall'auto-approval.

## Ownership Matrix

| Attività | Owner | Osservazione/prova e limite |
| --- | --- | --- |
| Apertura e turni | Script | Un processo e una sessione logica per la catena normale, turni seriali; identity/config/cwd, aperture e stato osservati. RPC raccomandato da SPJ-01; ancora da provare. |
| Fine del turno | Script | Terminale settled e stato senza lavoro pendente; non basta agent_end o una frase PASS. Error/aborted/length/deferred non sono successo. |
| Copia e baseline | Script | Worktree distinto posseduto, baseline reale pulita e identità Git; non usare il checkout originale come c4 né toccare copie altrui. |
| Codice e test scritti | Pi builder | Modifiche nel worktree permesso. Le sue spiegazioni sono authored-by-model, non ricevute di esecuzione. |
| Test eseguiti | Script | Comando, cwd, exit/error, output e durata osservati; controllo delle scritture e dell'identità prima/dopo. Timeout/output incompleto non diventano verde. |
| Freeze e inventario | Script | Alberi Git e digest canonico del ticket, CandidateRef v2 e inventario completo; no ID inventato dal modello. |
| Rischio | Jev, invocato dallo script | Soglie SPJ-02 invariate. Incerto/non classificabile/out-of-bound/indisponibile/vietato seleziona review diretta, non basso rischio. |
| Review | Pi principale | Stesso contesto, solo findings, niente prodotto/test modificati durante lettura; non indipendente. Script salva output e osserva mutazioni. |
| Domande semantiche | Jev; judge AI in-process quando ammesso | Cascata SPJ-02, prompt distinto senza tools/cronologia builder, al massimo uno per domanda/candidato. Negativo deciso non aggirabile. |
| Artefatti e consumo | Script | Ricevute, findings, cursori e charge deduplicati per ID; prove vecchie mantengono identità. Unknown resta unknown, non zero. |
| Recovery e contatori | Script | Massimo 3 fallimenti finali per ticket cumulativi; non tre per fase, non reset dopo fix/cambio candidato/ripresa. |
| Gate e handoff | Script; umano per decisione | Motivo, candidato, prove disponibili/mancanti, lavoro conservato e consumo. La risposta umana è attribuibile e circoscritta, non un PASS automatico. |
| Avanzamento locale | Script | Solo dopo controlli sufficienti sul candidato attuale; ricevuta completed-local distinta da delivery. Dipendenze locali soddisfatte solo da ricevute valide nello stesso scope. |
| Applicazione/integrazione | Script soltanto con autorità pertinente | Verifica target/base pulita, albero e readback dopo operazione. Nessun commit/merge dell'originale da una frase del Pi o dall'avanzamento locale. |
| PR/merge remoto | Separata corsia autorizzata | Autorità, Quick/Full selezionato per scope e CI/head esatti secondo contratto di delivery; nessun permesso implicito da questa decisione. |
| Stop | Script | Fail closed per prova insufficiente, drift irrisolto, stato/permessi/budget incoerenti. Nessun successo per esaurimento. |

## Guarantees: preserved or changed
- **Preservate:** copia separata, test process-owned, identità osservata, divieto di prove
  autoreferenziali, budget/permessi distinti, isolamento della chiave Jev, target/readback
  e delivery separata. Osservatore script, ricevute attribuibili; non sandbox OS universale.
- **Modificate esplicitamente:** un processo persistente e review nello stesso Pi, non
  scratch/reviewer indipendente; judge completion in-process, non foglia Pi. La differenza
  di contesto è un limite, non una garanzia equivalente. SPJ-02/03 conservano gate e claims.
- **Recovery confermata:** normale riuso senza nuove aperture; un crash può richiedere un
  secondo lancio, contato come tale. Non dichiarare «un solo processo per sempre» dopo resume.
- **Controllo osservato, non contenimento assoluto:** gli alberi/fingerprint prima e dopo
  rilevano scritture; non impediscono ogni side effect esterno. Prove dei fake non provano
  contenimento, risorse installate, autenticazione o qualità del modello in produzione.

## Failure and Resume Contract
1. Conservare candidato, diff, output, motivo, ultima versione valida e consumo prima di
   recuperare. Non ripulire o sovrascrivere worktree estranei. Se la conservazione fallisce,
   niente avanzamento. Nessuna applicazione di GC autorizzata da questa decisione.
2. Fix ordinario: nuovo turno builder e nuova freeze; invalidare prove interessate e rifare
   controlli causali. Non rinominare la ricevuta del vecchio candidato come corrente.
3. Mutazione inattesa del prodotto, inclusi test/review che scrivono: niente approvazione
   dalla vecchia ricevuta. Riconciliare e rieseguire sul nuovo albero se è sicuro e consentito;
   altrimenti gate. Cache convenzionali osservate come cache non sono prodotto; non ignorare
   genericamente file nuovi o path non classificabili. Non fare replay cieco sulla base cambiata.
4. Base/target cambiati: osservare nuova situazione, preservare lavoro, rivalutare admission
   e causalità delle prove. Solo riconciliazione dimostrabile nel mandato/budget esistenti;
   niente sovrascritture, rebase/merge implicito o riuso di un full PASS su un altro candidato.
5. Terzo fallimento finale: fermare quel ticket senza successo. Prima di un indipendente
   conservare il fallito e ripristinare con prova la versione valida nella sola copia posseduta.
   Dipendenze non soddisfatte restano bloccate. Un errore globale di ambiente/budget/autorità
   impedisce anche altri ticket; non è una scusa per nuove chiamate autorizzate per inferenza.
6. Crash: osservare che il vecchio processo è terminato, non soltanto timeout; verificare
   session ID/file, cursore, entry/charge, baseline/candidato e ricevute. Se integri e scope/
   budget validi, riaprire la stessa storia e registrare una nuova epoch/apertura; una sola
   istanza attiva. State mismatch, output incompleto o processo forse vivo: stop e umano.
7. Compaction non azzera storia o costi. Conteggiare assistant/tool/compaction/summary/usage
   una volta per charge osservata; stats cumulativi sono confronto, non addendo duplicato.
   Uso non riportato/costi interrotti ignoti restano espliciti; stime Pi non sono fattura.
8. Chiave Jev soltanto nello script/broker: non nel child env, prompt, argv o log Pi. Permesso
   d'invio e budget sono separati dal sapere tecnico del modello; vietato non diventa retry.

## Completion Vocabulary
Fine turno = lavoro automatico terminato, non correttezza. Candidato verificato = controlli
richiesti osservati sull'identità attuale. Completed-local = risultato utilizzabile nella
copia e nel suo scope; non ticket consegnato al provider. Integrazione locale = applicazione
osservata autorizzata al target. Delivery remoto = azione distinta autorizzata e verificata.
Le dipendenze per delivery continuano a usare il contratto relativo: non tradurre una
ricevuta locale in PR merged o requisito esterno completato.

## Alternatives and Next Step
Controlli manuali, stop dell'intera catena e richiesta prima di ogni riapertura sono stati
proposti e non scelti. Non si rimuovono protezioni per essere «più semplice».
SPJ-05: due richieste sintetiche, gate/rischio/review, mutazioni, drift, tre fallimenti,
indipendenti/dipendenti, crash e charge; solo fake e repo sintetico, prima della spec finale.
Resta non provato il trasporto reale, auth/provider, risorse delle estensioni, robustezza
sotto crash reale, qualità, costi e prestazioni. Nessun live, benchmark, install/reload,
PR/merge o wiki autorizzato. Consegna di questa decisione skills-only, inline e seriale.
