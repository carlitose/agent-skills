---
ticket_schema: 1
ticket_id: "SPJ-01"
execution_mode: AFK
blocked_by: []
---

# SPJ-01 — Verificare il trasporto di una sessione Pi lungo la catena

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-01`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Destination, Current Evidence, Not Yet Specified 1, Next Review.

## Question / Outcome
Quale interfaccia supportata della versione Pi effettivamente risolta consente allo script di inviare più turni nella stessa sessione senza creare altre foglie? Distinguere processo persistente, sessione logica e semplice riuso della cronologia. Raccogliere fatti e una raccomandazione tecnica, non scegliere fallback o garanzie al posto dell'utente.

## Evidence
Partire da `ticket-driver/scripts/leaf.py` (`invoke`, `leaf_argv`), `driver.py` (`execute`) e `benchmarks/delivery-bench/runner.py` (`arm_argv`). Leggere la documentazione primaria completa di Pi dalla versione/package risolti: README e i documenti SDK/RPC/CLI e rimandi pertinenti. Non assumere firme API dal nome di un flag o da ricordi; registrare versione, percorsi/fonti e limiti della ricerca. Per Jev, il confine locale osservabile è `arbiter.py` (`ask`, `classify`, `isolated_key`), senza chiamare l'API.

## Produces
- Output pianificato: `docs/research/solo-pi-jev-session-transport.md`, Artifact ID `artifact:solo-pi-jev-session-transport`, Role `research`.
- Alla creazione del rapporto, aggiungere qui il link `### Produces` nel grafo e nel rapporto il Parent reciproco a questo ticket, nella stessa modifica. Il rapporto non esiste ancora: non dichiararlo prodotto né inserire un link pendente.

## Acceptance Criteria
- [ ] Rapporto attribuito a versione Pi, commit osservato e fonti primarie; confronto delle sole opzioni effettivamente supportate, inclusi dipendenze e vincoli Windows/macOS/Linux.
- [ ] Descritti apertura, turni seriali, evento terminale, cwd/tools, interruzione, crash/ripresa e compattazione; informazioni mancanti restano esplicitamente ignote.
- [ ] Definita una prova riproducibile con fake e contatore di istanze/sessioni per due richieste, distinguendo continuità della cronologia da un solo processo.
- [ ] Specificata contabilizzazione per delte di turno/richiesta, senza duplicare prefissi o azzerare consumi dopo crash; segnalato il confine di isolamento della chiave Jev.
- [ ] Rapporto e mappa collegati reciprocamente attraverso il ticket; aggiornate solo le unknowns realmente risolte, senza chiudere SPJ-02/03/04 o rivendicare un smoke live.

## Frontier
Ready AFK per ricerca offline, non avviato. Nessun blocker canonico; una lacuna documentale è un risultato da registrare, non consenso a chiamare il provider o lanciare il driver.

## Step-by-Step Implementation Plan
1. Verificare checkout/base correnti e versione Pi risolta; leggere codice e documentazione, salvando riferimenti verificabili.
2. Confrontare i trasporti supportati contro il lifecycle della catena; proporre un confine profondo di sessione e le prove fake necessarie, senza implementarlo in produzione.
3. Scrivere il rapporto e aggiornare la mappa/grafo nella stessa modifica. Completion criterion: tutte le domande sopra hanno evidenza o un limite nominato; le decisioni umane restano aperte.

## Testing Plan
Verificare fonti, link, grafo e coerenza della matrice con il codice. Una prova locale puramente fake, se necessaria, deve stare fuori dal driver misurato e non chiamare Pi/Jev live; documentare cosa osserva. Test unitari/protocollo fake non provano integrazione reale, autenticazione o qualità del modello.

## Out of Scope
Scelta del fallback, indipendenza della review, nuove garanzie, codice di produzione, benchmark, credenziali/spesa, installazione o aggiornamento Pi, CLI/scheduler Autopilot, provider delivery e wiki impliciti. Consegna skills-only inline; nessuna delega.
