# Giudizio di qualità oltre i test nascosti

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-quality-judge`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-28](../tickets/delivery-bench-hard/done/28-quality-units-and-robustness.md)
- [DBH-29](../tickets/delivery-bench-hard/29-diff-coverage.md)
- [DBH-30](../tickets/delivery-bench-hard/30-diff-mutation.md)
- [DBH-31](../tickets/delivery-bench-hard/31-blind-opus-review.md)
- [DBH-32](../tickets/delivery-bench-hard/32-quality-pilot-and-full.md)

## Type
Feature

## Problem
I test nascosti dicono se il comportamento richiesto funziona. Non dicono se i test scritti
dall'agente valgono qualcosa, se il codice regge casi limite, né se contiene bug che i test non
toccano. L'utente, 2026-10-06: «Il solo giudice deterministico non può vedere ste cose».

## Decisions
Decisioni dell'utente, 2026-10-06:

1. Si misurano quattro cose: copertura dei test, forza dei test (mutation), robustezza e una
   revisione LLM alla cieca.
2. Il giudice è Opus 5.5, cioè `anthropic/claude-opus-5-5` in Pi.
3. Budget: «quello che serve».
4. Si giudicano tutte le richieste, anche quelle non accettate o non finite, perché
   «potrebbero avere lavoro utile».

L'esito ufficiale resta quello dei test nascosti. Le misure di qualità sono colonne a parte e
non cambiano mai `cell.json`, il ledger o l'accettazione.

## Facts
- Oggetto del giudizio:
  - `dbh-luna3d`: bracci `bare`, `pi-tools`, `pi-full`, 108 richieste;
  - `dbh-luna3e`: braccio `bare-goal`, 36 richieste.
  - Totale 144 richieste. Su `dbh-luna3d`, 8 non hanno diff.
- Ogni richiesta registra `diff.base`, `diff.tree` e `cells/<cell>/diffs/NN.diff`.
- L'albero di ogni richiesta si ricostruisce con `git ls-tree`/`git archive`. Servono come
  alternates `diffs/objects`, `snapshot/project/.git/objects`, `snapshot/origin.git/objects` e
  il repository del braccio (`lot.json` `arm_dir`):
  - `diffs/objects` contiene solo gli oggetti che il repository del braccio non aveva già;
  - lo snapshot è preso prima di ogni richiesta, quindi il lavoro committato nell'ultima richiesta
    sta solo nel braccio. In `dbh-luna3d` capita a 8 celle `pi-full`.
  - Le cartelle dei bracci esistono per entrambi i lotti. Un runner che renda lo store
    autosufficiente è un bug a parte, in coda.
- Gli scenari sono tre, tutti con `test_command` `python dev.py test`:

  | Scenario | Linguaggio | Immagine | Test |
  |---|---|---|---|
  | lua-vm | C | `gcc:14` | make con ASan/UBSan |
  | sql-engine | Python | `dbench-sql-engine:1` | `python -m unittest`; `coverage` non è nell'immagine |
  | crdt-yjs | JavaScript | `dbench-crdt-yjs:1` | `npm test`, che costruisce `dist/` con rollup |

- La robustezza è già misurata. Il giudice ufficiale esegue 3 test latenti nascosti per
  richiesta, uguali per tutti i bracci (`axes.robustness`), più invarianti e trappole
  (`axes.compass`), e `profile_report.py` li riporta.

## Target behavior
Un nuovo script, `benchmarks/delivery-bench/quality.py`, scrive tutto sotto
`results/<lot>/quality/`, separato dalle celle. Per ogni richiesta, che chiamiamo «unità»:

1. **Unità.** L'unità è (lotto, cella, richiesta, base, albero, diff). Sono incluse tutte le
   richieste, anche quelle senza diff, che figurano come «nessun codice».
2. **Robustezza.** Si riportano `axes.robustness` e `axes.compass` già giudicati, senza nuovi
   test.
3. **Copertura limitata alla diff.** È la quota delle righe eseguibili aggiunte nei file
   sorgente, esclusi i test, che il `test_command` dell'albero esegue. Gira nell'immagine dello
   scenario, offline:
   - Python: `coverage.py`, in un'immagine derivata con versione fissata;
   - C: build `--coverage` e `gcov`;
   - JavaScript: `NODE_V8_COVERAGE`. La mappatura da `dist/` a `src/` va verificata nel ticket.
4. **Mutation limitata alla diff.** Si generano mutanti deterministici, con seme fisso, solo
   sulle righe aggiunte nei sorgenti: operatori relazionali, aritmetici e booleani, costanti, e
   ritorno o cancellazione di un'istruzione. Al massimo N per unità. Il `test_command`
   dell'albero gira su ogni mutante, con un timeout. Il risultato si conta come ucciso,
   sopravvissuto, timeout o non compilabile; i non compilabili sono esclusi dalla quota.
5. **Revisione alla cieca.** Si avvia un processo `pi -p` nuovo con
   `--model anthropic/claude-opus-5-5`, `--no-extensions --no-skills --no-context-files` e solo
   gli strumenti di lettura.
   - L'albero è in una cartella con nome neutro.
   - Il revisore riceve la richiesta (`TASK.md`) e la diff dei soli file di codice e di test.
     Sono esclusi `docs/specs`, `docs/tickets` e `.pi/`, che rivelerebbero il braccio.
   - Risponde in JSON con una griglia fissa: probabili bug (gravità, file:riga, perché) e
     voti da 1 a 5 per rischio di correttezza, qualità dei test, design e leggibilità.
   - Per ogni revisione si registrano costo e token.
6. **Report.** Una tabella per braccio e scenario: accettazione ufficiale, robustezza,
   copertura, mutation, bug probabili, voti e costo del giudizio, con mediana e quartili.

## Non-goals
- Cambiare l'esito ufficiale, `runner.py`, i lotti o le celle.
- Scrivere nuovi test nascosti di robustezza: esistono già.
- Rigiocare i bracci.

## Gates
- **Tentativo:** un giudizio completo di `dbh-luna3d` più `dbh-luna3e`. Confermato
  dall'utente («ok», 2026-10-06).
- **Budget per tentativo:** nessun tetto («quello che serve»); la spesa reale va riportata.
  Confermato dall'utente.
- **Tempo per tentativo:** nessun limite. Confermato dall'utente.
- **Tentativi massimi:** 2. Il primo è un pilota su 10 unità, una per braccio e scenario più
  una scelta a caso con seme fisso; il secondo è il giudizio completo. Confermato dall'utente.
- **Approvazioni:**
  - merge su `main` con CI 8/8 e `--match-head-commit`;
  - spesa Opus coperta dal budget del tentativo;
  - build delle immagini derivate, che richiede la rete una volta sola.
- **Versione esatta:** nessuna.
- **Blocchi esistenti trovati:**
  - `dbh-luna3e` è in corso. Docker e CPU servono al suo giudice e i tempi misurati ne
    risentirebbero, quindi copertura, mutation e revisione si eseguono solo a lotto finito.
    Il checkout principale di agent-skills non si aggiorna prima.
  - I tetti di spesa dell'autorità dei lotti (49 $) valgono per i lotti, non per questo
    giudizio, che ha un suo record di spesa.
  - Le immagini girano offline e `coverage` manca in `dbench-sql-engine:1`, quindi serve
    un'immagine derivata.
  - Le diff di `pi-full` contengono spec e ticket. Senza filtro rivelerebbero il braccio al
    revisore.

## Pilot rule
Il pilota misura per ogni unità il tempo e il costo di ciascuna misura. Su ogni unità fa due
revisioni Opus indipendenti e confronta i bug trovati e i voti:
- se i voti differiscono al massimo di 1 punto e i bug gravi coincidono, il giudizio completo
  fa una revisione per unità;
- altrimenti ne fa tre e usa la mediana.

## Implementation Slices
- DBH-28: unità, alberi ricostruiti, robustezza e scheletro del report.
- DBH-29: copertura limitata alla diff, nei tre linguaggi.
- DBH-30: mutation limitata alla diff.
- DBH-31: revisione Opus alla cieca.
- DBH-32: pilota, poi giudizio completo e report.

## Verification
- Test unitari in `benchmarks/delivery-bench/test_quality.py`, su repository giocattolo:
  - unità e ricostruzione degli alberi;
  - righe aggiunte;
  - generatore di mutanti deterministico;
  - filtro di cecità;
  - parsing della risposta del revisore.
- Smoke reale su un'unità per scenario.
- CI 8/8.
