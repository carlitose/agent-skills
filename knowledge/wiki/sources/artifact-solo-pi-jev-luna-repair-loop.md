---
type: source
title: "Luna Yjs L4 — benchmark minimo del braccio e repair loop"
identity_key: artifact:solo-pi-jev-luna-repair-loop
identity_strength: stable
source_path: docs/specs/solo-pi-jev-luna-repair-loop.md
source_digest: sha256:d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Luna Yjs L4 — benchmark minimo del braccio e repair loop

Compiled from `docs/specs/solo-pi-jev-luna-repair-loop.md`. Identity is `artifact:solo-pi-jev-luna-repair-loop`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-11]]
- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-13]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-luna-repair-loop.md","payload_bytes":2596,"payload_sha256":"d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242"}],"payload_bytes":2596,"payload_sha256":"d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242","schema":1,"source_digest":"sha256:d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242","source_identity":"artifact:solo-pi-jev-luna-repair-loop","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2596,"payload_sha256":"d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242","schema":1,"source_digest":"sha256:d4510f2fb9d9e7588deb3806f32fe840f58e6e145ea6ed5604dfec89fed31242","source_identity":"artifact:solo-pi-jev-luna-repair-loop"} -->
```markdown
# Luna Yjs L4 — benchmark minimo del braccio e repair loop

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-repair-loop`
- Role: `spec`
- Standalone: true

### Children
- [SPB-11](../tickets/solo-pi-jev-luna-pilot/11-benchmark-minimum-arm.md)
- [SPB-13](../tickets/solo-pi-jev-luna-pilot/13-retest-minimum-arm.md)

## Mandato e minimo
Utente: «Comunque fai sti cazzo di benchmark minimo su questo braccio e vedi se funziona o
ci sono bug nel braccio! Se c’è fixa, è riprova il benchmark fino ad arrivare funzionante e
valutarlo davvero». Inline serial skills-only, nessuna delega/runner/delivery.
Minimo: una nuova catena Yjs L4 Luna medium sul braccio corretto SPB-10; R1 Counter,
R2 readOnly/lint/format, R3 replica undo/redo e replace, R4 add/reset. Stesso processo/sessione,
quattro richieste cumulative e protocollo di dipendenze originario. Fixed source separato;
nessun replay dello storico e nessun feedback oracle privato al partecipante.

## Criterio di funzionamento
Osservare i port reali e distinguere codice insufficiente da infrastruttura/protocollo errato.
Riparare soltanto difetti dimostrati del braccio, mantenere candidato/evidenze/fallimenti,
poi nuova prova con source congelato e admission completa. Non iterare finché oracle dà 4/4:
un NO fondato o test falliti è un risultato del modello; dipendenti non tentati restano tali.
Flusso locale completato e score dell'oracle sono giudizi separati. Se la catena non esercita
un segmento, dichiarare il limite invece di fingere copertura end-to-end.

## Ammissione
Validare handoff/verification SPB-10, target/graph/envelope/snapshot/SDK/model/skills/input,
immagini e originale €1000/costi cumulativi correnti. Copiare il più recente SPB-09 budget
10/47/7/367, nessun reset. Pubblica renew_launch_capacity sotto mandato attribuito, poi
admit_launch prelaunch; nessuna modifica manuale di authority/store. Renew dà un solo prossimo
slot; la richiesta umana di repair-loop, non budget residuo, autorizza nuove prove coerenti.
Ogni eventuale prova ulteriore usa nuova identità e consumo precedente intero. Unknown costo,
limite monetario, revoca, port irrecuperabile o scope diverso rimangono confini reali.

## Output
Preservare tutti gli attempt, input/charge/source/history refs, candidato e consegnato, score
per R e motivi di arresto. Rapporto di copertura reale, difetti corretti e limiti del braccio;
mai upgrade di test fake a prove live. SDK estimate non invoice/FX finale. Nessun cambio di
modello/soglie/dati, intervento manuale sul prodotto per forzare score, pubblicazione/installazione.

```
