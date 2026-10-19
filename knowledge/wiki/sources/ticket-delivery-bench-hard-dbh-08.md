---
type: source
title: "DBH-08 — Pilota: catena da 1"
identity_key: ticket:delivery-bench-hard/DBH-08
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/08-pilot.md
source_digest: sha256:90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-28
created_provenance: git-commit
disposition_changed: 2026-09-28
disposition_changed_provenance: git-rename
---

# DBH-08 — Pilota: catena da 1

Compiled from `docs/tickets/delivery-bench-hard/done/08-pilot.md`. Identity is `ticket:delivery-bench-hard/DBH-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-28** via `git-commit`
- Disposition changed: **2026-09-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Child source: [[sources/artifact-delivery-bench-hard-pilot]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-05]] — `ticket:delivery-bench-hard/DBH-05`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-06]] — `ticket:delivery-bench-hard/DBH-06`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-07]] — `ticket:delivery-bench-hard/DBH-07`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-11]] — `ticket:delivery-bench-hard/DBH-11`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[7],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-08.md","payload_bytes":3444,"payload_sha256":"90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba"}],"payload_bytes":3444,"payload_sha256":"90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba","schema":1,"source_digest":"sha256:90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba","source_identity":"ticket:delivery-bench-hard/DBH-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 7: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3444,"payload_sha256":"90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba","schema":1,"source_digest":"sha256:90785ad97c0d009e3d054148a77445bb8db4d60be00f6ace4ed5155d14f84cba","source_identity":"ticket:delivery-bench-hard/DBH-08"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-08"
execution_mode: AFK
blocked_by:
  - "DBH-05"
  - "DBH-06"
  - "DBH-07"
  - "DBH-11"
---

# DBH-08 — Pilota: catena da 1

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:08`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

### Produces
- [delivery-bench-hard-pilot.md](../../research/delivery-bench-hard-pilot.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Il lotto `dbh-pilot` con i cinque bracci, i tre scenari nuovi e 3 ripetizioni, fino alla
richiesta 1. Usa `openai-codex/gpt-6-luna` con thinking `medium` e i tetti di DBH-01. Dopo il
lotto:
- si esegue `judge-gated`;
- si scrive il report `docs/research/delivery-bench-hard-pilot.md` con profilo, esiti del
  driver, compaction e distribuzione della durata delle richieste;
- si fissano i tetti di tempo della misura completa.

## Acceptance Criteria
- [x] Il lotto registra autorità, modello e thinking, e le copie del driver prese da un
  checkout pulito di `main` con `prepare-drivers --source`.
- [x] Tutte le 45 celle sono giudicate, con i guasti d'infrastruttura a parte. Un guasto
  dell'harness si corregge solo fra due `run-lot` e va nel report.
- [x] Il report confronta i bracci sui cinque assi e riporta le compaction. Propone il tetto
  per richiesta della misura completa, basato sulla durata osservata, con la ragione.
- [x] Se spesa o durata superano i tetti di DBH-01, il lotto si ferma e il report lo dice.

## Outcome
2026-09-28. Il report è
[delivery-bench-hard-pilot.md](../../research/delivery-bench-hard-pilot.md).
- **Lotto**: `dbh`, non `dbh-pilot`. L'autorità lega il nome del lotto e copre pilota e misura
  completa nello stesso lotto, che la misura completa estende. Il lotto registra autorità
  (sha256 `52597cbf…`), modello, thinking, tetto di 5400 s e copie del driver da un checkout
  pulito di `main` `b22b985`.
- **Esito**: 45 celle su 45 giudicate alla richiesta 1, con un tentativo ciascuna, nessun guasto
  d'infrastruttura, nessun timeout e nessuna compaction. Una richiesta accettata su 45, e in 37
  celle la cartella consegnata è identica al seme. La regola di TBA-03 dà «indistinguibile»
  per tutti i bracci. Un rigiudizio di controllo su 4 celle dà esiti identici.
- **Guasto dell'harness**: il primo lancio è caduto sul tetto oltre l'ora (12 tentativi
  `infra:harness`, 0 $), è stato fermato e archiviato, e il lotto è ripartito dopo la
  correzione (DBH-11, #382). In più, i tre scenari hanno avuto il comando di test dei driver
  prima del lancio.
- **Spesa e durata**: 0,248 $ e 40 minuti, contro 40 $ e 12 ore. Una richiesta dura da 33 a
  329 s.
- **Tetti per la misura completa**: 5400 s per richiesta e tetto di catena uguale a tetto per
  richiesta × lunghezza, invariati. La ragione è nel report.

## Frontier
Chiuso. Sblocca la misura completa (DBH-09).

## Step-by-Step Implementation Plan
1. `init-lot` con i tre scenari nuovi, i cinque bracci, `--model` e `--thinking`.
2. `prepare-drivers --source`, poi `run-lot --through 1 --jobs 4`.
3. `judge-gated`, `profile_report.py`, report e PR.

## Testing Plan
Le prove sono i record del giudice del lotto. Un rigiudizio di controllo su un campione di celle
deve dare esito identico.

## Out of Scope
- Catene più lunghe di 1 (DBH-09).
- Correggere un braccio dentro il lotto.

```
