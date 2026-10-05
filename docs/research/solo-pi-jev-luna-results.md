# Solo Pi + Jev — pilota Luna L4

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-results`
- Role: `research`
- Parent: [SPB-02](../tickets/solo-pi-jev-luna-pilot/02-run-luna-pilot.md)

## Scope and Identity
Lotto nuovo `spj-luna-pilot`: sei celle seriali, tre scenari, due bracci, una ripetizione,
prime quattro richieste. Fonte SPB-01 congelata: tree
`42eda41336aea2913b3cfa56034162826c645720`. Nessuna modifica dei lotti storici.
Pi installato **1.0.0**, `openai-codex/gpt-6-luna`, reasoning **medium**. La versione 0.99.1
nella ricognizione iniziale della specifica non è quella effettivamente misurata.

Il controllo bare è fresco: stesso SDK/modello/tool e un processo RPC persistente per cella,
quattro turni sequenziali, prompt TASK bare. Non è un riuso dei risultati storici print/resume.
Nel candidato tutti i ruoli principali tentati condividono processo/sessione per cella;
review **shared-context**, non indipendente. Jev resta nel parent; il judge tool-less in-process
è stato osservato nello smoke separato, non esercitato come fallback nelle celle del pilota.

## Result
**Il pilota non dimostra un beneficio del nuovo flusso.** Il confronto Lua non è valido per
un errore di materializzazione del caller. SQL/Yjs restano osservazioni descrittive, non una
prova statistica di superiorità del bare né una misura generale della qualità di Luna.

| Scenario | Bare: consegne accettate | Persistente: consegne accettate | Richieste persistenti realmente tentate | Bloccate per dipendenza |
| --- | ---: | ---: | ---: | ---: |
| Lua | 2/4 | 0/4 | 1 | 3 |
| SQL | 0/4 | 0/4 | 1 | 3 |
| CRDT/Yjs | 1/4 | 0/4 | 1 | 3 |

24 snapshot di consegna giudicati. Il bare ha tentato 12 richieste; il persistente solo tre,
con nove richieste successive non eseguite: sono snapshot dell'ultima versione valida,
**non nove tentativi falliti del modello**. I totali grezzi 3/12 contro 0/12 includono Lua
non confrontabile. Limitando ai due scenari con materializzazione LF verificata: 1/8 contro
0/8 consegne, con solo due richieste realmente tentate nel persistente.

## Stops and Attribution
- **Lua:** il clone ereditava checkout CRLF prima che il caller impostasse autocrlf=false.
  Lo stage produceva un diff di soli fine-riga, comprendente fixture non UTF-8; la lettura
  letterale falliva con `UnicodeDecodeError`. I test pubblici erano passati, ma il builder
  aveva dichiarato di non avere implementato la richiesta. Errore infrastrutturale e mancata
  implementazione sono fatti distinti. Cella/costi conservati; nessun replay.
- **SQL:** tre fallimenti finali della prima richiesta; findings strutturati ancora aperti.
  L'ultimo candidato non consegnato non supera l'oracolo. Le dipendenti attendono.
- **Yjs:** tre fallimenti finali della prima richiesta; findings JavaScript rimangono
  `unparsed` nel parser di prose limitato ai path Python. È un limite del flusso, non una
  prova che la review fosse pulita. Anche l'ultimo candidato non consegnato è respinto.

Prima delle celle SQL/Yjs, il caller è stato corretto: LF imposto **durante** il clone e
uguaglianza del tree iniziale col seed verificata prima dell'avvio. Una fixture locale
riproduce RED con conversione CRLF e GREEN senza conversione; non è una prova live.
Il candidato SPB-01 è rimasto immutato. Le versioni del caller e le celle precedenti sono
conservate separatamente. Sei candidate tree distinti non consegnati sono conservati e
giudicati per la loro richiesta, senza costruire catene controfattuali.

## Robustness at the Last Delivered Snapshot
Gli aggregati seguenti riguardano L4; i test latenti/invarianti sono cumulativi nella catena,
quindi non si sommano i valori delle quattro richieste come osservazioni indipendenti.

| Scenario | Bare: latenti coperti | Persistente: latenti coperti | Bare: invarianti mantenuti | Persistente: invarianti mantenuti |
| --- | ---: | ---: | ---: | ---: |
| Lua, confronto non valido | 6/10 | 0/10 | 8/16 | 2/16 |
| SQL | 5/14 | 0/14 | 3/13 | 1/13 |
| CRDT/Yjs | 5/9 | 0/9 | 7/13 | 1/13 |

## Measured Time and Accounting
Somma delle sei invocazioni di cella: **3.917,313 s**; include controllo, snapshot e oracoli,
non soltanto inferenza. Preflight seed/oracle: **121,578 s**. Oracoli supplementari dei
candidati: **133,749 s**. Intervallo misurato dall'ammissione del pilota alla fine dell'aggregazione:
**5.592,734 s**, include pause/diagnosi. Non è la somma delle sole chiamate modello;
comandi diagnostici senza timer restano di durata ignota.

Stima sperimentale cumulativa, **smoke e tentativi inclusi**: **0,134416986 USD**, circa
**0,118974 EUR** al cambio contabile autorizzato. Solo pilota: 0,134137552 USD
(bare 0,102866340; persistente 0,031271212). Ripartizione cumulativa:
Pi 0,134231860 USD; Jev 0,000153426 USD; judge 0,000031700 USD.

Ledger: otto avvii Pi complessivi (due smoke, sei celle), 36 reservation tutte osservate,
268 charge attribuite e uniche, nessuna reservation inflight o usage sperimentale ignoto.
Sette chiamate semantiche: sei Jev complessive e un judge nello smoke; nel pilota cinque
Jev e nessun judge. Le completions native/tool-loop sono conteggiate separatamente.

Il tetto **1.000 EUR** non è un obiettivo di spesa. Il residuo **stimato** è 999,881026 EUR:
non è saldo di fattura né nuova autorizzazione a estendere L4. Prezzi SDK/Jev sono stime,
non fatture; fattura/FX finale e costo della sessione operatore restano **ignoti**, non zero.
Ulteriore spesa richiede riconciliazione dei costi ignoti e nuova ammissione entro il mandato.
Le riserve e i limiti del caller non provano un hard cap sulla fattura del provider.

## Evidence and Limits
Record privati content-addressed: manifest/source/SDK/skill e seed/suite/canary; journal e
uscita di ciascun processo; receipt dei test pubblici; snapshot e oracoli read-only; ledger;
versioni caller, diagnosi e fixture; candidati separati; aggregati e handoff canonico.
Nessun contenuto hidden, reference/trap, credenziale o risultato dell'oracolo è stato passato
nelle richieste Pi/Jev/judge. Questo descrive l'intake osservato, **non un sandbox OS**.

Lo smoke aveva osservato due richieste sullo stesso Pi, Jev reale e completion judge Luna
medium con receipt/usage. Non è un risultato del pilota, né prova del ciclo completo riuscito.
Le celle del pilota non hanno completato una richiesta persistente: runtime osservato e
qualità/consegna restano cose diverse. Nessun claim di produzione, review indipendente,
modello superiore, release o pubblicazione. Profili richiesti, CI sull'head esatto e autorità
di delivery restano gate separati; nessun commit/push/merge o installazione del repository
di lavoro eseguito. I commit seed delle fixture isolate sono soltanto metadati sperimentali.
