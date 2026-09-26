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
- [x] Repo privato dello scenario C con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
- [x] La soluzione di riferimento dell'oracolo passa tutta la suite nascosta a ogni lunghezza; uno stub che non fa nulla e una soluzione che cade in ogni trappola falliscono esattamente i controlli attesi.
- [x] La suite nascosta gira in un container dello scenario contro un repo consegnato senza modificarlo e produce il profilo per richiesta (accettazione, latenti, invarianti trasversali con distanza).
- [x] Nessun braccio ha visto richieste future, suite o catalogo: il repo privato non è raggiungibile dai checkout dei bracci.

## Frontier
**Completato** (2026-09-26, skills-only): scenario `c-recq` (libreria C11 di record `chiave=valore;…` e CLI `recq`) nel repo privato locale dell'oracolo (`dbench-private`, commit `18214b6`), mai in questo repo. Stato iniziale con latenti tipici del C (digest albero `cfe4b4fd…`) e `dev.py` che compila e testa dentro `gcc:14`, perché l'host non ha compilatore. Suite nascosta sha256 `d87c157f…` (66 controlli alla richiesta 8, 9 trappole con distanza registrata): libreria e CLI ricompilate con ASan+UBSan (`-fno-sanitize-recover=undefined`), un report del sanitizer fa fallire il controllo, `nm` per i simboli. Verifica per le 8 lunghezze: riferimento tutto verde, stub e soluzione-trappola falliscono esattamente l'atteso (`expected.json`, un collaterale dichiarato alla richiesta 8): 24/24 varianti conformi. Il repo privato non ha remote, vive fuori da ogni checkout e non è montato nei container dei bracci (nessun braccio è ancora stato eseguito); ogni richiesta porta un canary per il controllo di fuga in DB-06. Oracolo scritto nella sessione orchestratrice, separata dalle sessioni dei bracci (`openai-codex/gpt-6-sol`).

## Step-by-Step Implementation Plan
1. Scrivere le 8 richieste e le decisioni/trappole che piantano, seguendo il catalogo DB-02.
2. Scrivere soluzione di riferimento, suite nascosta e latenti; verificare con stub e soluzione-trappola.
3. Congelare il repo privato con hash e registrare l'inventario dei controlli.

## Testing Plan
Come DB-03, con build e sanitizer nel container.

## Out of Scope
- Eseguire bracci.
