---
ticket_schema: 1
ticket_id: "SPB-04"
execution_mode: AFK
blocked_by:
  - "SPB-03"
---

# SPB-04 — Riconciliare i costi e preparare una prova corretta L4

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-04`
- Role: `ticket`
- Parent: [Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md)

## Parent Spec
[Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md), Reentry Preparation — SPB-04.

## What to Build
Riconciliazione attribuita delle stime sperimentali/operatore e manifest di preparazione
per una singola catena persistente Yjs L4 sul codice corretto SPB-03, distinta dal pilota
vecchio e non ancora autorizzata a partire. Solo artefatti locali e prove statiche.

## Acceptance Criteria
- [ ] Ricostruzione SDK cumulativa operatore da intent Luna, con prefisso/byte/hash e scope; include compact/usage/nested tool usage, non solo ultimo ramo. Prezzi mancanti/identità ambigue sono gate, mai zero inventato.
- [ ] Ledger storico, risultati e sorgente vecchia immutati; tutti i tentativi/costi/launch conservati. Totale e residuo di riferimento distinguono SDK/Jev, operatore, fattura e cambio finale ignoti; no reset/nuovo tetto.
- [ ] Nuovo manifest per una sola catena `crdt-yjs`, quattro richieste, dipendenze R2→R1 ecc., modello Luna medium e soglie originali. Fonte runtime SPB-03 separata da CandidateRef documentale SPB-04; niente confronto col bare o successo live implicito.
- [ ] Nuova copia posseduta con seed/request/suite hashes invariati, clone LF e tree iniziale uguale; ticket runtime canonici pubblici senza hidden/oracle/credenziali. Partial/copy/preflight error retained, no overwrite.
- [ ] Snapshot finanziario da copia esatta del ledger originale, aggiunta operatore tramite owner Budget, contatori identici; manifest `live_launch_authorized: false`. Nessun lancio/call/reservation nuovo o raw operator-store renewal.
- [ ] Packaging/artifact graph e readback locale verificati; review/QA/audit inline canonico; gate di launch/SDK/runtime/CI/delivery espliciti. Nessun Docker pull/start, benchmark, ri-esecuzione hidden suite, pubblicazione o installazione.

## Frontier
Dipende dal handoff SPB-03 implementation-complete, non dal suo release pass. Il mandato
«fallo» risponde a «riconciliare il budget e preparare questa prova»: non autorizza lancio.
I dati SDK consentono stime, non una fattura; manca la futura ammissione live separata.

## Step-by-Step Implementation Plan
1. Validare spec/ticket/current input e handoff SPB-03; preservare delta/source identities.
2. Congelare prefisso sessione e ricostruire costi attributi SDK; preservare ledger origine.
3. Preparare nuova source/product copy e quattro ticket runtime usando owner esistenti.
4. Compilare manifest prep-only con snapshot finanziario, source/SDK/question/policy/settings,
   image metadata e limiti. Non creare una nuova CLI/runner/driver o chiamare il vecchio caller.
5. Review e causal QA statici, audit canonico e handoff con costi e gate. Aggiornare stima
   operatore al checkpoint finale senza rinominare gli snapshot o risultati precedenti.

## Testing Plan
Solo serializer/hash/tree/ownership/accounting/static checks. Usare Git/subprocess readback,
copy byte-for-byte e owner Budget su nuova copia finanziaria; niente endpoint, chiavi, model
catalog refresh o container run. Nessun repeat di suite SPB-03: questo delta è documentale e
preparazione; test runtime originali mantengono CandidateRef/receipt propri.

## Out of Scope
Esecuzione del benchmark; bare, Lua, SQL, nuovo lotto completo o L12; modello/reasoning/soglie
alternativi; nuova spesa live; altri ticket o runner/scheduler/driver; secret/hidden ingestion;
commit/push/PR/merge, install/reload, wiki sync, GC, modifica o reset di ledger/source storici.
