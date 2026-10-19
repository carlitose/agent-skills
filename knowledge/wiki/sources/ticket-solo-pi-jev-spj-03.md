---
type: source
title: "SPJ-03 — Confermare il contratto della review nel contesto condiviso"
identity_key: ticket:solo-pi-jev/SPJ-03
identity_strength: stable
source_path: docs/tickets/solo-pi-jev/03-decide-shared-context-review.md
source_digest: sha256:f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPJ-03 — Confermare il contratto della review nel contesto condiviso

Compiled from `docs/tickets/solo-pi-jev/03-decide-shared-context-review.md`. Identity is `ticket:solo-pi-jev/SPJ-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-wayfinder]]
- Child source: [[sources/artifact-solo-pi-jev-review-decision]]
- Blocked by: [[sources/ticket-solo-pi-jev-spj-02]] — `ticket:solo-pi-jev/SPJ-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[7],"status":"present"},"exclusions":{"headings":[11],"status":"present"},"frontier":{"headings":[8],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[10],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-spj-03.md","payload_bytes":3672,"payload_sha256":"f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd"}],"payload_bytes":3672,"payload_sha256":"f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd","schema":1,"source_digest":"sha256:f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd","source_identity":"ticket:solo-pi-jev/SPJ-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 7: Acceptance Criteria |
| testing | 10: Testing Plan |
| frontier | 8: Frontier |
| exclusions | 11: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3672,"payload_sha256":"f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd","schema":1,"source_digest":"sha256:f2798af1d26a3e53936ef45e866a45a3bfffedf2629d584888ac70e094e896dd","source_identity":"ticket:solo-pi-jev/SPJ-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPJ-03"
execution_mode: HITL
blocked_by:
  - "SPJ-02"
---

# SPJ-03 — Confermare il contratto della review nel contesto condiviso

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-03`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

### Children
- [Rilettura e correzione confermate](../../specs/solo-pi-jev-review-decision.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Decisions So Far, Current Evidence, Not Yet Specified 3.

## Question / Outcome
Che cosa significa review diretta se builder e reviewer sono turni dello stesso Pi? Confermare ruolo, scritture, lettura dei findings e claims di qualità senza chiamare indipendente una review condivisa.

## Evidence
Partire da `risk.py` (`directed_review`), `driver.py` (`risk_phase`, `_record_candidate`) e `findings.py`. Oggi il revisore ha un contesto fresco e una scratch distinta, con controllo delle scritture e del candidato. Leggere l'esito e la prova di conferma di SPJ-02; l'emissione del ticket non ne completa la dipendenza.

## Produces
[Decisione confermata tramite `to-spec`](../../specs/solo-pi-jev-review-decision.md), Artifact ID `artifact:solo-pi-jev-review-decision`, Role `spec`, Parent a questo ticket e Children reciproco sopra. Esempi e conferme reali chiariscono review condivisa, findings prima dei fix, parti rischiose/incerte, copertura completa e limite Autopilot di 3 fallimenti finali. Spec locale, non implementazione o delivery.

## Acceptance Criteria
- [x] Dipendenza SPJ-02 verificata su decisione e conferma attribuibili, non su una checkbox o un piano.
- [x] Invocata `grilling`, una domanda per volta, e ottenuta conferma reale: mantenere, modificare o omettere il turno di review, con garanzie perse dichiarate.
- [x] Distinti cambio di ruolo, separazione delle scritture e indipendenza del contesto; il solo prompt di reviewer, una scratch o Jev non rendono indipendente il giudizio dello stesso Pi.
- [x] Specificati quando fare review, input per funzione, formato/lettura dei findings, owner del giudizio, blocker/retry/stop e scritture permesse. Eventuali modifiche al prodotto richiedono nuovo candidato e rivalutazione delle evidenze interessate.
- [x] Spec tramite `to-spec` con prova della conferma e conseguenze rispetto al contratto storico; grafo reciproco e mappa aggiornati senza implementare o risolvere SPJ-04 per inferenza.

## Frontier
Dipendenza SPJ-02 verificata dal handoff documentale locale sulla sua identità; decisione SPJ-03 confermata dopo spiegazione semplice ed esempi. Qualità/handoff in corso, non delivery. Il risultato non è indipendente. SPJ-04 resta aperto e SPJ-05 non è eseguito; il flusso generale è stato riconfermato realmente dall'utente.

## Step-by-Step Implementation Plan
1. Verificare SPJ-02, leggere i confini attuali e la skill `grilling`.
2. Intervistare su ruolo, indipendenza e mutazioni; confrontare claims ammessi e garanzie perse. Completion criterion: contratto e compromessi confermati realmente, o edge ancora aperta.
3. Salvare la decisione attraverso `to-spec`, collegare i grafi e rimuovere solo l'unknown risolta dalla mappa.

## Testing Plan
Walkthrough di findings puliti, blocker, formato non leggibile e review che cambia l'albero; verificare quali evidenze decadono e che nessuno stato finga indipendenza. Controlli documentali e di grafo, senza provider o benchmark.

## Out of Scope
Policy Jev nuova, worktree/test/integrazione definitivi, implementazione, nuovo revisore Pi, chiamate live, lotti storici, CLI/scheduler Autopilot, delivery/wiki impliciti. Consegna skills-only inline; nessuna delega.

```
