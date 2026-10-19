---
type: source
title: "SPC-02 — Catena locale con prove osservate e gate tipati"
identity_key: ticket:solo-pi-jev-implementation/SPC-02
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-implementation/02-observed-chain.md
source_digest: sha256:10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPC-02 — Catena locale con prove osservate e gate tipati

Compiled from `docs/tickets/solo-pi-jev-implementation/02-observed-chain.md`. Identity is `ticket:solo-pi-jev-implementation/SPC-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-implementation]]
- Blocked by: [[sources/ticket-solo-pi-jev-implementation-spc-01]] — `ticket:solo-pi-jev-implementation/SPC-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-implementation-spc-02.md","payload_bytes":2675,"payload_sha256":"10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274"}],"payload_bytes":2675,"payload_sha256":"10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274","schema":1,"source_digest":"sha256:10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274","source_identity":"ticket:solo-pi-jev-implementation/SPC-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2675,"payload_sha256":"10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274","schema":1,"source_digest":"sha256:10094a40a948099ebe7dab5ecd9311e8d5217604440a763092f7ee476134e274","source_identity":"ticket:solo-pi-jev-implementation/SPC-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPC-02"
execution_mode: AFK
blocked_by:
  - "SPC-01"
---

# SPC-02 — Catena locale con prove osservate e gate tipati

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spc-02`
- Role: `ticket`
- Parent: [Contratto implementativo](../../specs/solo-pi-jev-implementation.md)

## Parent Spec
[Contratto implementativo](../../specs/solo-pi-jev-implementation.md): SPC-02 e decisioni SPJ-02/03/04.

## What to Build
Controller di una catena canonica pronta nel worktree separato, SessionOwner SPC-01,
freeze/test process-owned, Jev via seam e judge via port sostitutivo; non un folder scheduler
né un nuovo tool per consegnare questi ticket. Output facts/receipts e completed-local.

## Acceptance Criteria
- [ ] Due richieste con Git CandidateRef reali e test osservati avanzano nella sola copia; originali intatti, niente delivery inferred.
- [ ] Rischio high/uncertain/nonclassificabile seleziona review condivisa solo findings, coverage globale distinta e prosa incompleta non clean.
- [ ] Soglie Jev invariate, HTTP retry solo 429/529 max3, semantica positiva/negativa/uncertain/forbidden/bound/malformed con permessi separati e un judge per domanda/candidato.
- [ ] Negativo deciso non bypassato; insufficient/judge fail verso analisi/umano; binding di domanda/digest/stato/candidato e costo attribuibili.
- [ ] Tre fallimenti finali totali per ticket non resettati da fix/reentry/resume; lavoro fallito conservato, indipendenti da ultimo albero valido e dipendenti bloccati.
- [ ] Mutazioni e base drift invalidano prove, conservano lavoro e impediscono applicazione cieca; budget/ambiente globali fermano ogni ticket; controlli causali RED/GREEN e handoff limitato.

## Frontier
Dependency-blocked da SPC-01, non da nuove scelte umane. Adapter judge fake in scope;
SPC-03 implementa il vero bridge senza autorizzare chiamate live.

## Step-by-Step Implementation Plan
1. Verificare SPC-01 e ammettere scope controller/test/README, CandidateRef e budget.
2. Test RED attraverso controller con Git/processi fake; implementare invarianti confermate, non promuovere in blocco il prototipo.
3. GREEN, cleanup, freeze/review/QA/audit con prove e costi cumulativi e gate live/delivery distinti.

## Testing Plan
Local integration con repository sintetico e seams Pi/Jev/judge, caso test verde ma copertura
insufficiente, final failure 1/2/3, replay dello stesso candidato, restore e crash checkpoint.
Nessun live/model-quality/benchmark. Full profile e CI esatta per futuro code PR.

## Out of Scope
Provider delivery, autorizzazione live, mutazioni delle copie/dati storici, scheduler,
legacy task/shim, installazione/reload, GC e wiki.

```
