---
type: source
title: "EG-02 — Budget e tempo per tentativo, nessun legame di versione"
identity_key: ticket:explicit-gates/EG-02
identity_strength: stable
source_path: docs/tickets/explicit-gates/done/02-per-attempt-budget-no-version-binding.md
source_digest: sha256:77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed: 2026-10-06
disposition_changed_provenance: git-rename
---

# EG-02 — Budget e tempo per tentativo, nessun legame di versione

Compiled from `docs/tickets/explicit-gates/done/02-per-attempt-budget-no-version-binding.md`. Identity is `ticket:explicit-gates/EG-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **2026-10-06** via `git-rename`

## Graph

- Parent source: [[sources/artifact-explicit-gates]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-explicit-gates-eg-02.md","payload_bytes":2616,"payload_sha256":"77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689"}],"payload_bytes":2616,"payload_sha256":"77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689","schema":1,"source_digest":"sha256:77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689","source_identity":"ticket:explicit-gates/EG-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2616,"payload_sha256":"77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689","schema":1,"source_digest":"sha256:77847424be2c300ef0a06ccedf878b3312ccc04722832a5bddab7eab4922a689","source_identity":"ticket:explicit-gates/EG-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "EG-02"
execution_mode: AFK
blocked_by: []
---

# EG-02 — Budget e tempo per tentativo, nessun legame di versione

## Artifact Graph
- Artifact ID: `ticket:explicit-gates:02`
- Role: `ticket`
- Parent: [explicit-gates.md](../../specs/explicit-gates.md)

## Parent Spec
[explicit-gates.md](../../specs/explicit-gates.md), Decisioni 2 e 3.

## What to Build
Le skill trattano budget e tempo per tentativo, come li definisce `## Gates`:
- un nuovo tentativo parte con budget e tempo pieni;
- i tentativi precedenti restano registrati, ma non lo consumano.

Un'autorizzazione copre il lavoro, non una versione. Un nuovo candidato, release, head o
sorgente non è mai, da solo, un motivo per fermarsi o richiedere il consenso. È un limite solo
una versione nominata dall'utente.

## Acceptance Criteria
- [ ] Nessuna di queste skill richiede più un consumo cumulativo tra i tentativi né un limite di
      versione non chiesto: `execute-ticket/references/verification-cost.md`,
      `execute-ticket/references/skills-only.md`, `ticket-autopilot/references/technical-gates.md`,
      `execute-ticket/SKILL.md`, `qa-test-plan/SKILL.md`.
- [ ] Le voci 8 e 11 della policy obbligatoria (`extensions/mandatory-agent-skills.ts`) dicono lo
      stesso; `extensions/mandatory-agent-skills.test.ts` controlla il testo nuovo.
- [ ] Restano invariate:
  - la selezione causale delle verifiche;
  - la CI sulla head esatta;
  - la conservazione dei tentativi falliti;
  - lo stop su scope cambiato, revoca, budget del tentativo esaurito o tentativi massimi
    raggiunti.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa esterna, nessun limite di tempo o di tentativi, nessuna versione
esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`. Blocco esistente: le asserzioni
sul testo attuale in `extensions/mandatory-agent-skills.test.ts`.

## Step-by-Step Implementation Plan
1. `verification-cost.md`: sostituire il conto cumulativo con un conto per tentativo.
2. `skills-only.md`, passo 4: i gate della spec, un nuovo tentativo con budget pieno, nessun
   legame di versione.
3. `technical-gates.md`: la riga del mandato, il paragrafo sul limite di versione, i passi 2 e 4.
4. `execute-ticket/SKILL.md` e `qa-test-plan/SKILL.md`: allineare le diciture.
5. Le voci 8 e 11 di `mandatory-agent-skills.ts`, più i test.

## Testing Plan
- `node --test extensions/mandatory-agent-skills.test.ts`
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`
- `npm run -s lint`

## Out of Scope
- Il codice Python del runner, `goal.ts`, `to-spec` e `to-tickets` (EG-01).

```
