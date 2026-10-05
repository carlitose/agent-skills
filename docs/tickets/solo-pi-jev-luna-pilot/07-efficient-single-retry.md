---
ticket_schema: 1
ticket_id: "SPB-07"
execution_mode: AFK
blocked_by:
  - "SPB-06"
---

# SPB-07 — Un solo retry Luna e lavoro operatore misurato

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-07`
- Role: `ticket`
- Parent: [Retry Luna](../../specs/solo-pi-jev-luna-retry.md)

### Produces
- [Risultato retry e costi operatore](../../research/solo-pi-jev-luna-retry-results.md)

## Parent Spec
[Retry Luna](../../specs/solo-pi-jev-luna-retry.md).

## What to Build
Applicare batching/packet/helper reuse alla sola nuova Yjs L4 Luna medium autorizzata,
runtime SPB-06. Il problema di consumo è il flusso operatore, non un errore del contatore;
nessun nuovo codice di scheduler né falsa dichiarazione di reset della sessione operatore.

## Acceptance Criteria
- [ ] Diagnosi token/cache/costi con finestra e fonti attribuite; correzione del flusso esplicita, limite del reset visibile e nessun nuovo agente operatore.
- [ ] Dipendenza SPB-06/candidate/graph/source/SDK/skills/input/immagini e nuova authority verificati; ammissione costi originali cumulativi senza perdita dei 9/41/7/310 consumati.
- [ ] Un solo nuovo processo/cella Yjs L4 Luna medium; gate/fallimenti, port calls e dipendenze osservati senza retry/replay; snapshot delivered e candidato conservati separatamente.
- [ ] Oracle caller-only immutabile e no hidden feedback; storico, prep e source vecchi identici prima/dopo.
- [ ] Rapporto aggregato di score, tentativi/blocchi, nuovo vs vecchio con gli stessi input e limiti descrittivi; SDK/operatore/invoice/FX distinti.
- [ ] Review/QA/audit locali e costi/chiamate del segmento osservati, non presunti; nessun full-suite invariato ripetuto, delivery/install/runner/delega.

## Frontier
SPB-06 implementation-complete/release-blocked validato; nuova authority live esplicita
nella richiesta corrente. Questo task continua lo stesso mandato in modo limitato: nessun
tool di reset operatore disponibile; il processo del partecipante sarà realmente nuovo.

## Step-by-Step Implementation Plan
1. Small bounded facts and canonical admission, reuse existing caller/validators.
2. Immutable runtime snapshot SPB-06 and cumulative new-store Budget; refresh cost.
3. Exactly one native cell and immutable private oracle; no replacement after failure.
4. Bounded readback, frozen aggregate report/review/QA/verification, measured operator segment.

## Testing Plan
Current graph/serializer/Git/source hashes before spend; admitted single real cell with
public capture and immutable oracle; after-readback counts/refs/bindings/money, no replay.
Previous 24 local runtime tests keep original identity; no new release/CI pass claim.

## Out of Scope
Altri modelli/scenari/repliche, storico mutato, reset finto, altri agenti, nuovi scheduler,
hidden prompts, new hard caps/security layers, publication/commit/push/merge/install/reload/wiki sync.
