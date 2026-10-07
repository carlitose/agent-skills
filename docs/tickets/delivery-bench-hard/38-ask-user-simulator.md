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
- Parent: [delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md), Target behavior 2–5, Failure modes e Verification.

## What to Build
Un'estensione Pi `ask_user` caricata nei bracci di un lotto con richieste vaghe, e nel runner
l'utente simulato: `gpt-6-sol` in una sessione separata, con istruzioni fisse e il brief preciso
(richiesta corrente più le precedenti della catena), senza il nome del braccio. Cache per
scenario e richiesta delle domande normalizzate; limite di 10 domande per richiesta; rifiuto
delle risposte con nomi dei test nascosti o canary; domande, risposte e costo del simulato nel
tentativo e nel ledger, separati dal costo del braccio. `init-lot` accetta la variante vaga e
fissa gli sha256 delle richieste vaghe; il preflight fa una domanda vera.

## Acceptance Criteria
- [ ] La stessa domanda normalizzata riceve la stessa risposta in bracci e ripetizioni diversi,
      senza una nuova chiamata.
- [ ] L'undicesima domanda riceve il messaggio di limite senza chiamare il simulato.
- [ ] Il simulato non riceve mai il nome del braccio né il codice dell'agente.
- [ ] Una risposta con un nome di test nascosto o il canary viene rifiutata e registrata.
- [ ] Il costo del simulato è separato da quello del braccio nel ledger e nel report.
- [ ] I lotti con richieste precise funzionano come prima; suite completa del runner OK e CI 8/8.
- [ ] Preflight senza lotto dei tre bracci ok, con almeno una domanda reale.

## Frontier
Pronto; il preflight reale usa le richieste di DBH-37.

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
