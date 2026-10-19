---
type: source
title: "Findings non-blocker — correggere l'ammissione della review"
identity_key: artifact:solo-pi-jev-review-admission
identity_strength: stable
source_path: docs/specs/solo-pi-jev-review-admission.md
source_digest: sha256:d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Findings non-blocker — correggere l'ammissione della review

Compiled from `docs/specs/solo-pi-jev-review-admission.md`. Identity is `artifact:solo-pi-jev-review-admission`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-solo-pi-jev-luna-pilot-spb-08]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-solo-pi-jev-review-admission.md","payload_bytes":3101,"payload_sha256":"d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304"}],"payload_bytes":3101,"payload_sha256":"d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304","schema":1,"source_digest":"sha256:d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304","source_identity":"artifact:solo-pi-jev-review-admission","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3101,"payload_sha256":"d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304","schema":1,"source_digest":"sha256:d967f9e9df9af4920a8a8a6ba61494063ed97105e0d0b75364689c849656d304","source_identity":"artifact:solo-pi-jev-review-admission"} -->
```markdown
# Findings non-blocker — correggere l'ammissione della review

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-review-admission`
- Role: `spec`
- Standalone: true

### Children
- [SPB-08](../tickets/solo-pi-jev-luna-pilot/08-adjudicate-review-findings.md)

## Root cause and authority
Il 2026-10-02 l'utente chiede di correggere il braccio, non il candidato storico né di
rilanciare. SPB-07 conserva una review parsata con uno should-fix su YCounter.value prima
dell'integrazione: il controller usa `sufficient=passed and clean`, poi conta quality-failure
senza una decisione semantica. Anche un nit avrebbe lo stesso veto. È una deviazione certa
dal [Review Contract, punto 6](solo-pi-jev-review-decision.md): findings sono claims del
modello, blocking/coverage passano alle domande tipate; nit non equivale a blocker.
Non è dimostrato che la singola segnalazione YCounter sia falsa: il contratto pubblico parla
anche di incremento/value e conservazione prima dell'integrazione. L'espressione concatenata
citata dal review non è una riproduzione: increment() nel candidato non restituisce this.
Nessun hidden/oracle consultato per questa diagnosi e nessun nuovo score inferito.

## Target and design
Module: ChainController, Interface invariata run_ticket/DecisionEngine.decide. Seam già
accettata ai port Pi/Jev/judge; Git e test pubblici reali nei fixture, solo i port sono fake.
Test verdi + review parsata senza blocker esplicito rendono disponibile il contesto per la
question coverage esistente. La domanda adjudica anche le segnalazioni non-blocker contro
requisiti, diff e prove: YES completa localmente, NO è quality-failure, uncertain è gate
con analisi condivisa e nessuna failure aggiunta. Should-fix/nit restano nei findings e
nella prosa completa; non sono rinominati clean né scartati. Blocchi espliciti e test falliti
rimangono veto; unparsed conserva il gate immediato. Nessuna approvazione da sola severity.
Chiarire istruzioni coverage/review: niente requisiti extra, suggerimenti opzionali distinti
da violazioni concrete. Riutilizzare la cascata esistente; nessun nuovo protocollo, port,
permesso, question extra, sessione o retry. Un solo giudizio globale evita chiamate duplicate.

## Invariants, alternatives and verification
Restano CandidateRef/diff/receipt completi, bound 65536, policy e budget cumulativi, negative
non bypassabili, massimo 3 failure, readonly e dipendenze. Evitare sia il veto di ogni finding
sia l'approvazione automatica di ogni should-fix: la differenza deve essere causata dalla
risposta semantica osservata. Non modificare parser o file storici/prep/source/candidate.
RED/GREEN attraverso run_ticket: finding non-blocker + YES può completare; stessa forma con
NO fallisce; uncertain/permission/bound non diventano difetti del prodotto; explicit blocker
non è superato da fake YES. Nit, test falliti, unparsed, cascade e dependency restano coperti.
Regressioni mirate controller/repair e adapter prompt; non tutta la suite o oracle storici.
Prova live di Jev/qualità, release profile/exact-head CI/delivery restano gate separati.

```
