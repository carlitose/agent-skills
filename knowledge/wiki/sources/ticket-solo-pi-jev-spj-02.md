---
type: source
title: "SPJ-02 — Confermare il fallback quando Jev non decide"
identity_key: ticket:solo-pi-jev/SPJ-02
identity_strength: stable
source_path: docs/tickets/solo-pi-jev/02-decide-uncertainty-fallback.md
source_digest: sha256:cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPJ-02 — Confermare il fallback quando Jev non decide

Compiled from `docs/tickets/solo-pi-jev/02-decide-uncertainty-fallback.md`. Identity is `ticket:solo-pi-jev/SPJ-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-wayfinder]]
- Child source: [[sources/artifact-solo-pi-jev-uncertainty-decision]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[7],"status":"present"},"exclusions":{"headings":[11],"status":"present"},"frontier":{"headings":[8],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[10],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-spj-02.md","payload_bytes":4183,"payload_sha256":"cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952"}],"payload_bytes":4183,"payload_sha256":"cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952","schema":1,"source_digest":"sha256:cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952","source_identity":"ticket:solo-pi-jev/SPJ-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 7: Acceptance Criteria |
| testing | 10: Testing Plan |
| frontier | 8: Frontier |
| exclusions | 11: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4183,"payload_sha256":"cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952","schema":1,"source_digest":"sha256:cb30733f3a744e1be3247598bae256e0b902de7cd35669ffe5cf456156dd4952","source_identity":"ticket:solo-pi-jev/SPJ-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPJ-02"
execution_mode: HITL
blocked_by: []
---

# SPJ-02 — Confermare il fallback quando Jev non decide

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-02`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

### Children
- [Decisione sul fallback](../../specs/solo-pi-jev-uncertainty-decision.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Decisions So Far, Not Yet Specified 2, Frontier / Blocking Edges.

## Question / Outcome
Chi decide quando Jev è incerto o indisponibile senza introdurre un altro processo Pi? Il fallback semantico e quello del rischio per funzione sono distinti. La decisione confermata usa un judge in-process, non il subagent inizialmente proposto; non cambia soglie o risultati misurati.

## Evidence
`cascade.py` (`Cascade.batch`, `judge`) oggi può aprire un judge fresco; `risk.py` (`assess`, `directed_review`) instrada incertezza/hunk fuori bound verso review. Il contratto storico `docs/specs/ticket-driver.md` prescrive Jev → LLM fresco → umano e vieta l'autoapprovazione: il target nuovo richiede una decisione esplicita sulle eventuali variazioni.

## Produces
[Decisione confermata tramite `to-spec`](../../specs/solo-pi-jev-uncertainty-decision.md), Artifact ID `artifact:solo-pi-jev-uncertainty-decision`, Role `spec`, Parent a questo ticket e Children reciproco sopra. Conserva la decision table e le conferme reali del 2026-10-01; aggiorna la destinazione e la edge della mappa. Artefatto locale, non pubblicazione o implementazione.

## Acceptance Criteria
- [x] Invocata la skill canonica `grilling`: una domanda per volta, attendendo la risposta; ottenuta conferma reale della policy e conservato il riferimento alla risposta, senza inventare evidenza o trattare il silenzio come consenso.
- [x] Confrontate almeno gate umano, analisi nel Pi condiviso con successivo giudizio Jev e mantenimento di un giudice fresco solo come variazione esplicita della destinazione; nessuna opzione è preapprovata.
- [x] Decision table distingue domande semantiche da rischio; copre confident positivo/negativo, sotto soglia, servizio indisponibile, invio vietato dal repository, input fuori bound e risposta malformata.
- [x] Esplicitati retry/stop/handoff umano, consumo cumulativo e chi può approvare; un risultato incerto non equivale a PASS, rischio basso o nuova autorità di spesa.
- [x] Spec di decisione e grafo reciproco salvati attraverso `to-spec`; mappa aggiornata solo per risposte confermate. Una scelta che cambia materialmente Destination/scope ritorna al destination gate Wayfinder prima di aggiornare gli artefatti.

## Frontier
Decisione HITL confermata realmente e spec locale scritta; qualità e handoff in corso. Nessun blocker canonico. SPJ-01 e i sorgenti installati `/goal` informano il meccanismo scelto, non ne provano il funzionamento live. SPJ-03/04 restano aperti; nessuna dipendenza chiusa dalla sola emissione.

## Step-by-Step Implementation Plan
1. Leggere mappa, contratto storico e la skill `grilling`; presentare il trade-off tra zero Pi aggiuntivi, indipendenza e autonomia.
2. Intervistare una domanda alla volta e fermarsi alla conferma della policy; le soglie numeriche nuove non si inventano. Completion criterion: tutte le condizioni della decision table hanno un owner e un esito confermati, o il ticket resta aperto.
3. Registrare tramite `to-spec` opzioni, decisione, conseguenze e prova della conferma; aggiornare la edge senza implementare il fallback.

## Testing Plan
Ripassare la decision table con casi sintetici e controllare che nessun ramo approvi l'incertezza o nasconda un nuovo Pi. Verificare link/grafo e attribuzione della conferma. Nessun test del provider o benchmark.

## Out of Scope
Contratto dettagliato della review o ownership dello script, implementazione, chiamate live del nuovo contratto, nuove misure/spese, modifica dei lotti/copie storici, calibrazione, CLI/scheduler Autopilot, delivery/wiki impliciti. Consegna skills-only inline. I tentativi subagent richiesti separatamente non hanno prodotto un giudizio e non sono evidenza di review; nessuna delega ulteriore.

```
