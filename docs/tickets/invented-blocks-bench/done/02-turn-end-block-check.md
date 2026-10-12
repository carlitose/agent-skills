---
ticket_schema: 1
ticket_id: "IB-02"
execution_mode: AFK
blocked_by:
  - "IB-01"
---

# IB-02 — Controllo a fine turno sui blocchi

## Artifact Graph
- Artifact ID: `ticket:invented-blocks-bench:02`
- Role: `ticket`
- Parent: [invented-blocks-bench.md](../../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../../specs/invented-blocks-bench.md), Decision.

## What to Build
Un'estensione che, a fine turno, chiede a un modello se il turno finisce su un blocco e se il
blocco si può citare da parole dell'utente. Se non si può, rimanda l'agente al lavoro con un
messaggio breve; un blocco citato o un errore reale restano validi. Al massimo due rimandi di fila,
poi la decisione passa all'utente.

## Acceptance Criteria
- [x] Un blocco non citabile riporta l'agente al lavoro; uno citato no.
- [x] Niente rimandi infiniti: al massimo due di fila.
- [x] Test mirati senza modello; installata nel profilo dell'utente.

## Evidence
- pi-code `extensions/block-check.ts` (ramo `fix/todo-reminder`): PR #4, #5, #6, #7, #8, #9, #10;
  ultimo `9e7d01e`, pin in pi-personal-config (`2492350`), `update:personal` verificato.
- Il controllo chiede fatti semplici (`work_done`, `still_failing`, `asks_how`, `waits`,
  `user_quote`), non «si ferma?»: con quella domanda luna rispondeva «no» su stop evidenti.
- Correzioni trovate misurando: i giri di `/loop` sono le parole dell'utente e il lavoro si giudica
  sull'ultimo messaggio; chiedere a qualcuno, se richiesto, è lavoro finito; un controllo fallito
  si ritenta una volta; il testo delle skill iniettato nel messaggio utente non è dell'utente;
  la richiesta intera non vale come citazione di un blocco; un fallimento riportato non è lavoro
  finito.
- Serie di misure (`gpt-6-luna` medium, 3 × 3, giudice `gpt-6-sol`): `before` 0/9 →
  `after-ib02` 2/9 → `after-split` 4/9 → `after-ib03` 6/9 → `after-final` 7/9 → `after-final4`
  **9/9** (goal-prerequisite 3/3, main-stop 3/3 con 2 giri di loop e loop fermo, own-limit 3/3).
  Costo di listino dell'ultima: agente 0,10 $, giudice 0,18 $.

## Frontier
Fatto.

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Estensione e test. 2. PR, merge, pin. 3. Rimisura con IB-01.

## Testing Plan
- Test mirati dell'estensione; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.
