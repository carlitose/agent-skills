---
type: source
title: "EG-01 — `## Gates` chiesti e scritti in spec e ticket"
identity_key: ticket:explicit-gates/EG-01
identity_strength: stable
source_path: docs/tickets/explicit-gates/done/01-gates-in-specs-and-tickets.md
source_digest: sha256:06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# EG-01 — `## Gates` chiesti e scritti in spec e ticket

Compiled from `docs/tickets/explicit-gates/done/01-gates-in-specs-and-tickets.md`. Identity is `ticket:explicit-gates/EG-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-explicit-gates]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-explicit-gates-eg-01.md","payload_bytes":2022,"payload_sha256":"06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210"}],"payload_bytes":2022,"payload_sha256":"06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210","schema":1,"source_digest":"sha256:06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210","source_identity":"ticket:explicit-gates/EG-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2022,"payload_sha256":"06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210","schema":1,"source_digest":"sha256:06be2f973920fbf147da039658c1ab984a8a25c8d6cdf83e59bdef21075db210","source_identity":"ticket:explicit-gates/EG-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "EG-01"
execution_mode: AFK
blocked_by: []
---

# EG-01 — `## Gates` chiesti e scritti in spec e ticket

## Artifact Graph
- Artifact ID: `ticket:explicit-gates:01`
- Role: `ticket`
- Parent: [explicit-gates.md](../../specs/explicit-gates.md)

## Parent Spec
[explicit-gates.md](../../specs/explicit-gates.md), Decisione 1.

## What to Build
`to-spec` e `to-tickets` chiedono all'utente, in un solo giro e mentre scrivono, i gate del
lavoro, e li scrivono in una sezione `## Gates` della spec e di ogni ticket:
- tentativo;
- budget e tempo per tentativo;
- tentativi massimi;
- approvazioni;
- eventuale versione esatta;
- blocchi già nel codice, cercati prima.

Un gate senza risposta resta `open` e il ticket ha la frontiera "decisione umana richiesta".

## Acceptance Criteria
- [ ] `to-spec/SKILL.md` richiede la sezione `## Gates` in ogni spec, con i sei elementi, la
      ricerca dei blocchi esistenti e la domanda all'utente in un solo giro.
- [ ] Il modello del corpo ticket in `to-tickets/SKILL.md` contiene `## Gates`, che riprende i
      gate della spec applicabili più quelli propri del ticket. Un gate aperto rende la frontiera
      una decisione umana.
- [ ] `to-tickets/SKILL.md` resta entro il suo limite di 115 righe; `test_skill_graph.py` passa.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa esterna, nessun limite di tempo o di tentativi, nessuna versione
esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`. Blocco esistente: limite di 115
righe di `to-tickets/SKILL.md`.

## Step-by-Step Implementation Plan
1. `to-spec`: aggiungere la regola `## Gates` ai Defaults e una voce nei Quality checks.
2. `to-tickets`: aggiungere `## Gates` al corpo del ticket e una frase sul gate aperto, poi
   compattare altrove per restare entro le 115 righe.

## Testing Plan
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`
- `npm run -s lint`

## Out of Scope
- Budget per tentativo e legami di versione nelle altre skill (EG-02).

```
