---
type: source
title: "DBH-44 — I container avviati dall'agente non sopravvivono alla richiesta"
identity_key: ticket:delivery-bench-hard/DBH-44
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/44-stray-agent-containers.md
source_digest: sha256:3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-09
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# DBH-44 — I container avviati dall'agente non sopravvivono alla richiesta

Compiled from `docs/tickets/delivery-bench-hard/44-stray-agent-containers.md`. Identity is `ticket:delivery-bench-hard/DBH-44`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-09** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-44.md","payload_bytes":2599,"payload_sha256":"3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f"}],"payload_bytes":2599,"payload_sha256":"3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f","schema":1,"source_digest":"sha256:3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f","source_identity":"ticket:delivery-bench-hard/DBH-44","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2599,"payload_sha256":"3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f","schema":1,"source_digest":"sha256:3348a5d0541826e25231dc32eeea73e4962b62e30d0c2f09356e700597ef271f","source_identity":"ticket:delivery-bench-hard/DBH-44"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-44"
execution_mode: AFK
blocked_by: []
---

# DBH-44 — I container avviati dall'agente non sopravvivono alla richiesta

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:44`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md): difetto del banco,
come DBH-10..19.

## What to Build
Il 2026-10-08 la macchina era satura: 14 container `gcc:14` avviati dagli agenti stessi (13 da
`dbh-crew`, celle lua-vm con `lua continue.lua` in loop infinito o `all.lua` sotto ASan; 1 da
`dbh-chain12`, una compilazione bloccata) giravano da 15-28 ore, molto dopo la fine delle loro
celle. Sono stati rimossi a mano.

Alla fine di ogni tentativo, prima del giudice e qualunque sia l'esito (anche timeout), il runner
rimuove ogni container, in esecuzione o fermo, che monta in bind qualcosa dentro la cartella del
braccio, e li registra nel tentativo (`stray_containers`). I container del giudice
(`dbench-judge-*`) e quelli di altre celle restano. Senza Docker, o se non risponde, non rimuove
nulla e non afferma nulla.

## Acceptance Criteria
- [ ] Ogni grafia del percorso che il client Docker registra (`C:\x`, `C:/x`, `/c/x`, `/mnt/c/x`,
      `/run/desktop/mnt/host/c/x`) dentro la cartella del braccio porta alla rimozione; una
      cartella sorella, un'altra cella, il giudice e i volumi nominati no.
- [ ] Ogni tentativo registra `stray_containers`, e la rimozione avviene prima del giudice.
- [ ] La suite `test_runner` non parla mai con il Docker dell'host.
- [ ] Prova dal vivo con container `gcc:14` veri.

## Frontier
Pronto.

## Gates
- **Attempt:** una PR su `agent-skills` con CI verde. **Budget, tempo, tentativi:** nessuno fissato.
- **Approvals:** l'agente fa il merge con CI verde (regola dei ticket DBH).
- **Exact version:** nessuna.
- **Existing blocks searched:** nessun lotto in corso; il prossimo (`dbh-crew3`) userà questa
  correzione.

## Step-by-Step Implementation Plan
1. `remove_stray_containers` in `runner.py` (`docker ps -aq`, `inspect`, `rm -f`), chiamata in
   `run_attempt` dopo il comando dell'agente.
2. Test con un Docker finto; la suite spegne Docker per tutti gli altri test.
3. Prova dal vivo; README.

## Testing Plan
- `python -B -m unittest test_runner`; prova dal vivo con due container dentro e uno fuori.

## Out of Scope
- Container senza bind mount nella cartella del braccio (non attribuibili a una cella).
- Un tetto di tempo sui `docker run` degli agenti.

```
