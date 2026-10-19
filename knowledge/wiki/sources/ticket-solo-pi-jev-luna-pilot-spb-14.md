---
type: source
title: "SPB-14 — Eseguire il benchmark Luna sul braccio corrente"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-14
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/14-current-arm-benchmark.md
source_digest: sha256:e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-14 — Eseguire il benchmark Luna sul braccio corrente

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/14-current-arm-benchmark.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-14`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-current-arm-benchmark]]
- Child source: [[sources/artifact-solo-pi-jev-luna-current-arm-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-13]] — `ticket:solo-pi-jev-luna-pilot/SPB-13`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-14.md","payload_bytes":2467,"payload_sha256":"e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053"}],"payload_bytes":2467,"payload_sha256":"e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053","schema":1,"source_digest":"sha256:e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-14","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2467,"payload_sha256":"e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053","schema":1,"source_digest":"sha256:e8c1af572a34626c8035c6ba87c3c722a7fb7680ce6e21fea5a42ddd85647053","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-14"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-14"
execution_mode: AFK
blocked_by:
  - "SPB-13"
---

# SPB-14 — Eseguire il benchmark Luna sul braccio corrente

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-14`
- Role: `ticket`
- Parent: [Current-arm benchmark](../../specs/solo-pi-jev-luna-current-arm-benchmark.md)

### Produces
- [Risultato dei tre scenari](../../research/solo-pi-jev-luna-current-arm-results.md)

## Parent Spec
[Current-arm benchmark](../../specs/solo-pi-jev-luna-current-arm-benchmark.md).

## What to Build
Lotto Luna medium solo pi-jev-persistent: Lua VM e SQL engine nuove celle L4 sul runtime
SPB-12 invariato, Yjs r5 riusata soltanto dopo identità/protocollo/current-source validati.

## Acceptance Criteria
- [ ] Canonical graph/handoff/target/source e tre scenari/SDK/skills/images/argv/question/policy/mandato correnti validati prima di spending.
- [ ] Costo cumulativo completo12/57/9/428 come baseline, original €1000 e prior charges intatti; owner renewal/admission, nessun raw reset.
- [ ] Due nuove celle seriali Lua/SQL, un processo/sessione ciascuna; Yjs r5 riuso dichiarato validato, nessuna ripetizione o braccio bare.
- [ ] Candidati/consegnati, public receipts/semantic ports/score/gate per richiesta osservati con oracle privato immutabile; nessun hidden feedback o criterio cambiato.
- [ ] Report del solo current-arm/version: accepted/12 e tentati/blocked distinti, costi e bug/limiti evidenziati, frozen review/QA/handoff inline, niente release/delivery claim.

## Frontier
Ready: SPB-13 handoff implementation-complete, current runtime source SPB-12 e nuova
istruzione umana esplicita di benchmark Luna con questo braccio. No missing scope question.

## Step-by-Step Implementation Plan
1. Ammissione canonica e completo corpus/current-runtime, riuso Yjs e budget corrente.
2. Per-cell caller: Lua poi SQL, no replay; conserva tutti gli attempt e resource records.
3. Calcolo dei tre scenari, factual report e audit current-candidate senza suite immutata ripetuta.

## Testing Plan
Hash/source/graph/serializer/preflight/cumulative account; due real cells e static immutable
source/billing/oracle/readback. No fake PASS, no forced positive result or new suite replay.

## Out of Scope
Bare/control, new model/scenario/L12, lottery repeats, criterion/hidden/product intervention,
arm source edits mid-cohort, historical resets/relabels, delegation/runner/scheduler,
commit/push/PR/merge/install/reload/wiki sync.

```
