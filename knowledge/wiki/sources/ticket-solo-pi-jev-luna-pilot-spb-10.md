---
type: source
title: "SPB-10 — Rinnovare capacità e validare prima del launch"
identity_key: ticket:solo-pi-jev-luna-pilot/SPB-10
identity_strength: stable
source_path: docs/tickets/solo-pi-jev-luna-pilot/10-renew-launch-admission.md
source_digest: sha256:ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPB-10 — Rinnovare capacità e validare prima del launch

Compiled from `docs/tickets/solo-pi-jev-luna-pilot/10-renew-launch-admission.md`. Identity is `ticket:solo-pi-jev-luna-pilot/SPB-10`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-solo-pi-jev-launch-admission]]
- Blocked by: [[sources/ticket-solo-pi-jev-luna-pilot-spb-08]] — `ticket:solo-pi-jev-luna-pilot/SPB-08`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-solo-pi-jev-luna-pilot-spb-10.md","payload_bytes":2264,"payload_sha256":"ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32"}],"payload_bytes":2264,"payload_sha256":"ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32","schema":1,"source_digest":"sha256:ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-10","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2264,"payload_sha256":"ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32","schema":1,"source_digest":"sha256:ffea4b9b8e0680a01766a3046993e21ced627a5b1bbb5474c14c19b8eaaa7b32","source_identity":"ticket:solo-pi-jev-luna-pilot/SPB-10"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPB-10"
execution_mode: AFK
blocked_by:
  - "SPB-08"
---

# SPB-10 — Rinnovare capacità e validare prima del launch

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-10`
- Role: `ticket`
- Parent: [Launch admission](../../specs/solo-pi-jev-launch-admission.md)

## Parent Spec
[Launch admission](../../specs/solo-pi-jev-launch-admission.md).

## What to Build
API Budget per ammissione non avviante e rinnovo attestato di un solo prossimo lancio,
con consumo storico/fondi/autorità invariati. Il caller successivo usa la API, non raw ledger edits.

## Acceptance Criteria
- [ ] admit_launch rileva limite consumato prima della dichiarazione ready; launch riusa stessi guard senza spawn o incremento quando gated.
- [ ] renew_launch_capacity human:user/ref registra capacità per un solo prossimo launch, idempotente e riapribile; conserva autorità originale, consumi/charges/costi/gate e fondi.
- [ ] Invalid actor/ref, permessi negati, inflight/gate, costo ignoto o exhausted funds non vengono scavalcati dal rinnovo.
- [ ] Scope/ruoli/argv/soglie/cap finanziario invariati; SPB-09 gate e tutti gli storici preservati, nessun nuovo score o modello nei test.
- [ ] RED/GREEN, regressioni mirate e frozen review/QA/audit inline shared-context; nessun runner/delega/delivery/installazione.

## Frontier
Ready: SPB-08 handoff completo; SPB-09 è evidenza admission-gated, non dipendenza completa.
Nuovo mandato umano esplicito di benchmark minimo, fix/riprova del braccio, budget originale.

## Step-by-Step Implementation Plan
1. Canonical admission, record prior gate, RED del rinnovo mancante.
2. Minimal owner API and non-avviante preflight, causal contrasts and targeted Budget checks.
3. Frozen inline review/QA/handoff; caller live successivo separato dal ticket repair.

## Testing Plan
Actual state/file and fake ChainSession boundary, no native provider/hidden/network.
Preserve all attempts. Required release profile/exact-head CI/live trial separate.

## Out of Scope
Financial grant edits, budget/counter resets, actual launch in this repair, candidate product
fixes, parser/question/threshold changes, new model/scenario, runner/scheduler/subagent,
publication/commit/push/merge/install/reload/wiki sync.

```
