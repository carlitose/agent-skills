---
ticket_schema: 1
ticket_id: "DBH-18"
execution_mode: AFK
blocked_by:
  - "DBH-17"
---

# DBH-18 — Un'estensione di Pi legata al lotto, per i fornitori che ne hanno bisogno

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:18`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto dell'harness, trovato preparando la misura con Opus 5.5 chiesta dall'utente («poi
facciamo con opus 5-5, ricordati che pi deve avere la estensione di anthropic se no non funziona
con opus»).
- **Osservato**: su questo host Opus 5.5 funziona solo con l'estensione OAuth di Claude Pro/Max.
  I bracci e le foglie del driver girano con `--no-extensions`. Senza estensione, una richiesta
  minima riceve un 400 («Third-party apps now draw from extra usage, not plan limits») e Pi esce
  con 0. Con `-e` sull'estensione, la stessa richiesta riesce.
- **Cause**:
  - il runner non sa passare un'estensione ai bracci. La foglia del driver sa aggiungerla da
    `TICKET_DRIVER_PI_EXTENSION`, ma il runner toglie quella variabile dall'ambiente dei bracci;
  - un errore del fornitore prima di qualunque output viene contato come `infra:provider` solo
    se il messaggio corrisponde a un elenco fisso di errori di rete. Il 400 non corrisponde,
    quindi quella richiesta sarebbe contata come un fallimento dell'agente, senza segnalarlo. Il
    contratto §9 dice già «errore del provider senza output del modello».

Il comportamento atteso:
- `init-lot --pi-extension FILE` registra nel lotto il file e il digest della sua cartella;
- i bracci Pi lo caricano con `-e FILE`, i driver lo ricevono in `TICKET_DRIVER_PI_EXTENSION`;
- se il file o la sua cartella cambiano, il lotto si ferma prima del tentativo;
- un errore prima di qualunque output del modello è `infra:provider`, qualunque sia il messaggio.

## Acceptance Criteria
- [x] Un test lega un'estensione al lotto: il braccio `bare` riceve `-e` con il file, il driver
  riceve la variabile, e cambiare un file della cartella ferma la cella. Prima della correzione
  `init_lot` non accetta l'estensione.
- [x] Un test con il 400 prima dell'output e uscita 0 classifica il tentativo `infra:provider`, e
  la ripetizione è accettata. Prima della correzione è `agent`.
- [x] Senza estensione legata nessun braccio riceve `-e`, e la foglia copiata del driver aggiunge
  ancora `-e` dopo i flag del benchmark.

## Outcome
2026-09-29. I due test nuovi falliscono prima della correzione (`TypeError` su `pi_extension`;
`['agent']` invece di `['infra:provider', 'agent']`) e passano dopo, con tutti i test di
`benchmarks/delivery-bench`.
- Nei lotti già misurati (`luna-calib`, `db07-pilot`, `dbh`, `dbh-drivers2` e gli altri, 1006
  tentativi) nessun tentativo contato come `agent` è finito in errore senza output. La nuova
  regola non avrebbe cambiato nessuna classificazione.
- Contratto §6 e §9 aggiornati.

## Frontier
Chiuso. Vale dal prossimo `init-lot`.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: estensione legata, 400 prima dell'output.
2. `bind_extension` in `init-lot`, controllo in `load_lot`, `-e` per i bracci Pi, variabile per i
   driver, `classify` senza elenco di messaggi.
3. Contratto §6 e §9.

## Testing Plan
Test offline di `benchmarks/delivery-bench`.

## Out of Scope
- Più di un'estensione per lotto.
- Rate limit del piano Claude: un limite raggiunto è già `infra:provider` e aspetta come un buco
  di rete.
