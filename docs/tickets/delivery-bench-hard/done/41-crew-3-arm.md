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
- Parent: [delivery-bench-hard-crew-isolated.md](../../../specs/delivery-bench-hard-crew-isolated.md)

## Parent Spec
[delivery-bench-hard-crew-isolated.md](../../../specs/delivery-bench-hard-crew-isolated.md), Target behavior 2–3, Failure modes e Verification.

## What to Build
Il braccio `crew-3` in `benchmarks/delivery-bench/runner.py`: profilo di `pi-full` più la copia
patchata di `pi-messenger`; il coordinatore fa il PM di `crew-delivery`; i worker fanno da
developer (2) o da reviewer (1) secondo il compito, con le skill e l'estensione obbligatoria,
senza `/goal`. Il runner installa l'hook `pre-commit` nel progetto prima della prima richiesta.
I worktree stanno nella cartella del braccio, fuori da `project/`. Ogni richiesta registra
ticket creati, uniti e bloccati, review con verdetto, giri di QA, worktree creati e commit sul
principale fuori dalla coda di merge (violazioni).

## Acceptance Criteria
- [x] `crew-3` carica il profilo di `pi-full` e la copia di `pi-messenger`; i worker vedono le
      skill e l'estensione obbligatoria, non `/goal`; il prompt del PM chiede `crew-delivery`.
- [x] L'hook `pre-commit` del progetto rifiuta i commit su `main`; il merge fast-forward passa.
- [x] I worktree dei worker non stanno sotto `project/` e l'audit della cella resta valido.
- [x] Ogni richiesta registra ticket per stato, review, giri di QA, worktree e violazioni; il
      ledger e il report li riportano.
- [x] `crew-1`, `crew-2` e gli altri bracci restano invariati; suite del runner e CI verdi.
- [x] Preflight senza lotto di `crew-3` ok: un developer fa un ticket nel suo worktree, il
      reviewer lo approva e la coda di merge lo unisce.

## Evidence
- Codice e test offline dei criteri 1-5: PR #454 (`6d9c891`), suite del runner e CI 8/8.
- Preflight reale 1 (2026-10-09, luna medium, 0,022 $): skill `crew-delivery` visibili, routing ok,
  `pi-messenger` 0.15.2 copiato, mesh dell'utente invariata; DEV fatto nel worktree e merge
  fast-forward, ma nessuna REVIEW: il compito della prova non la chiedeva.
- Correzione (questa PR): la prova chiede anche `REVIEW p1` con riassunto `APPROVED`, e fallisce se
  manca (test `test_crew_3_preflight_runs_one_ticket_through_the_queue`, caso `no-review`).
- Preflight reale 2 (`dbh-crew3-preflight-2.json` nel repo privato, 0,018 $): `ok`, nessun
  problema; task DEV 1 e REVIEW 1 fatti, review `approved` 1, `merges_ff` 1, `main_violations` 0,
  `dirty_main` 0, `worktrees_left` 0, `refused_commits` 0; nessun container lasciato.

## Frontier
Fatto. Prossimo: DBH-42, lotto `dbh-crew3`.

## Gates
Come la spec: una PR con CI verde e merge con `--match-head-commit`; nessun tetto di spesa;
24 ore per tentativo, al massimo 2 tentativi. Durante un lotto si lavora in un worktree, senza
aggiornare il checkout principale.

## Step-by-Step Implementation Plan
1. Test rossi per profilo, argv dei worker, hook, cartella dei worktree e registrazione.
2. Braccio, prompt del PM, hook, conteggi, preflight `crew-3`.
3. Suite del runner e preflight reale.

## Testing Plan
- `test_runner.py` (classe Crew) e la suite del banco; preflight reale.

## Out of Scope
- Il lotto (DBH-42).
