---
type: source
title: "DB-07 — Pilota: catena da 1, cinque bracci, tre scenari"
identity_key: ticket:delivery-bench/DB-07
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/07-pilot-chain-1-all-arms.md
source_digest: sha256:45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# DB-07 — Pilota: catena da 1, cinque bracci, tre scenari

Compiled from `docs/tickets/delivery-bench/done/07-pilot-chain-1-all-arms.md`. Identity is `ticket:delivery-bench/DB-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Child source: [[sources/artifact-delivery-bench-pilot]]
- Blocked by: [[sources/ticket-delivery-bench-db-03]] — `ticket:delivery-bench/DB-03`
- Blocked by: [[sources/ticket-delivery-bench-db-04]] — `ticket:delivery-bench/DB-04`
- Blocked by: [[sources/ticket-delivery-bench-db-05]] — `ticket:delivery-bench/DB-05`
- Blocked by: [[sources/ticket-delivery-bench-db-06]] — `ticket:delivery-bench/DB-06`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-07.md","payload_bytes":2482,"payload_sha256":"45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc"}],"payload_bytes":2482,"payload_sha256":"45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc","schema":1,"source_digest":"sha256:45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc","source_identity":"ticket:delivery-bench/DB-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2482,"payload_sha256":"45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc","schema":1,"source_digest":"sha256:45382aa7c7402bae99834fb58e444c72a79dabe5d73e5a06966e8283801179bc","source_identity":"ticket:delivery-bench/DB-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DB-07"
execution_mode: HITL
blocked_by:
  - "DB-03"
  - "DB-04"
  - "DB-05"
  - "DB-06"
---

# DB-07 — Pilota: catena da 1, cinque bracci, tre scenari

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:07`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

### Produces
- [delivery-bench-pilot.md](../../research/delivery-bench-pilot.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire la catena da 1 in ciascuno dei tre scenari con i cinque bracci (3 ripetizioni), con `openai-codex/gpt-6-sol`, e leggere i profili: i bracci sono confrontabili? Quali guasti dell'harness emergono? L'utente autorizza il lotto e rivede i risultati prima della misura completa.

## Acceptance Criteria
- [x] Autorità, lotto e ledger fuori da Git; ogni cella con receipt, journal, tempo e profilo.
- [x] 15 celle per scenario (5 bracci × 3 ripetizioni), guasti d'infrastruttura ripetuti al massimo due volte.
- [x] Report a profilo e confronto appaiato; elenco dei guasti dell'harness con correzione o ticket.

## Frontier
**Completato** (2026-09-26, skills-only): lotto `db07-pilot`, 45 celle (3 scenari × 5 bracci × 3 ripetizioni) con `openai-codex/gpt-6-sol`, autorità dall'obiettivo di sessione vincolata per hash, lotto, ledger e record di cella nel repo privato fuori da Git. 45/45 richieste giudicate; nessun guasto d'infrastruttura, errore del giudice, timeout o riscontro dell'audit. Report e letture: [delivery-bench-pilot.md](../../../research/delivery-bench-pilot.md). In sintesi: accettazione al soffitto per bare, skills-only, Autopilot e c1a (9/9), indistinguibili per la regola di TBA-03; c3a 2/9 perché 7 run si fermano sul cancello semantico in attesa di un umano (candidati bloccati 7/7 accettabili a parte); costo da 0,74 $ (bare) a 8,26 $ (Autopilot) per 9 celle. Correzioni dell'harness nella stessa PR: esiti del driver e giudizio controfattuale (`judge-gated`), `run-lot --rep`, `profile_report.py --through/--rep` con la regola del vincitore. Revisione dell'utente: l'obiettivo di sessione autorizza DB-07 e DB-08 senza fermarsi; il report è il punto di revisione.

## Step-by-Step Implementation Plan
1. Autorizzazione e lotto.
2. Esecuzione seriale per scenario.
3. Report e revisione con l'utente.

## Testing Plan
Live; nessuna modifica ai bracci durante il pilota.

## Out of Scope
- Catene da 3 e 8 (DB-08).

```
