# Review admission — correzione locale SPB-08

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-review-admission-results`
- Role: `research`
- Parent: [SPB-08](../tickets/solo-pi-jev-luna-pilot/08-adjudicate-review-findings.md)

## Diagnosi: difetto del braccio, non verdetto sul Counter
Il controller ammetteva coverage soltanto con test verdi e review `clean`. Una review
parsata con should-fix o nit diventava quindi quality-failure senza Jev/judge. Il test
causale RED mostra un semplice consiglio opzionale che porta a `failed, 3`; GREEN, a parità
di API/test reali e con port semantico YES, dà `completed-local, 0`, senza rinominare la
review clean. Questo corregge la deviazione dal Review Contract SPJ-03 punto 6.

La segnalazione SPB-07 riguarda YCounter.value che non legge `_prelimContent` prima di essere
integrato. È una claim del reviewer da confrontare con il task, non un test eseguito: il
pseudo-esempio concatenato non è riproducibile così scritto, perché increment() non
restituisce this. Il task pubblico parla di increment/value e conservazione pre-integrazione;
non dimostriamo qui che la segnalazione sia falsa né risolviamo il candidato YCounter.
Non si può attribuire retroattivamente il suo intero 0/4 al solo braccio o alla sola
intelligenza del modello. Per questa correzione non sono stati consultati oracle/hidden.

## Comportamento corretto
- Test verdi + review parsata senza blocker esplicito: coverage riceve prosa completa,
  ticket, diff congelato e osservazioni pubbliche; should-fix/nit vengono adjudicati rispetto
  a requisiti e difetti materiali, non bocciati per etichetta.
- YES: completamento locale; NO: fallimento di qualità cumulativo, non aggirabile dal judge.
- Uncertain o chiamata non ammessa/disponibile: analisi condivisa e gate, non tre code failure.
- Blocker esplicito o test pubblico fallito: veto invariato; unparsed: gate immediato.
- Nessun nuovo port/domanda/retry/sessione, parser invariato, soglie/budget e limite 3 invariati.

Le istruzioni review/coverage ora distinguono requisiti da miglioramenti opzionali e claims
modello da prove osservate. Riutilizziamo una sola decisione globale, non due chiamate duplicate.
Le question/istruzioni storiche restano nei source snapshot originali; questo è un nuovo
contratto interno di ammissione, non una reinterpretazione delle decisioni precedenti.

## Test osservati e consumo conservato
RED 1: failed, 3 anziché completed-local, 0 — 5,572s; GREEN 1: passato — 2,907s.
Il primo comando aggregato ha avuto timeout a 100s; durata finale/output e chiusura per
ogni child non erano conservati. Artefatto `C:/dbench/tmp/spb08-timeout-1.json`; nessun PASS
attribuito a quell'invocazione. Il probe host non ha trovato il comando unittest/spb08 ancora
attivo. Niente rilancio aggregato: shard mirati con il capture/cleanup owner esistente.

**41 test selezionati passati**:
- controller: 13, capture 43,531s;
- repairs: 18 (sette nuovi contrasti + undici esistenti), capture 64,265s;
- adapter: 10, capture 8,828s.

Contrasti: should-fix con YES/NO/uncertain e fallback judge; nit; veto di blocker e test
fallito; regressioni unparsed, bound, readonly, negativo sticky, dipendenze e budget.
Git, freeze e processi di test sono reali; peer Pi, Jev e judge sono sostituiti ai port già
accettati. Non sono proof live di accuratezza del classifier, auth, modello o performance.
Capture selezionato: 116,624s; somma di tutte le invocazioni **almeno 225,103s**, includendo
RED/GREEN e timeout. E2E e durata completa del tentativo timeout ignoti. Non è tempo gratuito.
Il readback QA finale opera sul tree congelato e conserva le prove precedenti con il loro
CandidateRef; soltanto il subset causale necessario, non tutta la suite ripetuta.

## Storico, costi e limiti
SPB-07 resta 0/4 e conserva candidato, delivered, tre failure e tre richieste bloccate.
Vecchi ledger, prep/source e risultati non modificati. Nessuna nuova chiamata sperimentale:
contatori 10 launch, 47 reservation, 7 semantic call e 367 charge; stima sperimentale
cumulativa $0,183562666 al checkpoint SPB-07. Uso operatore successivo ancora da prezzare,
fattura/cambio finali ignoti; non presentiamo il vecchio totale combinato come conto attuale.
Nessuna nuova authority live dedotta dal Fixalo; nessun benchmark/oracle/replay, installazione,
commit del progetto, push/PR/merge/reload/wiki sync. Wiki query `compiled-markdown`,
`no-supported-rag-binding`: indice storico incompleto per SPB, contratto primario SPJ-03
verificato direttamente. Review/QA/audit inline seriali shared-context, non indipendenti.
Release profile/exact-head CI/delivery e nuova misura live rimangono gate separati.
