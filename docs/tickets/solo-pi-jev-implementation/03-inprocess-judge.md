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
