# Coverage input — correggere il gate prima del port

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-coverage-input`
- Role: `spec`
- Standalone: true

### Children
- [SPB-06: input coverage attribuito e bounded](../tickets/solo-pi-jev-luna-pilot/06-bound-coverage-input.md)

### Related
- [Osservazione SPB-05 congelata](../research/solo-pi-jev-luna-corrected-l4-results.md)

## Tipo, mandato e fatti
Bug analysis/local fix. Mandato corrente: «finisci i todos», incluso il bug in coda dopo
SPB-05. Skills-only, inline e seriale; nessuna nuova authority live o di delivery.
La diagnosi digest-bound privata SPB-05 conserva un envelope coverage di 102.108 B,
con 93.458 B di receipt, oltre il limite 65.536 B: nessun port Jev/judge chiamato.
Test pubblico finale verde e review clean; candidato oracle-rejected, non consegnato.

## Modulo, interfaccia e seam
Modulo: ChainController/DecisionEngine. Interfaccia pubblica `run_ticket` invariata;
il solo payload interno coverage cambia esplicitamente. Seam accettato dai test esistenti:
Git e test process reali, peer/port Jev/judge sostituiti e dichiarati, non live.
Nessuna nuova libreria, provider, ast/risk analyzer o compatibilità parallela.

## Target e decisione
Riutilizzare le osservazioni pubbliche bounded già usate da fix/review anche per coverage:
`test_observations` contiene receipt attribuite con argv, esito, candidato, path/SHA-256,
preview stdout/stderr e truncation flag. La capture integrale resta nel controller e nel
file immutabile; non si taglia o sostituisce l'artefatto. Il nuovo payload non contiene
un secondo duplicato degli stream integrali.

Ticket, candidato, review e diff letterale completo degli esatti Git tree rimangono nello
stato hashato. I test devono essere realmente verdi e il review clean prima dell'approvazione
semantica; non si converte un preview, un PASS dichiarato o un UNCERTAIN in YES. La domanda
resta copertura dei criteri nel diff, non un test-output digest letto dal modello. Preview
troncata dichiarata non prova di per sé un criterio: il port può rispondere incerto.

Il limite completo di DecisionEngine resta 65.536 B, la preview resta ≤32 KiB. Se ticket,
diff o metadata eccedono ancora il bound, entrambi i port restano non chiamati, i fatti
restano conservati e il motivo è specifico `semantic-input-bound`, con misura byte/limite.
Non alzare limiti, non troncare diff/ticket/review, non introdurre retry o cambio di soglie.

Questa modifica sostituisce esplicitamente la precedente regola CHAIN che inviava receipt
integrali anche a coverage: conservarle è obbligatorio; duplicarle nell'envelope no.
Lo stato hashato cambia, quindi non si migra/reinterpreta un checkpoint vecchio o si rigioca
un candidato già deciso. Dati storici, source snapshot SPB-03 e report SPB-05 intatti.

## Alternative e limiti
Aumentare il bound: respinto, sposta il problema e il costo senza risolvere duplicazioni.
Tagliare la capture o il diff: respinto, perde evidenza o implementazione dei criteri.
Dichiarare coverage completa dai soli test: respinto, i test verdi non sono copertura.
Questo fix locale non dimostra un ciclo Jev/judge reale o successo di Yjs; un eventuale
nuovo trial richiede nuova authority/costi. Nessuna correzione dei risultati già misurati.

## Verifica prevista
RED/GREEN verticale sul controller: grande output pubblico valido deve raggiungere il port
con payload bounded e receipt integrale ancora verificabile; green+clean non deve bypassare
un NO semantico. Poi un vero diff oltre bound deve mantenere gate, zero port calls e motivo
specifico. Regression mirate di controller/repair con Git/processi reali e port finti.
Packaging/grafo/LF, review diff read-only, QA e audit sul nuovo candidato. Nessun full
release profile o hosted CI presunto, benchmark/oracle replay, commit/push/install/wiki sync.
