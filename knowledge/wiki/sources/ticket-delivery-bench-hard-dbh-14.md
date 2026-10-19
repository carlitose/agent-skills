---
type: source
title: "DBH-14 — Aspettare prima di ripetere un tentativo fallito per l'infrastruttura"
identity_key: ticket:delivery-bench-hard/DBH-14
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/14-infra-retry-wait.md
source_digest: sha256:31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# DBH-14 — Aspettare prima di ripetere un tentativo fallito per l'infrastruttura

Compiled from `docs/tickets/delivery-bench-hard/done/14-infra-retry-wait.md`. Identity is `ticket:delivery-bench-hard/DBH-14`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-09]] — `ticket:delivery-bench-hard/DBH-09`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-14.md","payload_bytes":3178,"payload_sha256":"31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3"}],"payload_bytes":3178,"payload_sha256":"31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3","schema":1,"source_digest":"sha256:31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3","source_identity":"ticket:delivery-bench-hard/DBH-14","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3178,"payload_sha256":"31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3","schema":1,"source_digest":"sha256:31287053574fa825e2fba2619ad7edf9a7a64eaf34ad3fe598658619fc3316d3","source_identity":"ticket:delivery-bench-hard/DBH-14"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-14"
execution_mode: AFK
blocked_by:
  - "DBH-09"
---

# DBH-14 — Aspettare prima di ripetere un tentativo fallito per l'infrastruttura

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:14`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner osservato durante la misura completa (DBH-09).
- **Osservato**: il 29/09 fra le 06:33 e le 06:42 UTC la rete è caduta. Alla richiesta 12 di due
  celle `sql-engine` Pi è uscito tre volte con `fetch failed`, in circa 17 s ciascuna e senza
  spesa. Le ripetizioni si sono esaurite in meno di un minuto, e le due richieste contano come
  non accettate (contratto §9).
- **Causa**: il runner ripete un tentativo fallito per l'infrastruttura subito dopo aver
  ripristinato la cartella. Tre tentativi coprono meno di un minuto, quindi un'interruzione di
  qualche minuto li esaurisce tutti.

Il comportamento atteso:
- prima di ogni ripetizione il runner aspetta, e la seconda attesa è più lunga della prima;
- le attese, insieme, superano un'interruzione di 10 minuti;
- l'attesa non conta per i tetti ed è registrata;
- un esito dell'agente non è mai seguito da un'attesa.

## Acceptance Criteria
- [x] Un test fa fallire tre tentativi per l'infrastruttura. Prima della correzione il runner non
  aspetta mai. Dopo, aspetta due volte, la seconda più a lungo, per almeno 10 minuti in tutto, e
  ledger e richiesta registrano le attese.
- [x] Dopo un tentativo dell'agente il runner non aspetta.
- [x] Il numero massimo di ripetizioni e i tetti non cambiano. Il contratto §9 descrive l'attesa.

## Outcome
2026-09-29. I due test nuovi di `test_runner.py` falliscono prima della correzione: il runner non
aspetta mai (0 attese invece di 2, e 0 invece di 1). Dopo la correzione passano, insieme agli altri
test di `test_runner.py`, `test_judge.py` e `test_profile_report.py` (54, 2 saltati).
- Il runner aspetta 1 minuto prima della prima ripetizione e 10 minuti prima della seconda.
- Ogni attesa è un evento `infra-wait` del ledger, e la richiesta somma le sue attese in
  `infra_wait_seconds`. I tetti contano solo i tentativi.
- Nei test l'attesa si registra senza dormire.
- I record del lotto `dbh` non cambiano. La misura completa è girata senza la correzione, e il
  [report](../../research/delivery-bench-hard-results.md) lo dice.

## Frontier
Chiuso. Vale dal prossimo `run-lot`.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: tre tentativi falliti per l'infrastruttura, con le attese
   registrate al posto di dormire.
2. Attesa crescente prima di ogni ripetizione, con evento nel ledger e somma nella richiesta.
3. Contratto §9 e report di DBH-09 aggiornati.

## Testing Plan
Test offline di `test_runner.py`, `test_judge.py` e `test_profile_report.py`.

## Out of Scope
- Più ripetizioni o tetti diversi.
- Rigiocare le due richieste perse nel lotto `dbh`: il contratto §9 le conta come non accettate.
- L'attesa del giudice, che ne ha già una sua.

```
