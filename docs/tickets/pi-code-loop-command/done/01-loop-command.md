---
ticket_schema: 1
ticket_id: "PCL-01"
execution_mode: AFK
blocked_by: []
---

# PCL-01 — Estensione `/loop` nel pacchetto agent-skills

## Artifact Graph
- Artifact ID: `ticket:pi-code-loop-command:01`
- Role: `ticket`
- Parent: [pi-code-loop-command.md](../../../specs/pi-code-loop-command.md)

## Parent Spec
[pi-code-loop-command.md](../../../specs/pi-code-loop-command.md), tutto il Target behavior.

## What to Build
`extensions/loop.ts`, estensione autonoma del pacchetto Pi `carlitose-agent-skills-pi`: il
comando `/loop` con pausa facoltativa, giri ripetuti a fine turno, stato, stop, Esc, gestione
degli errori come `/goal`, indicatore e attesa headless. Registrata in `package.json`
(`pi.extensions`) e descritta nel README; arriva nel Pi dell'utente con il solo pin.

## Acceptance Criteria
- [x] `/loop 30s fai X` manda subito `[loop, giro 1] fai X` e, a fine turno, il giro 2 dopo 30 s;
      senza intervallo il giro 2 parte subito.
- [x] `/loop` mostra lo stato; `/loop stop` ferma il ciclo e annulla l'attesa.
- [x] Esc ferma il ciclo; un errore irrecuperabile lo ferma; uno transitorio riprova dopo almeno
      30 s.
- [x] Una nuova sessione non ripristina il ciclo.
- [x] `npm test` e `npm run lint` verdi in locale; CI 8/8.
- [x] Prova reale headless: 3 giri su luna, poi fermata.

## Evidence
- `extensions/loop.test.ts` 14/14 (`node --test`, timer finti); `npm test` quick 15/15 e
  `npm run lint` verdi in locale.
- Prova reale headless: `pi -p --no-extensions -e extensions/loop.ts` su `gpt-6-luna`,
  `/loop 2s ...`: 3 giri `[loop, round 1..3]` a circa 3-4 s l'uno dall'altro, processo ancora
  vivo (tenuto aperto dal ciclo) e fermato a mano; costo 0,00007 $.
- Scelta in corso d'opera: su richiesta dell'utente l'estensione vive in questo pacchetto e
  non nel fork di pi-code; copia il piccolo classificatore di errori di `/goal`.

## Frontier
Done.

## Gates
Come la spec: solo la prova reale a pagamento (al massimo 0,10 $), un giorno, 2 tentativi; merge
con CI 8/8, poi pin in `pi-personal-config`, `update:personal` e reload.

## Step-by-Step Implementation Plan
1. Parsing di argomenti e intervallo, testi di stato.
2. Stato del ciclo, invio dei giri, timer e indicatore.
3. Eventi: fine turno, Esc, errori, nuova sessione, chiusura.
4. Test `node --test` con timer finti.
5. Registrazione nel pacchetto e README.

## Testing Plan
- `node --experimental-strip-types --test extensions/loop.test.ts`, poi `npm test` e `npm run lint`.
- Prova reale con `pi -p`.

## Out of Scope
- Modifiche a `/goal`.
