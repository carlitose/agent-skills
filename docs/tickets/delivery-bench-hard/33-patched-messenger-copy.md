---
ticket_schema: 1
ticket_id: "DBH-33"
execution_mode: AFK
blocked_by: []
---

# DBH-33 — Copia corretta di pi-messenger per il benchmark

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:33`
- Role: `ticket`
- Parent: [delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md)

## Parent Spec
[delivery-bench-hard-crew-arms.md](../../specs/delivery-bench-hard-crew-arms.md), Target behavior 1 e 2.

## What to Build
`crew_messenger.py` copia il pacchetto `pi-messenger` installato in una cartella data e applica
patch ad ancore esatte, contando le occorrenze attese per file:
- `spawn(getPiCommand(), args, {` in `crew/agents.ts` e `crew/lobby.ts` diventa
  `spawn(process.execPath, [...argv da DBENCH_WORKER_ARGV, ...args], {`: nessuna shell, quindi
  niente `spawn EINVAL` su Windows;
- `"--no-session"` esce dagli argomenti dei worker (la loro `--session-dir` arriva da
  `DBENCH_WORKER_ARGV`);
- ogni `homedir()` e `os.homedir()` del pacchetto diventa
  `(process.env.DBENCH_MESSENGER_HOME || homedir())`: config, feed, agenti e profili restano
  nella cartella del braccio;
- la riga di `index.ts` che cancella `messenger/feed.jsonl` all'avvio viene tolta.

Se un'ancora manca o compare un numero diverso di volte la copia fallisce e non lascia nulla. A
copia riuscita scrive `dbench-patch.json` con versione, sha256 dei file di origine e patch
applicate.

## Acceptance Criteria
- [ ] Sul pacchetto installato (0.15.2) la copia riesce e non contiene più `getPiCommand(), args`,
      `"--no-session"`, la cancellazione di `feed.jsonl` né un `homedir()` senza la variabile.
- [ ] Un'ancora mancante fa fallire la copia e la cartella di destinazione non esiste.
- [ ] Un processo Node lanciato con la riga patchata parte su Windows senza shell (smoke).

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa a pagamento per questo ticket; merge con CI 8/8 e
`--match-head-commit`; nessuna versione esatta, ma le ancore valgono per il pacchetto installato.

## Step-by-Step Implementation Plan
1. Tabella delle patch (file, vecchio, nuovo, occorrenze).
2. Copia in una cartella temporanea, patch, rinomina atomica nella destinazione.
3. Manifesto.

## Testing Plan
- Unit su un pacchetto giocattolo e sul pacchetto installato (saltato se assente).
- Smoke: `spawn` patchato di un `node -e` su Windows.

## Out of Scope
- Bracci e runner (DBH-34).
