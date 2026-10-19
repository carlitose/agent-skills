---
type: source
title: "LIN-01 — Integrare l'archivio pi-lec03 a comportamento invariato"
identity_key: ticket:solo-pi-jev-archive-integration/LIN-01
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-archive-integration/01-integrate-lec03-archive.md
source_digest: sha256:6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# LIN-01 — Integrare l'archivio pi-lec03 a comportamento invariato

Compiled from `docs/tickets/solo-pi-jev-archive-integration/01-integrate-lec03-archive.md`. Identity is `ticket:solo-pi-jev-archive-integration/LIN-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-archive-integration]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-archive-integration-lin-01.md","payload_bytes":2333,"payload_sha256":"6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af"}],"payload_bytes":2333,"payload_sha256":"6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af","schema":1,"source_digest":"sha256:6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af","source_identity":"ticket:solo-pi-jev-archive-integration/LIN-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2333,"payload_sha256":"6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af","schema":1,"source_digest":"sha256:6a826b5e7d0197dcc4bb9cfd5408b1652a8679feb06ac6e6c9edcf9241a6a1af","source_identity":"ticket:solo-pi-jev-archive-integration/LIN-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "LIN-01"
execution_mode: AFK
blocked_by: []
---

# LIN-01 — Integrare l'archivio pi-lec03 a comportamento invariato

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-lin-01`
- Role: `ticket`
- Parent: [solo-pi-jev-archive-integration.md](../../specs/solo-pi-jev-archive-integration.md)

## Parent Spec
[solo-pi-jev-archive-integration.md](../../specs/solo-pi-jev-archive-integration.md): Decision, Invariants, Verification.

## What to Build
Portare in `main` tutto il contenuto di `archive/wt-pi-lec03`, cioè documentazione, arm
di benchmark e catena di `ticket-driver`, adattando `findings.py` e la domanda
`review.scope_complete` in modo che il comportamento distribuito resti identico.

## Acceptance Criteria
- [ ] Tutti gli 81 percorsi dell'archivio sono presenti; le uniche differenze rispetto
      all'archivio sono i due adattamenti della spec e i loro test.
- [ ] `ticket-driver/questions/review.scope_complete.json` è identico a `main` e la cartella
      `ticket-driver/questions/` contiene gli stessi sei file.
- [ ] `parse_findings` senza opzioni riconosce solo percorsi `.py`, come in `main`;
      con `any_extension=True` riconosce qualunque estensione; `chain_controller` usa l'opt-in.
- [ ] La variante adjudicated della domanda è in `benchmarks/delivery-bench/questions/`.
- [ ] `test_staged_behavior` passa: il cambio di sessione confronta il motore delle decisioni
      sottostante e mantiene l'osservazione della copertura.
- [ ] La suite `ticket-driver/tests`, i test nuovi di `benchmarks/delivery-bench` e il lint passano.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Applicare il commit d'archivio su un branch da `origin/main`.
2. Ripristinare la domanda distribuita e spostare la variante nei benchmark.
3. Rendere opt-in la regex estesa in `findings.py` e attivarla in `chain_controller.py`.
4. Correggere `_CoverageFeedback.path` e il reincapsulamento in `bind_session` (LEC v3).
5. Aggiungere i test di regressione; eseguire i test causali e il lint.

## Testing Plan
Unitari locali (`unittest`, `node --test` per i `.mjs` nuovi); CI del PR.
Benchmark live non eseguiti: fuori scope.

## Out of Scope
- Rilanciare benchmark, aggiornare il launcher esterno in `C:/dbench`, cambiare il pin installato.
- Spostare in `done/` i ticket importati.

```
