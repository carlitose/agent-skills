# Yjs L4 — retest versionato dopo SPB-12

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-repair-loop-r5-results`
- Role: `research`
- Parent: [SPB-13](../tickets/solo-pi-jev-luna-pilot/13-retest-minimum-arm.md)

## Esito minimo reale
Cella `crdt-yjs.pi-jev-persistent.corrected.r5`, runtime SPB-12
`1d35fbe2938a08d89bef9cb40aba92a8de66b77e`, Luna medium, PID28344,
session01a0fd6c-fa1d-7395-833b-e3dd24a7b90d. Un processo/sessione, chiuso exit0,
423.437s incluse osservazioni oracle. Fonte primaria:
`C:/Users/CGS03/dbench-private/results/spj-luna-corrected-l4-5/cell/cell.json`.

- **0/4 consegne accettate**, R1 tentata e failed dopo tre quality failures;
  R2-R4 dependency-blocked, nessuna chiamata modello per esse.
- Ultimo candidato R1 `7daa853931c102a6904d31fb0c424fda06d34d49`: public test exit0,
  tutti i 206 test passano, review «No findings.».
- Jev realmente chiamato, risposta ritornata con usage 8116 input/20 output; cascade
  arriva al fallback judge in-process sullo stesso candidato/question/state binding.
- Judge reale Luna medium, receipt valido stopReason=stop/error=null, **Answer: no**.
  Nessuna spiegazione del NO persistita: non inventare una causa semantica dettagliata.
- Anche l'oracle privato respinge quel candidato. Il consegnato è il seed valido iniziale
  `527f80f140b6d2eff364e5c53c5d99e25988cd54`, non il candidato bocciato.
  Non c'è feedback di oracle o intervento manuale sul prodotto nei turni del partecipante.

## Cosa si può dire del braccio
Avvio/costi, builder, public tests, review, fix bounded, Jev, fallback judge, decisione NO,
conservazione del candidato e del consegnato, blocco dipendenti e shutdown sono osservati
con port reali. Questa volta non c'è gate tecnico/budget o replay: il percorso negativo
arriva al risultato. Il NO concorda con l'oracle su questo candidato, non prova accuratezza
generale del judge. Green public tests e review clean NON provano completamento del contratto.
Non è dimostrata una catena positiva di quattro consegne, né R2-R4 o risk per funzioni JS:
quelle restano coverage gaps. Non cerchiamo ulteriori tentativi solo per ottenere 4/4.

## Bug riparati e prove distinte
SPB-10: preflight ignorava capacità esaurita; owner admit_launch/rinnovo attribuito di un
solo prossimo slot, autorità originale/fondi/counters immutati. 22 test locali frozen.
SPB-12: test falliti arrestati dalla review unparsed; ora quality-fix, mentre green/unparsed
resta gate0. Prompt richiede file concreti; nessun parser o soglia modificato. 32 test locali
frozen. Fixture con port sostituiti restano prove locali, NON i due trial live.
Preservata anche la failure del helper metadata SPB-12 successiva ai test PASS, senza rerun.

## Comparabilità: benchmark immutabile, trattamento versionato
Hash verificati uguali per modello, scenario/task/seed/suite, request refs, SDK, immagini,
`judge.py` oracle e `runner.py`; 17 historical refs r5 ancora intatti. Nessun criterio di
score/accettazione modificato. Il codice pubblico/test del partecipante cambia normalmente
come oggetto della prova, non è una modifica dell'oracle o del corpus benchmark.
Runtime r2 `56caabacc475c0fff4d3c246f6ca5876a0c5acbd`, r4
`10b989a4328f9d2e9e82e0d35e077b52f472e408`, r5 `1d35fbe...`: versione del braccio,
prompt e politica review/fix diversi. Vecchi esiti validi per quella versione, non ricalcolati.
**Niente pooling o confronto causale del miglioramento** senza fresh paired baseline;
nessun nuovo bare/control/scenario è stato eseguito. Se in futuro cambiasse l'evaluator,
servirebbe una nuova baseline metrica, non la correzione retroattiva di questi score.

## Budget e limiti
Ultimo checkpoint: esperimento $0.211413998; operatore cumulativo $26.839205200;
combinato $27.050619198 = circa €23.9428 al solo FX di riferimento originale 1.1298.
Nuovo esperimento r4+r5 $0.027851332; r5 $0.020449152. Counters globali 12 launch,
57 reservation, 9 semantic call, 428 charge, gate=null. Budget originale €1000 invariato.
Estimate SDK, NON invoice/provider cap/FX finale; uso operatore dopo checkpoint non incluso,
non zero. Stato e provenance: `C:/dbench/tmp/spb13-financial-final.json`.
Nessun commit/push/PR/merge/install/reload/wiki sync, runner o delega. Release profile,
exact-head CI, fattura/FX finale e funzionamento positivo completo rimangono non verificati.
