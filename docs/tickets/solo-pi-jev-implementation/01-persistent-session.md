---
ticket_schema: 1
ticket_id: "SPC-01"
execution_mode: AFK
blocked_by: []
---

# SPC-01 — Sessione RPC persistente e accounting della catena

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spc-01`
- Role: `ticket`
- Parent: [Contratto implementativo](../../specs/solo-pi-jev-implementation.md)

## Parent Spec
[Contratto implementativo](../../specs/solo-pi-jev-implementation.md): SPC-01 e Verification.

## What to Build
Owner Python del processo/sessione di catena con prompt seriali, terminale osservato,
entry/cursor accounting persistito e resume sicuro. Prima tracer bullet: due richieste
via peer RPC-shaped fake attraversano lo stesso owner; non implementa già tutto SPC-02/03.

## Evidence
SPJ-01–05 handoff canonici locali, decisioni reali e limiti del prototipo. ModelRuntime
binding e live non provati. Fonti Pi installate 0.99.1 e Context7 0.99.0, mai inventare API.

## Acceptance Criteria
- [ ] Due prompt consecutivi usano stesso PID/sessione, senza launcher per ruolo; native-shaped acceptance e settled distinti, handled/queued trattati correttamente.
- [ ] LF/CRLF, U+2028/U+2029, stderr/backpressure, deadline/EOF/malformed e bounded output testati; errore non è PASS e nessuna riapertura con processo forse vivo.
- [ ] Sessione/file e idle verificati; mismatch interrompe; un assistant error/aborted/length non diventa output valido. Receipt finale non deriva da sola acceptance.
- [ ] Entry/cursor e charge persistiti insieme, deduplicati per identità; assistant/tool/compaction/summary/usage e unknown conservati senza sommare stats due volte.
- [ ] Sentinel Jev assente dal child; safe resume dalla stessa storia solo con morte osservata/checkpoint/permesso/budget, nuova epoch contata e consumi conservati.
- [ ] RED causale osservato prima del codice, GREEN locale corrente e handoff canonico con limiti: niente live, produzione, delivery o adapter judge impliciti.

## Frontier
Ready per implementazione inline sulla prova SPJ-05 validata e sulle decisioni confermate.
Nessun gate HITL di design. Delivery/profilo globale/CI e binding live separati.

## Step-by-Step Implementation Plan
1. Normalizzare envelope e CandidateRef dal tree posseduto, scope chain_session.py/test dedicato e docgraph; conservare handoff SPJ precedenti.
2. Test RED con peer fake e native-shaped records; implementare owner che nasconde framing/lifecycle/journal, non scheduler.
3. GREEN mirato, simplification, freeze, review read-only condivisa, QA causale e verification-audit; nessun Git finalization.

## Testing Plan
Python unittest con child fake dichiarato e fixture persistente di sessione; assertions su PID,
event ordering, identity, charges, corrupt resume e env. Runtime ModelRuntime/Pi/Jev reali,
qualità e benchmark non eseguiti. Prima di futuro code PR, profilo obbligatorio e CI esatta.

## Out of Scope
SPC-02 workflow e SPC-03 bridge completion; scheduler, benchmark/harness/copie storiche,
install/pin/reload, commit/push/PR/merge, GC, wiki e compatibilità non richiesta.
