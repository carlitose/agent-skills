---
type: source
title: "SPL-01 — Superpowers su Pi, isolato e verificabile offline"
identity_key: ticket:delivery-bench-superpowers-luna/SPL-01
identity_strength: stable
source_path: docs/tickets/delivery-bench-superpowers-luna/01-superpowers-arm.md
source_digest: sha256:6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPL-01 — Superpowers su Pi, isolato e verificabile offline

Compiled from `docs/tickets/delivery-bench-superpowers-luna/01-superpowers-arm.md`. Identity is `ticket:delivery-bench-superpowers-luna/SPL-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-superpowers-luna]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-superpowers-luna-spl-01.md","payload_bytes":3483,"payload_sha256":"6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945"}],"payload_bytes":3483,"payload_sha256":"6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945","schema":1,"source_digest":"sha256:6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3483,"payload_sha256":"6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945","schema":1,"source_digest":"sha256:6750a4a4231a01f3fb2883752be8148a522fc743d0b1dc312729afec810e9945","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPL-01"
execution_mode: AFK
blocked_by: []
---

# SPL-01 — Superpowers su Pi, isolato e verificabile offline

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-superpowers-luna:SPL-01`
- Role: `ticket`
- Parent: [delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md)

## Parent Spec
[delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md),
Target behavior 1–6, Non-goals and invariants, Verification, Gates.

## What to Build
Aggiungere `pi-superpowers` al runner e ai report esistenti: snapshot locale esplicito,
bootstrap upstream, soltanto le sue skill, strumenti e goal identici a Pi-tools.
L'implementazione non richiede scenari privati e non avvia modelli live.
Scope: `benchmarks/delivery-bench/{runner.py,superpowers_arm.py,profile_report.py,test_superpowers_arm.py,README.md}`,
la specifica/il collegamento nella mappa e questi due ticket. Nessun file estraneo.

## Acceptance Criteria
- [ ] CLI init-lot e preflight accettano lo snapshot solo con `pi-superpowers` e lo richiedono per quel braccio.
- [ ] Manifest, bootstrap e skill sono verificati e congelati; il drift blocca prima di avviare il partecipante.
- [ ] L'argv esclude le skill scoperte implicitamente e carica esplicitamente solo quelle Superpowers.
- [ ] Stessi tool e goal di Pi-tools, nessuna regola mandatory personale; bracci esistenti invariati.
- [ ] Preflight rifiuta skill mancanti/estranee e routing ask-skills; non inventa evidenza del bootstrap nel JSONL.
- [ ] Report e --arm-from includono il nuovo braccio, senza cambiare punteggi o conclusioni statistiche.
- [ ] Test offline, lint e profilo quick documentati; nessuna affermazione di risultato live o integrazione.

## Frontier
Ready per implementazione offline nel worktree isolato. La misura privata è SPL-02.

## Gates
- Attempt: implementazione attraverso handoff di SPL-01.
- Budget per attempt: nessun limite impostato; nessuna chiamata modello live in questo ticket.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato; conservare tutti gli esiti di verifica.
- Approvals: autorizzato il lavoro locale; nessuna delegazione, installazione globale, push/PR/merge o pubblicazione.
- Exact version: target della misura Luna medium; snapshot Superpowers legato al contenuto, nessun pin umano.
- Existing blocks searched: repo/runner/specifiche/configurazione; il checkout principale è sporco,
  quindi worktree isolato sulla base `e9510a53`. Gli scenari privati assenti non servono a questo ticket.

## Step-by-Step Implementation Plan
1. Ammettere candidato e grafo; testare il nuovo comportamento con fixture senza provider.
2. Implementare binding e isolamento del pacchetto, integrazione lotto/preflight/report.
3. Verificare regressioni causali e policy obbligatorie, semplificare dopo GREEN, review e QA inline.
4. Restituire handoff e gate live, senza finalizzazione Git/provider.

## Testing Plan
Nuovi test offline per binding, drift, argv, continuazione, preflight e report; test esistenti
ArmProfileTests/PreflightTests e suite delivery-bench; npm run lint e npm test quick.
Validare link locali e ticket nel candidato completo prima del QA costoso. La misura privata
non è un test offline e resta esplicitamente non eseguita.

## Out of Scope
- Installare Superpowers nell'istanza personale o lanciare il lotto live.
- Cambiare i lotti storici o la configurazione dei bracci esistenti.

```
