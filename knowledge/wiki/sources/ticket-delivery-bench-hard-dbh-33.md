---
type: source
title: "DBH-33 — Copia corretta di pi-messenger per il benchmark"
identity_key: ticket:delivery-bench-hard/DBH-33
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/33-patched-messenger-copy.md
source_digest: sha256:4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed: 2026-10-06
disposition_changed_provenance: git-rename
---

# DBH-33 — Copia corretta di pi-messenger per il benchmark

Compiled from `docs/tickets/delivery-bench-hard/done/33-patched-messenger-copy.md`. Identity is `ticket:delivery-bench-hard/DBH-33`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **2026-10-06** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-crew-arms]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-33.md","payload_bytes":2873,"payload_sha256":"4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd"}],"payload_bytes":2873,"payload_sha256":"4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd","schema":1,"source_digest":"sha256:4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd","source_identity":"ticket:delivery-bench-hard/DBH-33","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2873,"payload_sha256":"4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd","schema":1,"source_digest":"sha256:4750c5e6188682ffced0933ad2ca06bdb56c295b7db558e38df6bf6850a43bdd","source_identity":"ticket:delivery-bench-hard/DBH-33"} -->
```markdown
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
- Parent: [delivery-bench-hard-crew-arms.md](../../../specs/delivery-bench-hard-crew-arms.md)

## Parent Spec
[delivery-bench-hard-crew-arms.md](../../../specs/delivery-bench-hard-crew-arms.md), Target behavior 1 e 2.

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
- [x] Sul pacchetto installato (0.15.2) la copia riesce e non contiene più `getPiCommand(), args`,
      `"--no-session"`, la cancellazione di `feed.jsonl` né un `homedir()` senza la variabile.
- [x] Un'ancora mancante fa fallire la copia e la cartella di destinazione non esiste.
- [x] Un processo Node lanciato con la riga patchata parte su Windows senza shell (smoke).

## Evidence
- `crew_messenger.prepare` with 14 exact-anchor patches; `test_crew_messenger` 8/8, including
  the installed 0.15.2 and a Node smoke of the patched spawn line (no shell; a missing
  `DBENCH_WORKER_ARGV` fails loudly).
- The patched copy loads in Pi (`-e <copy>/index.ts`) with the redirected home.
- Choice made during implementation: the fail-closed home check found `install.mjs`, the
  package's npx installer, which Pi never loads; the copy leaves it out.

## Frontier
Done.

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

```
