---
type: source
title: "SPB-11 — Benchmark minimo reale del braccio Yjs L4"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-11
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/11-benchmark-minimum-arm.md
source_digest: sha256:460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-11 — Benchmark minimo reale del braccio Yjs L4

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/11-benchmark-minimum-arm.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-11`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-repair-loop]]
- Child source: [[sources/artifact-solo-pi-jev-luna-repair-loop-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-10]] — `ticket:solo-pi-jev-luna-pilot/SPB-10`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-11.md","payload_bytes":2238,"payload_sha256":"460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371"}],"payload_bytes":2238,"payload_sha256":"460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371","schema":1,"source_digest":"sha256:460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-11","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2238,"payload_sha256":"460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371","schema":1,"source_digest":"sha256:460baf80dc6773473a29c06058af973e7bae7631795370860d407c2d72f90371","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-11"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-11"
execution_mode: AFK
blocked_by:
  - "SPB-10"
---

# SPB-11 — Benchmark minimo reale del braccio Yjs L4

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-11`
- Role: `ticket`
- Parent: [Repair loop](../../specs/solo-pi-jev-luna-repair-loop.md)

### Produces
- [Risultato](../../research/solo-pi-jev-luna-repair-loop-results.md)

## Parent Spec
[Repair loop](../../specs/solo-pi-jev-luna-repair-loop.md).

## What to Build
Nuova catena Luna medium Yjs L4 sul runtime congelato SPB-10, port e valutazione reali;
diagnosi causale e repair/retest di eventuali bug del braccio nel mandato/budget originale.

## Acceptance Criteria
- [ ] Snapshot SPB-10/target/graph/envelope/input/SDK/model/skills/images e mandato attuale verificati; API owner renewal + nonstarting preflight prima di ready.
- [ ] Budget storico 10/47/7/367 conservato, operatore aggiornato, €1000 e FX originali invariati; ogni nuova prova conserva il consumo completo.
- [ ] Processo/sessione reali unici per cella, quattro richieste cumulative e dipendenze originarie; candidati/consegnati e oracle caller-only immutabili.
- [ ] Score, port esercitati, difetti del braccio e errori del codice distinti; gate/unattempted non trasformati in 0/4 o fallimenti del modello.
- [ ] Se bug del braccio: causal fix congelato e nuovo trial distinto, non reset/replay/forzatura 4/4; limiti/costi/verifica/handoff inline riportati.

## Frontier
Ready: SPB-10 implementation-complete/release-blocked e mandato umano repair-loop valido.

## Step-by-Step Implementation Plan
1. Admission completa e nuovo source/cell; owner rinnova soltanto prossimo slot.
2. Trial reale; bounded readback di stato/port/errore senza hidden feedback al partecipante.
3. Repair soltanto di difetti dimostrati del braccio, retest distinto; factual report e audit.

## Testing Plan
Admission/hash/immutabilità/contabilità; benchmark reale, analisi causale degli output/port;
nessuna suite runtime invariata ripetuta. No fake PASS o release/CI/delivery claim.

## Out of Scope
New model/scenario/arm, hidden feedback, original grant/ledger resets, product intervention,
runner/scheduler/subagent, publication/commit/push/merge/install/reload/wiki sync.

```
