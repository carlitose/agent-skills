---
type: source
title: "SPB-04 — Riconciliare i costi e preparare una prova corretta L4"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-04
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/04-prepare-corrected-l4.md
source_digest: sha256:40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-04 — Riconciliare i costi e preparare una prova corretta L4

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/04-prepare-corrected-l4.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-pilot]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-03]] — `ticket:solo-pi-jev-luna-pilot/SPB-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-04.md","payload_bytes":3750,"payload_sha256":"40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1"}],"payload_bytes":3750,"payload_sha256":"40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1","schema":1,"source_digest":"sha256:40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3750,"payload_sha256":"40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1","schema":1,"source_digest":"sha256:40c4f67db289e63df66991fbb1814b4a375236ad1f20a5189ed70dd773a014c1","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-04"} -->
```markdown
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

```
