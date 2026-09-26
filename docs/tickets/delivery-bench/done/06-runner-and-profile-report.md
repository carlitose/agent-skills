---
ticket_schema: 1
ticket_id: "DB-06"
execution_mode: AFK
blocked_by:
  - "DB-01"
---

# DB-06 — Runner dei bracci e report a profilo

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:06`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Un comando unico per braccio × scenario × lunghezza che: consegna la richiesta N al braccio nel suo modo naturale, attende la consegna, esegue la suite nascosta della richiesta N, passa alla N+1; registra token, USD stimati (Jev a parte), tempo, e produce il profilo a cinque assi. Report deterministico e confronto appaiato con la regola di TBA-03 (`arm_comparison.py`). Ripetizioni e ledger come nei lotti Terminal-Bench (autorità, ledger fuori da Git, guasti d'infrastruttura ripetuti).

## Acceptance Criteria
- [x] Il comando esegue una catena completa per un braccio con processi finti e scrive il profilo per richiesta; test offline RED→GREEN.
- [x] Ogni braccio gira nel suo modo naturale (una sessione per Pi nudo e skills-only; driver per ticket; Autopilot con runner) e riceve la richiesta N+1 solo dopo la consegna della N.
- [x] Il report riporta i cinque assi senza numero unico, la distanza delle trappole violate e i guasti d'infrastruttura classificati e ripetuti.
- [x] Un tetto di tempo per catena termina il braccio e conserva il profilo parziale.

## Frontier
**Completato** (2026-09-26, skills-only): [`runner.py`](../../../../benchmarks/delivery-bench/runner.py) (lotto con autorità umana vincolata per hash e fuori da Git, celle estese e mai rigiocate, consegna di `TASK.md` senza canary con commit `bench` e push fast-forward, comando naturale per braccio, albero di processi posseduto e terminato, tetto per richiesta e per catena, istantanea e ripristino per i guasti d'infrastruttura con al massimo 2 ripetizioni, giudice ripetuto a parte, uso e USD dalle sessioni del braccio o dalle foglie del driver, Jev a parte, audit dopo ogni richiesta, ledger append-only, copie di configurazione del driver con hash) e [`profile_report.py`](../../../../benchmarks/delivery-bench/profile_report.py) (cinque assi affiancati, distanze e tipi delle trappole violate, confronto appaiato con `bare` secondo la regola di TBA-03, guasti per classe; nessun nome di controllo nascosto). Test offline RED→GREEN: 13 test del runner con Pi, driver e giudice finti su repository Git veri (RED sullo scheletro: 12/12 in errore, `C:/dbench/evidence/db06-red.txt`) e 6 test del report. Smoke d'integrazione col giudice Docker reale e un Pi finto che non lavora (lotto `db06-smoke`, catene da 2 sui tre scenari): 6/6 richieste giudicate con albero identico, controlli passati contenuti nelle attese dello stub, richiesta 1 Python byte-identica al `TASK.md` di bench38, `node_modules` di cella per TypeScript, audit pulito. Il contratto registra layout delle celle, comando di test TypeScript, classi di guasto e posizione dei lotti.

## Step-by-Step Implementation Plan
1. Test RED con bracci finti.
2. Runner, ledger, classificatore riusati da Terminal-Bench.
3. Report e confronto appaiato.

## Testing Plan
Offline con bracci finti; una catena da 1 reale in DB-07.

## Out of Scope
- Scrivere scenari.
- Migliorare i bracci.
