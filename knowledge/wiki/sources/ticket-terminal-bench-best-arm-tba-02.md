---
type: source
title: "TBA-02 — Lotto skills-only sui 63 task originali"
identity_key: ticket:terminal-bench-best-arm/TBA-02
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/02-run-skills-only-lot.md
source_digest: sha256:15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-25
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBA-02 — Lotto skills-only sui 63 task originali

Compiled from `docs/tickets/terminal-bench-best-arm/02-run-skills-only-lot.md`. Identity is `ticket:terminal-bench-best-arm/TBA-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]
- Blocked by: [[sources/ticket-terminal-bench-best-arm-tba-01]] — `ticket:terminal-bench-best-arm/TBA-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-02.md","payload_bytes":1540,"payload_sha256":"15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac"}],"payload_bytes":1540,"payload_sha256":"15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac","schema":1,"source_digest":"sha256:15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac","source_identity":"ticket:terminal-bench-best-arm/TBA-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1540,"payload_sha256":"15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac","schema":1,"source_digest":"sha256:15e08bd6bcfab439bb60e76f71cba6e0e7d654be2cbd30f090fac102a39645ac","source_identity":"ticket:terminal-bench-best-arm/TBA-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBA-02"
execution_mode: AFK
blocked_by:
  - "TBA-01"
---

# TBA-02 — Lotto skills-only sui 63 task originali

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:02`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Eseguire il braccio skills-only una volta per task sulla stessa lista di 63 task del lotto B (GPU esclusi), con la stessa policy flat-rate (1.000 richieste per start), `-n 3` e lot/authority/ledger propri. Sezione spec: Decisions 1–3.

## Acceptance Criteria
- [ ] Lot file, authority e ledger nuovi, fuori da Git, vincolati alla head integrata di TBA-01.
- [ ] 63 celle avviate al massimo una volta, senza retry; ogni cella ha result.json Harbor, ricevuta e journal.
- [ ] Nessun container si sovrappone al lotto B; il report grezzo elenca reward, eccezioni, richieste, tempo e costo stimato per task.

## Frontier
Bloccato da TBA-01 e dalla fine del lotto B (Pi bare, TBF-04).

## Step-by-Step Implementation Plan
1. Verificare che il lotto B sia chiuso e nessun container sia attivo.
2. Creare lot/authority con policy flat-rate e braccio skills-only; install-only di controllo.
3. Lanciare Harbor, monitorare, raccogliere i risultati.

## Testing Plan
Controlli live sul ledger e sui result.json; nessun gate di budget (token flat-rate).

## Out of Scope
- Seconda ripetizione (decisa in TBA-03).
- Modifiche all'agente.

```
