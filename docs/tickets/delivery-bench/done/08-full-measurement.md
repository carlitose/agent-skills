---
ticket_schema: 1
ticket_id: "DB-08"
execution_mode: HITL
blocked_by:
  - "DB-07"
---

# DB-08 — Misura completa: catene da 3 e 8

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:08`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

### Produces
- [delivery-bench-results.md](../../research/delivery-bench-results.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire le catene da 3 (3 ripetizioni) e da 8 (1 ripetizione) per i cinque bracci nei tre scenari, poi il report finale: tabella braccio × lunghezza × scenario sui cinque assi e la raccomandazione operativa («per task da N richieste usa X»), con i limiti dichiarati.

## Acceptance Criteria
- [x] Nuova autorizzazione esplicita dell'utente con tetto di tempo per catena. *(Coperta dall'obiettivo di sessione, che autorizza DB-07 e DB-08 senza fermarsi; nessun nuovo messaggio. Tetto del contratto: 60 min per richiesta, 60 × L per catena.)*
- [x] Tutte le celle con profilo; le ripetizioni extra della catena da 8 solo dove la regola di TBA-03 lo richiede.
- [x] Report finale con raccomandazione e limiti; nessun numero unico.

## Frontier
**Completato** (2026-09-27, skills-only). Il lotto `db07-pilot` è stato proseguito:
- catene da 3 su 45 celle;
- catena da 8 sulla ripetizione 1 (15 celle);
- ripetizione 2 della catena da 8 per `bare`, skills-only, Autopilot e c1a, come chiesto dalla
  regola di TBA-03, che è decisa a ogni lunghezza.

In tutto 270 richieste giudicate. Nessun guasto d'infrastruttura, timeout o riscontro
dell'audit; 119,10 $ stimati per DB-08. Report, raccomandazione e limiti:
[delivery-bench-results.md](../../../research/delivery-bench-results.md).

In sintesi:
- Su C e Python il braccio non conta.
- Sul frontend, skills-only è l'unico che non perde richieste (48/48 alla catena da 8 su tutti
  gli scenari, 0 regressioni). L'accettazione da sola non lo distingue da Pi nudo (Holm 0,094).
- Autopilot non è davanti su nessun asse, a 5,4× il costo.
- c3a in AFK si ferma sul cancello.

Correzioni nella stessa PR:
- lettura della bussola lungo la catena;
- difetto di una suite nascosta, corretto e rilegato con `amend-suite`; otto giudizi
  riclassificati esattamente e 30/30 alberi rigiudicati identici.

## Step-by-Step Implementation Plan
1. Autorizzazione.
2. Catene da 3, poi da 8.
3. Report finale.

## Testing Plan
Live.

## Out of Scope
- Migliorare i bracci nello stesso lotto.
