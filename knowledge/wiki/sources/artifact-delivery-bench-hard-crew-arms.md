---
type: source
title: "Bracci Crew: un principale e i suoi worker pi-messenger"
identity_key: artifact:delivery-bench-hard-crew-arms
identity_strength: stable
source_path: docs/specs/delivery-bench-hard-crew-arms.md
source_digest: sha256:3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-06
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Bracci Crew: un principale e i suoi worker pi-messenger

Compiled from `docs/specs/delivery-bench-hard-crew-arms.md`. Identity is `artifact:delivery-bench-hard-crew-arms`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Child source: [[sources/ticket-delivery-bench-hard-dbh-33]]
- Child source: [[sources/ticket-delivery-bench-hard-dbh-34]]
- Child source: [[sources/ticket-delivery-bench-hard-dbh-35]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[7],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-delivery-bench-hard-crew-arms.md","payload_bytes":4985,"payload_sha256":"3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f"}],"payload_bytes":4985,"payload_sha256":"3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f","schema":1,"source_digest":"sha256:3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f","source_identity":"artifact:delivery-bench-hard-crew-arms","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 7: Non-goals |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 9: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4985,"payload_sha256":"3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f","schema":1,"source_digest":"sha256:3fff6c3570bb89698bd15871ce0e3dca771a03cbc80ac013615f7cde7827cd9f","source_identity":"artifact:delivery-bench-hard-crew-arms"} -->
```markdown
# Bracci Crew: un principale e i suoi worker pi-messenger

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-crew-arms`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-33](../tickets/delivery-bench-hard/done/33-patched-messenger-copy.md)
- [DBH-34](../tickets/delivery-bench-hard/done/34-crew-arms.md)
- [DBH-35](../tickets/delivery-bench-hard/done/35-crew-lot.md)

## Type
Feature del banco di prova (`benchmarks/delivery-bench/`).

## Problem
Vogliamo sapere se dividere il lavoro tra più Pi aiuta luna sulle stesse catene di
`dbh-luna3d`. La Crew di pi-messenger 0.15.2 non avvia nessun worker su Windows:
`crew/agents.ts` lancia `spawn("pi.cmd", args)` senza shell, e Node 24 lo rifiuta con
`spawn EINVAL` (riprodotto). Il pacchetto inoltre legge e scrive sotto `~/.pi/agent`, cioè
nel Pi dell'utente.

## Decisions (utente)
1. La base è `pi-tools`: con le catene da 4 fa 30/36, `pi-full` fa 29/36 costando il 50% in più.
2. Planner e reviewer della Crew sono spenti. I worker si vedono solo nel watcher.
3. La correzione del bug vive in una copia del pacchetto di proprietà del runner, solo per il
   benchmark. Il Pi dell'utente resta com'è.
4. Due bracci:
   - `crew-1`: il principale lavora e ha 1 worker (`crew.concurrency.workers = 1`);
   - `crew-2`: il principale fa solo da gestore e ha 2 worker.
5. I worker usano lo stesso modello e lo stesso thinking del lotto (`gpt-6-luna`, `medium`).

## Target behavior
1. **Copia corretta.** Il runner copia `pi-messenger` 0.15.2 dall'installazione di
   `pi-personal-config` in una cartella del lotto e applica patch ad ancore esatte. Se
   un'ancora non combacia la preparazione fallisce, senza patch parziali. Le patch:
   - i worker partono con `process.execPath` e il `cli.js` di Pi del lotto, senza shell;
   - al posto di `--no-session` i worker usano `--session-dir <arm>/worker-sessions`;
   - i worker ricevono `--no-extensions --no-skills --no-context-files --approve`, il
     profilo `pi-tools` senza `goal.ts`, e la copia di pi-messenger;
   - la config utente `~/.pi/agent/pi-messenger.json` è sostituita da un file del runner;
   - la cancellazione di `~/.pi/agent/messenger/feed.jsonl` è tolta.
2. **Isolamento.** Ogni braccio ha il suo `PI_MESSENGER_DIR` sotto la cartella del braccio.
   Niente sotto `~/.pi/agent/messenger` cambia durante un lotto (si confronta prima e dopo).
3. **Piano senza planner.** Prima di ogni richiesta il runner scrive
   `.pi/messenger/crew/plan.json` con il testo di `TASK.md` e zero task. Il principale crea i
   task con `task.create` e li fa eseguire con `work`. La config della Crew nel progetto
   fissa i worker, il modello e `review.enabled = false`.
4. **Prompt.** `crew-1` riceve il prompt di `pi-tools` più una riga che offre il worker.
   `crew-2` riceve una riga che gli chiede di non modificare file e di delegare ogni modifica.
   Il principale lavora sotto `/goal` come `pi-tools`; i worker no.
5. **Costo e tempo.** Il costo della richiesta somma le sessioni del principale e dei worker;
   il ledger li riporta anche separati.
6. **Preflight.** Una richiesta minima per braccio deve avviare almeno un worker, leggerne
   il costo e lasciare intatto `~/.pi/agent/messenger`.

## Non-goals
- Correggere pi-messenger nel Pi dell'utente o upstream.
- Usare il planner o il reviewer della Crew.
- Cambiare i bracci esistenti, i giudici o le catene già misurate.

## Failure modes
- Ancora di patch assente (pacchetto aggiornato): preparazione del lotto rifiutata.
- Un worker che non parte: la richiesta continua col solo principale; il ledger lo registra.
- Worker ancora vivi a fine richiesta: il runner li termina con il suo albero di processi.

## Verification
- Unit: patch su una copia giocattolo del file, ancore mancanti, argv dei worker.
- Integrazione: preflight reale dei due bracci.
- Lotto: catene da 4, 3 ripetizioni × 3 scenari, confrontate con `dbh-luna3d`.

## Gates
Risposte dell'utente del 2026-10-06 («va bene fallo»).
- Tentativo: un lotto completo dei due bracci Crew, catene da 4, 3 ripetizioni × 3 scenari.
- Budget per tentativo: 25 $ a prezzo di listino. `pi-tools` è costato 3,69 $ su 36 richieste;
  con i worker si stima 2-3 volte tanto per braccio.
- Tempo per tentativo: 24 ore.
- Tentativi massimi: 2.
- Approvazioni: merge con CI 8/8 e `--match-head-commit`; nessun deploy né pubblicazione.
- Versione esatta: nessuna. Le patch puntano a pi-messenger 0.15.2 solo perché è quello
  installato; un pacchetto diverso fa fallire la preparazione.
- Blocchi esistenti cercati (runner, lotti, memorie):
  - il bug `spawn EINVAL`, che questa spec risolve;
  - il giudizio di qualità e il lotto da 12 usano gli stessi CPU e Docker: un solo lotto
    alla volta. Ordine deciso: prima il giudizio di qualità in corso, poi il lotto Crew,
    poi il lotto da 12.
  - durante un lotto il checkout principale di `agent-skills` non si aggiorna.

```
