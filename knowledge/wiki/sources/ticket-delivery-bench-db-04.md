---
type: source
title: "DB-04 — Scenario C: parser, memoria e limiti"
identity_key: ticket:delivery-bench/DB-04
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/04-c-scenario.md
source_digest: sha256:ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# DB-04 — Scenario C: parser, memoria e limiti

Compiled from `docs/tickets/delivery-bench/done/04-c-scenario.md`. Identity is `ticket:delivery-bench/DB-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Blocked by: [[sources/ticket-delivery-bench-db-02]] — `ticket:delivery-bench/DB-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-04.md","payload_bytes":3111,"payload_sha256":"ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f"}],"payload_bytes":3111,"payload_sha256":"ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f","schema":1,"source_digest":"sha256:ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f","source_identity":"ticket:delivery-bench/DB-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3111,"payload_sha256":"ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f","schema":1,"source_digest":"sha256:ce325602154ec764812aa716c40cc086b541618482da943ef528c3285857a44f","source_identity":"ticket:delivery-bench/DB-04"} -->
```markdown
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

```
