---
type: source
title: "TBA-03 — Report appaiato e scelta del vincitore"
identity_key: ticket:terminal-bench-best-arm/TBA-03
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/03-select-the-winner.md
source_digest: sha256:462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-25
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBA-03 — Report appaiato e scelta del vincitore

Compiled from `docs/tickets/terminal-bench-best-arm/03-select-the-winner.md`. Identity is `ticket:terminal-bench-best-arm/TBA-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]
- Blocked by: [[sources/ticket-terminal-bench-best-arm-tba-02]] — `ticket:terminal-bench-best-arm/TBA-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-03.md","payload_bytes":1676,"payload_sha256":"462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69"}],"payload_bytes":1676,"payload_sha256":"462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69","schema":1,"source_digest":"sha256:462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69","source_identity":"ticket:terminal-bench-best-arm/TBA-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1676,"payload_sha256":"462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69","schema":1,"source_digest":"sha256:462ba3ee23324f5c21bc515419baafd38a6bb468fcf11c3f9eff774c53354d69","source_identity":"ticket:terminal-bench-best-arm/TBA-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBA-03"
execution_mode: AFK
blocked_by:
  - "TBA-02"
---

# TBA-03 — Report appaiato e scelta del vincitore

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:03`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Confrontare Pi bare (lotto B) e skills-only (TBA-02) task per task con la regola della spec: se la differenza è di al massimo 3 task o McNemar esatto dà p ≥ 0,05, eseguire una ripetizione in più per entrambi i bracci prima di decidere, altrimenti a parità vince il braccio più semplice. Committare report, vincitore e split dev/held-out deterministico. Sezioni spec: Decisions 3–4.

## Acceptance Criteria
- [ ] La tabella appaiata copre gli stessi 63 task; le eccezioni senza voto contano come fallimento e sono contate a parte.
- [ ] Il report riporta il p-value McNemar calcolato e la decisione secondo la regola, senza pesi soggettivi.
- [ ] La split dev(42)/held-out(21) è derivata dall'ordinamento SHA-256 dei nomi task e committata prima di qualsiasi modifica all'agente.

## Frontier
Bloccato da TBA-02.

## Step-by-Step Implementation Plan
1. Ridurre i due ledger e i result.json in una tabella appaiata.
2. Applicare la regola; se serve, eseguire la ripetizione extra di entrambi i bracci.
3. Scrivere report e split; PR e merge.

## Testing Plan
Ricalcolo deterministico della tabella dai file sorgente; test unitario della funzione McNemar e della split.

## Out of Scope
- Sviluppo del vincitore (TBA-04).
- Confronti su harness modificato.

```
