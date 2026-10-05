---
ticket_schema: 1
ticket_id: "SPB-08"
execution_mode: AFK
blocked_by:
  - "SPB-07"
---

# SPB-08 — Adjudicare i findings non-blocker

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-08`
- Role: `ticket`
- Parent: [Review admission](../../specs/solo-pi-jev-review-admission.md)

### Produces
- [Risultato e limiti](../../research/solo-pi-jev-review-admission-results.md)

## Parent Spec
[Review admission](../../specs/solo-pi-jev-review-admission.md).

## What to Build
Riparare il veto automatico di should-fix/nit nel braccio, riusando la decisione coverage
esistente e il contratto SPJ-03. Non correggere YCounter, cambiare SPB-07 o creare un trial.

## Acceptance Criteria
- [ ] Review parsata non-blocker e test verdi raggiungono la cascata, conservando findings/prosa/candidate/diff/ricevute; solo YES può completare.
- [ ] NO resta failure cumulativa e non chiama judge; uncertain resta gate umano senza contare failure, anche con should-fix.
- [ ] Blocker espliciti, test falliti e review unparsed non possono essere approvati; nit non è veto automatico.
- [ ] Coverage/review distinguono requisiti da suggerimenti senza affermare che il caso YCounter è falso o che il nuovo braccio è live-validato.
- [ ] Storico, prep/source/SPB-07 e budget 10/47/7/367 invariati; test locali causali e handoff attuale, nessun modello/oracle/replay/delivery/installazione.

## Frontier
Ready: SPB-07 implementation-complete/release-blocked con handoff validato. Interfaccia e
Seam già accettate; authority umana Fixalo del 2026-10-02 15:50 Europe/Madrid per fix locale.

## Step-by-Step Implementation Plan
1. Current canonical admission, RED sul veto di un finding non-blocker.
2. Minima correzione del controller, GREEN; ulteriori contrastanti NO/uncertain/blocker/nit.
3. Istruzioni grounded, targeted regression, freeze/review/QA/audit inline shared-context.

## Testing Plan
Real Git/public Python receipts in synthetic repos, fake peer/Jev/judge at existing ports.
Preserve RED and all attempts, select changed controller/repair plus prompt adapter checks.
No unchanged full profile repeated; release profile and exact-head CI remain unexecuted.

## Out of Scope
YCounter implementation, hidden feedback, historical result revisions, other native launches,
new ports/security/thresholds/budgets, independent reviewer, runner/scheduler, commit/push/PR,
merge/install/reload/wiki sync.
