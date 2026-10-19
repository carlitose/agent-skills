---
type: source
title: "LPM-01 — Togliere l'estensione `/loop` da agent-skills"
identity_key: ticket:loop-moves-to-pi-loop/LPM-01
identity_strength: stable
source_path: docs/tickets/loop-moves-to-pi-loop/done/01-remove-loop-extension.md
source_digest: sha256:0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-09
created_provenance: git-commit
disposition_changed: 2026-10-09
disposition_changed_provenance: git-rename
---

# LPM-01 — Togliere l'estensione `/loop` da agent-skills

Compiled from `docs/tickets/loop-moves-to-pi-loop/done/01-remove-loop-extension.md`. Identity is `ticket:loop-moves-to-pi-loop/LPM-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-09** via `git-commit`
- Disposition changed: **2026-10-09** via `git-rename`

## Graph

- Parent source: [[sources/artifact-loop-moves-to-pi-loop]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-loop-moves-to-pi-loop-lpm-01.md","payload_bytes":2175,"payload_sha256":"0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0"}],"payload_bytes":2175,"payload_sha256":"0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0","schema":1,"source_digest":"sha256:0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0","source_identity":"ticket:loop-moves-to-pi-loop/LPM-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2175,"payload_sha256":"0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0","schema":1,"source_digest":"sha256:0f9ecb6f57c4b80bdaefc03b67d3047fd7f8a486de7a734b2e74017cdcc2e0d0","source_identity":"ticket:loop-moves-to-pi-loop/LPM-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "LPM-01"
execution_mode: AFK
blocked_by: []
---

# LPM-01 — Togliere l'estensione `/loop` da agent-skills

## Artifact Graph
- Artifact ID: `ticket:loop-moves-to-pi-loop:01`
- Role: `ticket`
- Parent: [loop-moves-to-pi-loop.md](../../../specs/loop-moves-to-pi-loop.md)

## Parent Spec
[loop-moves-to-pi-loop.md](../../../specs/loop-moves-to-pi-loop.md), Decision e Verification.

## What to Build
Togliere `extensions/loop.ts`, `extensions/loop.test.ts` e la voce `./extensions/loop.ts` in
`package.json`; il README rimanda a `@carlitose86/pi-loop`. In `pi-personal-config`, con il pin
del nuovo head, aggiungere `@carlitose86/pi-loop` e la sua estensione.

## Acceptance Criteria
- [x] agent-skills dichiara solo `./extensions/mandatory-agent-skills.ts`; `npm test` e CI verdi.
- [x] `pi-personal-config` dipende da `@carlitose86/pi-loop@0.1.0` e ne carica `extensions/loop.ts`;
      `test:package` verde.
- [x] Dopo `update:personal` il comando `/loop` esiste una sola volta.

## Evidence
- agent-skills #459 (`d269ca4`): `loop.ts` e `loop.test.ts` tolti, `pi.extensions` solo
  `mandatory-agent-skills.ts`; `npm test` 16/16, CI 8/8.
- `pi-personal-config` #74 (`e1349cd`): pin `d269ca4`, `@carlitose86/pi-loop@0.1.0` nelle dipendenze
  incluse e la sua `extensions/loop.ts` caricata; test:package 6/6, deps 3/3, updater 32/32,
  controls 13/13, telegram 7/7.
- `update:personal` verificato: il checkout `~/.pi/agent/local/agent-skills` è a `d269ca4` e non ha più
  `loop.ts`; `/loop` arriva solo da `@carlitose86/pi-loop`. Reload chiesto; il comando dal vivo
  non è stato provato.

## Frontier
Fatto.

## Gates
Come la spec: il lavoro fino all'installazione, nessun budget, tempo o tentativo fissato; merge
con CI verde, pin, `update:personal` e reload da parte dell'agente.

## Step-by-Step Implementation Plan
1. agent-skills: file, `package.json`, README; `npm test`; PR, merge.
2. `pi-personal-config`: pin, dipendenza, estensione, test; PR, merge; `update:personal`.

## Testing Plan
- `npm test` in agent-skills; `test:package`, `test:deps`, `test:updater` in `pi-personal-config`.

## Out of Scope
- Comportamento di `/loop`.

```
