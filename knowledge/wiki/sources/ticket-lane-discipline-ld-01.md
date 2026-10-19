---
type: source
title: "LD-01 — Blocchi citati e percorso diretto misurato"
identity_key: ticket:lane-discipline/LD-01
identity_strength: stable
source_path: docs/tickets/lane-discipline/done/01-cited-blocks-and-measured-direct-lane.md
source_digest: sha256:98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# LD-01 — Blocchi citati e percorso diretto misurato

Compiled from `docs/tickets/lane-discipline/done/01-cited-blocks-and-measured-direct-lane.md`. Identity is `ticket:lane-discipline/LD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-lane-discipline]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-lane-discipline-ld-01.md","payload_bytes":2035,"payload_sha256":"98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0"}],"payload_bytes":2035,"payload_sha256":"98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0","schema":1,"source_digest":"sha256:98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0","source_identity":"ticket:lane-discipline/LD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2035,"payload_sha256":"98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0","schema":1,"source_digest":"sha256:98f94c72b651bf788f8b9db667be10ea44ad4f5fab2aedf2d9a9432c1dc814b0","source_identity":"ticket:lane-discipline/LD-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "LD-01"
execution_mode: AFK
blocked_by: []
---

# LD-01 — Blocchi citati e percorso diretto misurato

## Artifact Graph
- Artifact ID: `ticket:lane-discipline:01`
- Role: `ticket`
- Parent: [lane-discipline.md](../../../specs/lane-discipline.md)

## Parent Spec
[lane-discipline.md](../../../specs/lane-discipline.md), Decisioni 1 e 2.

## What to Build
La policy obbligatoria e la mappa di `ask-skills` dicono:
- prima di fermarsi per un blocco, l'agente ne cita la fonte; quello che non sa citare non è
  un gate; una decisione mancante si chiede una volta, senza ripeterla a un loop;
- il percorso diretto conta anche i test, si misura prima del commit, passa a skills-only
  quando sfora e non vale mai per soldi, autenticazione e permessi, cancellazione di dati.

## Acceptance Criteria
- [x] La voce 2 di `extensions/mandatory-agent-skills.ts` dice: test compresi, misura con
      `git diff --stat` prima del commit, nessun commit come diretto oltre i limiti, passaggio
      a `execute-ticket`, esclusione di soldi, autenticazione e permessi, cancellazione di dati.
- [x] La voce 8 contiene la regola del blocco citato.
- [x] `ask-skills/SKILL.md` e `README.md` descrivono il percorso diretto allo stesso modo.
- [x] `extensions/mandatory-agent-skills.test.ts` controlla le frasi nuove; le asserzioni
      esistenti restano vere.

## Frontier
Ready.

## Gates
Come la spec: nessuna spesa a pagamento, nessun limite di tempo o di tentativi, nessuna
versione esatta. Approvazione: merge con CI 8/8 e `--match-head-commit`, poi pin,
`update:personal` e reload.

## Step-by-Step Implementation Plan
1. Voce 2 e voce 8 di `mandatory-agent-skills.ts`.
2. Le frasi nuove nei test.
3. `ask-skills/SKILL.md` e `README.md`.

## Testing Plan
- `node --test extensions/mandatory-agent-skills.test.ts`
- `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py ticket-autopilot/tests/test_context_budget.py -q`
- `npm run -s lint`

## Out of Scope
- `goal.ts`, Autopilot, `OPERATING-DEFAULTS.md`.

```
