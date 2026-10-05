# Findings non-blocker — correggere l'ammissione della review

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-review-admission`
- Role: `spec`
- Standalone: true

### Children
- [SPB-08](../tickets/solo-pi-jev-luna-pilot/08-adjudicate-review-findings.md)

## Root cause and authority
Il 2026-10-02 l'utente chiede di correggere il braccio, non il candidato storico né di
rilanciare. SPB-07 conserva una review parsata con uno should-fix su YCounter.value prima
dell'integrazione: il controller usa `sufficient=passed and clean`, poi conta quality-failure
senza una decisione semantica. Anche un nit avrebbe lo stesso veto. È una deviazione certa
dal [Review Contract, punto 6](solo-pi-jev-review-decision.md): findings sono claims del
modello, blocking/coverage passano alle domande tipate; nit non equivale a blocker.
Non è dimostrato che la singola segnalazione YCounter sia falsa: il contratto pubblico parla
anche di incremento/value e conservazione prima dell'integrazione. L'espressione concatenata
citata dal review non è una riproduzione: increment() nel candidato non restituisce this.
Nessun hidden/oracle consultato per questa diagnosi e nessun nuovo score inferito.

## Target and design
Module: ChainController, Interface invariata run_ticket/DecisionEngine.decide. Seam già
accettata ai port Pi/Jev/judge; Git e test pubblici reali nei fixture, solo i port sono fake.
Test verdi + review parsata senza blocker esplicito rendono disponibile il contesto per la
question coverage esistente. La domanda adjudica anche le segnalazioni non-blocker contro
requisiti, diff e prove: YES completa localmente, NO è quality-failure, uncertain è gate
con analisi condivisa e nessuna failure aggiunta. Should-fix/nit restano nei findings e
nella prosa completa; non sono rinominati clean né scartati. Blocchi espliciti e test falliti
rimangono veto; unparsed conserva il gate immediato. Nessuna approvazione da sola severity.
Chiarire istruzioni coverage/review: niente requisiti extra, suggerimenti opzionali distinti
da violazioni concrete. Riutilizzare la cascata esistente; nessun nuovo protocollo, port,
permesso, question extra, sessione o retry. Un solo giudizio globale evita chiamate duplicate.

## Invariants, alternatives and verification
Restano CandidateRef/diff/receipt completi, bound 65536, policy e budget cumulativi, negative
non bypassabili, massimo 3 failure, readonly e dipendenze. Evitare sia il veto di ogni finding
sia l'approvazione automatica di ogni should-fix: la differenza deve essere causata dalla
risposta semantica osservata. Non modificare parser o file storici/prep/source/candidate.
RED/GREEN attraverso run_ticket: finding non-blocker + YES può completare; stessa forma con
NO fallisce; uncertain/permission/bound non diventano difetti del prodotto; explicit blocker
non è superato da fake YES. Nit, test falliti, unparsed, cascade e dependency restano coperti.
Regressioni mirate controller/repair e adapter prompt; non tutta la suite o oracle storici.
Prova live di Jev/qualità, release profile/exact-head CI/delivery restano gate separati.
