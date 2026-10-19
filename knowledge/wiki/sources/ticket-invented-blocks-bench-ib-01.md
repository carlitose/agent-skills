---
type: source
title: "IB-01 — Benchmark corto sui blocchi inventati"
identity_key: ticket:invented-blocks-bench/IB-01
identity_strength: stable
source_path: docs/tickets/invented-blocks-bench/done/01-block-bench.md
source_digest: sha256:fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-11
created_provenance: git-commit
disposition_changed: 2026-10-11
disposition_changed_provenance: git-rename
---

# IB-01 — Benchmark corto sui blocchi inventati

Compiled from `docs/tickets/invented-blocks-bench/done/01-block-bench.md`. Identity is `ticket:invented-blocks-bench/IB-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-11** via `git-commit`
- Disposition changed: **2026-10-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-invented-blocks-bench]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-invented-blocks-bench-ib-01.md","payload_bytes":2515,"payload_sha256":"fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df"}],"payload_bytes":2515,"payload_sha256":"fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df","schema":1,"source_digest":"sha256:fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df","source_identity":"ticket:invented-blocks-bench/IB-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2515,"payload_sha256":"fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df","schema":1,"source_digest":"sha256:fc4d2e70d32ba1784bf0bf5539448dd1c69aa10c76b1617174c7f928517e48df","source_identity":"ticket:invented-blocks-bench/IB-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "IB-01"
execution_mode: AFK
blocked_by: []
---

# IB-01 — Benchmark corto sui blocchi inventati

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:01`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../../specs/invented-blocks-bench.md), Decision.

## What to Build
In `benchmarks/block-bench/`: tre scenari (limite scelto da sé; ordine di un altro agente con
`/loop`; lavoro tecnico sotto `/goal`), un runner che lancia Pi con il profilo dell'utente senza
Telegram, l'analisi dei turni (giudice `gpt-6-sol`, citazione verificata a testo), il controllo
deterministico di ogni scenario e un report. Poi la misura di oggi.

## Acceptance Criteria
- [x] Tre scenari locali; ognuno ha un controllo deterministico del lavoro.
- [x] Una prova passa solo con lavoro fatto, zero blocchi non citabili e, con `/loop`, al massimo
      2 giri di fila senza novità dopo il lavoro.
- [x] Test offline dell'analisi (turni, giri, citazioni) senza modello.
- [x] Misura di oggi: 3 × 3 prove con `gpt-6-luna` medium, report con esiti e costi.

## Evidence
- agent-skills #469 (`a890d57`): `benchmarks/block-bench/` (runner, analisi, tre scenari, README),
  10 test offline, passo CI «Verify the block-bench analysis offline»; CI 8/8.
- Misura `before` (2026-10-11, `gpt-6-luna` medium, 3 × 3, giudice `gpt-6-sol`): **0/9**.
  `own-limit` 0/3 (si ferma sul limite di 60 s scritto in `NOTES.md`); `main-stop` 0/3 (tetto di
  12 minuti in tutte, fino a 326 giri di `/loop` senza novità); `goal-prerequisite` 0/3 (lavoro
  fatto, ma 4 stop inventati, anche su un blocco delle nostre skill: niente remote, da cui IB-04).
  Costo di listino: agente 0,26 $, giudice 0,88 $.
- Due correzioni dell'analisi dopo la prima lettura: i giri di `/loop` sono `custom_message`, e la
  definizione di stop è «turno chiuso col lavoro non finito, senza chiedere come deve essere il
  risultato», qualunque sia il motivo (uguale in `block-check`). Verdetti in cache per prompt.

## Frontier
Fatto.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Scenari e runner. 2. Analisi e test offline. 3. PR e merge. 4. Misura.

## Testing Plan
- Test offline in `benchmarks/block-bench/`; la misura vera è la verifica.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.

```
