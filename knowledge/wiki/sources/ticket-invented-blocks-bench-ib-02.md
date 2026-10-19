---
type: source
title: "IB-02 — Controllo a fine turno sui blocchi"
identity_key: ticket:invented-blocks-bench/IB-02
identity_strength: stable
source_path: docs/tickets/invented-blocks-bench/done/02-turn-end-block-check.md
source_digest: sha256:1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-12
created_provenance: git-commit
disposition_changed: 2026-10-12
disposition_changed_provenance: git-rename
---

# IB-02 — Controllo a fine turno sui blocchi

Compiled from `docs/tickets/invented-blocks-bench/done/02-turn-end-block-check.md`. Identity is `ticket:invented-blocks-bench/IB-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-12** via `git-commit`
- Disposition changed: **2026-10-12** via `git-rename`

## Graph

- Parent source: [[sources/artifact-invented-blocks-bench]]
- Blocked by: [[sources/ticket-invented-blocks-bench-ib-01]] — `ticket:invented-blocks-bench/IB-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-invented-blocks-bench-ib-02.md","payload_bytes":2492,"payload_sha256":"1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a"}],"payload_bytes":2492,"payload_sha256":"1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a","schema":1,"source_digest":"sha256:1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a","source_identity":"ticket:invented-blocks-bench/IB-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2492,"payload_sha256":"1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a","schema":1,"source_digest":"sha256:1a075453fec5ddaaf53468e3085db8ce35faaaac97d7f8b03d643b62ddd82a8a","source_identity":"ticket:invented-blocks-bench/IB-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "IB-02"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-02 — Controllo a fine turno sui blocchi

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:02`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../../specs/invented-blocks-bench.md), Decision.

## What to Build
Un'estensione che, a fine turno, chiede a un modello se il turno finisce su un blocco e se il
blocco si può citare da parole dell'utente. Se non si può, rimanda l'agente al lavoro con un
messaggio breve; un blocco citato o un errore reale restano validi. Al massimo due rimandi di fila,
poi la decisione passa all'utente.

## Acceptance Criteria
- [x] Un blocco non citabile riporta l'agente al lavoro; uno citato no.
- [x] Niente rimandi infiniti: al massimo due di fila.
- [x] Test mirati senza modello; installata nel profilo dell'utente.

## Evidence
- pi-code `extensions/block-check.ts` (ramo `fix/todo-reminder`): PR #4, #5, #6, #7, #8, #9, #10;
  ultimo `9e7d01e`, pin in pi-personal-config (`2492350`), `update:personal` verificato.
- Il controllo chiede fatti semplici (`work_done`, `still_failing`, `asks_how`, `waits`,
  `user_quote`), non «si ferma?»: con quella domanda luna rispondeva «no» su stop evidenti.
- Correzioni trovate misurando: i giri di `/loop` sono le parole dell'utente e il lavoro si giudica
  sull'ultimo messaggio; chiedere a qualcuno, se richiesto, è lavoro finito; un controllo fallito
  si ritenta una volta; il testo delle skill iniettato nel messaggio utente non è dell'utente;
  la richiesta intera non vale come citazione di un blocco; un fallimento riportato non è lavoro
  finito.
- Serie di misure (`gpt-6-luna` medium, 3 × 3, giudice `gpt-6-sol`): `before` 0/9 →
  `after-ib02` 2/9 → `after-split` 4/9 → `after-ib03` 6/9 → `after-final` 7/9 → `after-final4`
  **9/9** (goal-prerequisite 3/3, main-stop 3/3 con 2 giri di loop e loop fermo, own-limit 3/3).
  Costo di listino dell'ultima: agente 0,10 $, giudice 0,18 $.

## Frontier
Fatto.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Estensione e test. 2. PR, merge, pin. 3. Rimisura con IB-01.

## Testing Plan
- Test mirati dell'estensione; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.

```
