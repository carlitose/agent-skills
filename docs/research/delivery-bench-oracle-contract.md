# delivery-bench — contratto dell'oracolo e protocollo di esecuzione

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-oracle-contract`
- Role: `research`
- Parent: [01-oracle-contract-and-run-protocol.md](../tickets/delivery-bench/01-oracle-contract-and-run-protocol.md)

## Stato
Output di DB-01, non ancora prodotto. Questo file esiste perché il ticket lo dichiara come
`Produces`; il contenuto arriva con l'esecuzione di DB-01. Le decisioni già prese sono nella
[mappa](../specs/delivery-bench-wayfinder.md).

## Domande a cui deve rispondere
- Formato della richiesta grezza e di uno scenario (stato pubblico, richieste 1..8, suite
  nascosta per richiesta, latenti, trappole con distanza).
- Esecuzione della suite nascosta in un container contro un repo consegnato, senza toccarlo.
- Consegna della richiesta N+1 solo dopo la N, per ciascun braccio nel suo modo naturale.
- Come Autopilot riceve la richiesta grezza e dove avviene il merge.
- Record del profilo a cinque assi e tetto di tempo per catena.
