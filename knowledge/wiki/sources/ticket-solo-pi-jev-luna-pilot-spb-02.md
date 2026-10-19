---
type: source
title: "SPB-02 — Pilota Luna L4 e rapporto locale"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-02
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/02-run-luna-pilot.md
source_digest: sha256:ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-02 — Pilota Luna L4 e rapporto locale

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/02-run-luna-pilot.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-luna-pilot]]
- Child source: [[sources/artifact-solo-pi-jev-luna-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-01]] — `ticket:solo-pi-jev-luna-pilot/SPB-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-02.md","payload_bytes":3014,"payload_sha256":"ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934"}],"payload_bytes":3014,"payload_sha256":"ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934","schema":1,"source_digest":"sha256:ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3014,"payload_sha256":"ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934","schema":1,"source_digest":"sha256:ac28df9c58428f25faacb1321087aedc7cb51d20355b7ed8bbe3c9d020f16934","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-02"
execution_mode: AFK
blocked_by:
  - "SPB-01"
---

# SPB-02 — Pilota Luna L4 e rapporto locale

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-02`
- Role: `ticket`
- Parent: [Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md)

### Produces
- [Rapporto locale](../../research/solo-pi-jev-luna-results.md)

## Parent Spec
[Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md): scope/observation/budget/oracle/comparability.

## What to Build
Eseguire un lotto nuovo e bounded con fonte SPB-01 congelata: bare fresco contro Pi+Jev
persistente, Luna medium, tre scenari difficili, una ripetizione, prime quattro richieste.
Produrre rapporto locale solo aggregati, con identità, stop, prove e costi attribuibili.

## Acceptance Criteria
- [ ] Dependency SPB-01 valida, native gates necessari risolti con prove reali, mandato/budget residuo e fonte/SDK/skill/canary/seed/suite verificati prima di spendere.
- [ ] Sei celle seriali isolate, 24 richieste giudicabili più smoke separato; nessuna estensione a L12/ripetizioni/modelli o modifica dei lotti precedenti.
- [ ] Candidato persistente conserva stesso processo/sessione per cella; bare fresco stessa versione/modello/manifest; ruoli e calls reali contati senza doppie charges.
- [ ] Test/oracle proprietari e snapshot identificati; hidden output mai al modello; falliti/gated preservati e distinti dalle consegne, senza catene controfattuali.
- [ ] Rapporto locale riporta accettazione, failure cause, qualità/robustezza, tempi misurati e somme/costi ignoti distinti; un pilota descrittivo non prova superiorità statistica.
- [ ] Handoff canonico e controlli anti-fuga; nessuna pubblicazione/installazione o claim release da questa misura.

## Frontier
Dependency-blocked da SPB-01; permesso economico noto, nessuna prova native/auth/pricing
ancora osservata. Non autorizzare run-lot storico con altro nome di braccio per inferenza.

## Step-by-Step Implementation Plan
1. Validare dipendenza, fonte e specifica; preparare soli artefatti/copiedi lotto nuovi con grants reali, ledger sperimentale, limiti e costi cumulativi.
2. Verificare Docker/canary/suite/seed/manifest e snapshot isolati; eseguire celle esplicite serialmente e conservare processi/tentativi prima di qualsiasi retry.
3. Oracolo read-only per snapshot, conteggio separato candidati gated, aggregati e leak-check.
4. Review/QA del rapporto e riduzione/validazione canonica; gate di release e confrontabilità espliciti.

## Testing Plan
Fixture della selezione/contabilità/aggregati e osservazioni native del lotto. Docker hidden
judge invariato con digest prima/dopo; nessuna suite nascosta nel contesto di Pi/Jev/judge.
Budget EUR cumulativo originale include smoke/infra/compaction e non si resetta al nuovo ticket.

## Out of Scope
L12, rep extra, tuning del modello per migliorare risultati, altri bracci/benchmark, installazioni,
Sonnet, copy edits storici, scheduler delivery, deleghe, PR/merge/push, wiki sync e cleanup estranei.

```
