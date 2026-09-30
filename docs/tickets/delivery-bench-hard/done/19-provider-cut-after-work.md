---
ticket_schema: 1
ticket_id: "DBH-19"
execution_mode: AFK
blocked_by:
  - "DBH-18"
---

# DBH-19 — Un errore del fornitore che chiude una sessione avviata è infrastruttura

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:19`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto dell'harness, trovato durante la misura con Opus 5.5 (lotto `dbh-opus`).
- **Osservato**: il 30/09 verso le 16:35 UTC si è esaurita la finestra di quota del piano Claude.
  Dodici tentativi sono stati respinti con un 429 prima di rispondere: il runner li ha contati
  come infrastruttura e li ha ripetuti. Quattro sessioni erano già avviate, e il 429 le ha
  chiuse a metà lavoro; una quinta l'aveva chiusa alle 14:13 un «Overloaded». Il runner ha
  contato queste cinque come esito del braccio e ha giudicato il lavoro troncato. Tre sono state
  accettate lo stesso, due no: in entrambe la foglia del driver era morta sull'errore.
- **Causa**: `classify` riconosce un errore del fornitore solo prima di qualunque output del
  modello (DBH-18). Dopo, un'uscita non nulla conta come errore dell'agente, anche quando a
  chiudere la sessione è il fornitore.
- **Anche in `dbh`**: rileggendo i lotti misurati, lo stesso caso c'è due volte nel lotto di
  DBH-09. Il buco di rete del 29/09 ha chiuso con `fetch failed` due richieste 11 di
  `sql-engine`, dopo 26 e 40 minuti di lavoro. Nel lotto annullato `dbh-drivers` i casi sono 4.
  Nessun caso negli altri lotti.

Il comportamento atteso:
- una sessione chiusa da un errore transitorio del fornitore (quota, sovraccarico, errore del
  server o di rete) è `infra:provider` anche dopo l'output del modello: l'harness ripristina la
  cella e ripete la richiesta, con le stesse attese;
- un errore dovuto alla richiesta del braccio, per esempio un contesto troppo lungo, resta un
  esito del braccio;
- quando le ripetizioni si esauriscono, la cella è ripristinata prima del giudizio: il lavoro a
  metà di un tentativo troncato non si giudica, e la richiesta conta come non accettata.

## Acceptance Criteria
- [x] Un braccio Pi che lavora e poi riceve un 429 ha il tentativo `infra:provider`, e la
  ripetizione è accettata. Lo stesso per una foglia del driver chiusa da «Overloaded». Prima
  della correzione sono `agent`.
- [x] Un contesto troppo lungo dopo il lavoro resta `agent`.
- [x] Sei tentativi troncati esauriscono la richiesta: il lavoro troncato non resta nel progetto
  e la richiesta non è accettata. Prima della correzione è giudicata accettata.
- [x] Report di DBH-09 con una correzione esplicita, contratto §9 aggiornato, nota di correzione
  su DBH-18.

## Outcome
2026-09-30. I due test nuovi falliscono prima della correzione e passano dopo, con tutti i test
di `benchmarks/delivery-bench`.
- Lotto `dbh`: togliendo le due coppie troncate, e anche le due richieste 12 esaurite dallo
  stesso buco di rete, la regola di TBA-03 alla catena da 12 non cambia. Nessun braccio supera
  `bare`; skills-only passa da Holm 0,157 a 0,127.
- Lotto `dbh-opus`: le cinque richieste sono già giudicate e non si rieseguono. Il report di
  quel lotto le tratta con un'analisi di sensibilità. La correzione vale dal `run-lot` dopo la
  catena da 4.

## Frontier
Chiuso.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: 429 dopo il lavoro, foglia del driver chiusa da «Overloaded»,
   contesto troppo lungo, sei tentativi troncati.
2. `TRANSIENT_PROVIDER` e il caso in `classify`; ripristino della cella quando le ripetizioni si
   esauriscono.
3. Scansione dei lotti misurati; correzione del report di DBH-09, contratto §9, nota su DBH-18.

## Testing Plan
Test offline di `benchmarks/delivery-bench`.

## Out of Scope
- Scegliere l'ultimo messaggio per tempo invece che per percorso: nei run osservati dei driver i
  due ordini coincidono.
- Rieseguire richieste già giudicate.
