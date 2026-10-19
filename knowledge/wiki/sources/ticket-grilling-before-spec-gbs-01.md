---
type: source
title: "GBS-01 — Requisiti aperti: `grilling -> to-spec`"
identity_key: ticket:grilling-before-spec/GBS-01
identity_strength: stable
source_path: docs/tickets/grilling-before-spec/done/01-route-open-requirements.md
source_digest: sha256:7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-10
created_provenance: git-commit
disposition_changed: 2026-10-10
disposition_changed_provenance: git-rename
---

# GBS-01 — Requisiti aperti: `grilling -> to-spec`

Compiled from `docs/tickets/grilling-before-spec/done/01-route-open-requirements.md`. Identity is `ticket:grilling-before-spec/GBS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-10** via `git-commit`
- Disposition changed: **2026-10-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-grilling-before-spec]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-grilling-before-spec-gbs-01.md","payload_bytes":2104,"payload_sha256":"7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63"}],"payload_bytes":2104,"payload_sha256":"7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63","schema":1,"source_digest":"sha256:7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63","source_identity":"ticket:grilling-before-spec/GBS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2104,"payload_sha256":"7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63","schema":1,"source_digest":"sha256:7c8d0c4753eac8d41b6545f7ea2baec593e5a8df5ba0cce4b57fb2dcb4a36a63","source_identity":"ticket:grilling-before-spec/GBS-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "GBS-01"
execution_mode: AFK
blocked_by: []
---

# GBS-01 — Requisiti aperti: `grilling -> to-spec`

## Artifact Graph
- Artifact ID: `ticket:grilling-before-spec:01`
- Role: `ticket`
- Parent: [grilling-before-spec.md](../../../specs/grilling-before-spec.md)

## Parent Spec
[grilling-before-spec.md](../../../specs/grilling-before-spec.md), Decision e Verification.

## What to Build
In `ask-skills/SKILL.md`: una richiesta i cui requisiti aperti cambierebbero il risultato o i suoi
test, quando qualcuno può rispondere, passa per `grilling -> to-spec`. In `grilling/SKILL.md`: la
sezione *Before a spec* con le regole di stop della spec.

## Acceptance Criteria
- [x] `ask-skills` ha la rotta `grilling -> to-spec`, e una richiesta completa resta `to-spec`.
- [x] `grilling` ha *Before a spec*: solo requisiti; niente processo; niente domande già risolte o
      senza effetto; assunzione senza risposta; nessun giro di conferma separato.
- [x] `ask-skills/SKILL.md` resta entro il limite di righe; test e CI verdi.
- [x] Pin in `pi-personal-config` e `update:personal` verificato.

## Evidence
- agent-skills #465 (`e6e07b0`): rotta in `ask-skills` (94/94 righe), sezione *Before a spec* in
  `grilling`, test in `test_skill_graph.py`; CI 8/8.
- `pi-personal-config` #75 (`370b6d5`): pin `e6e07b0`; test:package 6/6, updater 32/32 (test:deps 1 fallimento
  su `@sinclair/typebox` presente anche su main, dovuto a `node_modules`).
- `update:personal` verificato: `~/.agents/skills` e `~/.pi/agent/local/agent-skills` hanno la nuova rotta.
  Reload chiesto, non osservato. La misura sul lotto vago resta da fare quando l'utente lo dice.

## Frontier
Fatto.

## Gates
Come la spec: il lavoro fino all'installazione; merge con CI verde, pin, `update:personal` e reload
da parte dell'agente; nessun lotto.

## Step-by-Step Implementation Plan
1. `ask-skills`, `grilling`, test.
2. PR e merge; pin e installazione.

## Testing Plan
- `test_skill_graph.py`, `test_change_status_skill.py`, limiti di righe; suite completa alla CI.

## Out of Scope
- Rifare il lotto vago.

```
