---
ticket_schema: 1
ticket_id: "TBA-05"
execution_mode: HITL
blocked_by: []
---

# TBA-05 — Benchmark privato stile Terminal-Bench (condizionale)

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:05`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Creare un piccolo set privato di task Harbor nel nostro dominio, con istruzione, immagine, test nascosti e verifier separato, da usare come held-out non contaminato o come fallback se l'harness originale diventa inutilizzabile. Sezione spec: Decision 5.

## Acceptance Criteria
- [ ] Esiste un via libera esplicito dell'utente con numero di task e domini.
- [ ] Ogni task è un pacchetto Harbor valido con verifier separato e soluzione di riferimento che passa; `harbor run` con l'adapter lo carica.
- [ ] I task non riusano testo o soluzioni di Terminal-Bench.

## Frontier
Richiede una decisione umana: attivare o no, con che dimensione. Oggi l'harness originale funziona, quindi resta condizionato.

## Step-by-Step Implementation Plan
1. Raccogliere dall'utente scope e domini.
2. Scrivere i task con `harbor init` e validarli con la soluzione di riferimento.
3. Integrare nel protocollo di TBA-04 come held-out aggiuntivo.

## Testing Plan
Validazione dei task con la soluzione di riferimento e con uno stub che deve fallire.

## Out of Scope
- Sostituire Terminal-Bench nel report di selezione.
