---
ticket_schema: 1
ticket_id: "DB-03"
execution_mode: AFK
blocked_by:
  - "DB-02"
---

# DB-03 — Scenario Python: catena da 8 richieste su bench38

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:03`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Estendere bench38 (modulo di fatturazione, 5 latenti di arrotondamento) in una catena di 8 richieste in sequenza. La richiesta 1 resta bench38 invariato; le 2-8 si appoggiano alle scelte precedenti (regole di arrotondamento, contratto money, sconti) e piantano le trappole del catalogo. Suite nascosta per richiesta con latenti nuovi. Oracolo: Claude Fable in sessione separata; bracci su `openai-codex/gpt-6-sol`.

## Acceptance Criteria
- [ ] Repo privato dello scenario Python con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
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
Soluzione di riferimento, stub e soluzione-trappola contro la suite nascosta nel container; hash del repo congelato.

## Out of Scope
- Eseguire bracci.
- Cambiare la richiesta 1 (bench38 resta confrontabile con i dati storici).
