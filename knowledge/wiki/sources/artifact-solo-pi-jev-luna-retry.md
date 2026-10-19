---
type: source
title: "Luna Yjs — retry singolo e riduzione del lavoro operatore"
identity_key: artifact:solo-pi-jev-luna-retry
identity_strength: stable
source_path: docs/specs/solo-pi-jev-luna-retry.md
source_digest: sha256:2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Luna Yjs — retry singolo e riduzione del lavoro operatore

Compiled from `docs/specs/solo-pi-jev-luna-retry.md`. Identity is `artifact:solo-pi-jev-luna-retry`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-07]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-luna-retry.md","payload_bytes":3445,"payload_sha256":"2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545"}],"payload_bytes":3445,"payload_sha256":"2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545","schema":1,"source_digest":"sha256:2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545","source_identity":"artifact:solo-pi-jev-luna-retry","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3445,"payload_sha256":"2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545","schema":1,"source_digest":"sha256:2f23b056efc5b30a3dfc4388fefe54329ca387a3ed16f4acf5e508c4403fd545","source_identity":"artifact:solo-pi-jev-luna-retry"} -->
```markdown
# Luna Yjs — retry singolo e riduzione del lavoro operatore

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-retry`
- Role: `spec`
- Standalone: true

### Children
- [SPB-07: retry Luna e lavoro operatore misurato](../tickets/solo-pi-jev-luna-pilot/07-efficient-single-retry.md)

## Mandato e diagnosi
L'utente autorizza correggere il consumo del turno, poi un solo nuovo Yjs L4 Luna medium,
skills-only con budget cumulativo e storico invariato. Non autorizza altre repliche o delivery.
La finestra goal precedente 11:36:34.582–12:48:55.190 UTC contiene 17.519.912 token:
17.084.928 cacheRead, 345.846 input, 89.138 output; stima SDK $3,1483694, 110 tool call.
Il numero segnalato 17,6M non equivale a nuovi token generati o a costo del benchmark.
Causa operativa: lungo prefisso della sessione dal 28/09 ripetuto fra molte chiamate,
letture/script/audit ripetuti e più ticket; benchmark nativo precedente 396,453 s.

## Correzione del flusso, non del contatore
Usare piccoli packet di metriche/ref e helper già verificati. Accorpare ammissione,
preparazione ed esecuzione seriale in un caller per la sola cella autorizzata, non scheduler.
Non riscrivere grandi audit, ristampare file/receipt/log integrali o ripetere suite invariate.
Preservare costi/failed attempts. Preferire un vero taglio di sessione al ticket successivo.
Il tool di reset della sessione corrente non è disponibile: questa continuazione limitata
resta nella sessione esistente, dichiarata; batching non significa reset o cache eliminata.
Non creare un altro agente operatore, runner o app per fingere indipendenza/sessione fresca.
Il confronto finale misura chiamate/token/costi del segmento, non promette un risparmio noto.

## Nuova misura
Una nuova cella persistente crdt-yjs L4 con runtime congelato SPB-06 tree
56caabacc475c0fff4d3c246f6ca5876a0c5acbd. Stesse quattro richieste pubbliche canoniche,
seed/suite/question/policy/settings e openai-codex/gpt-6-luna medium. Clone LF separato,
nuovo processo/sessione del partecipante, Jev parent-isolated e judge in-process.
SPB-05 e source/prep precedenti non vengono modificati o rieseguiti. Gate/fallimenti,
candidato e delivered separati, tre dipendenze bloccate non sono tentativi del modello.
Oracle privato immutabile caller-only; nessun hidden feedback ai partecipanti.

## Ammissione e costi
Validare SPB-06, current tree/target/graph, source/SDK/skills/input/immagini. Copiare il
più recente ledger cumulativo in un nuovo store: 9 launch, 41 reservation, 7 semantic call,
310 charge già consumati. Non usare la vecchia preview con soli 8 launch. Budget originale
€1.000 e limiti restano invariati; nuova authority di scope autonoma e attribuita al messaggio
umano corrente. Refresh operatore prima di ogni reservation; SDK ≠ fattura/FX finale/hard cap.
Un futuro cambio di sessione richiede continuità esplicita dei segmenti di costo, non zero
né ricerca cieca dell'ancora originaria nel file più recente.

## Verifica e limiti
Solo packaging/serializer/source e readback causale della nuova cella, senza ripetere i 24
test SPB-06 invariati o oracle storici. Report solo aggregati, stessi vecchi confronti con
ref già verificati, confronto descrittivo non appaiato. Review/QA/audit inline shared-context,
non indipendenti. Release profile/exact-head CI/delivery/install/wiki sync restano gate.
Nessun secondo lancio per sostituire un errore e nessuna autorità derivata dal residuo.

```
