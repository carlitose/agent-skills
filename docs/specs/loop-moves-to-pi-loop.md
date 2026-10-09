# `/loop` esce da agent-skills: vive solo in `@carlitose86/pi-loop`

## Artifact Graph
- Artifact ID: `artifact:loop-moves-to-pi-loop`
- Role: `spec`
- Standalone: true

### Children
- [LPM-01](../tickets/loop-moves-to-pi-loop/01-remove-loop-extension.md)

## Type
Decision.

## Problem
`/loop` ([pi-code-loop-command](pi-code-loop-command.md)) è nato in `extensions/loop.ts` di questo
pacchetto. Poi è stato pubblicato come pacchetto a sé: npm `@carlitose86/pi-loop@0.1.0`
(repository `carlitose/pi-loop`), che dichiara solo `./extensions/loop.ts`. Due copie dello
stesso comando divergono, e `pi-personal-config` fallisce `test:package` perché si aspetta che
agent-skills dichiari solo `mandatory-agent-skills.ts`.

## Decision
Utente, 2026-10-07 («toglilo da agent-skills dopo i lotti») e 2026-10-09 («Fai 1 per ora»):
- agent-skills toglie `extensions/loop.ts`, `extensions/loop.test.ts` e la voce in
  `package.json` `pi.extensions`; il README rimanda a `@carlitose86/pi-loop`.
- `pi-personal-config` installa `@carlitose86/pi-loop` e carica la sua estensione, nello stesso
  cambio del pin che toglie la copia di agent-skills: `/loop` non resta mai assente né doppio.

## Non-goals
- Cambiare il comportamento di `/loop`. La spec originale resta come storia della funzione.

## Verification
- agent-skills: `npm test` (lint, limiti e test node), CI.
- `pi-personal-config`: `test:package` torna verde; `update:personal`; dopo il reload `/loop`
  risponde una sola volta.

## Gates
- **Attempt:** il lavoro fino alla merge e all'installazione. **Budget, tempo, tentativi:**
  nessuno fissato.
- **Approvals:** merge con CI verde da parte dell'agente, pin, `update:personal` e reload (regola
  di sincronizzazione dopo ogni passo integrato). Nessuna pubblicazione npm.
- **Exact version:** `@carlitose86/pi-loop` 0.1.0, l'unica pubblicata.
- **Existing blocks:** nessun lotto in corso (`dbh-vague` finito, `dbh-crew3` non lanciato). Il
  checkout `~/.pi/agent/local/agent-skills` carica tutte le `pi.extensions` del pacchetto: dopo
  la sincronizzazione non porterà più `/loop`, quindi `pi-personal-config` deve portarlo.
