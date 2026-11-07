---
type: source
title: "SPL-02 — Misurare Superpowers e controlli contemporanei con Luna medium"
identity_key: ticket:delivery-bench-superpowers-luna/SPL-02
identity_strength: stable
source_path: docs/tickets/delivery-bench-superpowers-luna/02-measure-and-report.md
source_digest: sha256:1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SPL-02 — Misurare Superpowers e controlli contemporanei con Luna medium

Compiled from `docs/tickets/delivery-bench-superpowers-luna/02-measure-and-report.md`. Identity is `ticket:delivery-bench-superpowers-luna/SPL-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-superpowers-luna]]
- Blocked by: [[sources/ticket-delivery-bench-superpowers-luna-spl-01]] — `ticket:delivery-bench-superpowers-luna/SPL-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-superpowers-luna-spl-02.md","payload_bytes":3505,"payload_sha256":"1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5"}],"payload_bytes":3505,"payload_sha256":"1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5","schema":1,"source_digest":"sha256:1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3505,"payload_sha256":"1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5","schema":1,"source_digest":"sha256:1ca51fe1016bd8c7557efbf513d556134ed420f7e3c8afb00ad3af254f4f27a5","source_identity":"ticket:delivery-bench-superpowers-luna/SPL-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SPL-02"
execution_mode: HITL
blocked_by:
  - "SPL-01"
---

# SPL-02 — Misurare Superpowers e controlli contemporanei con Luna medium

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-superpowers-luna:SPL-02`
- Role: `ticket`
- Parent: [delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md)

## Produces
- [Risultati del confronto](../../research/delivery-bench-superpowers-luna-results.md)

## Parent Spec
[delivery-bench-superpowers-luna.md](../../specs/delivery-bench-superpowers-luna.md),
Goal and decisions, Implementation slices, Verification, Gates.

## What to Build
Nuovo lotto con bare, Pi-tools, Pi-full e Pi-superpowers: Luna medium, scenari lua-vm,
sql-engine e crdt-yjs, 4 richieste, 3 ripetizioni. Report separato dai lotti storici.

## Acceptance Criteria
- [ ] Scenari privati e provenienza recuperati, senza contaminare i contesti dei partecipanti.
- [ ] Snapshot locale Superpowers, strumenti e skill personali congelati prima del lotto.
- [ ] Accesso Luna e Docker verificati; preflight passato sui quattro bracci.
- [ ] Autorità del lotto attribuita alla conferma dell'utente, con scope e stima dei costi espliciti.
- [ ] 144 posizioni di richiesta giudicate oppure fallimenti/gate conservati senza inventare punteggi.
- [ ] Report per braccio/scenario con correttezza, robustezza, regressioni, costi e tempi; confronto appaiato contemporaneo.

## Frontier
Dependency-blocked da SPL-01; input live mancante: percorso/accesso agli scenari privati.
`C:/Users/CGS03/dbench-private` e `C:/Users/rdpuser/dbench-private` non sono presenti.
Non ricostruire l'oracolo dai report e non sostituire gli scenari con altri problemi.

## Gates
- Attempt: una misura nuova completa attraverso il report, distinta da SPL-01.
- Budget per attempt: nessun limite impostato dall'utente; costi correnti stimati prima del live,
  uso soltanto dell'accesso OpenAI richiesto; sconosciuto non significa zero.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato; nessun retry implicito dell'intero lotto.
- Approvals: conferma «si facciamo cosi» per il confronto Luna medium; non Anthropic/Jev,
  delegazione, installazione globale, push/merge o pubblicazione.
- Exact version: `openai-codex/gpt-6-luna`, thinking `medium`; congelare le risorse prima dell'avvio.
- Existing blocks searched: specifiche/report/runner e percorsi locali; scenari privati assenti.
  Accesso di generazione Luna e Docker non provati per il lotto. Servono dati/ambiente, non
  un nuovo consenso sul modello. Non iniziare il preflight a pagamento finché gli input mancano.

## Step-by-Step Implementation Plan
1. Ottenere il percorso esistente degli scenari e validare la provenienza, senza modificarli.
2. Preparare lo snapshot upstream e la stima; eseguire il preflight e legare l'autorità del lotto.
3. Eseguire soltanto il protocollo concordato con il runner di benchmark esistente.
4. Scrivere il report con evidenze attribuibili e limiti; nessuna pubblicazione implicita.

## Testing Plan
Controlli live esplicitamente separati dai test offline; mantenere fallimenti, retry,
compaction, costi mancanti e richieste non giudicate. Un giudice generativo Anthropic non fa
parte della misura. Per affermazioni live usare il contratto Verification Audit.

## Out of Scope
- Cambiare scenari, rigiocare lotti storici, estendere a catene da 12 o altri modelli.
- Dedurre accesso operativo da una voce nel registro locale.

```
