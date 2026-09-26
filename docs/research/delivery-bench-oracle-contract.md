# delivery-bench — contratto dell'oracolo e protocollo di esecuzione

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-oracle-contract`
- Role: `research`
- Parent: [DB-01 — Contratto dell'oracolo e protocollo di esecuzione](../tickets/delivery-bench/done/01-oracle-contract-and-run-protocol.md)

## Stato
Output di DB-01 (2026-09-26). Risponde alle voci *Not Yet Specified* della
[mappa](../specs/delivery-bench-wayfinder.md) e fissa i formati che DB-03..DB-06 devono
rispettare. Codice pubblico: [`benchmarks/delivery-bench/`](../../benchmarks/delivery-bench/)
(`judge.py`, `example/`, `test_judge.py`). Il materiale nascosto vive solo nel repo privato.

## 1. Vocabolario
- **Scenario**: stato iniziale pubblico + 8 richieste in sequenza + suite nascosta.
- **Richiesta N**: testo grezzo, in spagnolo come bench38, consegnato solo dopo la N-1.
- **Catena da L**: le richieste 1..L di uno scenario; 1, 3 e 8 sono prefissi della stessa catena.
- **Cella**: un braccio × uno scenario × una ripetizione, con il suo repo e le sue sessioni.
- **Consegna N**: lo stato della cartella `project/` della cella quando il braccio termina la
  richiesta N (working tree, commit o no). È l'unica cosa giudicata.

## 2. Repo privato dell'oracolo
`C:/Users/CGS03/dbench-private/` (Git locale, mai spinto, mai in agent-skills; lo scrive solo
l'oracolo, Claude Fable, in sessioni separate da quelle dei bracci):

```
catalog.md                  catalogo delle trappole approvato (DB-02)
scenarios/<id>/
  scenario.json             schema 1: id, image, command, requests, timeout_seconds
  seed/                     stato iniziale pubblico (diventa project/ della cella)
  requests/01.md..08.md     richieste grezze; l'ultima riga è un canary che l'harness toglie
  hidden/                   suite nascosta: run.py + dbench_checks.py (+ file di supporto)
  reference/01..08/         soluzione di riferimento cumulativa, come overlay sul seed
  trap/01..08/              soluzione che cade in ogni trappola, overlay cumulativo
  images/Dockerfile         immagine del giudice dello scenario
