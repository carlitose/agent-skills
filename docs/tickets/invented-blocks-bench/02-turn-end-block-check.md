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
- Parent: [invented-blocks-bench.md](../../specs/invented-blocks-bench.md)

## Parent Spec
[invented-blocks-bench.md](../../specs/invented-blocks-bench.md), Decision.

## What to Build
Un'estensione che, a fine turno, chiede a un modello se il turno finisce su un blocco e se il
blocco si può citare da parole dell'utente. Se non si può, rimanda l'agente al lavoro con un
messaggio breve; un blocco citato o un errore reale restano validi. Al massimo due rimandi di fila,
poi la decisione passa all'utente.

## Acceptance Criteria
- [ ] Un blocco non citabile riporta l'agente al lavoro; uno citato no.
- [ ] Niente rimandi infiniti: al massimo due di fila.
- [ ] Test mirati senza modello; installata nel profilo dell'utente.

## Frontier
Dopo IB-01 (serve la misura di oggi).

## Gates
Come la spec: misure autorizzate dall'utente («ok»); merge con CI verde, pin,
`update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. Estensione e test. 2. PR, merge, pin. 3. Rimisura con IB-01.

## Testing Plan
- Test mirati dell'estensione; rimisura con `block-bench`.

## Out of Scope
- Winbox, betsharemarket e le sessioni vere.
