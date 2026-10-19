---
type: source
title: "DB-03 — Scenario Python: catena da 8 richieste su bench38"
identity_key: ticket:delivery-bench/DB-03
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/03-python-scenario-bench38-chain.md
source_digest: sha256:88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# DB-03 — Scenario Python: catena da 8 richieste su bench38

Compiled from `docs/tickets/delivery-bench/done/03-python-scenario-bench38-chain.md`. Identity is `ticket:delivery-bench/DB-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Blocked by: [[sources/ticket-delivery-bench-db-02]] — `ticket:delivery-bench/DB-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-03.md","payload_bytes":3485,"payload_sha256":"88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb"}],"payload_bytes":3485,"payload_sha256":"88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb","schema":1,"source_digest":"sha256:88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb","source_identity":"ticket:delivery-bench/DB-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3485,"payload_sha256":"88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb","schema":1,"source_digest":"sha256:88b1027fc43fca6bb115651c87997d90d646e38fd5cda3fdf25278568d9a63bb","source_identity":"ticket:delivery-bench/DB-03"} -->
```markdown
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
- [x] Repo privato dello scenario Python con stato iniziale pubblico, 8 richieste grezze in sequenza (la 1-3 e la 1-8 sono prefissi della stessa catena), suite nascosta per richiesta, difetti latenti seminati e trappole del catalogo approvato con distanze registrate.
- [x] La soluzione di riferimento dell'oracolo passa tutta la suite nascosta a ogni lunghezza; uno stub che non fa nulla e una soluzione che cade in ogni trappola falliscono esattamente i controlli attesi.
- [x] La suite nascosta gira in un container dello scenario contro un repo consegnato senza modificarlo e produce il profilo per richiesta (accettazione, latenti, invarianti trasversali con distanza).
- [x] Nessun braccio ha visto richieste future, suite o catalogo: il repo privato non è raggiungibile dai checkout dei bracci.

## Frontier
**Completato** (2026-09-26, skills-only): scenario `python-billing` nel repo privato locale dell'oracolo (`dbench-private`, commit `18214b6`), mai in questo repo. Stato iniziale = seed-baseline di bench38 (digest albero `d5faaee3…`); richiesta 1 byte-identica al `TASK.md` di bench38 più il canary; richieste 2-8 in spagnolo come la 1. Suite nascosta sha256 `6ba6b3c0…` (69 controlli alla richiesta 8, 9 trappole con distanza registrata) in `python:3.12-slim`, eseguita dal `judge.py` pubblico con repo in sola lettura (albero identico prima e dopo). `verify_scenario.py`, per ognuna delle 8 lunghezze: il riferimento passa tutto, lo stub fallisce tutto tranne le invarianti preesistenti dichiarate in `expected.json`, la soluzione-trappola fallisce esattamente le trappole attive più il collaterale dichiarato: 24/24 varianti conformi. Riferimento e trappole generati da un unico sorgente annotato (`tools/build_overlays.py`). Il repo privato non ha remote, vive fuori da ogni checkout e non è montato nei container dei bracci (nessun braccio è ancora stato eseguito); ogni richiesta porta un canary per il controllo di fuga in DB-06. Oracolo scritto nella sessione orchestratrice, separata dalle sessioni dei bracci (`openai-codex/gpt-6-sol`).

## Step-by-Step Implementation Plan
1. Scrivere le 8 richieste e le decisioni/trappole che piantano, seguendo il catalogo DB-02.
2. Scrivere soluzione di riferimento, suite nascosta e latenti; verificare con stub e soluzione-trappola.
3. Congelare il repo privato con hash e registrare l'inventario dei controlli.

## Testing Plan
Soluzione di riferimento, stub e soluzione-trappola contro la suite nascosta nel container; hash del repo congelato.

## Out of Scope
- Eseguire bracci.
- Cambiare la richiesta 1 (bench38 resta confrontabile con i dati storici).

```
