# Solo Pi + Jev — prova della catena con fake

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-chain-prototype`
- Role: `research`
- Parent: [SPJ-05](../tickets/solo-pi-jev/05-prototype-two-request-chain.md)

## Question and Branch
Il flusso confermato regge due richieste, review e gate nella stessa sessione principale,
senza un processo per ogni ruolo, e conserva prove/errori/consumo durante i recovery?
Logic branch: backend e lifecycle, non UI. Utile se rende osservabili continuità, identità,
stop e riaperture. È un prototipo throwaway, non il futuro driver.

## Dependencies and Method
SPJ-01/02/03/04 verificati tramite i rispettivi handoff canonici locali e decisioni reali;
la matrice è confermata, non dedotta da default. Consegna skills-only inline e seriale.
Scratch posseduta: `C:/dbench/tmp/spj05-prototype/`, separata da repo e copie misurate.

Un processo Python fake persistente sostituisce Pi, con comandi/eventi LF JSON e storia
persistita; un judge fixture nello stesso processo sostituisce la completion. Due richieste
lavorano in un worktree Git sintetico distinto dall'originale sintetico. Freeze usa gli
alberi reali e il digest del ticket tramite funzioni canoniche, non ID inventati. Lo script
lancia il vero subprocess di test della fixture e conserva exit/output/candidato.
Jev è sostituito da risposte sintetiche: classifier e soglie reali, strict judge parser e
findings parser del sorgente posseduto. `arbiter.ask` usa un transport in memoria nei test
HTTP 429/529: nessuna richiesta HTTP, Pi reale o accesso a credenziali.

## Reproduction and Source References
Comando dalla scratch: `python -X utf8 -B -m unittest -v test_prototype`.
Nessun install. Fonte finale `prototype.py`, SHA-256
`8c7c575239e7df278d8abc6c86c0d28897bbf5b75dcffcdd0f8bc48e3380547d`;
`test_prototype.py`, SHA-256
`5c48ff389e6e690c1d342bb7ec90a1923a623822d69339c7b17128fe1ed78288`.
`attempt-1..4.json` e `.log` conservano comandi, tempi, fingerprint ed esiti; `cases/`
conserva workspace/original/sessione/diff/result.json per caso, nessun GC. Varianti iniziali
in `versions/`, ricostruite dai delta e verificate contro SHA originali dei log, non spacciate
per il codice finale. Riferimenti locali preservati; nessun artifact pubblicato al provider.

## Observed Results
| Tentativo | Prova e risultato | Durata invocazione |
| --- | --- | --- |
| 1 | 18 test passati sul modello iniziale; non sufficiente per reentry/accounting Jev. | 85,109 s |
| 2 | Due test causali aggiuntivi FALLITI: contatore 6 invece di 3 alla reentry; zero charge Jev conservate. | 9,328 s |
| 3 | Dopo correzione delle due omissioni e cache delle decisioni, 20 test passati. | 84,969 s |
| 4 | Dopo fix della pipe stdin del child già morto e EOL delle sole fixture, due test crash/resume mirati passati con ResourceWarning trattato come errore. | 8,610 s |

Somma nota di TUTTE le invocazioni: **188,016 s**, non elapsed end-to-end o benchmark.
Letture, costruzione, review e metadata hanno durata ignota. La suite completa del tentativo
3 non viene rinominata come PASS sul codice finale: sul delta finale sono passati i due
controlli causali interessati. Tempo, token e usage delle fixture non sono stime di costo
reale del modello o prestazioni di Pi. Failure precedenti non cancellate.

## Causal Coverage
- Due richieste completate localmente, stessa session ID, stesso PID e una sola apertura;
  ricevute per ruoli/test distinte e CandidateRef differenti. Originale sintetico intatto.
- Jev confident sì/no; negativo non aggirato da judge né re-query sullo stesso input;
  incerto, unavailable, malformed, vietato e bound; permesso judge separato e insufficienza
  verso analisi condivisa/umano. Judge unico per domanda/candidato, nessuna foglia nascosta.
- Review solo delle funzioni high/uncertain, soglia 2,5; low non omette il controllo globale.
  Blocker ferma o rientra al builder, nit non è blocker; output non letto/formato .ts non
  supportato resta incompleto, non clean.
- Test rossi: due fix possibili, stop al terzo fallimento; reentry non resetta. Test verdi
  con prove insufficienti non approvano. Prove precedenti restano sulle vecchie identità.
- Test/review che modificano prodotto invalidano il candidato; drift della base blocca
  globalmente senza sovrascrivere la modifica esterna. Diff fallito preservato e baseline
  valida ripristinata solo nella fixture posseduta. Indipendente continua, dipendente aspetta.
- Crash/malformed/nonfinal stop non sono PASS; processo ancora vivo, budget o autorizzazione
  mancanti, checkpoint corrotto impediscono resume. Resume tra checkpoint integri mantiene
  sessione/charge, conta seconda apertura e non duplica il processo. Compaction non azzera.
- Charge fake Pi/compaction/judge e Jev conservate: stesse entry deduplicate, unavailable
  usage esplicitamente ignoto. La sentinel Jev non è vista dal child o negli artifact Pi.
- Stderr drenato separatamente; U+2028 nel testo non spezza i record LF. Non basta il buon
  trasporto: semantic insufficiente e candidato mutato producono gate anche con output valido.

## Answer and Recommendation
**GO alla spec e prima tracer bullet, con limiti**, non approvazione di produzione.
Il modello rende coerenti le decisioni, e i due difetti trovati rafforzano i test richiesti:
contatori duraturi e accounting di tutti gli attori. Le correzioni attuano scelte già
confermate, non le sostituiscono; nessuna ulteriore decisione di design necessaria.

Tenere test/invarianti e confini di proprietà; non promuovere il prototipo in blocco.
Scartare peer fixture, prompt di test e Git setup sintetico dall'implementazione reale.

## Limits and Next Frontier
**Non provati:** protocollo RPC nativo/configurazione installata, adapter ModelRuntime,
auth/provider/modello effettivo, qualità di builder/review/decisioni, crash reale del
controller, completa durability/budget enforcement, contenimento OS e prestazioni.
Il peer è ispirato a RPC, non un test di conformità dell'API. Rischio e permessi sono fixture;
la semantica delle risposte del modello non è verificata. Fake usage non è fattura.
Review di questa prova inline shared-context, non indipendente. Non affermare che tutti
gli input fuori bound siano decidibili: la fixture distingue bound Jev e sufficienza judge.

Prossimo passo: spec implementativa delle decisioni confermate, ticket AFK tracer-bullet e
TDD con peer sostitutivi; adapter e gap reali espliciti. Non modificare benchmark, driver
storici/copie, ledger o Sonnet VOID. Live, nuove misure, pubblicazione/merge, installazione,
reload e wiki richiedono autorità pertinente: nessuna viene concessa da questa prova.
