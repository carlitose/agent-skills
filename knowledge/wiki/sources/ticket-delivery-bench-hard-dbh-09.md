---
type: source
title: "DBH-09 — Misura completa: catene da 4 e 12"
identity_key: ticket:delivery-bench-hard/DBH-09
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/09-full-measurement.md
source_digest: sha256:1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed: 2026-09-29
disposition_changed_provenance: git-rename
---

# DBH-09 — Misura completa: catene da 4 e 12

Compiled from `docs/tickets/delivery-bench-hard/done/09-full-measurement.md`. Identity is `ticket:delivery-bench-hard/DBH-09`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **2026-09-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Child source: [[sources/artifact-delivery-bench-hard-results]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-08]] — `ticket:delivery-bench-hard/DBH-08`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-12]] — `ticket:delivery-bench-hard/DBH-12`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-13]] — `ticket:delivery-bench-hard/DBH-13`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[7],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-09.md","payload_bytes":3542,"payload_sha256":"1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7"}],"payload_bytes":3542,"payload_sha256":"1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7","schema":1,"source_digest":"sha256:1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7","source_identity":"ticket:delivery-bench-hard/DBH-09","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 7: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3542,"payload_sha256":"1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7","schema":1,"source_digest":"sha256:1098075fea547d04fb431cfa0e07853b79b203a0f973b73a5c291d59872c98a7","source_identity":"ticket:delivery-bench-hard/DBH-09"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-09"
execution_mode: AFK
blocked_by:
  - "DBH-08"
  - "DBH-12"
  - "DBH-13"
---

# DBH-09 — Misura completa: catene da 4 e 12

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:09`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

### Produces
- [delivery-bench-hard-results.md](../../research/delivery-bench-hard-results.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Estendere le celle del pilota, dentro i tetti di DBH-01 e con i tetti di tempo fissati da
DBH-08:
- le ripetizioni 1-3 fino alla richiesta 4;
- la ripetizione 1 fino alla 12;
- altre ripetizioni della catena da 12 solo dove la regola di TBA-03 le chiede.

Il report finale è `docs/research/delivery-bench-hard-results.md`. Contiene:
- la tabella braccio × lunghezza × scenario sui cinque assi, con le compaction;
- la regola di TBA-03;
- la raccomandazione operativa per questo regime;
- il confronto con la prima misura e con la calibrazione di DBH-03;
- i limiti.

## Acceptance Criteria
- [x] Tutte le celle richieste hanno un profilo. Le ripetizioni extra ci sono solo dove la
  regola, sui tassi, le chiede.
- [x] Il report ha tabella, regola, raccomandazione e limiti, senza un numero unico. Non nomina
  controlli o trappole nascosti.
- [x] La mappa passa a Completed e ha il link al report.
- [x] Spesa e durata stanno sotto i tetti, altrimenti il lotto si ferma e il report lo dice.

## Outcome
2026-09-29. Il report è
[delivery-bench-hard-results.md](../../research/delivery-bench-hard-results.md).
- **Celle**: il lotto `dbh` ha 45 celle.
  - Le 3 ripetizioni arrivano alla richiesta 4.
  - La ripetizione 1 arriva alla 12 per tutti i bracci.
  - La regola, sui tassi, ha chiesto la ripetizione 2 della catena da 12: dopo la ripetizione 1
    per skills-only (con `bare` come base), poi per Autopilot. Con quella la regola è decisa.
  - In tutto 372 richieste giudicate, con un rigiudizio di controllo su 5 celle identico al
    record.
- **Regola di TBA-03**:
  - alla catena da 1 dà `bare`;
  - alla catena da 4 dà skills-only, «meglio» di `bare` con Holm 0,031;
  - alla catena da 12 dà `bare`: skills-only e Autopilot sono sopra ma indistinguibili, e i
    due driver sono «peggio».
- **Report**: ha tabelle, regola, raccomandazione, confronto e limiti, senza un numero unico e
  senza nomi di controlli o trappole.
- **Guasti**: due catene si sono fermate su due difetti del runner, DBH-12 e DBH-13. Sono stati
  corretti fra due `run-lot`, e le catene sono riprese. Un buco di rete di circa 10 minuti ha
  esaurito i retry di due richieste, che contano come non accettate (contratto §9). La regola
  non cambia togliendole.
- **Spesa e durata**: 17,46 $ per DBH-09 (17,71 $ col pilota) e 19,6 ore, contro 250 $ e 72 ore.
  Nessun timeout, con un massimo di 3642 s per richiesta contro un tetto di 5400.

## Frontier
Chiuso. La mappa è completa.

## Step-by-Step Implementation Plan
1. `run-lot --through 4`, poi `--through 12 --rep 1`.
2. Applicare la regola, eseguire le ripetizioni richieste, poi `judge-gated`.
3. `profile_report.py` alle lunghezze 1, 4 e 12. Scrivere report e aggiornamento della mappa,
   poi aprire la PR.

## Testing Plan
Le prove sono i record del giudice del lotto. Un difetto dell'oracolo si corregge secondo il
contratto §9, fra due `run-lot`, e con un rigiudizio.

## Out of Scope
- Migliorare i bracci.
- Lotti della prima misura.

```
