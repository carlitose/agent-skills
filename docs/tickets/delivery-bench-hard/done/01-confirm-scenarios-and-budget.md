---
ticket_schema: 1
ticket_id: "DBH-01"
execution_mode: HITL
blocked_by: []
---

# DBH-01 — Conferma di scenari, lunghezze, tetti e budget

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:01`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Confermare con l'utente, tramite `grilling`, una domanda alla volta, le decisioni 3-11 della
mappa. Decidere poi i tetti di tempo e di spesa che fanno da autorità per i lotti DBH-03, DBH-08
e DBH-09. Il punto di partenza è la proposta seguente, da confermare o cambiare:
- **Scenari**: `lua-vm`, `sql-engine` e `crdt-yjs`
  ([ricerca](../../research/delivery-bench-hard-candidates.md)).
- **Lunghezze**: catene da 12 richieste, lette a 1, 4 e 12. Tre ripetizioni fino alla
  richiesta 4, una fino alla 12, e altre solo se la regola di TBA-03 le chiede.
- **Tetti di tempo**: 90 minuti per richiesta e 90 × L per catena nel pilota. Il pilota fissa
  il tetto della misura completa. Al massimo 4 celle in parallelo, perché la macchina è
  condivisa con Terminal-Bench.
- **Budget** (stime di Pi; il provider è in abbonamento):

  | Lotto | USD | Durata massima |
  |---|---:|---:|
  | calibrazione | 10 $ | — |
  | pilota | 40 $ | 12 ore |
  | misura completa | 250 $ | 72 ore |

  Jev è fuori da questi importi, con un tetto di 1 $.

La stima parte da DB-08, che è costato circa 0,50 $ per richiesta con sol. Luna costa 1/20 per
token, e le richieste nuove dovrebbero usare da 3 a 5 volte i token. La misura completa ha circa
420 richieste nel caso peggiore.

## Acceptance Criteria
- [x] Ogni decisione 3-11 della mappa è confermata o cambiata dall'utente, e la mappa riporta
  l'esito.
- [x] Un'autorità dei lotti, `results/dbh-authority.json` nel repo privato, registra il messaggio
  dell'utente, i tetti, i lotti coperti e il modello `openai-codex/gpt-6-luna` con thinking
  `medium`. La mappa ne cita lo sha256.
- [x] Nessun lotto parte prima di questa conferma.

## Outcome
2026-09-27. L'utente ha dato un goal di sessione: «finisci di aggiornare il benchmark ed esegui di
nuovo tutti i bracci, finiti pulisci i worktree e fai report», con l'istruzione di non fermarsi
a chiedere. Il goal vale come conferma: la proposta sopra è adottata così com'è, e la mappa lo
registra. Due autorità nel repo privato, una per lotto:
- `results/dbh-authority.json`, sha256 `52597cbf5ddb590c190a6cb478abc6fe733cc4e2158d8dcf3def50545d9e8e51`.
  Copre il lotto `dbh`: pilota e misura completa, cinque bracci, tre scenari, 3 ripetizioni,
  catene fino a 12.
- `results/luna-calib-authority.json`, sha256
  `352fae74c044342429d0cc284572239d4dc6e2da15d7eaad5621e6f91a14733e`. Copre `luna-calib`.

Entrambe nominano il modello, e il runner rifiuta un lotto con un modello diverso (DBH-02).
Limite dichiarato: la revisione del catalogo delle trappole (DBH-04) è delegata dal goal, e
l'utente non l'ha vista.

## Frontier
Richiede una decisione umana: la conferma dell'utente sulla proposta sopra.

## Step-by-Step Implementation Plan
1. Caricare `grilling` e fare una domanda alla volta, a partire da quelle che cambiano di più
   l'ambito: scenari, poi lunghezze, poi tetti.
2. Aggiornare la mappa con le risposte.
3. Scrivere l'autorità nel repo privato e citarne il digest.

## Testing Plan
Nessun test automatico. Le prove sono l'artefatto di autorità e la mappa aggiornata.

## Out of Scope
- Il catalogo delle trappole (DBH-04).
- Scrivere gli scenari o lanciare lotti.
