---
ticket_schema: 1
ticket_id: "DBH-22"
execution_mode: AFK
blocked_by: []
---

# DBH-22 — Viewer dal vivo del lotto, sul terminale

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:22`
- Role: `ticket`
- Parent: [delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md)

## Parent Spec
[delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md),
sezione *Comportamento atteso* 4.

## What to Build
`benchmarks/delivery-bench/watch.py`, di sola lettura, per seguire un lotto mentre gira:
- `cell --lot L --cell C`: segue il JSONL della sessione della cella e stampa messaggi
  dell'assistente, chiamate ai tool con argomenti abbreviati, risultati abbreviati, errori
  evidenziati e costo per turno; continua quando la richiesta successiva riprende la sessione;
- `lot --lot L`: tabella aggiornata delle celle (richiesta corrente, giudicate, accettate,
  errori) e spesa di listino totale rispetto al tetto dell'autorità;
- `open --lot L`: su Windows apre con `wt.exe` una scheda per ogni cella in corso più una per lo
  stato; altrove stampa i comandi.

## Acceptance Criteria
- [ ] Su un JSONL sintetico, `cell` stampa nell'ordine messaggio, tool call, risultato, errore e
      costo; righe nuove aggiunte al file compaiono senza rilanciare.
- [ ] `lot` legge `lot.json`, `cells/*/cell.json` e il ledger e mostra la spesa contro il tetto
      dell'autorità.
- [ ] `open` costruisce un comando `wt.exe` con una scheda per cella; il test ne verifica
      l'argv senza lanciarlo.
- [ ] Nessun comando scrive nel lotto né nelle sessioni (test: digest della cartella prima e
      dopo).
- [ ] Funziona con le sole librerie standard di Python, anche fuori da Windows.

## Frontier
Ready. Indipendente da DBH-21.

## Step-by-Step Implementation Plan
1. Lettore incrementale del JSONL (posizione in byte, righe parziali ignorate fino al `\n`).
2. Rendering degli eventi di sessione di Pi 1.0.2 (messaggi, `toolCall`, `toolResult`, `usage`).
3. Vista di stato da `lot.json`, `cell.json` e ledger, con aggiornamento periodico.
4. `open` con `wt.exe new-tab` per cella.
5. Test in `benchmarks/delivery-bench/test_watch.py`.

## Testing Plan
- Unitari su JSONL e lotti sintetici; prova manuale su un lotto esistente (`dbh-opus`) in sola
  lettura.

## Out of Scope
- Interagire con le istanze di Pi o fermarle dal viewer.
- pi-messenger o estensioni dentro i bracci.
