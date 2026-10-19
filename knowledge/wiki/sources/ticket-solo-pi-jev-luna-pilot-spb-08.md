---
type: source
title: "SPB-08 — Adjudicare i findings non-blocker"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-08
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/08-adjudicate-review-findings.md
source_digest: sha256:d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-08 — Adjudicare i findings non-blocker

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/08-adjudicate-review-findings.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-review-admission]]
- Child source: [[sources/artifact-solo-pi-jev-review-admission-results]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-07]] — `ticket:solo-pi-jev-luna-pilot/SPB-07`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-08.md","payload_bytes":2403,"payload_sha256":"d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66"}],"payload_bytes":2403,"payload_sha256":"d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66","schema":1,"source_digest":"sha256:d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2403,"payload_sha256":"d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66","schema":1,"source_digest":"sha256:d3d9c14a2e9d19c18a1b30203df645fb4c67fdab0c06d1340b4ad9be429bea66","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-08"} -->
```markdown
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

```