results/<lot>/<cell>/       record del giudice (non versionati)
```

Lo stub è il seed senza modifiche. `scenario.json` d'esempio e formato completo:
[`example/scenario.json`](../../benchmarks/delivery-bench/example/scenario.json).

## 3. Formato della richiesta
Markdown come il `TASK.md` di bench38: cosa aggiungere, vincoli espliciti («requisiti che
valgono quanto la funzionalità»), nessun test nascosto citato. La richiesta 1 dello scenario
Python è il `TASK.md` di bench38 byte per byte. L'harness scrive la richiesta N come `TASK.md`
nella radice di `project/`, la committa da sola (`git commit -- TASK.md`, autore `bench`) sul
ramo corrente e la spinge su `origin/main` se il push è fast-forward. Il prompt è identico per
tutti i bracci salvo il suffisso del braccio (§6):

> Lee TASK.md en la raiz del repositorio y haz lo que pide, hasta el final. Trabaja solo en
> este directorio. Lo que cuenta es el estado de esta carpeta cuando termines.

## 4. Suite nascosta e giudice
Ogni controllo ha `id`, `kind` (`feature`, `latent`, `invariant`, `trap`), `request` (in cui
entra), e per le trappole `trap = {type, rule, temptation, distance}` con
`distance = temptation - rule` e tipi `deprecated`, `architecture`, `closed-bug`, `contract`,
`convention`. Il registro [`dbench_checks.py`](../../benchmarks/delivery-bench/example/hidden/dbench_checks.py)
esegue per la richiesta N ogni controllo con `request <= N`; una `feature` di una richiesta
precedente diventa `invariant` (la regressione di un'accettazione passata è bussola). Una
trappola entra alla richiesta della tentazione. La suite copia `/repo` in una cartella di
lavoro senza `.git`, `node_modules` e cache, e scrive `/out/result.json` (schema 1).

[`judge.py`](../../benchmarks/delivery-bench/judge.py) esegue:
1. digest SHA-256 dell'intero albero di `project/` (`.git` compreso);
2. `docker run --rm --network none --cpus 2 --memory 2g --pids-limit 1024`, con `project/`
   montato `readonly` su `/repo`, `hidden/` `readonly` su `/hidden`, una cartella temporanea
   su `/out`, e `command --request N`, con timeout dello scenario (poi `docker kill`);
3. secondo digest: se differisce, il giudizio è invalido (`JudgeError`), mai un punteggio;
4. validazione del risultato (controlli futuri, distanze incoerenti, id duplicati o assenza di
   controlli d'accettazione per N lo invalidano) e calcolo degli assi.

Rifiuta una suite dentro il progetto giudicato. Prova (2026-09-26, `python:3.12-slim`): lo
scenario d'esempio con la soluzione di riferimento passa 5/5 e albero identico; lo stub fallisce
esattamente i 5 controlli attesi, con la trappola di convenzione a distanza 1
(`C:/dbench/evidence/db01-judge-example-{reference,stub}.json`, sha256 `9366d2ba…`, `bb279f84…`;
`DBENCH_LIVE_DOCKER=1 python -B -m unittest test_judge` verde, 12 test).

Immagini: Python `python:3.12-slim`; C `dbench-c:1` (da `gcc:14` + `python3`, ASan/UBSan);
TypeScript `dbench-ts:1` (da `mcr.microsoft.com/playwright:v1.63.0-noble`, con le dipendenze
del lockfile del seed e `@playwright/test` preinstallati in `/opt/app/node_modules`; il progetto
si copia sotto `/opt/app/` e la risoluzione di Node sale fino a quelle dipendenze).

## 5. Record del profilo
Il giudice produce per ogni richiesta: `acceptance` (feature della richiesta N passate/totali e
`accepted` se tutte passano), `robustness` (latenti trovati/totali fino a N, elenco mancati),
`compass` (invarianti fallite, trappole violate con tipo, regola, tentazione e distanza).
Il runner (DB-06) aggiunge per richiesta: `usage` (token input/output/cache e USD stimati da Pi,
per sessione o per foglia del driver), `jev` (chiamate e USD stimati, a parte), `seconds` (dal
lancio del braccio all'ultimo evento di sessione), `exit`, `timed_out`, tentativi
d'infrastruttura. Il record di cella ha schema 1 con `lot`, `cell`, `arm`, `scenario`, `rep`,
`length`, `requests[]` e `chain_cap_hit`. Nessun numero unico: il report mette i cinque assi uno
accanto all'altro (Decisione 7).

## 6. Bracci nel modo naturale
Tutti: `openai-codex/gpt-6-sol`, `--thinking high`, cwd = `project/` della cella, origin =
repo bare locale `origin.git` della cella con `main` spinto. I processi Pi dei bracci girano con
`--no-extensions --no-context-files --approve` (niente Telegram, memoria, MCP o regole globali
che possano far trapelare la mappa) e un `.pi/settings.json` di progetto, escluso via
`.git/info/exclude`, che riattiva la compaction nativa: le impostazioni globali la disattivano e
una catena da 8 in una sessione supererebbe i 272K di contesto. Le foglie del driver e di
Autopilot girano nei loro worktree senza quel file (limite dichiarato).

| Braccio | Comando per la richiesta N | Memoria tra richieste |
|---|---|---|
| `bare` | `pi -p … --no-skills --session-dir S [--continue] -- PROMPT` | una sessione per la catena |
| `skills-only` | `pi -p … --session-dir S [--continue] -- PROMPT + suffisso skills-only di bench38` | una sessione |
| `driver-c1a` | `python -B <copia driver>/scripts/ticket_driver.py run --candidate c1a --task requests/NN.md --repo project --live-authorization A` | nessuna: un run per richiesta, repo e worktree |
| `driver-c3a` | come c1a con `--candidate c3a`; chiave Jev iniettata solo nel processo del driver | come c1a |
| `autopilot` | `pi -p … --session-dir S [--continue] -- PROMPT + suffisso Autopilot` | una sessione orchestratrice; foglie e ledger del runner |

`--continue` dalla richiesta 2. La copia del driver (una per scenario, sotto
`C:/dbench/arms/`) cambia solo configurazione, con hash registrati: `policy.json` (provider,
modello, thinking, `test_command` dello scenario), gli argomenti delle foglie
(`--no-extensions --no-context-files`, come gli altri bracci) e la regola `allowed()` di Jev,
estesa alle celle `driver-*` sotto `C:/dbench/runs`. Nessuna logica del driver cambia.
`test_command`: Python `python -B -m unittest discover -s tests -t .`; C `python dev.py test`
(compila e prova in `gcc:14` via Docker: sull'host non c'è compilatore); TypeScript
`node scripts/test.mjs` (vitest, dipendenze nella cartella della cella, sopra `project/` e
sopra i worktree).

## 7. Protocollo di Autopilot
Suffisso: il testo di bench38 («Usa el flujo completo de ticket-autopilot, incluido su runner,
para llevar este trabajo de principio a fin») più un fatto d'ambiente: *`origin` es un
repositorio local sin proveedor de PR: usa el runner con `--provider github --provider-mode
simulated`; cuando el runner no pueda fusionar, integra tú la rama en `main` de esta carpeta.*
Passi attesi per ogni richiesta:
1. `to-spec` scrive la spec in `docs/specs/`; `to-tickets` emette ticket canonici con
   `ticket-emit`; commit e push su `origin/main`.
2. `ticket-autopilot.py run <cartella> --repo project --provider github --provider-mode
   simulated --base main`: il runner crea ledger e worktree `.project-ticket-autopilot-worktrees/`.
3. Per ticket: `activate`; `stage implement` e `simplify` con l'albero del worktree;
   `leaf-result-template` + `resume` per `review`, `qa-plan`, `qa-execute`;
   `verification-checkpoint` con il bundle di `verification-audit`; `stage verify`,
   `stage finalize` → `verified`.
4. `delivery`: commit e push del ramo `ticket-autopilot/<run>/<ticket>` su `origin`, richiesta di
   corpo PR per `explain-pr`; il merge simulato è rifiutato dal runner («simulated provider
   evidence cannot authorize merge»), quindi il braccio integra il ramo in `main`.

Prova senza modello (2026-09-26, `C:/dbench/probe/autopilot-01`, sonde `autopilot_probe*.{sh,py}`,
sintesi `C:/dbench/evidence/db01-autopilot-probe.json` sha256 `c46eedd7…`): il runner ha accettato
il repo effimero (provider `local-or-unsupported`, `provider_mode: simulated`), ha attraversato
tutti i passi 2-3 fino a `verified` e al passo 4 ha spinto il ramo sull'origin locale
restituendo la richiesta di corpo PR. Non eseguiti nella sonda: resa del corpo, PR simulata,
merge; il rifiuto del merge simulato è nel codice (`ticket-autopilot/scripts/autopilot/cli.py`).
Autopilot gira solo come braccio misurato, nei repo effimeri: la consegna dei ticket DB resta
skills-only.

## 8. Isolamento verificabile
Alla richiesta N il braccio vede: `project/` (seed, storia Git con `TASK.md` 1..N, il proprio
lavoro), la propria cartella di sessione, `origin.git`, le skill installate, la copia del driver
per i bracci driver. Non vede: `dbench-private/` (suite, catalogo, riferimenti, richieste future,
risultati del giudice), questa mappa di proposito (le skill installate sono una copia di
agent-skills che contiene `docs/`: la scoperta accidentale si rileva, non si impedisce). Prove:
- **percorso**: il giudice rifiuta una suite dentro il progetto; celle in `C:/dbench/runs/`,
  materiale nascosto in `C:/Users/CGS03/dbench-private/`, risultati del giudice mai nella cella;
- **canary**: ogni file nascosto e ogni richiesta privata contengono un canary
  (`dbench-canary-<scenario>-<hex>`) che l'harness toglie prima della consegna; l'audit di fine
  cella cerca canary, il percorso `dbench-private` e la stringa `delivery-bench` in tutte le
  sessioni Pi, nei run del driver e nel ledger del runner; un riscontro invalida la cella.

## 9. Tetti di tempo, ripetizioni, guasti
- **Tetto**: 60 minuti per richiesta, 60 × L minuti per catena. Allo scadere l'harness termina
  l'albero di processi, giudica lo stato presente (`timed_out`) e, se il tetto di catena è
  superato, registra le richieste restanti come non consegnate (accettazione 0).
- **Ripetizioni** (Decisione 9): 3 celle per braccio e scenario. Le celle del pilota (DB-07)
  sono catene da 1; DB-08 le **prosegue** con le richieste 2-3 (catene da 3, 3 ripetizioni) e
  prosegue la ripetizione 1 fino all'8. È equivalente a lanciare catene nuove perché il braccio
  non conosce né la lunghezza né le richieste future; cambia solo l'intervallo tra richieste
  (la cache del provider può scadere: effetto sul costo, dichiarato).
- **Statistica**: accettazione come esito binario per (scenario, ripetizione, richiesta),
  appaiata col braccio `bare`; McNemar esatto con correzione di Holm e differenza minima di 3
  (regola TBA-03, funzioni riprese da `arm_comparison.py`). Gli altri assi sono descrittivi.
- **Guasti d'infrastruttura**: errore del provider senza output del modello, crash di Pi prima
  della prima chiamata a strumento, errore del giudice, crash dell'host. Massimo 2 ripetizioni
  per richiesta: l'harness salva `project/` e sessione prima di ogni richiesta e li ripristina.
  Gli errori dell'agente (timeout, lavoro sbagliato, uscita non nulla dopo aver lavorato) contano.

## 10. Riuso
Da `bench38_harness.py`: seme Python (`SEED`, `TASK`, `ACCEPTANCE` diventano seed, richiesta 1 e
controlli della richiesta 1), conteggio dei token dalla sessione (`session_usage`), lancio
distaccato e raccolta, metriche di uso del runner (`runner_use`). Da Terminal-Bench: ledger
fuori da Git, file d'autorità per lotto, classificazione dei guasti e massimo due ripetizioni;
non il bridge Harbor (i bracci qui lavorano su un repo dell'host, non in un task container). Da
`arm_comparison.py` (TBA-03, non ancora integrato): McNemar e Holm.

## 11. Domande ancora aperte
- La compaction nelle foglie del driver e di Autopilot resta quella globale (disattivata): se
  una foglia supera il contesto, è un errore del braccio, registrato come tale; da rivedere dopo
  il pilota (DB-07).
- Il merge di Autopilot passa dal braccio, non dal runner: se il pilota mostra che il braccio si
  perde lì, lo si registra come limite del braccio in questo ambiente, non si cambia il runner.
- Concorrenza con i lotti Terminal-Bench: celle in parallelo solo fino a 4 processi Pi alla
  volta; si alza dopo il pilota se il provider non restituisce 429.
