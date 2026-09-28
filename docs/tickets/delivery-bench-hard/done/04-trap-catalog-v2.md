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
- [x] Il catalogo copre i tre scenari con i vincoli sopra. Ogni trappola ha tipo, regola,
  tentazione e distanza.
- [x] L'utente ha rivisto tipi, richieste e distanze, senza vedere codice nascosto, e ha
  approvato o chiesto modifiche. L'approvazione è registrata nel repo privato.
- [x] Nel repo pubblico ci sono solo conteggi e distanze aggregate.

## Outcome
2026-09-28. Il catalogo è `catalog-v2.md` nel repo privato (commit `84bcd352`, sha256
`f7984569…`).
- **Release fissate**: Lua 5.4.6 con la sua suite ufficiale, sqlglot 30.13.0 (sdist PyPI) e Yjs
  13.6.27 (tag `v13.6.27`), tutte con licenza MIT.
- **Trappole**: 7 per scenario, 21 in tutto, e ogni scenario copre le cinque tipologie. Le regole
  stanno nelle richieste 2-4 e le tentazioni nelle 8-12. Le distanze vanno da 5 a 10 in `lua-vm` e
  da 6 a 10 negli altri due.
- **Contratti**: in ogni scenario la via più corta di almeno una tentazione rompe un contratto già
  consegnato (formato binario, risultati di query o codifica, come nella decisione 7 della mappa).
- **Latenti reali**: 5 bug documentati di Lua (lua.org/bugs), 7 fix upstream di sqlglot successivi
  alla release e 5 del ramo `v13` di Yjs. Ciascuno è legato alla richiesta che lo attraversa.
  Per le regole sui bug reali il riferimento lo scriviamo noi: la patch upstream non è la fonte.
- **Revisione**: l'utente ha rivisto la sintesi per scenario (tipi, richieste, regole, tentazioni
  e distanze) senza vedere codice nascosto. Il 28/09 alle 07:30 UTC ha approvato i tre scenari e
  il metodo comune senza modifiche. L'approvazione è registrata nel catalogo.

## Frontier
Chiuso.

## Step-by-Step Implementation Plan
1. Studiare le release fissate: convenzioni reali del codice, contratti pubblici e bug
   documentati.
2. Scrivere il catalogo nel repo privato.
3. Presentare all'utente la sintesi (tipi, richieste, distanze) e raccogliere l'approvazione.

## Testing Plan
Revisione umana. La verifica meccanica delle trappole avviene nei ticket di scenario.

## Out of Scope
- Suite nascoste e soluzioni di riferimento (DBH-05/06/07).
