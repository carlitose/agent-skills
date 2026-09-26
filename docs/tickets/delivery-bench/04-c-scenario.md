---
ticket_schema: 1
ticket_id: "DB-04"
execution_mode: AFK
blocked_by:
  - "DB-02"
---

# DB-04 — Scenario C: parser, memoria e limiti

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:04`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Costruire un programma C piccolo (parser di un formato di record, buffer, limiti) con stato iniziale pubblico e una catena di 8 richieste; latenti tipici del C (overflow, off-by-one, ownership, errori non controllati) e trappole del catalogo. Suite nascosta con sanitizer (ASan/UBSan) e test di confine nel container.

## Acceptance Criteria
- [ ] Repo privato dello scenario C con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
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
Come DB-03, con build e sanitizer nel container.

## Out of Scope
- Eseguire bracci.
