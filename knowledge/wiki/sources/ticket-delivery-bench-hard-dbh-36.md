---
type: source
title: "DBH-36 — Lotto delle catene da 12"
identity_key: ticket:delivery-bench-hard/DBH-36
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/36-chain-12-lot.md
source_digest: sha256:4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-07
created_provenance: git-commit
disposition_changed: 2026-10-13
disposition_changed_provenance: git-rename
---

# DBH-36 — Lotto delle catene da 12

Compiled from `docs/tickets/delivery-bench-hard/done/36-chain-12-lot.md`. Identity is `ticket:delivery-bench-hard/DBH-36`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-07** via `git-commit`
- Disposition changed: **2026-10-13** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-chain-12]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-35]] — `ticket:delivery-bench-hard/DBH-35`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-36.md","payload_bytes":3729,"payload_sha256":"4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654"}],"payload_bytes":3729,"payload_sha256":"4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654","schema":1,"source_digest":"sha256:4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654","source_identity":"ticket:delivery-bench-hard/DBH-36","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3729,"payload_sha256":"4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654","schema":1,"source_digest":"sha256:4340ffbe00e5a6f0c2d775b91c95bf0107071eb9099c0252e0b8d0d43a9aa654","source_identity":"ticket:delivery-bench-hard/DBH-36"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-36"
execution_mode: AFK
blocked_by:
  - "DBH-35"
---

# DBH-36 — Lotto delle catene da 12

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:36`
- Role: `ticket`
- Parent: [delivery-bench-hard-chain-12.md](../../../specs/delivery-bench-hard-chain-12.md)

## Parent Spec
[delivery-bench-hard-chain-12.md](../../../specs/delivery-bench-hard-chain-12.md), Target behavior e Gates.

## What to Build
Il lotto `dbh-chain12`: `pi-tools`, `pi-full` e `bare-goal`, catene da 12, 3 ripetizioni × 3
scenari, `gpt-6-luna` medium, stesse suite di `dbh-luna3d`. Avvio visibile con il watcher, poi
il report a confronto con le catene da 4 (accettazione, costo, tempo, giri di `/goal`,
regressioni) e il giudizio di qualità sulle sue unità.

## Acceptance Criteria
- [x] Preflight senza lotto dei tre bracci riuscito.
- [x] Il lotto finisce entro 24 ore, oppure si ferma al tetto di tempo con il motivo
      registrato; la spesa a prezzo di listino è riportata.
- [x] Il report confronta i bracci per richiesta 1–12 e con le catene da 4, giri di `/goal`
      compresi.

## Evidence
- Preflight senza lotto dei tre bracci ok prima del lancio (2026-10-07).
- Lotto `dbh-chain12`: 2026-10-07T17:07Z → 2026-10-08T16:52Z (23 h 45 min), 27 celle,
  318 tentativi, 304 richieste giudicate, nessun tetto di catena raggiunto. Spesa a listino
  43,20 USD (40,84 agent, 2,36 ritentativi `infra:provider`), valutatore `/goal` escluso.
- Celle invalidate dall'audit: `crdt-yjs.pi-full.r1` (cross-cell), `sql-engine.pi-full.r2`
  (private-path), `sql-engine.pi-full.r3` (cross-cell, private-path).
- Accettazione (celle valide) per richieste 1-4 / 5-8 / 9-12, totale; catene da 4, richieste 1-4:
  - pi-tools 64% / 58% / 72%, 70/108; catene da 4 30/36 (83%).
  - pi-full 88% / 62% / 88%, 57/72; catene da 4 29/36 (81%).
  - bare-goal 83% / 67% / 69%, 79/108; catene da 4 25/36 (69%).
- Giri di `/goal` per richiesta: mediana 1 / 1 / 2 (pi-tools / pi-full / bare-goal), massimo
  97 / 32 / 500. Quasi tutto l'eccesso è un difetto del banco: 1.118 dei 1.500 verdetti
  «not yet met» chiedono la prova che TASK.md sia «nuovo e distinto» (DBH-43). Tempo, costo e
  giri sono gonfiati da questo; l'accettazione sui test nascosti molto meno.
- Report completo nel repo privato: `results/dbh-chain12/report.md`.
- Giudizio di qualità (2026-10-12/13, `quality.py`, recensioni Opus 5.5 alla cieca, 3 per unità,
  mediana): 304 unità, 302 con codice; file del lotto identici prima e dopo. Sulle celle valide:

  | Braccio | Accettate | Coverage | Mutation | Review (1-5) |
  |---|---|---|---|---|
  | pi-tools | 70/108 | 95% | 75% | 3,2 |
  | pi-full | 57/72 | 97% | 75% | 3,5 |
  | bare-goal | 79/108 | 97% | 75% | 3,5 |

  Catene da 4 (`quality-full`): review 3,5 / 3,5 / 3,2, coverage e mutation uguali. Le catene
  lunghe non peggiorano la qualità del codice accettato; pi-tools perde 0,3 punti di review.
  Spesa recensioni a listino 280,37 USD. 99 recensioni erano fallite per rate limit (429) con
  4 flussi paralleli e sono state rifatte con 2. Report: `results/quality-chain12/`
  (`report.md`, `valid-cells.md`, `run.json`).

## Frontier
Fatto.

## Gates
Come la spec: nessun tetto di spesa (abbonamento a canone fisso), 24 ore per tentativo, al massimo 2 tentativi; un solo
lotto alla volta; il checkout principale di `agent-skills` non si aggiorna durante il lotto.

## Step-by-Step Implementation Plan
1. Preflight, autorità del lotto con i gate, `init-lot`.
2. Avvio visibile e watcher; controllo della spesa proiettata.
3. Report e giudizio di qualità.

## Testing Plan
- Esecuzione reale; ledger e celle controllati a fine lotto.

## Out of Scope
- Bracci Crew sulle catene da 12.

```
