# Solo Pi + Jev — pilota Luna del candidato persistente

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-pilot`
- Role: `spec`
- Standalone: true

### Children
- [SPB-01: adattatore e prova nativa](../tickets/solo-pi-jev-luna-pilot/01-native-persistent-arm.md)
- [SPB-02: pilota e rapporto locale](../tickets/solo-pi-jev-luna-pilot/02-run-luna-pilot.md)
- [SPB-03: riparazioni locali dopo il pilota](../tickets/solo-pi-jev-luna-pilot/03-repair-observation-boundaries.md)
- [SPB-04: riconciliare e preparare una prova separata L4](../tickets/solo-pi-jev-luna-pilot/04-prepare-corrected-l4.md)
- [SPB-05: eseguire la sola catena corretta e confrontare i vecchi Luna](../tickets/solo-pi-jev-luna-pilot/05-run-corrected-l4.md)
- [Riconciliazione e preparazione, non misura live](../research/solo-pi-jev-luna-reentry-preparation.md)

### Related
- [Contratto implementativo SPC](solo-pi-jev-implementation.md)
- [Wayfinder SPJ](solo-pi-jev-wayfinder.md)
- [DBH-09](../research/delivery-bench-hard-results.md)
- [DBH-16](../research/delivery-bench-hard-drivers.md)

## Type and Status
Feature/experiment spec. Mandato dell'utente: «dobbiamo fare i banchmark con questo,
prova il luna, so che è scarso»; alla domanda sul tetto inclusivo di Pi/Jev/judge:
«1000 euro». Tetto complessivo 1.000 EUR, non obiettivo di spesa. Accettazione operativa
esplicitata: prova breve poi pilota a L4; L12 e ulteriori ripetizioni esclusi. Nessuna
pubblicazione, merge, installazione globale o riapertura di lotti precedenti autorizzata.

## Goal
Misurare il nuovo flusso persistente contro un bare fresco, stesso Luna medium, stessi
seed/richieste/suite dei tre scenari difficili. Prima verificare i confini nativi che i
fake SPC non dimostrano. Non attribuire un risultato negativo al modello senza separare
errori di trasporto, osservazione, budget, permessi e stop semantici del candidato.

## Confirmed Inputs and Provenance
- Candidato SPC-03: tree `651f04e3b9aa65c21335e849d80da391fe76a07d`; handoff
  `C:/dbench/tmp/spc03-handoff.json`, implementation-complete/release-blocked. SPB non
  cancella quei gate né rinomina prove simulate come native.
- Nuovo worktree posseduto `C:/pi-spb01`, da main `001d36229093e3b4d759d585a8406be5826dc47a`,
  index/worktree inizializzati con il tree SPC senza commit o mutazioni dell'altro checkout.
- `openai-codex/gpt-6-luna` presente nel catalogo locale; Pi 0.99.1. Auth/provider/routing
  restano da osservare, non dedotti dal catalogo. Fonte API installata prevale su Context7
  `/earendil-works/pi/v0.99.0`, consultato per RPC/custom entries/ModelRuntime.
- Scenari privati già esistenti: lua-vm, sql-engine, crdt-yjs. Seed, richieste e hidden suite
  rimangono immutabili. Jev usa la credenziale già esistente, isolata dal processo Pi.
- Cambio contabile di riferimento ECB del 1 ottobre 2026: 1 EUR = 1.1298 USD; fonte
  `https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html`.
  Quote, data di acquisizione e artefatto browser vanno nel record privato del mandato.
  Spesa in USD e equivalente EUR rimangono distinti; stime SDK non sono fatture.

## Scope and Admission
Nuovo lotto `spj-luna-pilot`, mai appendere ai lotti dbh/driver/Opus. Sonnet resta VOID.
Due bracci: `bare`, `pi-jev-persistent`. Tre scenari, una ripetizione, prime quattro richieste:
sei catene e 24 richieste giudicate, più una prova nativa breve separata, non sommata al pilota.
Esecuzione seriale inline. Il candidato può essere avviato solo come braccio di questa misura,
non per implementare/consegnare SPB né come runner/scheduler di ticket del repository.

SPB-01 possiede un adapter di una cella esplicita nel benchmark, non una nuova CLI di delivery.
Il caller fornisce cella, argv Pi esatto, copie, ticket canonici, comandi test, snapshot owner,
mandato e budget. Il ciclo segue soltanto la sequenza sperimentale già definita; niente
selezione di cartelle, provider mutation, approvazione automatica di gate o scheduler ledger.

## Persistent Arm Boundary
Riutilizzare ChainSession/ChainController/DecisionEngine/ChainJudge. Un processo/sessione Pi
per la catena e tutti i ruoli principali. Judge = completion tool-less nel medesimo processo;
Jev resta nel parent. Permesso distinto per entrambi, dati limitati a richiesta/codice/prove
pubbliche della cella: niente hidden suite, reference/trap/oracle results, chiavi o altri lotti.

Ingress di ogni richiesta: serializer canonico produce Ticket Envelope/body con scope e
comandi test del caller; non fare passare prosa legacy come ticket. Una facciata di prompt
spiega builder/fix/review/analysis e il formato dei findings; non inventa metadata modello.
La review conserva criterio globale e read-only, né il prompt né l'adapter approvano il codice.

Per un prodotto sperimentale il caller può autorizzare esplicitamente una directory posseduta
(es. `.`) oltre a file letterali, comprese nuove sorgenti/test. ChainController deve riconoscere
quella directory durante freeze senza autorizzare path esterni, `..`, assoluti o `.git`.
Preservare il comportamento dei caller con scope solo-file, checkpoint e restoration.

Modello e thinking dei ruoli registrati: builder/review/analysis Luna medium; bridge judge
passa esplicitamente reasoning medium a completeSimple e ne conserva il binding nella receipt.
Nessun fuzzy fallback/provider alternativo se il runtime non trova quel modello/configurazione.

## Observation, Budget and Failures
Record privati conservano identità sorgente/SDK/skill, pid/sessione/launch, candidate per ticket,
receipt test/oracle, binding/question/state/contract, native/custom usage e tutti i tentativi.
Non sommare l'osservazione usage di DecisionEngine alla stessa charge della sessione. Native
alias deduplicati per identità verificata; usage mancante/fallimento interrotto rimane ignoto.

Mandato monetario è cumulativo, include Jev, compaction e judge; nessun reset da retry o nuova
cella. Budget gate prima di avvio/chiamata e dopo consumi osservati; costi ignoti fermano nuova
spesa finché riconciliati. Nessuna promessa di tetto sulla fattura da soli contatori SDK.
Caller usa limiti finiti di tempo/call/launch e una riserva per la chiamata in volo; registra
l'effettivo limite applicato e il rischio residuo, non un enforcement non eseguito. Prima della
prova, quote/pricing/riserva e comando modello devono essere legati al record del lotto.

Al terzo fallimento finale ticket fallito; uncertain/errore non è PASS. Conservare candidati
falliti/gated separati dalla versione consegnata e giudicarli a parte, senza ricostruire una
catena controfattuale. Le richieste successive dipendenti attendono; eventuali indipendenti
partono dalla versione valida, secondo contratto SPC. Non aggirare il gate per finire L4.
Timeout non dimostra morte. Ripresa richiede morte/checkpoint/permesso/budget osservati;
nessuna ripartenza cieca e nessuna cancellazione delle copie con evidenza.

## Oracle and Comparability
Riutilizzare il judge Docker privato invariato, read-only/no network, prima/dopo digest uguali.
Snapshot per richiesta; solo il caller/oracolo vede le suite nascoste. Bare fresco sullo stesso
Pi/catalogo/manifest corrente: i risultati Luna storici sono contesto, non controllo appaiato.
C1a/c3a storici non sono rinominati nel nuovo braccio. Report L4 descrittivo: successo di
trasporto e accettazione sono cose diverse; un pilota piccolo non prova superiorità causale.

## Implementation Slices and Verification
SPB-01: adattatore posseduto, scope-directory e reasoning esplicito, fixture causali RED/GREEN,
review/QA/audit locali, poi prova nativa budget-bound di due richieste + Jev/judge. Gate di
SDK/model/auth/event/billing osservati o riportati esattamente; non basta un test fake.
SPB-02: congelare la fonte validata SPB-01, copie sperimentali nuove, controllare Docker,
canary/seed/suite/skill digest e limiti; eseguire sei celle serialmente, osservare e giudicare
snapshot, aggregare risultato/costi/stop e scrivere rapporto locale senza dati privati.

Profili obbligatori e CI sull'head esatto restano necessari prima di futura pubblicazione.
Nessun test completo ripetuto per semplice drift del candidato; ogni check ha ragione causale
ed account cumulativo. Wiki compilata non contiene gli artefatti SPC: query read-only in
compiled-markdown/no-supported-rag-binding; primarie e handoff prevalgono, sync deferred.

## Post-pilot Repairs — SPB-03
Mandato successivo esplicito: «Correggi tutto», riferito ai difetti spiegati dopo SPB-02.
Corsia skills-only, inline e seriale; solo correzioni e prove locali. Non autorizza nuove
chiamate Pi/Jev/judge, benchmark, pubblicazione, installazione o alterazione dei risultati.
Baseline locale delle riparazioni: tree SPB-02 `6fca3cd863db87e0db1e19d405a47980640f5200`.
Gli esiti e i costi originali del pilota conservano fonte e identità proprie.

Fatti: il reader findings riconosce soltanto `.py`; il fix riceve findings ma non receipt
process-owned; il confronto Git UTF-8 può generare un'eccezione non classificata; il clone
privato è stato corretto per LF solo nella scratch. La stima economica SPB-02 non comprende
la sessione operatore. Nessuna correzione dimostra capacità del modello o successo live.

Target e invarianti:
- Findings per file C/JavaScript/TypeScript/Python e altri file relativi con estensione,
  mantenendo severity/path/line/prosa. Una review non interpretabile conserva testo e causa,
  apre un gate senza consumare i tre fallimenti di codice, senza diventare clean o PASS.
- Ogni fix e review riceve esito e osservazioni pubbliche dei test del controllore, legati
  al candidato, con receipt integrale content-addressed e preview bounded esplicitamente
  troncata. Nessun dato hidden, nessun criterio indebolito o assenza scambiata per successo.
- Errori di processo/cattura e diff non UTF-8 sono infrastruttura, non errore del modello:
  candidato, receipt e diff grezzo sono conservati; gate durevole senza replay. Un timeout
  di test resta un esito di test fallito, non prova di morte. Inflight resta irrisolto se
  il turn si interrompe. Scope/read-only/permessi e tre fallimenti reali restano invariati.
- Un helper posseduto clona solo verso una destinazione nuova, forza LF durante il clone,
  verifica l'uguaglianza del tree iniziale con il seed e non scrive l'originale.
- Budget distingue stima sperimentale, stima cumulativa operatore e fattura ignota. Totale
  e residuo combinati sono null se manca una componente; non si presentano 0,12 EUR come
  costo totale. Osservazioni operatore attribuite/idempotenti/cumulative, mai reset al ribasso.
  Nuova spesa/launch richiede contabilità operatore riconciliata e headroom inclusivo; nessuna
  promessa di hard cap sulla fattura. Ledger storici non migrati o riscritti per inferenza.

Verification: fixture locali RED/GREEN per findings C/JS, errore di formato che non diventa
fallimento di codice, fix che dipende dallo stderr del test, diff non UTF-8 conservato,
processo/cattura falliti, clone LF con configurazione ereditata CRLF, conti combinati ignoti,
dedup e regressione negativa/tre fallimenti/dipendenze. Sessione/model/classifier sono
sostituiti; Git e subprocess di test sono reali. Profili release e CI rimangono gate separati.

## Reentry Preparation — SPB-04
Dopo SPB-03 l'utente chiede se ripartire. La risposta propone di riconciliare il budget e
preparare una nuova catena L4; «fallo» autorizza queste due attività, non un lancio live.
Skills-only inline, nessuna delega, runner, provider mutation, pubblicazione o installazione.

Fatto nuovo: il JSONL operatore conserva usage SDK per assistant, eventuali toolResult,
usage entries, compactions e branch summaries. Il formato e `getSessionStats` installati
includono anche la storia compattata, non solo l'ultimo contesto. Il costo operatore non
va più lasciato genericamente ignoto se questi record sono disponibili e attribuiti.

Target:
- Ricostruire stime SDK dal messaggio umano che chiede il benchmark Luna (entry
  `fd66faa3`, `2026-10-01T21:31:19.174Z`), comprendendo preparazione, misura e riparazioni.
  Registrare file/sessione, prefisso immutabile in byte e SHA-256, scope temporale, record,
  componenti, dedup e copertura. Missing/malformed costs o compact senza usage restano gate.
  Non attribuire automaticamente i giorni precedenti di lavoro estraneo a questo lotto.
- Conservare tutti gli otto launch, 36 reservation, sette semantic calls e 268 charge dello
  storico; originale non scritto. Budget, stima operatore e fattura sono cose diverse:
  totale/residuo sono stime al cambio contabile originale, mai garanzia di fattura/hard cap.
- Preparare soltanto `spj-luna-corrected-l4-prep-1`, una catena persistente `crdt-yjs` con
  prime quattro richieste e dipendenze sequenziali. Scelta tecnica minima: attraversa il
  parser JS che nel pilota non interpretava i findings. Nessun bare, Lua, nuova ripetizione
  completa, L12 o conclusione comparativa. Una nuova autorizzazione è necessaria per lanciarla.
- Fonte sperimentale corretta: CandidateRef SPB-03 e tree
  `6e78e725a4c3eee881c1d8b54a1a1abb4facf320`. Separare questa identità runtime dal candidato
  documentale SPB-04. Nuova copia immutabile, seed/public requests canonici invariati,
  LF nel clone e tree iniziale uguale al seed. Hidden suite soltanto hash/provenienza nel
  caller; mai contenuto nei ticket/prompt/progetto. Nessuna suite/oracle eseguita ora.
- Manifest prep-only con quote/modello/argv/settings/question/policy hashes, receipt e
  cost snapshot; `live_launch_authorized: false`. La copia finanziaria parte dai byte
  del ledger originale e usa soltanto l'owner Budget per aggiungere stima operatore;
  non è un nuovo mandato, non rinnova il vecchio lotto né azzera contatori.
- Preflight statico: grafo/tree/serializer, copie e input, hash SDK/skills/image metadata
  già presenti (senza pull/start), contabilità e gate. In assenza di risorsa, conservare
  la preparazione e nominare la mancanza: nessuna installazione o consenso dedotto.

Verification: confrontare i componenti con i record SDK e l'owner `getSessionStats`,
verificare hash/prefisso e prezzi presenti, cumulativo invariato e readback Budget sulla
copia. Validare quattro ticket runtime con serializer canonico, solo richieste pubbliche,
LF/tree originale/copia, manifest/source/SDK/skills. Niente suite runtime completa ripetuta
per documentazione; profili release/CI e ciclo reale corretto restano gate propri.

## Corrected L4 Execution — SPB-05
Nuovo mandato: «Avvia il banchmaerk e poi confrontiamolo con i vecchi sempre su quello luna».
Si riferisce alla sola catena Yjs L4 preparata in SPB-04: un avvio/cella persistente,
quattro richieste seriali, Luna medium, fonte corretta SPB-03 `6e78e725a4c3eee881c1d8b54a1a1abb4facf320`.
Non estende a bare/SQL/Lua/L12, nuove ripetizioni, modelli, delivery o deleghe. Confronto
storico descrittivo di Yjs sullo stesso Luna, non nuovo controllo appaiato o inferenza causale.

Ammissione: validare SPB-04, grafi/target/source/SDK/skills/input/immagini; aggiornare usage
operatore. Copiare la preview finanziaria cumulativa in un nuovo store posseduto, senza
alterare vecchi byte o contatori. Budget owner continua a consumare il medesimo tetto
€1.000 e limiti residui; un record separato conserva questa nuova autorizzazione di scope,
non un nuovo tetto né raw modifica di authority/ledger. Il caller controlla entrambi i
mandati (originale finanziario e nuovo avvio), identità e slot residui. Solo l'API Budget
aggiunge osservazioni/consumi. Fattura/cambio finale ignoti: SDK è stima, non hard cap.

Usare il source snapshot e i quattro request input preparati invariati; nuovo clone prodotto
separato dall'input prep, LF/tree seed uguali. Una sessione/PID per tutti i ruoli, Jev nel
parent isolato, judge in-process, domande/policy/soglie/test invariati. Niente hidden/oracle
nei prompt. Una cella esplicita tramite adapter esistente, nessun runner di consegna o
nuovo scheduling. Fonte/eventi/candidati/test/diff/usage/limiti e tentativi restano attribuiti.

Tre fallimenti reali, formato/infrastruttura/uncertainty distinti, nessun replay o reset.
Conservare e giudicare snapshot delivered e candidati gated separati; richieste dipendenti
restano bloccate, non tentate. Oracle privato invariato/read-only/no-network, solo dopo il
turn e mai feedback al modello; errore oracle è gate, non model failure o dato inventato.

Confronto: SPB-02 Yjs persistente e bare, poi aggregati storici DBH Luna compatibili per
prime quattro richieste se identità seed/suite/request/modello verificata. Registrare
SDK/skill/protocollo, repliche e denominatori diversi; gli invalidi/VOID non diventano
comparabili. Nessuna nuova esecuzione dei vecchi lotti. Rapporto solo aggregati: tentati,
bloccati, consegnati, accettati, candidati separati, difetti osservati e costi cumulativi.
Review/QA/audit locali sul documento congelato; release profile, exact-head CI e publication
restano gate separati. Nuova misura non cancella la provenienza dei fallimenti precedenti.

## Non-goals
L12, nuove ripetizioni oltre l'unica catena autorizzata SPB-05/modelli, riavvio Sonnet, editing lotti/copie storiche, Autopilot come
lane di consegna, deleghe, nuove soglie Jev, autoapprovazione, merge/push/PR, install/pin/reload,
GC/cleanup estranei e certificazione produzione. Nessuna garanzia di qualità o minor costo.
