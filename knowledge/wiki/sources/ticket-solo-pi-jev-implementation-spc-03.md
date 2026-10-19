---
type: source
title: "SPC-03 — Bridge command del judge in-process"
identity_key: ticket:solo-pi-jev-implementation/SPC-03
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-implementation/03-inprocess-judge.md
source_digest: sha256:4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPC-03 — Bridge command del judge in-process

Compiled from `docs/tickets/solo-pi-jev-implementation/03-inprocess-judge.md`. Identity is `ticket:solo-pi-jev-implementation/SPC-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-implementation]]
- Blocked by: [[sources/ticket-solo-pi-jev-implementation-spc-02]] — `ticket:solo-pi-jev-implementation/SPC-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-implementation-spc-03.md","payload_bytes":2622,"payload_sha256":"4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f"}],"payload_bytes":2622,"payload_sha256":"4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f","schema":1,"source_digest":"sha256:4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f","source_identity":"ticket:solo-pi-jev-implementation/SPC-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2622,"payload_sha256":"4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f","schema":1,"source_digest":"sha256:4584e8053833483a0e82f8da51755f128e04d7859f4b5d82823fc603f8e25f9f","source_identity":"ticket:solo-pi-jev-implementation/SPC-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPC-03"
execution_mode: AFK
blocked_by:
  - "SPC-02"
---

# SPC-03 — Bridge command del judge in-process

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spc-03`
- Role: `ticket`
- Parent: [Contratto implementativo](../../specs/solo-pi-jev-implementation.md)

## Parent Spec
[Contratto implementativo](../../specs/solo-pi-jev-implementation.md): SPC-03 e fallback SPJ-02.

## What to Build
Extension opt-in nel processo Pi principale che espone una completion dedicata tramite
command; native custom receipt non model-visible, binding di domanda/stato/candidato/modello,
usage/errori. Collegamento controller SPC-02 senza altro processo o cronologia builder.

## Acceptance Criteria
- [ ] Command idle consuma input del controller con binding/permessi/budget espliciti; niente tool richiamabile dal modello, installazione o attivazione globale.
- [ ] ModelRuntime.completeSimple tool-less, prompt/contesto nuovo e modello configurato esatto; niente fuzzy fallback, loop /goal o nuovi AgentSession/processi.
- [ ] Risposta finalizzata con text/stop/usage o fallimento sanitizzato attribuibile; tool call/error/abort/length/malformed non decide e non perde i consumi restituiti.
- [ ] Receipt custom non entra nella cronologia model-facing; call ID, question/state digest e CandidateRef verificati dallo script; un'invocazione per domanda/candidato, accounting senza duplicati.
- [ ] Adapter nativo handled/entry_appended e controller fake osservati con SDK backend stub; docs/API verificate contro versione installata, RED/GREEN e handoff canonico con gate live/model/auth/quality aperti.

## Frontier
Dependency-blocked da SPC-02. Nessuna nuova scelta di design: binding tecnico/model/auth reali
restano da verificare dentro il mandato pertinente, non autorità ottenuta dalla scrittura.

## Step-by-Step Implementation Plan
1. Verificare SPC-02, leggere primarie Pi/examples/declarations e ammettere delta opt-in.
2. Backend stub RED, bridge GREEN e tests command/context/stop/accounting; mai chiamare provider per far passare test.
3. Review dei nested fields/side effects e conformance owned adapter, freeze/QA/audit; dichiarare gap reali.

## Testing Plan
Node test con complete backend e ExtensionAPI sostitutivi; records nativi e peer fake Python
per interop. Nessun SDK/model/auth smoke live, benchmark, installazione o reload. Required
code profile e hosted CI esatta prima di futuro PR.

## Out of Scope
MCP/subagent/reviewer separato, loop /goal, credenziali alternative, live/provider spend,
benchmark/copie storiche, scheduler, PR/merge, install/pin/reload/GC e wiki.

```
