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
