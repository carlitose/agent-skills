---
type: source
title: "IB-03 — `/loop` si ferma dopo giri senza novità"
identity_key: ticket:invented-blocks-bench/IB-03
identity_strength: stable
source_path: docs/tickets/invented-blocks-bench/done/03-loop-idle-stop.md
source_digest: sha256:3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-11
created_provenance: git-commit
disposition_changed: 2026-10-13
disposition_changed_provenance: git-rename
---

# IB-03 — `/loop` si ferma dopo giri senza novità

Compiled from `docs/tickets/invented-blocks-bench/done/03-loop-idle-stop.md`. Identity is `ticket:invented-blocks-bench/IB-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-11** via `git-commit`
- Disposition changed: **2026-10-13** via `git-rename`

## Graph

- Parent source: [[sources/artifact-invented-blocks-bench]]
- Blocked by: [[sources/ticket-invented-blocks-bench-ib-01]] — `ticket:invented-blocks-bench/IB-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-invented-blocks-bench-ib-03.md","payload_bytes":1875,"payload_sha256":"3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d"}],"payload_bytes":1875,"payload_sha256":"3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d","schema":1,"source_digest":"sha256:3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d","source_identity":"ticket:invented-blocks-bench/IB-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1875,"payload_sha256":"3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d","schema":1,"source_digest":"sha256:3d120534446917fb7ec3c5edb645eff0fe230d2c03b6f74273c2d9447525e37d","source_identity":"ticket:invented-blocks-bench/IB-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "IB-03"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-03 — `/loop` si ferma dopo giri senza novità

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:03`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../../specs/invented-blocks-bench.md), Decision.

## What to Build
In `@carlitose86/pi-loop`: se due giri di fila non usano strumenti che cambiano qualcosa e la
risposta resta la stessa, il loop si ferma e lo dice all'utente.

## Acceptance Criteria
- [x] Due giri senza novità fermano il loop con un messaggio; un giro con lavoro azzera il conto.
- [x] Test mirati; pubblicazione da parte dell'utente (2FA) e pin.

## Evidence
- carlitose/pi-loop #1 (`d0940ff`): confronto di novità con un modello per giro (scelta (a)
  dell'utente: nella `main-stop` ogni giro riscrive `OUTBOX.md` con parole diverse, un confronto
  meccanico non lo vedrebbe); `PI_LOOP_NOVELTY=0` lo spegne.
- carlitose/pi-loop #2 (`bd58b26`): si confrontano solo i giri del loop; un turno avviato da
  un'altra estensione (il rimando di `block-check`) non conta e non azzera.
- `@carlitose86/pi-loop` 0.2.0 pubblicato dall'utente il 2026-10-13 (shasum `a45516a`); pin in
  pi-personal-config (`fda715a`), `update:personal` verificato (0.2.0 installato).
- Misura con pi-loop locale: `main-stop` 3/3, loop fermo dopo 2 giri (era 0/3, fino a 326 giri).

## Frontier
Fatto.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Modifica e test in pi-loop. 2. Pubblicazione e pin. 3. Rimisura con IB-01.

## Testing Plan
- Test di pi-loop; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.

```
