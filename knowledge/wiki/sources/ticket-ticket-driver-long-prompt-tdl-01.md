---
type: source
title: "TDL-01 — Il prompt oltre il limite della riga di comando passa da un file della sessione"
identity_key: ticket:ticket-driver-long-prompt/TDL-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-long-prompt/done/01-prompt-in-a-session-file.md
source_digest: sha256:89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TDL-01 — Il prompt oltre il limite della riga di comando passa da un file della sessione

Compiled from `docs/tickets/ticket-driver-long-prompt/done/01-prompt-in-a-session-file.md`. Identity is `ticket:ticket-driver-long-prompt/TDL-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-ticket-driver-long-prompt]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-long-prompt-tdl-01.md","payload_bytes":2126,"payload_sha256":"89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd"}],"payload_bytes":2126,"payload_sha256":"89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd","schema":1,"source_digest":"sha256:89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd","source_identity":"ticket:ticket-driver-long-prompt/TDL-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2126,"payload_sha256":"89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd","schema":1,"source_digest":"sha256:89ae9011609a39e7b8849b2f424422b84ab37cbc67678a86316139e7ae464fbd","source_identity":"ticket:ticket-driver-long-prompt/TDL-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TDL-01"
execution_mode: AFK
blocked_by: []
---

# TDL-01 — Il prompt oltre il limite della riga di comando passa da un file della sessione

## Artifact Graph
- Artifact ID: `ticket:ticket-driver-long-prompt:01`
- Role: `ticket`
- Parent: [ticket-driver-long-prompt.md](../../specs/ticket-driver-long-prompt.md)

## Parent Spec
[ticket-driver-long-prompt.md](../../specs/ticket-driver-long-prompt.md)

## What to Build
In `ticket-driver/scripts/leaf.py`, `leaf_argv` lascia il prompt come argomento finché la riga di
comando sta nel limite della piattaforma; oltre, lo scrive in `prompt.md` nella cartella della
sessione e passa `@<file>` con un messaggio breve. `invoke` mette nella ricevuta, in `stderr`, il
motivo e il dettaglio di una cattura fallita. La foglia finta dei test legge anche `@<file>`.

## Acceptance Criteria
- [x] Un prompt breve resta l'ultimo argomento, senza file. Un prompt di 40 000 caratteri su
  Windows, e di 200 000 altrove, passa da `prompt.md` con gli stessi byte, e la riga di comando sta
  sotto i 32 767 caratteri. Prima della correzione `leaf_argv` non ha il parametro `platform`.
- [x] Un lancio vero con un prompt di 200 000 byte arriva intero alla foglia. Prima della
  correzione, su Windows, fallisce con `launch`.
- [x] Un lancio fallito ha `stdout` vuoto e in `stderr` `launch:` con il tipo d'errore. Prima della
  correzione `stderr` è vuoto.
- [x] L'intera suite di `ticket-driver` passa.

## Outcome
2026-09-30. I tre test nuovi falliscono prima della correzione e passano dopo, con l'intera suite
di `ticket-driver`.

## Frontier
Chiuso. Vale da una nuova `prepare-drivers`; le copie del lotto `dbh-opus` non cambiano.

## Step-by-Step Implementation Plan
1. Test RED in `test_leaf_launch.py`.
2. `_with_prompt` in `leaf.py`, usato da Pi e dalle foglie sostitutive; diagnostica in `invoke`.
3. Foglia finta dei test che legge `@<file>`; suite di `ticket-driver`.

## Testing Plan
`python -B -m unittest discover -s tests -t .` da `ticket-driver`.

## Out of Scope
- `capture_command` e lo stdin.
- La selezione degli hunk del revisore diretto.

```
