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
