---
type: source
title: "DBH-38 — Strumento ask_user e utente simulato nel runner"
identity_key: ticket:delivery-bench-hard/DBH-38
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/38-ask-user-simulator.md
source_digest: sha256:50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-07
created_provenance: git-commit
disposition_changed: 2026-10-07
disposition_changed_provenance: git-rename
---

# DBH-38 — Strumento ask_user e utente simulato nel runner

Compiled from `docs/tickets/delivery-bench-hard/done/38-ask-user-simulator.md`. Identity is `ticket:delivery-bench-hard/DBH-38`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-07** via `git-commit`
- Disposition changed: **2026-10-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-vague-requests]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-38.md","payload_bytes":3452,"payload_sha256":"50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53"}],"payload_bytes":3452,"payload_sha256":"50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53","schema":1,"source_digest":"sha256:50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53","source_identity":"ticket:delivery-bench-hard/DBH-38","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3452,"payload_sha256":"50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53","schema":1,"source_digest":"sha256:50588e2c0c307c4e77f35fc80aef903e829ddbec31b2c8d0c582364949157f53","source_identity":"ticket:delivery-bench-hard/DBH-38"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-38"
execution_mode: AFK
blocked_by: []
---

# DBH-38 — Strumento ask_user e utente simulato nel runner

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:38`
- Role: `ticket`
- Parent: [delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md), Target behavior 2–5, Failure modes e Verification.

## What to Build
Un'estensione Pi `ask_user` caricata nei bracci di un lotto con richieste vaghe, e nel runner
l'utente simulato: `gpt-6-sol` in una sessione separata, con istruzioni fisse e il brief preciso
(richiesta corrente più le precedenti della catena), senza il nome del braccio. Cache per
scenario e richiesta delle domande normalizzate; limite di 10 domande per richiesta; rifiuto
delle risposte con nomi dei test nascosti o canary; domande, risposte e costo del simulato nel
tentativo e nel ledger, separati dal costo del braccio. `init-lot` accetta la variante vaga e
fissa gli sha256 delle richieste vaghe; il preflight fa una domanda vera.

## Acceptance Criteria
- [x] La stessa domanda normalizzata riceve la stessa risposta in bracci e ripetizioni diversi,
      senza una nuova chiamata.
- [x] L'undicesima domanda riceve il messaggio di limite senza chiamare il simulato.
- [x] Il simulato non riceve mai il nome del braccio né il codice dell'agente.
- [x] Una risposta con un nome di test nascosto o il canary viene rifiutata e registrata.
- [x] Il costo del simulato è separato da quello del braccio nel ledger e nel report.
- [x] I lotti con richieste precise funzionano come prima; suite completa del runner OK e CI 8/8.
- [x] Preflight senza lotto dei tre bracci ok, con almeno una domanda reale.

## Evidence
- `benchmarks/delivery-bench/ask_user/index.ts` (strumento `ask_user`, nessun import),
  `simulator.py` (utente simulato, cache con lock, limite 10, filtro, ritentativi) e in
  `runner.py` `init-lot --vague`, `preflight --vague`, `ask_user_setup`, `forbidden_names`,
  la classe `infra:simulator`; `profile_report.py` ha la sezione delle domande.
- Test offline: `test_simulator.py` (6) e `VagueLotTests` (7) più il preflight vago in
  `test_runner.py`; suite `test_runner test_simulator test_profile_report` 82 test OK.
- Preflight reale senza lotto `--vague` di `pi-tools`, `pi-full`, `bare-goal` con
  `gpt-6-luna` medium: ok, una domanda reale a `gpt-6-sol` per braccio (circa 0,0006 $ ognuna).
- Prova sul brief reale di `lua-vm` 1-3: il simulato dà il messaggio d'errore esatto, non
  dice come implementare («Eso lo decides tú») e risponde «No lo sé, decide tú.» a test
  nascosti e a domande fuori dal brief.

## Frontier
Fatto.

## Gates
Come la spec: una PR con CI 8/8 e merge con `--match-head-commit`; nessun tetto di spesa;
24 ore per tentativo, al massimo 2 tentativi. Durante `dbh-chain12` si lavora in un worktree,
senza aggiornare il checkout principale.

## Step-by-Step Implementation Plan
1. Test rossi per cache, limite, cecità sul braccio, filtro e costo separato.
2. Estensione `ask_user` che chiama il runner attraverso un file di scambio o un comando locale.
3. Simulato, cache e registrazione nel runner; variante vaga in `init-lot` e preflight.

## Testing Plan
- Unit test in `test_runner.py`; suite completa; preflight reale.

## Out of Scope
- Giudicare la qualità delle domande.

```
