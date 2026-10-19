---
type: source
title: "Gate espliciti, per tentativo, senza legami di versione"
identity_key: artifact:explicit-gates-wayfinder
identity_strength: stable
source_path: docs/specs/explicit-gates-wayfinder.md
source_digest: sha256:a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-06
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Gate espliciti, per tentativo, senza legami di versione

Compiled from `docs/specs/explicit-gates-wayfinder.md`. Identity is `artifact:explicit-gates-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/artifact-explicit-gates]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-explicit-gates-wayfinder.md","payload_bytes":1971,"payload_sha256":"a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122"}],"payload_bytes":1971,"payload_sha256":"a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122","schema":1,"source_digest":"sha256:a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122","source_identity":"artifact:explicit-gates-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | 8: Out of Scope |
| decisions | 6: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1971,"payload_sha256":"a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122","schema":1,"source_digest":"sha256:a44c034c9016f86e9ebdff64cb9bde67da5d041aaefa1714fa7ea7c9242d0122","source_identity":"artifact:explicit-gates-wayfinder"} -->
```markdown
# Gate espliciti, per tentativo, senza legami di versione

## Artifact Graph
- Artifact ID: `artifact:explicit-gates-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [Spec: gate espliciti](explicit-gates.md)

## Type
Wayfinding spec

## Status
Done

## Destination
Le skill chiedono all'utente ogni gate (cos'è un tentativo, budget e tempo per tentativo,
tentativi massimi, approvazioni, blocchi già nel codice) mentre si scrivono spec e ticket, e lo
scrivono in una sezione `## Gates`. Budget e tempo valgono per tentativo. Un'autorizzazione copre
il lavoro, non una versione.

## Decisions So Far
- 2026-10-06, risposte dell'utente al giro di grilling, confermate con "Ok":
  - D1: tentativo, budget e tempo si decidono a priori e vanno chiesti;
  - D2: nessun legame di versione, salvo una versione nominata dall'utente;
  - D3: la sezione `## Gates` va sia nella spec sia in ogni ticket;
  - D4: `/goal` (`goal.ts`) non si tocca.
- Origine: una sessione Pi su un altro progetto ha girato 65 turni in 17 ore. Una finestra
  autorizzata era legata alla versione della release e il budget era cumulativo tra i
  tentativi; il blocco è emerso solo dopo averla avviata. Registrato in [la spec](explicit-gates.md).

## Not Yet Specified
- Nessuno.

## Out of Scope
- Il gateway del progetto nations-league, che sta su un'altra macchina.
- `goal.ts` (D4).
- Il codice Python del runner `ticket-autopilot`: Autopilot è sospeso.

## Frontier / Blocking Edges
- Nessuno: EG-01 (#433) e EG-02 completati.

## Ticket Plan
- EG-01, task, AFK, nessun blocco: chiedere e scrivere `## Gates` in `to-spec` e `to-tickets`.
- EG-02, task, AFK, nessun blocco: budget e tempo per tentativo, nessun legame di versione, in
  `verification-cost`, `skills-only`, `technical-gates`, `execute-ticket`, `qa-test-plan` e
  nella policy obbligatoria.

## Next Review
- Dopo il merge dei due ticket: sincronizzare il pin di `pi-personal-config`, a lotto
  `dbh-luna3e` finito.

```
