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
