---
type: source
title: "Ticket Driver — le cache degli strumenti del revisore diretto"
identity_key: spec:ticket-driver-reviewer-tool-caches
identity_strength: stable
source_path: docs/specs/ticket-driver-reviewer-tool-caches.md
source_digest: sha256:a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-01
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Driver — le cache degli strumenti del revisore diretto

Compiled from `docs/specs/ticket-driver-reviewer-tool-caches.md`. Identity is `spec:ticket-driver-reviewer-tool-caches`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-01** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-reviewer-tool-caches-tdc-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/spec-ticket-driver-reviewer-tool-caches.md","payload_bytes":2271,"payload_sha256":"a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5"}],"payload_bytes":2271,"payload_sha256":"a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5","schema":1,"source_digest":"sha256:a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5","source_identity":"spec:ticket-driver-reviewer-tool-caches","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2271,"payload_sha256":"a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5","schema":1,"source_digest":"sha256:a274a1ac2a75764b0c6ed9b539c7a099f67d97568158c58b16561a7b7d8ebdd5","source_identity":"spec:ticket-driver-reviewer-tool-caches"} -->
```markdown
# Ticket Driver — le cache degli strumenti del revisore diretto

## Artifact Graph
- Artifact ID: `spec:ticket-driver-reviewer-tool-caches`
- Role: `spec`
- Standalone: true

### Children
- [TDC-01](../tickets/ticket-driver-reviewer-tool-caches/done/01-tool-caches-are-not-writes.md)

## Osservazione e causa
Nella misura con Opus 5.5 (lotto `dbh-opus`, catena da 12) un run di c3a su `sql-engine` si è
fermato al cancello con `directed reviewer wrote outside artifact`. Il giudizio controfattuale
del candidato fermo lo accetta.

Il revisore diretto lavora in una cartella scratch nuova, e deve scrivere solo
`.ticket-driver/review-directed.md`: ogni altro percorso nella scratch ferma il run. Qui il
revisore ha lanciato pytest dalla sua cartella di lavoro, e pytest ha lasciato `.pytest_cache`
nella scratch. Il controllo l'ha contata come una scrittura del revisore. Lo stesso accade a
`__pycache__` quando il revisore importa un modulo che si trova nella scratch.

## Comportamento richiesto
- Le cartelle di cache degli strumenti di test e di analisi (`__pycache__`, `.pytest_cache`,
  `.mypy_cache`, `.ruff_cache`, `.hypothesis`) e il loro contenuto non sono scritture del
  revisore. Conta il nome di una cartella: un file con lo stesso nome resta una scrittura.
- Il ledger del run registra le cache ignorate (`directed-tool-caches`), con i percorsi di primo
  livello.
- Ogni altro percorso nella scratch ferma il run come oggi, anche accanto a una cache. L'evento
  `directed-artifact-violation` elenca solo quei percorsi.
- Invariati: l'impronta del prodotto, che resta il controllo delle scritture con percorso
  assoluto, e tutto il resto del revisore diretto.

## Verifica
Test prima della correzione in `ticket-driver/tests/test_c3.py`: un revisore che lascia solo
cache integra; uno che lascia cache e un file proprio resta fermo, con il solo file
nell'evento. Il test esistente sulla scrittura relativa nel prodotto resta verde. Poi l'intera
suite di `ticket-driver`. Le copie del driver del lotto `dbh-opus` non cambiano: la correzione
vale da una nuova `prepare-drivers`.

## Fuori ambito
- Impedire al revisore di eseguire i test, o cambiare la sua cartella di lavoro.
- Le cache nella worktree del candidato, che non passano da questo controllo.

```
