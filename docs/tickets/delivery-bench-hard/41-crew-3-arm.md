---
ticket_schema: 1
ticket_id: "DBH-41"
execution_mode: AFK
blocked_by:
  - "DBH-40"
---

# DBH-41 — Braccio crew-3 nel runner

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:41`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md)

## Parent Spec
[delivery-bench-hard-crew-isolated.md](../../specs/delivery-bench-hard-crew-isolated.md), Target behavior 2–3, Failure modes e Verification.

## What to Build
Il braccio `crew-3` in `benchmarks/delivery-bench/runner.py`: profilo di `pi-full` più la copia
patchata di `pi-messenger`, 2 worker, coordinatore che lavora anche lui e usa `crew-delivery`.
I worker caricano le skill e l'estensione obbligatoria, senza `/goal`. I worktree dei worker
stanno nella cartella del braccio, fuori da `project/`. Ogni richiesta registra compiti creati,
completati e bloccati, worktree creati e commit su `main` fatti fuori dall'integrazione.

## Acceptance Criteria
- [ ] `crew-3` carica il profilo di `pi-full` e la copia di `pi-messenger`; i worker vedono le
      skill e l'estensione obbligatoria, non `/goal`.
- [ ] I worktree dei worker non stanno sotto `project/` e l'audit della cella resta valido.
- [ ] Ogni richiesta registra compiti per stato e worktree; il ledger e il report li riportano.
- [ ] `crew-1`, `crew-2` e gli altri bracci restano invariati; suite del runner e CI verdi.
- [ ] Preflight senza lotto di `crew-3` ok: un worker fa un compito nel suo worktree e il
      coordinatore lo integra.

## Frontier
Pronto (DBH-40 fatto).

## Gates
Come la spec: una PR con CI verde e merge con `--match-head-commit`; nessun tetto di spesa;
24 ore per tentativo, al massimo 2 tentativi. Durante un lotto si lavora in un worktree, senza
aggiornare il checkout principale.

## Step-by-Step Implementation Plan
1. Test rossi per profilo, argv dei worker, cartella dei worktree e registrazione dei compiti.
2. Braccio, prompt del coordinatore, conteggio dei compiti, preflight `crew-3`.
3. Suite del runner e preflight reale.

## Testing Plan
- `test_runner.py` (classe Crew) e la suite del banco; preflight reale.

## Out of Scope
- Il lotto (DBH-42).
