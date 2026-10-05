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
