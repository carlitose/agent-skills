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
- Parent: [loop-moves-to-pi-loop.md](../../specs/loop-moves-to-pi-loop.md)

## Parent Spec
[loop-moves-to-pi-loop.md](../../specs/loop-moves-to-pi-loop.md), Decision e Verification.

## What to Build
Togliere `extensions/loop.ts`, `extensions/loop.test.ts` e la voce `./extensions/loop.ts` in
`package.json`; il README rimanda a `@carlitose86/pi-loop`. In `pi-personal-config`, con il pin
del nuovo head, aggiungere `@carlitose86/pi-loop` e la sua estensione.

## Acceptance Criteria
- [ ] agent-skills dichiara solo `./extensions/mandatory-agent-skills.ts`; `npm test` e CI verdi.
- [ ] `pi-personal-config` dipende da `@carlitose86/pi-loop@0.1.0` e ne carica `extensions/loop.ts`;
      `test:package` verde.
- [ ] Dopo `update:personal` il comando `/loop` esiste una sola volta.

## Frontier
Pronto.

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
