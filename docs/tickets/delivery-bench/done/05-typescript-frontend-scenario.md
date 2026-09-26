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
- [x] Repo privato dello scenario frontend TypeScript con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
- [x] La soluzione di riferimento dell'oracolo passa tutta la suite nascosta a ogni lunghezza; uno stub che non fa nulla e una soluzione che cade in ogni trappola falliscono esattamente i controlli attesi.
- [x] La suite nascosta gira in un container dello scenario contro un repo consegnato senza modificarlo e produce il profilo per richiesta (accettazione, latenti, invarianti trasversali con distanza).
- [x] Nessun braccio ha visto richieste future, suite o catalogo: il repo privato non è raggiungibile dai checkout dei bracci.

## Frontier
**Completato** (2026-09-26, skills-only): scenario `ts-reservas` (Svelte 5 + TypeScript + Vite, versioni fissate da lockfile) nel repo privato locale dell'oracolo (`dbench-private`, commit `18214b6`), mai in questo repo; digest albero dello stato iniziale `5a50ea62…`. Immagine del giudice `dbench-ts:1` (Playwright 1.63 più le dipendenze del lockfile, id `sha256:cf96e22b…`, Dockerfile nel repo privato). Suite nascosta sha256 `42cdfc89…` (63 controlli alla richiesta 8, 12 trappole con distanza registrata): build Vite nel container, Chromium headless con l'API finta servita dal routing di Playwright (nessuna rete, nessun server), orologio e fuso orario fissati; comportamento, validazione, race tra richieste, errori dell'API e accessibilità (focus, aria, tastiera), mai pixel, più regole statiche sui sorgenti. Verifica per le 8 lunghezze: 24/24 varianti conformi, nessun collaterale; il riferimento alla richiesta 8 resta verde su 3 ripetizioni in container concorrenti. Tempo del giudice: 6-23 s per il riferimento, fino a ~275 s per lo stub (attese dei controlli che falliscono). Il repo privato non ha remote, vive fuori da ogni checkout e non è montato nei container dei bracci (nessun braccio è ancora stato eseguito); ogni richiesta porta un canary per il controllo di fuga in DB-06. Oracolo scritto nella sessione orchestratrice, separata dalle sessioni dei bracci (`openai-codex/gpt-6-sol`).

## Step-by-Step Implementation Plan
1. Scrivere le 8 richieste e le decisioni/trappole che piantano, seguendo il catalogo DB-02.
2. Scrivere soluzione di riferimento, suite nascosta e latenti; verificare con stub e soluzione-trappola.
3. Congelare il repo privato con hash e registrare l'inventario dei controlli.

## Testing Plan
Come DB-03, con build dell'app e Playwright headless nel container.

## Out of Scope
- Backend vero.
- Giudizi visivi o LLM come giudice.
