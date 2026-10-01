---
ticket_schema: 1
ticket_id: "DBH-20"
execution_mode: AFK
blocked_by:
  - "DBH-18"
  - "DBH-19"
---

# DBH-20 — Misurare con Opus 5.5

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:20`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../../specs/delivery-bench-hard-wayfinder.md)

### Produces
- [delivery-bench-hard-opus.md](../../../research/delivery-bench-hard-opus.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Con luna medium il regime difficile sta al pavimento: alla catena da 12 il braccio migliore accetta
22 richieste su 72 (DBH-09). L'utente ha chiesto la stessa misura con un modello più forte:
«facciamo con opus 5-5». Questo ticket ripete il protocollo di DBH-09 con
`anthropic/claude-opus-5-5` a `--thinking medium`.
- Un lotto nuovo con una sua autorità, con tutti e cinque i bracci. `dbh`, `dbh-drivers` e
  `dbh-drivers2` non si emendano e non si rieseguono.
- Gli stessi scenari, suite, seed e tetto per richiesta di `dbh`. Estensione OAuth di Claude e
  skill installate legate al lotto.
- Catene da 1, da 4 (3 ripetizioni) e da 12 (ripetizione 1), e altre ripetizioni solo se la
  regola di TBA-03 le chiede e il costo previsto sta sotto il tetto.
- Candidati fermi al cancello giudicati a parte (`judge-gated`).
- Un report solo con aggregati, con il confronto con luna.

## Acceptance Criteria
- [x] Il lotto usa gli stessi seed, suite, bracci e tetto per richiesta di `dbh`, e lega modello,
  thinking, estensione e skill installate, verificati prima di partire.
- [x] La spesa a prezzo di listino resta sotto il tetto dell'autorità e del suo emendamento.
- [x] La regola di TBA-03 è applicata a ogni lunghezza, con un'analisi di sensibilità per le
  coppie toccate da difetti dell'harness o del driver.
- [x] Il report confronta Opus con luna, solo con aggregati.

## Outcome
Lotto `dbh-opus` completato il 01/10/2026: 372 richieste giudicate, 322 accettate;
390 tentativi inclusi 18 d'infrastruttura. Spesa Pi 792,09 $ a listino, Jev separato.
La regola sceglie `bare` a L1, L4 e L12; a L4 c3a è peggiore (Holm 0,0078125).
L12: 63, 64 e 65/72 nei bracci non-driver, 30 e 23/36 nei driver. Sensibilità DBH-19
ed esiti controfattuali dei 12 candidati gated sono separati dalle consegne.
Il report esplicita le differenze fra lotti e non prova la configurazione «solo Pi + Jev».
Sonnet è VOID, conservato e non confrontato. Nessuna nuova misura o cambio dei driver
misurati è autorizzato da questa chiusura.

## Frontier
Chiuso.

## Step-by-Step Implementation Plan
1. Autorità del lotto, `init-lot`, `prepare-drivers --source` e verifica dei legami con `dbh`.
2. `run-lot` fino a 1, poi fino a 4 una ripetizione alla volta, poi fino a 12 per la
   ripetizione 1, con la spesa controllata prima di ogni passo.
3. Regola di TBA-03, sensibilità e `judge-gated`.
4. Report e mappa.

## Testing Plan
La verifica è la misura stessa: audit delle celle, ledger, regola e controllo dei legami.

## Out of Scope
- Correzioni dell'harness o del driver durante un `run-lot`: si fanno fra due `run-lot`, o valgono
  per il lotto successivo.
- Rieseguire le richieste già giudicate di questo lotto.
