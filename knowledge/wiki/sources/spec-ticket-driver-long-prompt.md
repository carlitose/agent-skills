---
type: source
title: "Ticket Driver — un prompt oltre il limite della riga di comando"
identity_key: spec:ticket-driver-long-prompt
identity_strength: stable
source_path: docs/specs/ticket-driver-long-prompt.md
source_digest: sha256:461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Driver — un prompt oltre il limite della riga di comando

Compiled from `docs/specs/ticket-driver-long-prompt.md`. Identity is `spec:ticket-driver-long-prompt`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-long-prompt-tdl-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/spec-ticket-driver-long-prompt.md","payload_bytes":2690,"payload_sha256":"461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390"}],"payload_bytes":2690,"payload_sha256":"461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390","schema":1,"source_digest":"sha256:461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390","source_identity":"spec:ticket-driver-long-prompt","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2690,"payload_sha256":"461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390","schema":1,"source_digest":"sha256:461ac3668d5afd462b0626a5f61f6a29565a392f7b0ac7e9892706e620950390","source_identity":"spec:ticket-driver-long-prompt"} -->
```markdown
# Ticket Driver — un prompt oltre il limite della riga di comando

## Artifact Graph
- Artifact ID: `spec:ticket-driver-long-prompt`
- Role: `spec`
- Standalone: true

### Children
- [TDL-01](../tickets/ticket-driver-long-prompt/done/01-prompt-in-a-session-file.md)

## Osservazione e causa
Nella misura con Opus 5.5 (lotto `dbh-opus`, catena da 4) tre run di c3a su `sql-engine` si sono
fermati al cancello con `directed reviewer unavailable`. La ricevuta del revisore diretto dice
`failure: launch`, durata 0 s e nessuna uscita: il processo non è mai partito.

La foglia passa il prompt a Pi come ultimo argomento. Il prompt del revisore diretto contiene il
task e gli hunk interi di ogni funzione a rischio. Ricostruiti dai run, modello e hunk arrivano a
32 702, 31 992 e 44 121 caratteri nei tre run fermi, e a 28 218 al massimo nei run in cui il
revisore è partito. Con il task in più, i tre superano i 32 767 caratteri che Windows ammette per
una riga di comando, e `Popen` fallisce prima di creare il processo. Su Linux lo stesso accade a un
argomento oltre 128 KiB.

La ricevuta non dice perché: `invoke` scarta il messaggio di `CaptureFailure`, e mette lo stderr
della cattura nel campo `stdout`.

## Comportamento richiesto
- Finché la riga di comando sta nel limite della piattaforma, il prompt resta un argomento
  letterale, identico byte per byte a oggi. Limiti: 32 000 caratteri per l'intera riga su Windows,
  120 000 byte per il prompt altrove.
- Oltre il limite, la foglia scrive il prompt in `prompt.md` nella cartella della sua sessione e
  passa `@<file>` seguito da un messaggio breve che rimanda al file. Pi include il file nel primo
  messaggio. Vale per ogni foglia (builder, giudici, revisori) e per le foglie sostitutive.
- Una cattura fallita lascia nella ricevuta, dentro `stderr`, lo stderr del processo seguito da
  motivo e dettaglio (per esempio `launch: FileNotFoundError: …`). `stdout` resta l'uscita del
  processo. Il motivo (`failure`) non cambia.

## Verifica
Test prima della correzione in `ticket-driver/tests/test_leaf_launch.py`: argv sotto il limite con
il prompt nel file, su Windows e altrove; un lancio vero con un prompt di 200 000 byte che arriva
intero alla foglia; un lancio fallito con la diagnostica nella ricevuta. Poi l'intera suite di
`ticket-driver`. Le copie del driver del lotto `dbh-opus` non cambiano: la correzione vale da una
nuova `prepare-drivers`.

## Fuori ambito
- Cambiare `capture_command`, che eredita lo stdin per contratto.
- Ridurre gli hunk del revisore diretto o cambiarne la selezione.
- Un prompt letterale che inizia con `@`, che Pi leggerebbe come file: i modelli dei prompt
  iniziano con un titolo.

```
