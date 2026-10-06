---
ticket_schema: 1
ticket_id: "DBH-34"
execution_mode: AFK
blocked_by:
  - "DBH-33"
---

# DBH-34 — Bracci crew-1 e crew-2 nel runner

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:34`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md)

## Parent Spec
[delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md), Target behavior 2-6.

## What to Build
Due bracci nuovi su base `pi-tools`, con `/goal` per il principale:
- `crew-1`: il principale lavora e ha 1 worker;
- `crew-2`: il principale non modifica file e ha 2 worker.

Per ogni braccio il runner:
- prepara la copia corretta di pi-messenger (DBH-33) e la carica con `-e`;
- dà al principale `PI_MESSENGER_DIR` e `DBENCH_MESSENGER_HOME` nella cartella del braccio, e
  `DBENCH_WORKER_ARGV` con il `cli.js` di Pi, `--session-dir <braccio>/worker-sessions`,
  `--no-extensions --no-skills --no-context-files --approve` e il profilo `pi-tools` senza
  `goal.ts`;
- prima di ogni richiesta scrive nel progetto `.pi/messenger/crew/plan.json` (il testo di
  `TASK.md`, zero task) e `config.json` (modello e thinking del lotto per i worker, numero di
  worker, review spenta);
- somma nel costo della richiesta le sessioni del principale e dei worker, e le riporta anche
  separate nel ledger.

Il preflight avvia una richiesta minima per braccio e controlla che almeno un worker sia partito,
che il suo costo sia letto e che `~/.pi/agent/messenger` sia rimasto identico.

## Acceptance Criteria
- [ ] `arm_argv` e l'ambiente dei due bracci contengono la copia, le variabili e i flag
      indicati; gli altri bracci restano identici (test).
- [ ] Piano e config della Crew sono scritti prima di ogni richiesta (test).
- [ ] Il costo somma principale e worker (test con sessioni finte).
- [ ] Preflight reale dei due bracci riuscito.

## Frontier
Bloccato da DBH-33.

## Gates
Come la spec: il preflight reale spende pochi centesimi e rientra nei 25 $ del primo tentativo;
merge con CI 8/8 e `--match-head-commit`; il preflight non gira mentre un lotto o il giudizio di
qualità usano la macchina.

## Step-by-Step Implementation Plan
1. `ARMS`, `PI_ARMS`, `ARM_PROFILES`, `GOAL_ARMS`, `ARM_SKILLS` e i suffissi dei prompt.
2. Preparazione della copia in `init-lot`, legata nel lotto con il suo manifesto.
3. Ambiente, piano e config per richiesta.
4. Costo dei worker e ledger.
5. Preflight.

## Testing Plan
- `python -B -m unittest test_runner` (test nuovi).
- Preflight reale.

## Out of Scope
- Il lotto (DBH-35).
