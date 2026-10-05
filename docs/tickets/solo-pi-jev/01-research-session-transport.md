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

### Produces
- [Trasporto e lifecycle di catena](../../research/solo-pi-jev-session-transport.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Destination, Current Evidence, Not Yet Specified 1, Next Review.

## Question / Outcome
Quale interfaccia supportata della versione Pi effettivamente risolta consente allo script di inviare più turni nella stessa sessione senza creare altre foglie? Distinguere processo persistente, sessione logica e semplice riuso della cronologia. Raccogliere fatti e una raccomandazione tecnica, non scegliere fallback o garanzie al posto dell'utente.

## Evidence
Partire da `ticket-driver/scripts/leaf.py` (`invoke`, `leaf_argv`), `driver.py` (`execute`) e `benchmarks/delivery-bench/runner.py` (`arm_argv`). Leggere la documentazione primaria completa di Pi dalla versione/package risolti: README e i documenti SDK/RPC/CLI e rimandi pertinenti. Non assumere firme API dal nome di un flag o da ricordi; registrare versione, percorsi/fonti e limiti della ricerca. Per Jev, il confine locale osservabile è `arbiter.py` (`ask`, `classify`, `isolated_key`), senza chiamare l'API.

## Outcome
[Rapporto offline](../../research/solo-pi-jev-session-transport.md) sulla versione Pi risolta 0.99.1, base osservata `001d36229093e3b4d759d585a8406be5826dc47a`. RPC raccomandato per il controller Python; SDK alternativa supportata. Commit upstream Pi ignoto nel metadata, prova fake definita ma non eseguita, nessuno smoke live o modifica del driver.

## Acceptance Criteria
- [x] Rapporto attribuito a versione Pi, commit osservato e fonti primarie; confronto delle sole opzioni effettivamente supportate, inclusi dipendenze e vincoli Windows/macOS/Linux.
- [x] Descritti apertura, turni seriali, evento terminale, cwd/tools, interruzione, crash/ripresa e compattazione; informazioni mancanti restano esplicitamente ignote.
- [x] Definita una prova riproducibile con fake e contatore di istanze/sessioni per due richieste, distinguendo continuità della cronologia da un solo processo.
- [x] Specificata contabilizzazione per delte di turno/richiesta, senza duplicare prefissi o azzerare consumi dopo crash; segnalato il confine di isolamento della chiave Jev.
- [x] Rapporto e mappa collegati reciprocamente attraverso il ticket; aggiornate solo le unknowns realmente risolte, senza chiudere SPJ-02/03/04 o rivendicare un smoke live.

## Frontier
Rapporto locale preparato in corsia skills-only, soggetto al handoff canonico di qualità e a consegna provider separatamente autorizzata. Non è integrazione o refactoring completo. Prossimo passo SPJ-02: conferma umana del fallback; SPJ-03/04 restano aperti.

## Step-by-Step Implementation Plan
1. Verificare checkout/base correnti e versione Pi risolta; leggere codice e documentazione, salvando riferimenti verificabili.
2. Confrontare i trasporti supportati contro il lifecycle della catena; proporre un confine profondo di sessione e le prove fake necessarie, senza implementarlo in produzione.
3. Scrivere il rapporto e aggiornare la mappa/grafo nella stessa modifica. Completion criterion: tutte le domande sopra hanno evidenza o un limite nominato; le decisioni umane restano aperte.

## Testing Plan
Verificare fonti, link, grafo e coerenza della matrice con il codice. Una prova locale puramente fake, se necessaria, deve stare fuori dal driver misurato e non chiamare Pi/Jev live; documentare cosa osserva. Test unitari/protocollo fake non provano integrazione reale, autenticazione o qualità del modello.

## Out of Scope
Scelta del fallback, indipendenza della review, nuove garanzie, codice di produzione, benchmark, credenziali/spesa, installazione o aggiornamento Pi, CLI/scheduler Autopilot, provider delivery e wiki impliciti. Consegna skills-only inline; nessuna delega.
