---
ticket_schema: 1
ticket_id: "IB-01"
execution_mode: AFK
blocked_by: []
---

# IB-01 — Benchmark corto sui blocchi inventati

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:01`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../specs/invented-blocks-bench.md), Decision.

## What to Build
In `benchmarks/block-bench/`: tre scenari (limite scelto da sé; ordine di un altro agente con
`/loop`; lavoro tecnico sotto `/goal`), un runner che lancia Pi con il profilo dell'utente senza
Telegram, l'analisi dei turni (giudice `gpt-6-sol`, citazione verificata a testo), il controllo
deterministico di ogni scenario e un report. Poi la misura di oggi.

## Acceptance Criteria
- [ ] Tre scenari locali; ognuno ha un controllo deterministico del lavoro.
- [ ] Una prova passa solo con lavoro fatto, zero blocchi non citabili e, con `/loop`, al massimo
      2 giri di fila senza novità dopo il lavoro.
- [ ] Test offline dell'analisi (turni, giri, citazioni) senza modello.
- [ ] Misura di oggi: 3 × 3 prove con `gpt-6-luna` medium, report con esiti e costi.

## Frontier
Pronto.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Scenari e runner. 2. Analisi e test offline. 3. PR e merge. 4. Misura.

## Testing Plan
- Test offline in `benchmarks/block-bench/`; la misura vera è la verifica.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.
