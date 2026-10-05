# SPJ-01: trasporto e lifecycle di una sessione Pi di catena

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-session-transport`
- Role: `research`
- Parent: [SPJ-01](../tickets/solo-pi-jev/01-research-session-transport.md)

### Related
- [Frontier Solo Pi + Jev](../specs/solo-pi-jev-wayfinder.md)
- [Contratto storico](../specs/ticket-driver.md)
- [Isolamento della chiave Jev](../specs/ticket-driver-jev-key-isolation.md)

## Question

Quale interfaccia supportata del Pi effettivamente risolto permette a uno script Python di inviare richieste seriali nella stessa sessione e nello stesso processo, osservandone fine, interruzione, ripresa e consumi senza altre foglie Pi?

## Answer

**RPC è la raccomandazione tecnica per il controller Python:** un solo subprocess Pi in `--mode rpc`, un solo session ID verificato, un solo lettore continuo degli eventi e una richiesta applicativa attiva per volta. Il TypeScript SDK offre la stessa continuità tramite un `AgentSession` conservato dal processo Node/Bun, ma richiede un host JavaScript o un ponte aggiuntivo. Entrambe sono interfacce documentate; nessuna è stata provata contro un modello in questa ricerca.

`pi -p --continue` ricostruisce una cronologia: ogni invocazione è un processo nuovo. `--session-dir` sceglie lo store, non una sessione da riusare. Pi JSON mode è one-shot e non accetta turni successivi via stdin. La TUI è persistente ma non è il protocollo machine-to-machine raccomandato. Non servono ACP, un nuovo protocollo compilato dal modello o un server esterno.

Questa è **ricerca offline, non selezione implementativa approvata**. Non sceglie fallback, review, owners, politica dopo un crash o autorizzazione a riprendere. SPJ-02/03/04 restano aperti; SPJ-05 dovrà provare il flusso confermato con fake. Non dimostra qualità, autenticazione, costo o risparmio live.

## Provenienza e fonti primarie

Ricerca del 2026-10-01 sul checkout `research/spj01-session-transport`, base e target remoto osservato `001d36229093e3b4d759d585a8406be5826dc47a` di `carlitose/agent-skills`. Nessun sorgente del driver o harness è cambiato. Le letture sono attribuite a questa base, non ai checkout congelati dei benchmark.

Pi risolto dal Python Windows: shim `C:/Users/CGS03/AppData/Roaming/npm/pi.CMD`; package `@earendil-works/pi-coding-agent` **0.99.1**, radice `C:/Users/CGS03/AppData/Roaming/npm/node_modules/@earendil-works/pi-coding-agent`. `bin.pi` è `dist/bundle/cli.js`, che carica `cli-runtime.js`; questo importa `chunks/chunk-GUORCHFS.js`. Node osservato `v24.15.0`, Python `3.12.10`, requisito package Node `>=22.19.0`. `pi --version` e `pi --offline --no-extensions --help` confermano versione e flag senza aprire una sessione di modello. Non sono smoke RPC/SDK.

**Commit upstream Pi ignoto:** il package non espone `gitHead`. Non attribuire il commit del progetto al package Pi né sostituire una versione indicizzata vicina alla 0.99.1. Context7 restituisce documenti della 0.99.0 e alcuni rimandi a `main`: usati solo per orientamento; le conclusioni sono verificate sui documenti e sulle dichiarazioni distribuiti nella 0.99.1 risolta.

Fonti Pi sotto la radice sopra; i documenti Markdown elencati sono stati letti interamente:

| ID | Fonte e ancoraggi | Cosa sostiene |
| --- | --- | --- |
| P1 | `README.md`, `package.json`, `docs/index.md`, `docs/cli.md`, `docs/cli-integration.md`; help installato | Identità, requisito Node, modi, durata, flag e precedenza dello store. |
| P2 | `docs/rpc.md`, `docs/rpc-commands.md`, `docs/json.md`; `dist/modes/rpc/rpc-mode.js`: `handleCommand`, `rebindSession`, `shutdown` | JSONL, accettazione vs completamento, stato, abort, cursor, EOF. |
| P3 | `docs/sdk.md`; `dist/core/sdk.d.ts`: `CreateAgentSessionOptions`; `examples/sdk/README.md`, `01-minimal.ts`, `05-tools.ts`, `06-extensions.ts`, `11-sessions.ts`, `13-session-runtime.ts` | Factory, cwd/tools, session manager, disposal e sostituzione runtime. |
| P4 | `docs/sessions.md`, `docs/session-format.md`, `docs/message-types.md`, `docs/compaction.md`; `dist/core/agent-session.js`: `_emitAgentSettled`, `abort`, `getSessionStats` | Cronologia, entry IDs, fine del run, usage e compaction. |
| P5 | `docs/configuration.md`, `docs/settings.md`, `docs/extensions.md`, `docs/rpc-extension-ui.md`, `docs/security.md`, `docs/how-pi-works.md`, `docs/windows.md` | Discovery, trust, UI RPC, cache warming, shell e assenza di sandbox. |
| P6 | `examples/rpc-client.ts`, `dist/modes/rpc/rpc-client.js`: `collectEvents`, `promptAndWait`; `dist/modes/rpc/rpc-types.d.ts`: `RpcCommand` | Client TypeScript supportato e forme effettive dei comandi. |
| R1 | [leaf.py](../../ticket-driver/scripts/leaf.py): `pi_command`, `leaf_argv`, `invoke`, `usage`; [driver.py](../../ticket-driver/scripts/driver.py): `execute` | Lancio nativo, foglia one-shot, directory nuova e controllo per richiesta. |
| R2 | [runner.py](../../benchmarks/delivery-bench/runner.py): `arm_argv`, `cursor`, `new_events`, `summarize` | Continuazione di cronologia nei bracci Pi, nuovo driver per task, delte storiche. |
| R3 | [arbiter.py](../../ticket-driver/scripts/arbiter.py): `isolated_key`, `allowed`, `ask`, `classify`; [ticket_driver.py](../../ticket-driver/scripts/ticket_driver.py): `main`; [cascade.py](../../ticket-driver/scripts/cascade.py): `batch`, `judge`; [risk.py](../../ticket-driver/scripts/risk.py): `assess`, `directed_review` | Confine Jev, soglie e fallback/review oggi separati. |

Impronte SHA-256 delle fonti decisive distribuite, per distinguere copie della stessa versione:

| Fonte | SHA-256 |
| --- | --- |
| `package.json` | `c701ddbf28b5170deb478b8586ee713f9372027c04736946a4ffe82168ece5ba` |
| `docs/rpc.md` | `37a03d180115460a0a275022f4aeabef1e5345458df6a9b6e8a6de18474de720` |
| `docs/sdk.md` | `b334600d946c412ae2de5f95b2386ff3f0ac040c216f5132418f4c1f1994c025` |
| `docs/rpc-commands.md` | `4deeee367852f4633ef594bc079f9e9fb14640a4e3ba8a69b7c89b6f54740838` |
| `dist/bundle/cli.js` | `e79626f2dd6f94aa45d30f3fa63cd84319a6eefcd150b353cfaf274366926774` |
| `dist/bundle/cli-runtime.js` | `f007046e3311ee270a78770b357b695d070fe70f2e8df623e4f1461fa8dfb272` |
| `dist/bundle/chunks/chunk-GUORCHFS.js` | `b858ce2c4ddbfa1594142e39d7b6ebce328010e116c08db9663602cd26171425` |

Le impronte non equivalgono a esecuzione del protocollo. Il manifest completo resta nel handoff locale; il rapporto non dipende dalla sua disponibilità per leggere i fatti sopra. Documentazione ufficiale proprietaria: [repository Pi](https://github.com/earendil-works/pi), percorso `packages/coding-agent/`; il suo `main` non è un pin della copia installata.

### Query della wiki esistente

Operazione read-only `compiled-markdown`, motivo `no-supported-rag-binding`: la binding di `knowledge/` non nomina un adapter RAG supportato. Letti purpose/schema, catalogo e pagine pertinenti, senza filing o sync. `[[sources/artifact-ticket-driver]]` e `[[sources/artifact-ticket-driver-jev-key-isolation]]` rimandano ai contratti primari R1/R3; i loro Children danno il contesto dei ticket storici. Non contengono il contratto del Pi 0.99.1 né il nuovo trasporto: sono provenienza del disegno precedente, non prova della nuova integrazione.

## Opzioni supportate e vincoli di piattaforma

| Opzione | Processo / sessione | Dipendenze e limite | Esito della ricerca |
| --- | --- | --- | --- |
| RPC | Un figlio Pi persistente può conservare una sessione tra comandi. | Python standard library + Node/Pi; framing, backpressure, correlazione, UI e contenimento del processo sono responsabilità del client. | Raccomandata per il controller Python, da prototipare. |
| SDK | Un host Node/Bun può mantenere un `AgentSession` e chiamare `prompt()` serialmente. | Package importabile nel progetto host; lifecycle/resources espliciti. Python richiederebbe un ponte; non basta un package globale per risolvere ogni import locale. | Alternativa supportata, non esclusa per qualità/prestazioni. |
| Print/JSON con `--session` o `--continue` | Cronologia persistita, nuovo processo per invocazione. | CLI/Pi; selezionare il file esatto evita l'ambiguità di “most recent”. JSON non è bidirezionale. | Non realizza il requisito del singolo processo lungo la catena. |
| TUI | Processo interattivo e sessione persistenti. | Terminale/PTY e controllo dell'editor, senza il wire contract RPC. | Non scelta per l'automazione machine-to-machine. |

Windows nativo: risolvere `node.exe` e `bin.pi` dal metadata dello shim, verificando che il file sia dentro il package; non passare un `.CMD` a un launcher che richiede un eseguibile nativo, né introdurre `shell=True`. Il resolver attuale R1 è una base riutilizzabile, non un transport RPC. Git Bash serve al tool Bash; PowerShell è un tool opzionale Windows. Un futuro adapter deve possedere il contenimento e lo stop di **tutto** il processo e dei suoi figli: la cattura one-shot attuale non diventa bidirezionale cambiando soltanto `-p`.

macOS/Linux: il launcher Pi/Node e le pipe JSONL sono supportati dal contratto; toolchain e shell devono essere disponibili. Non effettuata una prova su questi sistemi. WSL è un ambiente Linux distinto, non una prova di Windows nativo. SDK documentato per Node/Bun; versione minima Bun e parità operativa Bun non accertate qui. Nessuna installazione, modifica della configurazione, update o reload.

## Lifecycle: fatti e proposta di confine

Il modulo proposto possiede apertura, lettori, correlazione, session identity, stop e checkpoint dei consumi; il chiamante gli passa i turni. Il seam sostituibile è il trasporto/launcher, non un modello finto che firma il risultato. È una proposta di confine, non un'API Pi aggiuntiva implementata. Owners di worktree, test, freeze e integrazione restano SPJ-04.

| Passo | Contratto Pi osservato | Vincolo da provare nel candidato |
| --- | --- | --- |
| Apertura | RPC resta attivo fino allo shutdown; `get_state` dà session ID/file, streaming/compacting e code. SDK factory crea la sessione e il suo manager. | Avviare una sola istanza per catena; contare separatamente lanci OS e sessioni logiche. Conservare cwd/config/versione e usare uno store dedicato persistente se serve crash recovery. |
| Turni seriali | `prompt` RPC restituisce disposition `started`, `queued` o `handled`; durante streaming senza scelta steer/followUp viene rifiutato. | Listener prima dell'invio; al massimo una richiesta applicativa in volo. Non usare steer/followUp come separazione implicita di richieste. `handled` non significa generazione né completamento: non attendere un evento che quel comando non ha avviato. |
| Fine | `agent_end` chiude un low-level run; retry, overflow, compaction o lavoro accodato possono seguire. `agent_settled` è il terminale di lavoro automatico. SDK `prompt()` attende il run. | Attendere settled e ricontrollare stato/identità/code, senza perdere una fine veloce. Il terminale non è PASS: esaminare messaggi finalizzati e cause error/aborted/length/deferred prima di valutare il risultato. |
| Cwd e tools | CLI discovery e default tools dipendono da cwd/settings/trust. SDK accetta cwd, tools, loader e managers espliciti. | Un cwd prodotto fisso; fingerprint di risorse/toolset. Un prompt “review read-only” non crea isolamento né blocca tecnicamente scritture. RPC non documenta un comando generico `set_tools`; non inventarlo. |
| Interruzione | `abort` aspetta idle ma non svuota code: RPC documenta `clear_queue` prima di abort. EOF stdin dispone il runtime ed esce. | Smettere di inviare; svuotare code, abortire, osservare esito; chiusura ordinata e deadline distinta per shutdown. Se necessario terminare l'albero e osservarne la morte prima di riaprire. Conservare prove parziali. |
| Crash/ripresa | `--session <path>` / `SessionManager.open()` ricostruiscono il contesto persistito. `--no-session` è irrecuperabile dopo exit. Un runtime switch sostituisce l'AgentSession e richiede rebind degli observer. | Un rilancio è una **nuova istanza**, anche con lo stesso session ID. Registrare epoch/lanci ed esito incompleto; riconciliare file/candidato/cursor prima di altri turni. Non presumere riavvio automatico autorizzato. |
| Compaction | Entry append-only, summary + entry recenti per il contesto; gli originali e i consumi restano. Eventi `compaction_start/end`; retry di summary e recovery possono proseguire. | Non creare una nuova sessione né azzerare accounting. Usare eventi e entry persistite, non `get_messages` come registro completo. Non trattare compaction, errore o cancellazione come successo. |

Fonte P6: `promptAndWait()` installa il listener prima di inviare, ma la sua implementazione 0.99.1 attende la raccolta degli eventi senza una propria distinzione di `handled`. Per una catena arbitraria il client deve trattare le disposition esplicitamente; non assumere che un helper risolva ogni caso. Anche l'esempio commentato `continueSession` in `sdk.d.ts` non è un campo di `CreateAgentSessionOptions`: la via riscontrata è il `sessionManager` esplicito di `11-sessions.ts`.

RPC usa JSONL con separazione sul byte LF, eventuale CR precedente rimosso; U+2028/U+2029 **non** separano record. Stdout sempre consumato, stderr drenato separatamente, scrittura completa con backpressure. Gli ID correlano risposte di comando; gli eventi di sessione in generale **non hanno request ID**. La serializzazione applicativa più lo stato impedisce attribuzioni concorrenti ambigue, non offre idempotenza del provider.

Un `response.success=true` conferma accettazione/gestione, non qualità o commit. Se il client muore tra invio, accettazione, modifica e checkpoint, il protocollo non promette exactly-once: il medesimo ID non autorizza replay. Stop e riconciliazione precedono qualunque eventuale nuova richiesta. La decisione di continuare dopo un fallimento e la base della richiesta successiva appartengono a SPJ-04.

Estensioni: in RPC select/confirm/input/editor diventano `extension_ui_request` bloccanti; il controller deve rispondere esplicitamente o preservare il gate, non autoapprovare. Alcune UI TUI sono no-op. `--approve` concede project trust, **non** autorità per acquisti, merge o bypass delle policy. Cwd, trust e tool allowlist non sono sandbox OS. Un SDK host non carica automaticamente i builtin CLI codemode/tool-search/MCP: parità di risorse non è implicita.

## Contabilità senza doppio conteggio

Una richiesta applicativa può contenere più turni assistant, tool result con usage e summarization. `message_update.usage` è cumulativo **nel messaggio**: non sommare tutti i delta e poi `message_end`. Anche `agent_end.messages`, lo stream, gli entry JSONL e `get_session_stats` sono viste sovrapposte, non quattro spese.

Proposta per il prototipo e la futura spec:

1. Prima di una richiesta, checkpoint durabile di chain/request/attempt, session ID/file, epoch del processo, candidato osservato e ultimo entry ID contabilizzato. Un contatore di lanci è distinto dal session ID. Lettore attivo prima dell'invio e nessun'altra richiesta accodata.
2. Al terminale, usare `get_entries` con `since` per leggere **solo nuovi entry in append order**; ricondurre le charge a `(sessionId, entryId)` e consumarle una volta. Usare lo stream solo come osservazione provvisoria, poi riconciliarlo. Cursor e charge devono essere persistiti atomically/idempotently rispetto al journal del controller; un cursor senza charge o viceversa non deve saltare/raddoppiare consumo dopo crash.
3. Includere usage di assistant, toolResult con usage, `compaction`, `branch_summary` ed entry `usage`, anche kind sconosciuti come metadata di consumo. `get_session_stats` somma **tutti** gli entry, inclusi rami abbandonati e storia compattata: può controllare le somme e fornire delte tra checkpoint coerenti, ma non va sommato alle charge già lette. `get_messages` è una proiezione del contesto, non l'accounting completo. [P2/P4]
4. I token del prefisso rimandato al provider nei turni successivi sono nuovi input/cache token effettivamente fatturati: **non deduplicare testo tra chiamate**. Deduplicare soltanto la stessa charge rappresentata più volte. `reasoning` è già dentro `output`; non aggiungerlo una seconda volta. Separare input/output/cacheRead/cacheWrite, costi Pi stimati e uso Jev. Il listino Pi non è la fattura della subscription.
5. Retry e tentativi falliti restano nello stesso conto cumulativo. Dopo crash leggere gli entry non contabilizzati e deduplicare sugli ID già registrati; mai riportare zero solo perché è cambiato PID o si è compattato. Cursor mancante, sessione diversa, file riscritto o charge già contata con contenuto diverso aprono un errore di riconciliazione, non un reset automatico.
6. Usage non persistito/reportato, richieste provider interrotte e custom compaction senza usage restano **costo ignoto**, non zero. Costi attribuibili a un intervallo vanno a request/attempt; cache warming tra richieste resta overhead di catena separato, senza assegnazione arbitraria. Durate misurate per invocazione, loro somma ed elapsed di catena sono grandezze distinte; un elapsed non misurato resta ignoto.

Nel codice storico `leaf.usage()` e `runner.summarize()` hanno i propri confini per foglie e tentativi; la lettura di un intero store persistente a ogni richiesta duplicherebbe i prefissi. Le nuove delte/cursor non vanno applicate retroattivamente ai risultati misurati. La contabilità sopra è un requisito proposto, non una modifica di quei metodi né un nuovo report di spesa.

### Jev: confine osservato, non API chiamata

`isolated_key()` rimuove `TYPESAFE_API_KEY` dall'ambiente del driver, la trattiene in un ContextVar e la ripristina uscendo. `ticket_driver.main()` mantiene lo scope intorno all'intera esecuzione dei candidati Jev e ai recheck approvati; `ask()` usa la chiave per l'header e valida endpoint, answers e usage. Non consultata alcuna credenziale, account o API Jev.

Una sessione persistente deve essere lanciata e **interamente terminata dentro** quello scope, con i suoi figli; riaprire un figlio dopo il ripristino dell'ambiente cambierebbe l'isolamento. Niente chiave in argv, prompt, log, hash o messaggi RPC. L'isolamento dell'environment impedisce quella forma di ereditarietà: non è un sandbox né protegge file di credenziali accessibili all'utente OS. SDK nello stesso processo Python non esiste; un host Node aggiuntivo è comunque un child boundary da sanitizzare.

Jev rischio per funzione e gate semantici restano due usi distinti. `allowed()` e gli input bound restano vincoli; risposte sotto soglia, indisponibilità, divieto di uscita dati e input troppo grandi non diventano PASS. Sostituire `Cascade.judge()` o `directed_review()` richiede SPJ-02/03, non il cambio di trasporto.

## Prova riproducibile proposta per SPJ-05

**Definita, non eseguita qui.** Fixture sintetiche, niente task, controlli o risultati privati di benchmark. Solo Python standard library e un fake executable; nessun import di un client provider attivo, nessun avvio di Pi/Jev reale, nessuna installazione. Il prototipo vive fuori dal driver misurato e dopo le decisioni HITL.

Il launcher fake registra `start_count` e token di istanza; il server fake crea un solo `sessionId`, conserva history e risponde al sottoinsieme RPC documentato. Produce response/event/entry controllati; Jev è un transport fake separato con usage predeterminato. Le counters devono essere osservate nel fake/process boundary, non semplicemente dichiarate da un oggetto chiamato “session”.

| Caso | Iniezione / azione | Osservazione richiesta |
| --- | --- | --- |
| Due richieste | Aprire una volta; prompt A, settled, checkpoint; prompt B che dipende da un token sintetico di A. | Due request ID distinti, una sessione logica, `start_count=1`, stessa istanza, B vede history di A, nessuna foglia judge/reviewer extra. Solo continuità/lifecycle, non comprensione del modello. |
| ACK precoce e retry | Response accepted; `agent_end(willRetry=true)`; altro run; settled. | B non parte all'ACK o al primo agent_end. Gli usage di entrambi i tentativi restano contabilizzati. |
| Fine veloce / handled | Settled immediato; separatamente response handled senza run. | Listener non perde il terminale; handled non blocca aspettando un settled inesistente e non è una generazione riuscita. |
| Framing/backpressure | Record LF in frammenti, CRLF, testo con U+2028/U+2029; stderr e output oltre buffer. | Record ricostruiti senza separator splitting spurio; stderr non parsato come JSON; nessun deadlock con lettori attivi. |
| Compaction e deduplica | Usage update cumulativi 2/5, message_end 5, entry assistant 5; compaction usage 3 e nuovo assistant usage 7. | Charge per entry una volta: 5+3+7, non somme dei delta o ripetizione delle history. Sessione/istanza stabili. |
| Usage extra / mancante | Entry tool usage, branch summary, usage kind nuovo; custom summary senza usage. | Consumi noti mantenuti separatamente; charge mancanti restano unknown e non PASS “costo zero”. |
| Abort / exit | Code pendenti; clear_queue, abort; EOF; variante child non termina. | Nessuna richiesta successiva in automatico; reaping/timeout espliciti; nuova istanza vietata prima di osservare la morte della precedente. |
| Crash e ripresa | Crash dopo charge prima del checkpoint; riapertura fake dello stesso session ID, se prevista dalla policy confermata. | Lancio 2 ed epoch 2 visibili: non chiamarlo singolo processo. Charge deduplicata, candidato riconciliato, attempt incompleto preservato; nessun replay cieco. |
| Identità inattesa | Session ID cambia, cursor ignoto, entry già vista cambia o worktree deriva. | Stop con motivo attribuibile; niente reset del consumo né successivo prompt/integrazione automatica. |
| Chiave Jev | Chiave **sintetica** nel parent, isolamento prima del fake child e recheck. | Il child non la vede; il fake Jev riceve l'header previsto. Nessun valore segreto nel journal. Non è prova di sicurezza OS. |
| Garanzie | Test sintetici verdi ma evidenza insufficiente; Jev incerto/indisponibile; review scrive. | Attese secondo SPJ-02/03/04 confermati; questo rapporto non sceglie esiti o owner e non considera i fake live. |

Il test deve fallire se il launcher viene riaperto tra A e B, anche quando un fake ricostruisce la stessa history. Una prova distinta di resume deve invece mostrare esplicitamente il secondo lancio: queste due asserzioni non sono intercambiabili. Dopo SPJ-05, eventuali smoke reali richiedono mandato, ambiente e budget separati.

## Unknowns e prossima frontier

Risolte documentalmente: esistenza di RPC e SDK persistenti, terminale `agent_settled`, necessità di serializzazione client, apertura/resume, compaction e superfici disponibili per usage. Non risolte: comportamento reale delle estensioni installate in RPC, autenticazione/provider, recupero sotto crash reale, qualità/costo, differenze macOS/Linux/Bun, e commit upstream non pubblicato dal package.

La ripresa tecnica non garantisce la continuità di ogni risorsa privata di un'estensione: documentati rebind e ricostruzione dello stato, non parità universale. Parità della configurazione specifica e contenimento del processo vanno verificati nel futuro adapter; non usare il pin o i manifest dei lotti storici come prova di questa copia Pi.

**Prossimo passo: SPJ-02, grilling del fallback.** Poi SPJ-03 (review) e SPJ-04 (owners/garanzie); soltanto dopo SPJ-05 e la spec implementativa. Il rapporto non termina il refactoring, non cambia il contratto storico, non riapre Sonnet VOID, non autorizza benchmark, pubblicazione provider, GC o sincronizzazione personale.
