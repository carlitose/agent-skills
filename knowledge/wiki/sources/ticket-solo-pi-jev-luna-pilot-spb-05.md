---
type: source
title: "SPB-05 — Eseguire la catena corretta Yjs L4 e confrontare i vecchi Luna"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-05
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/05-run-corrected-l4.md
source_digest: sha256:db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-05 — Eseguire la catena corretta Yjs L4 e confrontare i vecchi Luna

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/05-run-corrected-l4.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-pilot]]
- Child source: [[sources/artifact-solo-pi-jev-luna-corrected-l4-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-04]] — `ticket:solo-pi-jev-luna-pilot/SPB-04`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-05.md","payload_bytes":4254,"payload_sha256":"db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf"}],"payload_bytes":4254,"payload_sha256":"db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf","schema":1,"source_digest":"sha256:db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4254,"payload_sha256":"db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf","schema":1,"source_digest":"sha256:db1364ae79e8dc333c7db3d60962cccbc0b7fdafc9accccdd5c8f6d281e2eedf","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-05"
execution_mode: AFK
blocked_by:
  - "SPB-04"
---

# SPB-05 — Eseguire la catena corretta Yjs L4 e confrontare i vecchi Luna

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-05`
- Role: `ticket`
- Parent: [Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md)

### Produces
- [Risultato corretto e confronto storico Luna](../../research/solo-pi-jev-luna-corrected-l4-results.md)

## Parent Spec
[Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md), Corrected L4 Execution — SPB-05.

## What to Build
Un solo avvio della cella persistente Yjs L4 preparata in SPB-04, sul medesimo Luna medium,
seguito da confronto descrittivo con vecchi risultati Yjs Luna e rapporto locale verificato.
Mandato umano: «Avvia il banchmaerk e poi confrontiamolo con i vecchi sempre su quello luna».

## Acceptance Criteria
- [ ] Spec/ticket/SPB-04/current target/source/SDK/skills/dati/immagini verificati; nuova authority di scope e budget originale cumulativo attribuiti, senza riscrivere/reset dei ledger storici; costi operatore aggiornati prima di nuova spesa.
- [ ] Una sola nuova cella Yjs L4, stesso Luna medium/question/policy/soglie/tool/settings/prime quattro richieste; clone LF/tree seed uguali, processo/sessione unici, Jev nel parent isolato e judge in-process, oppure preciso gate osservato senza replay.
- [ ] Tutti i turn/test/diff/findings/usage/candidate e snapshot delivered conservati, fallimenti reali separati da format/infra/gate; richieste dipendenti bloccate non contate come tentativi.
- [ ] Oracle privato invariato e immutabile/no-network giudica i quattro snapshot e gli eventuali candidati separatamente, senza feedback hidden ai partecipanti; errore oracle preservato e classificato, non falsificato come model failure.
- [ ] Rapporto aggregato confronta SPB-02 Yjs persistente/bare e vecchi DBH Luna solo con dati/identità verificate; denominatori/repliche/protocolli/SDK/skill diversi espliciti, nessun controllo appaiato nuovo o superiorità generale.
- [ ] Costi sperimentali e operatore distinti/cumulativi, ignoti/invoice/FX visibili; source/risultati/store prep e storici intatti; review/QA/audit inline, no delivery/install/runner/delega.

## Frontier
Dipendenza SPB-04 implementation-complete; il release-blocked documentale non è un PASS
release e non impedisce la misura isolata ora esplicitamente autorizzata. Budget originale
€1.000, 8 launch e 7 semantic call già consumati; nessun nuovo budget. Auth/runtime da
osservare nella cella, un fallimento non autorizza la sostituzione.

## Step-by-Step Implementation Plan
1. Canonical validation della dipendenza e input; nuova provenance della sola richiesta live.
2. Snapshot fresco SDK operatore, copia del checkpoint finanziario per owner Budget; LF
   clone, source/SDK/skills/input/immagini e packaging readback. Stop sugli ignoti.
3. Un avvio esplicito con adapter esistente; quattro richieste seriali con dipendenze e
   oracle caller-only. Conservare record anche in caso di errore/partial/unknown cost.
4. Confrontare vecchi risultati dello stesso scenario/modello senza eseguirli o modificarli;
   aggregare misure/costi e spiegare limiti e meccanismi, non inferire cause da un punteggio.
5. Freeze, review read-only, QA causale di evidenze/counts/hash/costi e audit/handoff locali.

## Testing Plan
Prima della spesa: grafo/tree/delta/serializer/hash, quote e headroom, clone iniziale,
SDK/skill e immagine locale già presenti. Nessun full-suite repeat SPB-03 per delta docs.
Durante la sola cella: test pubblici process-owned e oracle invariato sugli snapshot privati.
Dopo: statico+local integration readback di protocollo/dipendenze/denominatori/uso/costi,
source/pricing/data invariati e distinzione candidate/delivered. SDK/hidden output solo
artefatti privati, report pubblico solo aggregati. I vecchi test mantengono identità proprie.

## Out of Scope
Bare fresco, SQL/Lua, lotto completo o L12; nuove repliche/modelli/soglie; replay/reset;
nuovo runner/scheduler/driver di consegna; subagents; secret/hidden ingestion nei prompt;
commit/push/PR/merge, pubblicazione, install/reload, wiki sync o GC. Consenso live non è
consenso a delivery né fattura nota né certificazione del modello/produzione.

```
