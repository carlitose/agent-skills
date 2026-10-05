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
