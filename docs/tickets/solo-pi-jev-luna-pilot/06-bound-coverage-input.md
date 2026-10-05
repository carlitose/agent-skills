---
ticket_schema: 1
ticket_id: "SPB-06"
execution_mode: AFK
blocked_by:
  - "SPB-05"
---

# SPB-06 — Input coverage attribuito e bounded senza perdere artefatti

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-06`
- Role: `ticket`
- Parent: [Coverage input](../../specs/solo-pi-jev-coverage-input.md)

## Parent Spec
[Coverage input](../../specs/solo-pi-jev-coverage-input.md), Target e decisione.

## What to Build
Dopo il rapporto SPB-05, chiudere il bug coverage del todo con una riparazione locale:
preview pubbliche attribuite già esistenti, capture/diff integrali conservati, nessun
limite alzato o replay. Mandato umano: «finisci i todos»; non estende i permessi live/delivery.

## Acceptance Criteria
- [ ] Grande output di un test pubblico verde, con review clean, raggiunge il port coverage entro 65.536 B usando `test_observations` ≤32 KiB, candidata e path/hash/truncation visibili; stream integrale rimane nella receipt originale.
- [ ] Ticket/review/diff letterali completi e CandidateRef restano nello stato hashato; risposta NO o incerta non viene approvata né bypassata dai soli test verdi.
- [ ] Input semantico ancora troppo grande produce gate con motivo specifico `semantic-input-bound` e misura/limite, nessuna chiamata Jev/judge, nessuna perdita del diff/receipt o nuova failure fittizia.
- [ ] Threshold, retry, budget/permessi, dependency, ownership, readonly e reentry conservati; niente migrazione di decisioni/checkpoint storici, nessuna compatibilità parallela.
- [ ] RED/GREEN causali e regressioni mirate locali, grafo/LF/source/provenance, review/QA/audit seriali; port finti dichiarati, nessuna prova live o release presunta.
- [ ] SPB-05 report/authority/cella/costi e snapshot prep/storici immutati; niente benchmark/oracle replay, delivery/install/wiki sync.

## Frontier
AFK: diagnosi primaria esatta e handoff SPB-05 implementation-complete/release-blocked
conservati. Contratto di payload interno esplicitamente cambiato nella spec; seam esistente.

## Step-by-Step Implementation Plan
1. Validare grafo/envelope/base SPB-05 e autorità locale; ammettere solo causal checks senza provider.
2. RED un output pubblico grande; riusare `_test_observations` nello stato coverage e GREEN.
3. RED un diff completo oltre bound; distinguere motivo del gate senza modificare la soglia; GREEN.
4. Regression negative di NO/uncertainty e dipendenze; docs, freeze, review, QA e handoff separati.

## Testing Plan
Real Git e Python test process, synthetic fixture peer/Jev/judge come nei test esistenti.
Due RED/GREEN verticali, regressioni controller/repair; osservare binding, budget/calls,
receipt/diff originali e port input. Profilo release completo e exact-head CI rimangono gate.
Non eseguire test pubblici Yjs o oracle privato di nuovo e non importare hidden nei prompt.

## Out of Scope
Cambio di modello/soglie/input bound, truncation silenziosa, successo deciso dai soli test,
nuovi runtime/processi Pi/port reali, mutazione source/lotti storici, publish/commit/push/PR,
merge/install/reload, runner/delega, full-suite/profile senza specifica ammissione.
