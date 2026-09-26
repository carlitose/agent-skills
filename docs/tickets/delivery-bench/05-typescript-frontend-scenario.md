---
ticket_schema: 1
ticket_id: "DB-05"
execution_mode: AFK
blocked_by:
  - "DB-02"
---

# DB-05 — Scenario frontend TypeScript (Svelte, Playwright, API finte)

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:05`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Costruire una piccola app Svelte + TypeScript con API finte (mock server) e una catena di 8 richieste; verifier nascosto Playwright deterministico su comportamento, stato tra pagine, validazione dei form, race tra richieste, gestione errori dell'API e accessibilità (focus, aria, tastiera); mai pixel. Trappole: route stabili, componente condiviso riusato e non duplicato, token di design coerenti.

## Acceptance Criteria
- [ ] Repo privato dello scenario frontend TypeScript con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
- [ ] La soluzione di riferimento dell'oracolo passa tutta la suite nascosta a ogni lunghezza; uno stub che non fa nulla e una soluzione che cade in ogni trappola falliscono esattamente i controlli attesi.
- [ ] La suite nascosta gira in un container dello scenario contro un repo consegnato senza modificarlo e produce il profilo per richiesta (accettazione, latenti, invarianti trasversali con distanza).
- [ ] Nessun braccio ha visto richieste future, suite o catalogo: il repo privato non è raggiungibile dai checkout dei bracci.

## Frontier
Bloccato da DB-02.

## Step-by-Step Implementation Plan
1. Scrivere le 8 richieste e le decisioni/trappole che piantano, seguendo il catalogo DB-02.
2. Scrivere soluzione di riferimento, suite nascosta e latenti; verificare con stub e soluzione-trappola.
3. Congelare il repo privato con hash e registrare l'inventario dei controlli.

## Testing Plan
Come DB-03, con build dell'app e Playwright headless nel container.

## Out of Scope
- Backend vero.
- Giudizi visivi o LLM come giudice.
