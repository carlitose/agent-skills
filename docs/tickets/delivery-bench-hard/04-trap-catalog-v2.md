---
ticket_schema: 1
ticket_id: "DBH-04"
execution_mode: HITL
blocked_by:
  - "DBH-01"
---

# DBH-04 — Catalogo delle trappole v2

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:04`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Il catalogo delle trappole e dei latenti per `lua-vm`, `sql-engine` e `crdt-yjs`, nel repo
privato dell'oracolo (`catalog-v2.md`), rivisto dall'utente come in DB-02.

Per ogni scenario il catalogo ha:
- **almeno cinque trappole**, una per tipologia del contratto: deprecato, architettura, bug
  chiuso, contratto, convenzione;
- **regole e tentazioni distanti**: la regola a una delle richieste 2-4 e la tentazione a una
  delle 8-12, con la distanza calcolata;
- **almeno una tentazione** la cui via più corta rompe un contratto già consegnato: formato
  binario, API, encoding o risultati di query;
- **i latenti scelti fra i bug reali documentati** della release fissata, ciascuno con la
  richiesta che lo attraversa.

## Acceptance Criteria
- [ ] Il catalogo copre i tre scenari con i vincoli sopra. Ogni trappola ha tipo, regola,
  tentazione e distanza.
- [ ] L'utente ha rivisto tipi, richieste e distanze, senza vedere codice nascosto, e ha
  approvato o chiesto modifiche. L'approvazione è registrata nel repo privato.
- [ ] Nel repo pubblico ci sono solo conteggi e distanze aggregate.

## Frontier
Richiede una decisione umana: la revisione del catalogo. È bloccato da DBH-01, che conferma gli
scenari.

## Step-by-Step Implementation Plan
1. Studiare le release fissate: convenzioni reali del codice, contratti pubblici e bug
   documentati.
2. Scrivere il catalogo nel repo privato.
3. Presentare all'utente la sintesi (tipi, richieste, distanze) e raccogliere l'approvazione.

## Testing Plan
Revisione umana. La verifica meccanica delle trappole avviene nei ticket di scenario.

## Out of Scope
- Suite nascoste e soluzioni di riferimento (DBH-05/06/07).
