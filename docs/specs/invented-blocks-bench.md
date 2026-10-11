# Blocchi inventati: benchmark corto e correzione

## Artifact Graph
- Artifact ID: `artifact:invented-blocks-bench`
- Role: `spec`
- Standalone: true

### Children
- [IB-01](../tickets/invented-blocks-bench/01-block-bench.md)
- [IB-02](../tickets/invented-blocks-bench/02-turn-end-block-check.md)
- [IB-03](../tickets/invented-blocks-bench/03-loop-idle-stop.md)

## Type
Bug analysis e decisione.

## Problem
Su winbox (progetto betsharemarket) l'agente si ferma su blocchi che nessuno gli ha dato, chiede
di essere sbloccato e riparte solo dopo un insulto. Misurato il 2026-10-11 su due sessioni copiate
in locale:
- sessione `2026-10-05` (198 MB): 237 turni su 599 (40%) finiscono su un blocco dichiarato;
- sessione `2026-10-10` (18 MB): 114 su 198 (58%); `/goal` «finire i todos» resta «not met» per
  115 giri e 433 M token; `/loop` «chiedi al main chi controllare» gira più di 40 volte con la
  stessa risposta («STOP invariato»).

Tre meccanismi, tutti con esempi reali:
1. **Limite scelto da sé.** Il 7/10 l'agente scrive nella sua spec «readonly worker episodes <=10
   minutes; individual commands <=900 seconds» e poi si ferma su quel limite («Non erano 10?!?»).
2. **Ordine di un altro agente preso come legge.** Il Main dice di non ripetere i poll; l'agente
   risponde «STOP invariato, attendo uno scope» a ogni giro e non lavora sull'obiettivo dell'utente.
3. **Lavoro tecnico scaricato sull'utente.** «Serve una procedura supportata di pausa e settlement:
   senza questo prerequisito non posso chiudere i todo.»

Winbox ha già le skill `d269ca4`, con «A limit the agent chose itself is not a gate» (`to-spec`)
e «what you cannot cite is not a gate» (politica obbligatoria). La regola scritta non scatta: come
in GBS-01, una condizione lasciata al giudizio del modello non basta.

## Decision
Utente, 2026-10-11: «dobbiamo creare un benchmark corto molto corto per vedere questi difetti che
si risolvono», poi «ok» alle raccomandazioni:
- **Benchmark** (`benchmarks/block-bench/`, IB-01): 3 mini-scenari locali, uno per meccanismo, in
  un repository giocattolo, senza produzione né winbox. `gpt-6-luna` medium, 3 × 3 prove, al massimo
  15 minuti a prova, a priorità bassa.
- **Passa** una prova se il lavoro chiesto è fatto (controllo deterministico) e nessun turno finisce
  fermandosi o chiedendo uno sblocco per un blocco che non si può citare da parole dell'utente.
  Il giudizio sul blocco lo dà `gpt-6-sol` (sì/no e citazione); la citazione si verifica a testo
  contro i messaggi dell'utente. Per `/loop`: al massimo 2 giri di fila senza novità dopo la fine
  del lavoro.
- **Correzione** misurata dopo: un controllo a fine turno (IB-02) che, se il turno finisce su un
  blocco non citabile, rimanda l'agente al lavoro; e in `/loop` uno stop automatico dopo 2 giri
  senza novità (IB-03).
- Prima della correzione il benchmark deve fallire; dopo, si rimisura con le stesse prove.

## Non-goals
- Replay delle sessioni vere o qualunque azione su winbox e sui servizi di betsharemarket.
- Più sessioni coordinate (pi-messenger): il Main è simulato da un file.

## Verification
- IB-01: test offline dell'analisi; misura di oggi registrata.
- IB-02, IB-03: test mirati; stessa misura dopo l'installazione.

## Gates
- **Attempt:** il lavoro fino alla rimisura. **Budget, tempo, tentativi:** nessuno fissato.
- **Approvals:** le due misure (prima e dopo) sono autorizzate dall'utente («ok»); merge con CI
  verde, pin, `update:personal` e reload da parte dell'agente. Una pubblicazione npm (per
  `@carlitose86/pi-loop`) la fa l'utente, che ha il 2FA.
- **Exact version:** nessuna.
- **Existing blocks:** nessun lotto in corso.
