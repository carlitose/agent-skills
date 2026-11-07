---
type: source
title: "PLX-01 — Intake da piano e ciclo di qualità condiviso"
identity_key: ticket:requirements-plan-execution/PLX-01
identity_strength: stable
source_path: docs/tickets/requirements-plan-execution/01-plan-intake.md
source_digest: sha256:a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PLX-01 — Intake da piano e ciclo di qualità condiviso

Compiled from `docs/tickets/requirements-plan-execution/01-plan-intake.md`. Identity is `ticket:requirements-plan-execution/PLX-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-requirements-plan-execution]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-requirements-plan-execution-plx-01.md","payload_bytes":3009,"payload_sha256":"a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079"}],"payload_bytes":3009,"payload_sha256":"a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079","schema":1,"source_digest":"sha256:a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079","source_identity":"ticket:requirements-plan-execution/PLX-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3009,"payload_sha256":"a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079","schema":1,"source_digest":"sha256:a818b78a770aa5429c74f329846399e0b02584ff63867355df049196e9935079","source_identity":"ticket:requirements-plan-execution/PLX-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PLX-01"
execution_mode: AFK
blocked_by: []
---

# PLX-01 — Intake da piano e ciclo di qualità condiviso

## Artifact Graph
- Artifact ID: `ticket:requirements-plan-execution:PLX-01`
- Role: `ticket`
- Parent: [Esecuzione da requisiti e piano](../../specs/requirements-plan-execution.md)

## Parent Spec
[requirements-plan-execution.md](../../specs/requirements-plan-execution.md), Target behavior,
Invariants and non-goals, Verification, Gates.

## What to Build
Intake requirements-and-plan dentro skills-only/execute-ticket senza ticket intermedi;
un solo ciclo di qualità, identità standalone e promozione canonica quando necessaria.

## Acceptance Criteria
- [ ] Policy iniettata, router e README distinguono intake da piano e canonico senza una quarta corsia.
- [ ] Requisiti chiari e consegna coesa entrano con un piano, senza spec/ticket/CandidateRef fittizi.
- [ ] Ambiguità, consegne indipendenti, ticket espliciti/esistenti e audit completo seguono il percorso dovuto.
- [ ] Test, GREEN/simplificazione, review, QA, gestione drift e handoff restano obbligatori e condivisi.
- [ ] Identità standalone include nuovi file; criteri/autorità e prove precedenti non vengono persi.
- [ ] Canonical parser/CandidateRef/Verification Record e corsie direct/Autopilot restano compatibili.
- [ ] Test mirati, quick locale e lint riportano esiti reali, con nessun claim live o di costo risparmiato.

## Frontier
Ready: proposta confermata, lavoro locale isolato; nessuna installazione o misura live.

## Gates
- Attempt: implementazione locale fino all'handoff di PLX-01.
- Budget per attempt: nessun limite impostato; nessuna spesa modello/servizio autorizzata qui.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato.
- Approvals: «va bene» alla proposta; solo modifiche locali e test offline. No installazione,
  benchmark, commit, push, PR, merge o pubblicazione.
- Exact version: nessuna; base osservata `e9510a538cf37403ed89f9f5c4378750857b9bf7`.
- Existing blocks searched: policy/router, execute-ticket, leaf, package/test-local e Git.
  Usare checkout isolato per non toccare file estranei; fallimento quick storico non trasferibile.

## Step-by-Step Implementation Plan
1. Aggiungere regressioni dell'intake da piano e osservare RED mirato.
2. Rendere condiviso il ciclo di qualità con intake espliciti, riferimenti e handoff proporzionati.
3. Allineare policy/router/README e leaf standalone senza cambiare i contratti macchina.
4. Verificare packaging, test mirati, quick e lint; review inline del candidato congelato.

## Testing Plan
Policy Node e riferimento intake, source/graph readback, quick locale obbligatorio e file limits;
revisione statica dei casi contrastanti; nessun modello live, benchmark o suite full implicita.

## Out of Scope
Installare o ricaricare Pi, modificare benchmark/lotti, schema macchina, scheduler/delegazione,
Git/provider delivery, retro-correggere gli artefatti del lotto precedente.

```
