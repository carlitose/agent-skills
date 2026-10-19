---
type: source
title: "Yjs L4 — minimo del braccio e repair loop, SPB-11"
identity_key: artifact:solo-pi-jev-luna-repair-loop-results
identity_strength: stable
source_path: docs/research/solo-pi-jev-luna-repair-loop-results.md
source_digest: sha256:361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Yjs L4 — minimo del braccio e repair loop, SPB-11

Compiled from `docs/research/solo-pi-jev-luna-repair-loop-results.md`. Identity is `artifact:solo-pi-jev-luna-repair-loop-results`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-11]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[],"status":"not-identified"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[],"status":"not-identified"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-luna-repair-loop-results.md","payload_bytes":1923,"payload_sha256":"361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f"}],"payload_bytes":1923,"payload_sha256":"361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f","schema":1,"source_digest":"sha256:361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f","source_identity":"artifact:solo-pi-jev-luna-repair-loop-results","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | no matching section identified in the source; complete source retained |
| limitations | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1923,"payload_sha256":"361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f","schema":1,"source_digest":"sha256:361b52c55f56f52c7fbed906346381517632e2efebe61f68319adac463dc785f","source_identity":"artifact:solo-pi-jev-luna-repair-loop-results"} -->
```markdown
# Yjs L4 — minimo del braccio e repair loop, SPB-11

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-repair-loop-results`
- Role: `research`
- Parent: [SPB-11](../tickets/solo-pi-jev-luna-pilot/11-benchmark-minimum-arm.md)

## Cella r4, versione osservata
Runtime SPB-10 `10b989a4328f9d2e9e82e0d35e077b52f472e408`; Luna medium, PID30376,
session01a0fd56-8749-75b8-8e64-5a4debcc71ac, singolo processo, chiuso exit0.
221.234s. Fonte: `C:/Users/CGS03/dbench-private/results/spj-luna-corrected-l4-4/cell/cell.json`.
R1 tentata, human-gated/failures0; R2-R4 dependency-blocked e non tentate. Candidato e
consegnato non accettati dall'oracle. 0/4 consegne, NON quattro fallimenti del modello.

## Difetto osservato e successiva riparazione
Public `python dev.py test` exit2: errori TypeScript nel nuovo Counter. Review contiene
blocker concreto e finding su directory `tests`; parser mantiene findings parziali ma stato
unparsed. La precedenza review-format arresta tutto senza turno fix nonostante i test falliti.
SPB-12 ripara solo questa precedenza e chiarisce marker file, senza cambiare parser/test/oracle.
RED human-gated0, GREEN failed3/fix contro green-test gate0; 32 test locali frozen, port
sostituiti. Questi NON aggiornano lo score o il runtime della r4: la prova resta archiviata.
Nessun Jev/judge esercitato nella r4. Il retest ha nuova versione/identità, separata:
[SPB-13 r5](solo-pi-jev-luna-repair-loop-r5-results.md).

## Validità e costi
Task/seed/suite/oracle/modello/SDK/immagini invariati tra r2/r4/r5 verificati per hash.
Braccio/politica review-fix diversi: niente pooling, ricalcolo o confronto causale paired.
La r4 costa incrementalmente $0.007402180 SDK sperimentali; costi operatore sono cumulativi
nel budget originale, non zero. Contabilità finale del goal nel report r5; fattura/FX finale
non disponibili. Nessun hidden feedback, delivery/installazione/delega o PASS di release.

```
