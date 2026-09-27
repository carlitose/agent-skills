# delivery-bench difficile — quale problema, con quale oracolo

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-candidates`
- Role: `research`
- Parent: [delivery-bench-hard-wayfinder.md](../specs/delivery-bench-hard-wayfinder.md)

## Domanda
Quale problema software molto complesso (non un'app) può diventare uno scenario di delivery-bench?
Deve avere 12 richieste in sequenza e un giudice nascosto deterministico, offline e quasi
perfetto, e deve girare nell'harness attuale (container per scenario, `--network none`).
Serve a scegliere gli scenari della [mappa](../specs/delivery-bench-hard-wayfinder.md) (DBH-01).
Fonti consultate il 2026-09-27.

## Risposta
Proposta: tre sistemi reali, maturi e con licenza MIT. Per ciascuno esiste un oracolo esterno che
non dobbiamo inventare:

| Scenario | Seme | Oracolo esterno | Latenti reali |
|---|---|---|---|
| `lua-vm` (C) | interprete Lua 5.4 a una release fissata: lexer, parser, generatore di codice, VM a registri, GC incrementale e generazionale, API C | suite ufficiale di test della stessa release; ASan/UBSan come in `c-recq` | bug documentati della release, con esempio minimo e patch |
| `sql-engine` (Python) | executor SQL in puro Python di sqlglot: parse, 17 regole di ottimizzazione, piano, esecuzione | confronto differenziale con SQLite/DuckDB; risultati attesi calcolati una volta e congelati, come in sqllogictest; la suite di sqlglot come invarianti | fix upstream successivi con i loro test di regressione |
| `crdt-yjs` (JavaScript tipizzato con JSDoc/tsc) | Yjs: CRDT con tipi condivisi, encoding degli update, undo | test casuali con seed (PRNG di `lib0`) che confrontano la convergenza fra client; la suite di Yjs; decodifica dei documenti prodotti alle richieste precedenti | come sopra |

Questi problemi separano i bracci per tre motivi:
- **Evoluzione di una codebase matura.** Le richieste fanno evolvere ogni volta un sistema
  esteso, che nessun braccio può tenere tutto in contesto.
- **Invarianti forti.** Ogni nuova funzionalità può rompere quelle vecchie: una suite ufficiale,
  un'equivalenza con un motore di riferimento, la convergenza.
- **Contratti che una tentazione può rompere.** Formato binario, API C, encoding degli update,
  convenzioni del codice esistente.

Scartati:
- **Maelstrom/Jepsen**: il giudizio dipende da processi e tempo reali, quindi due giudizi dello
  stesso albero possono differire. Il nostro giudice deve dare lo stesso risultato ogni volta.
- **Un compilatore da zero**: è oltre la scala di una catena.
- **App frontend**: le esclude l'utente.
- **happy-dom con web-platform-tests**: l'harness del browser pesa più del problema.

## Evidenza
- **Benchmark esistenti** (SWE-EVO, DeepSWE, HORIZON):
  - **SWE-EVO** ([arXiv 2512.18470](https://arxiv.org/abs/2512.18470)). Contiene 48 task tratti
    dalle release note di 7 progetti Python maturi. Ogni task tocca in media circa 21 file e ha
    874 test. GPT-5.4 con OpenHands risolve il 25%, contro il 72,8% di GPT-5.2 su SWE-bench
    Verified. Far evolvere codebase mature è ciò che separa, mentre il problema isolato satura.
  - **DeepSWE** ([deepswe.lol](https://deepswe.lol/)). Ha 113 task originali su 91 repository e 5
    linguaggi, con verificatori scritti a mano sul comportamento, e prompt brevi che chiedono
    molto codice (circa 5,5× SWE-bench Pro). Il migliore arriva al 70%, claude-sonnet-4.6 high al
    32%. Fra i repository c'è `yjs/yjs`.
  - **HORIZON** ([horizonbench.org](https://horizonbench.org/)). È un aggregatore di 33 classifiche,
    con peso principale su METR Time Horizon. Non ha task propri, quindi non è una fonte di scenari.
- **Come fare l'oracolo** (Carlini, sqllogictest):
  - **Carlini, «Building a C compiler with a team of parallel Claudes»**
    ([Anthropic, 2026-02-05](https://www.anthropic.com/engineering/building-c-compiler)).
    - Il verificatore deve essere quasi perfetto, altrimenti l'agente risolve il problema sbagliato.
    - Sono serviti suite di qualità, come la GCC torture suite, e un confronto differenziale
      con GCC come compilatore noto buono.
    - Vicino al limite del modello, ogni nuova funzionalità rompeva spesso quelle esistenti:
      è l'asse robustezza/bussola di delivery-bench.
    - Il lavoro è costato circa 2000 sessioni e 20.000 $, che è la scala del compilatore da zero.
  - **sqllogictest** ([sqlite.org](https://sqlite.org/sqllogictest/doc/trunk/about.wiki)). Verifica
    che un motore SQL calcoli risultati corretti confrontandoli con altri motori. Gli script
    prototipo si completano con i risultati di un motore di riferimento. Misura solo la
    correttezza, non prestazioni, transazioni o concorrenza.
- **I tre semi proposti** (Lua, sqlglot, Yjs):
  - **Lua**:
    - [Suite ufficiale](https://www.lua.org/tests/): una per release, anche per la 5.4.x.
      `lua -e"_U=true" all.lua` esegue i test portabili e finisce con «final OK». Una suite non
      funziona con una release diversa.
    - [Pagina dei bug](https://www.lua.org/bugs.html): ogni release ha bug documentati con
      esempio minimo e patch o commit di correzione. La 5.4.6 ne ha 11, fra cui generazione di
      codice, messaggi d'errore e overflow.
    - Il sorgente è C con compatibilità C89, e un bug documentato della 5.4.3 riguarda proprio
      commenti C99: è una convenzione reale del progetto.
  - **sqlglot**:
    - Il [post sull'executor](https://github.com/tobymao/sqlglot/blob/main/posts/python_sql_engine.md)
      descrive tokenizer, parser a discesa ricorsiva, 17 regole di ottimizzazione sull'AST,
      piano ed esecuzione. Esegue i 24 query TPC-H, ma è lento e non fa ottimizzazioni fisiche.
    - Il [test dell'executor](https://github.com/tobymao/sqlglot/blob/main/tests/test_executor.py)
      confronta i risultati con DuckDB su TPC-H e TPC-DS.
  - **Yjs**:
    - Il [README](https://github.com/yjs/yjs) lo descrive come CRDT con tipi condivisi,
      undo/redo, snapshot e editing offline, con licenza MIT.
    - [`tests/testHelper.js`](https://github.com/yjs/yjs/blob/main/tests/testHelper.js) usa il
      PRNG del test case di `lib0/testing`, simula i client con un router di messaggi in memoria
      e confronta la convergenza. L'encoding v2 è definito ma disattivato in quei test.
- **Scartato: Maelstrom** ([jepsen-io/maelstrom](https://github.com/jepsen-io/maelstrom)). Nodi come
  binari che parlano JSON su stdin/stdout, guasti iniettati (partizioni, kill, pause) e checker
  fino alla serializzabilità stretta con Elle. Gira sulla JVM con processi e tempo reali.

## Incognite
- **Contaminazione.** I tre progetti sono pubblici e con ogni probabilità nei dati di
  addestramento. Le richieste sono originali, quindi la soluzione non esiste da nessuna parte.
  Il modello però conosce gli interni, e questo vale per tutti i bracci allo stesso modo. Per
  confrontare modi di lavorare va bene, per misurare la capacità del modello no.
- **Da verificare nei ticket di scenario:**
  - release esatte e dimensione del seme;
  - tempo della suite nel container;
  - dipendenze offline dell'immagine (DuckDB, pandas, `node_modules`);
  - ambiente dei bracci sull'host Windows (Lua si compila nel container come `c-recq`).
- **Determinismo dei test casuali di Yjs e dei confronti differenziali**: va provato
  rigiudicando due volte lo stesso albero.
- **Durata di una richiesta con luna medium su codebase così grandi**: la misura il pilota.

## Prossimo passo
Confermare scenari, lunghezza, tetti e budget in DBH-01, poi il catalogo delle trappole v2
(DBH-04).
