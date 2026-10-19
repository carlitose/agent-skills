---
type: source
title: "SPJ-04 — Confermare gli owner di worktree, prove e integrazione"
identity_key: ticket:solo-pi-jev/SPJ-04
identity_strength: stable
source_path: docs/tickets/solo-pi-jev/04-decide-script-ownership.md
source_digest: sha256:c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPJ-04 — Confermare gli owner di worktree, prove e integrazione

Compiled from `docs/tickets/solo-pi-jev/04-decide-script-ownership.md`. Identity is `ticket:solo-pi-jev/SPJ-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-wayfinder]]
- Child source: [[sources/artifact-solo-pi-jev-script-ownership-decision]]
- Blocked by: [[sources/ticket-solo-pi-jev-spj-01]] — `ticket:solo-pi-jev/SPJ-01`
- Blocked by: [[sources/ticket-solo-pi-jev-spj-03]] — `ticket:solo-pi-jev/SPJ-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[7],"status":"present"},"exclusions":{"headings":[11],"status":"present"},"frontier":{"headings":[8],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[10],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-spj-04.md","payload_bytes":3872,"payload_sha256":"c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33"}],"payload_bytes":3872,"payload_sha256":"c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33","schema":1,"source_digest":"sha256:c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33","source_identity":"ticket:solo-pi-jev/SPJ-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 7: Acceptance Criteria |
| testing | 10: Testing Plan |
| frontier | 8: Frontier |
| exclusions | 11: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3872,"payload_sha256":"c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33","schema":1,"source_digest":"sha256:c480acd8c8c73bf78954d7b63bc637398653ce3f00acab9edc48f591aeb45a33","source_identity":"ticket:solo-pi-jev/SPJ-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPJ-04"
execution_mode: HITL
blocked_by:
  - "SPJ-01"
  - "SPJ-03"
---

# SPJ-04 — Confermare gli owner di worktree, prove e integrazione

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-04`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

### Children
- [Gestione confermata](../../specs/solo-pi-jev-script-ownership-decision.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Destination, Not Yet Specified 4, Frontier / Blocking Edges.

## Question / Outcome
Quali attività e garanzie restano nello script che guida il Pi condiviso, e quali passano a Pi, Jev o umano? Una sessione unica non decide da sola isolamento, prove e integrazione.

## Evidence
Leggere `driver.py` (`preflight`, `create_worktree`, `_record_candidate`, `integrate_candidate`, `execute`), i contratti puri CandidateRef/Ticket Envelope e gli esiti attribuibili di SPJ-01 e SPJ-03. Il contratto storico distingue integrazione locale da PR/merge remoto; `c4` non integra automaticamente e può ancora invocare un reviewer separato.

## Produces
[Decisione confermata tramite `to-spec`](../../specs/solo-pi-jev-script-ownership-decision.md), con matrice script/Pi/Jev/AI/umano, esempi e selezioni reali. Copia separata e prove osservate, indipendenti dalla versione valida dopo un fallimento, ripresa automatica sicura contata, drift riconciliato senza riuso cieco. Spec locale, non implementazione, live o delivery.

## Acceptance Criteria
- [x] Esiti SPJ-01 e SPJ-03 verificati con fonti e conferme reali; nessuna dipendenza completata per sola emissione.
- [x] Invocata `grilling`, una domanda per volta, e ottenuta conferma reale della matrice script/Pi/Jev/umano per lifecycle, worktree, test, freeze, artefatti, gate, integrazione locale e stop.
- [x] Per ogni garanzia attuale: preservata, modificata o rimossa, con osservatore, prova e limite dichiarati. CandidateRef usa alberi Git e digest canonico; dichiarazioni del modello non diventano ricevute osservate.
- [x] Confermati comportamento su drift della base/candidato, test che scrivono, richieste fallite, crash/ripresa e handoff umano; costo/consumo cumulativo e credenziali Jev non si azzerano né si ereditano nel Pi.
- [x] Distinte fine del turno, candidato verificato, `completed-local`, integrazione locale e delivery remoto; stop/gate non sono successo. Spec tramite `to-spec`, prova di conferma, grafo e mappa aggiornati senza implementazione.

## Frontier
Dipendenze SPJ-01/03 verificate tramite handoff locali sulle proprie identità. Matrice e failure paths confermati dopo domande singole con esempi, fino a «Confermo la gestione spiegata». Qualità/handoff documentali in corso; nessun avvio live o applicazione al progetto originale. Prossimo passo SPJ-05 offline, non codice di produzione.

## Step-by-Step Implementation Plan
1. Verificare le dipendenze e confrontare ownership attuale con il trasporto raccomandato e la review confermata.
2. Usare `grilling` per confermare la matrice e la gestione dei failure paths; dichiarare garanzie e autonomia eventualmente perse. Completion criterion: ogni attività ha owner e prova confermati, o il ticket resta aperto.
3. Salvare attraverso `to-spec` la decisione, le alternative e le conferme; collegare il grafo e aggiornare la frontier.

## Testing Plan
Walkthrough documentale di catena buona, test rossi, base avanzata, candidato cambiato, crash e tentativo di integrare senza autorità. Verificare che le prove appartengano all'albero corretto e che il consumo sia cumulativo. Controlli di link/grafo, nessuna esecuzione live.

## Out of Scope
Scheduler, provider delivery, nuove soglie o policy Jev, codice di produzione, credenziali/spesa, lotti/copie misurati, CLI Autopilot, installazione/reload e wiki impliciti. Consegna skills-only inline; nessuna delega.

```
