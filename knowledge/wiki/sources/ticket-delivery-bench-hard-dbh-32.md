---
type: source
title: "DBH-32 — Pilota e giudizio completo"
identity_key: ticket:delivery-bench-hard/DBH-32
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/32-quality-pilot-and-full.md
source_digest: sha256:65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed: 2026-10-07
disposition_changed_provenance: git-rename
---

# DBH-32 — Pilota e giudizio completo

Compiled from `docs/tickets/delivery-bench-hard/done/32-quality-pilot-and-full.md`. Identity is `ticket:delivery-bench-hard/DBH-32`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **2026-10-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-quality-judge]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-29]] — `ticket:delivery-bench-hard/DBH-29`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-30]] — `ticket:delivery-bench-hard/DBH-30`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-31]] — `ticket:delivery-bench-hard/DBH-31`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-32.md","payload_bytes":2522,"payload_sha256":"65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b"}],"payload_bytes":2522,"payload_sha256":"65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b","schema":1,"source_digest":"sha256:65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b","source_identity":"ticket:delivery-bench-hard/DBH-32","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2522,"payload_sha256":"65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b","schema":1,"source_digest":"sha256:65e5362a1f2c11a4c2208c24824f82cad9079f18ad3803742da2cc90ee6a0e5b","source_identity":"ticket:delivery-bench-hard/DBH-32"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-32"
execution_mode: AFK
blocked_by:
  - "DBH-29"
  - "DBH-30"
  - "DBH-31"
---

# DBH-32 — Pilota e giudizio completo

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:32`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
Pilota su 10 unità: una per braccio e scenario, più una scelta a caso con seme fisso. Per ogni unità si fanno due revisioni Opus e si applica la regola della spec:
- una revisione per unità, se i voti differiscono al massimo di 1 punto e i bug gravi coincidono;
- altrimenti tre revisioni, con la mediana.

Poi il giudizio completo di `dbh-luna3d` e `dbh-luna3e` e il report finale, con la spesa reale.

Spec: Pilot rule e Gates.

## Acceptance Criteria
- [x] Il pilota riporta tempo e costo per misura e per unità, e l'accordo tra le due revisioni.
- [x] Il giudizio completo copre tutte le 144 unità, con il report in `results/<lot>/quality/`.
- [x] Spesa reale e tempo sono riportati; i tentativi restano registrati.

## Evidence
- Pilota: 12 unità, accordo 10/12 tra le due revisioni, quindi tre revisioni con la mediana nel
  giudizio completo; spesa 5,52 $ (`results/quality-pilot/pilot.md`).
- Giudizio completo: 144 unità (136 con codice) con copertura, mutazione e 3 revisioni Opus
  ciascuna. I file per unità sono in `results/<lot>/quality/{coverage,mutation,review}/`, il
  report unico dei due lotti in `results/quality-full/report.md`.
- Tempo 9,6 ore; 408 revisioni per 105,32 $ a prezzo di listino (abbonamento).
- `lot files identical: True`: digest dei due lotti uguali prima e dopo (`run.json`).

## Frontier
Fatto.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Eseguire il pilota.
2. Scegliere il numero di revisioni.
3. Eseguire il giudizio completo.
4. Riportare all'utente.

## Testing Plan
- Esecuzione reale, controllando che `cell.json` e il ledger restino identici byte per byte.

## Out of Scope
- Rigiocare i bracci.
- Cambiare l'esito ufficiale.

```
