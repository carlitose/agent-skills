---
ticket_schema: 1
ticket_id: "DBH-24"
execution_mode: AFK
blocked_by: []
---

# DBH-24 — Il giudice aspetta Docker, e ogni richiesta lascia il suo diff

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:24`
- Role: `ticket`
- Parent: [delivery-bench-hard-luna-three-arms.md](../../../specs/delivery-bench-hard-luna-three-arms.md)

## Parent Spec
[delivery-bench-hard-luna-three-arms.md](../../../specs/delivery-bench-hard-luna-three-arms.md),
sezioni *Comportamento atteso* 5–6 e *Fallimenti previsti*.

## What to Build
Un difetto dell'harness e un'aggiunta chiesta dall'utente, trovati nel lotto `dbh-luna3`.
- **Osservato**: Docker Desktop si è fermato durante la ripetizione 1 delle catene da 4. Il runner
  ha registrato tutti i 33 giudizi come `judge-error` («hidden suite wrote no result (exit 1)») ed
  è andato avanti; il lavoro di quelle richieste non si poteva più giudicare. Il lotto è stato
  annullato (`VOID.md`, circa 0,85 $).
- **Causa**: un giudice irraggiungibile è trattato come un verdetto, non come infrastruttura.
- **Aggiunta**: l'utente vuole, oltre ai test, un giudizio dell'agente sulle bocciature
  («non sarebbe meglio anche un tuo giudizio?»). Serve il diff di ogni richiesta.

Comportamento:
- prima di ogni tentativo del giudice Docker il runner controlla che il daemon risponda; se non
  risponde aspetta con gli intervalli d'infrastruttura (`judge-wait` nel ledger) senza consumare
  tentativi; dopo l'ultima attesa la cella si ferma con un errore e la richiesta resta
  `unjudged`;
- una richiesta `unjudged` (giudice assente o host fermo durante il giudizio) alla ripresa viene
  solo giudicata: nessun nuovo tentativo del braccio;
- prima del giudizio il runner salva `cells/<cella>/diffs/NN.diff`: le modifiche della sola
  richiesta N rispetto allo stato lasciato dalla N-1 (anche senza commit del braccio), senza
  `TASK.md`, senza toccare il repository del braccio;
- `profile_report.py` conosce `pi-tools` e `pi-full` e non conta le richieste `unjudged`.

## Acceptance Criteria
- [x] Giudice irraggiungibile: attese registrate, nessun tentativo consumato, poi `judged`.
- [x] Giudice che non torna: `LotError`, richiesta `unjudged`, cella non conclusa; alla ripresa
      nessuna nuova chiamata al braccio e richiesta giudicata.
- [x] Host fermo durante il giudizio: alla ripresa solo il giudizio; host fermo durante la
      richiesta: comportamento di prima (`infra:host` e nuovo tentativo).
- [x] Diff per richiesta: contiene solo il lavoro di quella richiesta, rispetta `.gitignore`,
      esclude `TASK.md`, e `.git` del braccio resta identico byte per byte.
- [x] La suite di `benchmarks/delivery-bench` passa.

## Frontier
Done.

## Step-by-Step Implementation Plan
1. `docker_ready`, `wait_for_judge` e lo stato `unjudged` in `runner.py`.
2. `request_diff` con indice temporaneo e archivio di oggetti della cella.
3. `profile_report.py`: bracci nuovi e richieste aperte.
4. Test in `test_runner.py`.

## Testing Plan
- Unitari offline con Pi finto e giudice finto; il controllo di Docker è sostituito nei test.
- Live: il lotto `dbh-luna3b` (DBH-23).

## Out of Scope
- Il giudizio dell'agente sulle bocciature (si fa nel report di DBH-23).
- Rigiudicare il lotto annullato `dbh-luna3`.
