# Solo Pi + Jev — decisione sul fallback

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-uncertainty-decision`
- Role: `spec`
- Parent: [SPJ-02](../tickets/solo-pi-jev/02-decide-uncertainty-fallback.md)

## Type
Decision spec, confermata tramite grilling; non implementazione o misura.

## Status
Decisione SPJ-02 confermata nella conversazione del 2026-10-01. La review dettagliata e
la matrice di ownership restano a SPJ-03/04. Trasporto reale, autenticazione del judge e
integrazione nel controller non sono stati provati. Pubblicazione separata.

## Decision

Una sola sessione principale e un solo processo Pi per la catena. Jev continua a rispondere
alle domande tipate e a classificare il rischio per funzione. Un gate semantico che Jev non
decide può usare **una completion in-process sul modello di frontiera configurato**, con
prompt separato, senza strumenti, sessione agente aggiuntiva o processo Pi figlio. Non
si usa il comando `/goal` per decidere il gate: si riusa il suo meccanismo di completion.

Il judge riceve domanda, criteri e prove osservate del candidato congelato, non la cronologia
del builder. Contesto distinto non significa indipendenza di modello, fornitore o delle
prove selezionate dal controller; nessuna qualità equivalente è dimostrata. Il judge non
può attestare file, test o permessi che non gli sono stati forniti come prove.

Un esito del judge mancante, incerto, malformato o non attribuibile consente soltanto analisi
nel Pi principale e poi gate umano. L'analisi è condivisa e **non approva**. Rischio per
funzione indecidibile seleziona review obbligatoria nel Pi principale, non un judge per
funzione o un rischio basso. Il contratto completo di quella review appartiene a SPJ-03.

## Confirmation Evidence

Conferme reali dalla conversazione e dal tool `question`, in ordine; non dedotte dal goal
«termina i todos», da una proposta o da assenza di risposta:

1. La richiesta «Senza creare istanze pi, usa subagent la estensione che abbiamo», poi
   «Usa la estensione subagent», chiedeva inizialmente l'estensione. Il tentativo
   `general-purpose` è fallito prima di restituire un giudizio: `No API key found for
   amazon-bedrock`. Il primo nome `worker` era sconosciuto; il catalogo reale riportava
   `Explore`, `general-purpose`, `Plan`. Nessuno dei tentativi è evidenza di review.
2. Fallback dopo fallimento/incertezza del secondo giudice: scelta «Analisi condivisa,
   poi gate»; analisi non indipendente e gate umano se manca un giudizio valido.
3. Rischio indecidibile: scelta «Review nel Pi principale», obbligatoria e non classificata
   automaticamente come rischio basso.
4. Dopo la domanda dell'utente su `/goal` e lettura dei sorgenti, scelta «Judge in-process»:
   sostituisce il subagent con prompt dedicato, prove del candidato, nessuno strumento o
   cronologia del builder. Non è autorizzazione a chiamate live o benchmark.
5. Invio vietato a Jev: scelta «Verifica separata, fail closed»; permesso esplicito per il
   judge e per quei dati, oppure analisi nel contesto già consentito e gate umano.
6. Bound: scelta «Confermo il limite»; soglie invariate, massimo 3 tentativi Jev, un solo
   judge per domanda/candidato, niente retry fino a PASS o bypass di un negativo deciso.
7. Conferma finale «Confermo e registra SPJ-02» dopo riepilogo completo e distinzione tra
   un processo Pi e ulteriori chiamate al modello. Autorizza questa spec e aggiornamento
   della destinazione Wayfinder; lascia SPJ-03/04 aperti e non autorizza live, benchmark,
   installazione o reload.

Le opzioni con emoji sono riportate qui senza il prefisso grafico. I precedenti tentativi
non cambiano i risultati misurati e non sono uno smoke del trasporto nuovo.

## Decision Table

Per «positivo/negativo» si intende l'esito rispetto ai criteri della singola domanda, non
l'approvazione dell'intero candidato. Le choice conservano il valore ammesso della domanda.

| Osservazione | Gate semantico | Rischio per funzione |
| --- | --- | --- |
| Risposta tipata e confident positiva | Accettare l'esito della domanda; proseguire solo se tutti gli altri gate lo consentono. | Applicare classificazione e soglia attuali; review quando il rischio la seleziona. |
| Risposta tipata e confident negativa | Rispettare l'esito; recovery/stop secondo i criteri. Non chiamare il judge per aggirarlo. | Applicare classificazione attuale, senza abbassarla per convenienza. |
| Sotto soglia / incerta | Un judge in-process, poi analisi condivisa e gate se ancora indecidibile. | Review condivisa obbligatoria; non rischio basso. |
| Servizio Jev indisponibile | Dopo i tentativi consentiti entro il bound, judge se consentito; poi analisi/gate. | Review condivisa obbligatoria; indisponibilità registrata. |
| Invio Jev vietato dal repository | Nessuna chiamata Jev. Verificare separatamente il permesso del judge per quei dati; altrimenti analisi già consentita e gate. | Nessuna chiamata Jev; review nel contesto già consentito. Se quel contesto non può ricevere i dati, gate umano. |
| Input fuori bound | Non troncare prove decisive per inventare una risposta. Judge solo con payload ammesso e sufficiente; altrimenti analisi/gate. | Selezionare review, conservando identità e limite dell'input. |
| Risposta malformata / incompleta | Non è un esito deciso; judge se ammesso, poi analisi/gate. | Review obbligatoria; non una classificazione valida. |
| Judge incerto, non disponibile o malformato | Analisi condivisa per il handoff, poi gate umano. Nessuna approvazione automatica. | Nessun judge di rischio previsto; vale il contratto di review SPJ-03. |
| Prove o candidato non corrispondenti | Risposta non utilizzabile per il candidato corrente. Stop/gate; l'owner del drift sarà definito in SPJ-04. | Non riutilizzare il risultato per un altro albero. |

## Bounds, Identity and Accounting

- Conservare le soglie della policy letta: `noul_low=0.2`, `noul_high=0.8`,
  `choice_min_confidence=0.75`, `risk_score_high=2.5`. Nessuna calibrazione dai benchmark.
- Massimo 3 tentativi Jev come nella policy esistente, non tre richieste obbligatorie:
  `arbiter.ask` ritenta solo HTTP 429/529; risposta incerta, altri errori o invio vietato
  non autorizzano re-query per ottenere un esito diverso. Nessun ciclo illimitato. Un
  limite di consumo può fermare prima, mai aumentarsi implicitamente per un retry.
- Massimo una invocazione judge per domanda e candidato congelato. Una risposta negativa
  valida non si sottopone a nuovi judge finché diventa positiva. Un nuovo candidato
  richiede nuove prove, ma non azzera spesa, tentativi storici o consumo della catena.
- Non utilizzare il parser permissivo di `/goal` che può accettare un semplice yes/no.
  Restano domande e criteri canonici, valori ammessi e `undetermined`; una sola risposta
  finale tipata valida può decidere. Output con tool call, errore, cancellazione, troncamento
  decisivo o candidato non corrispondente fallisce chiuso. Prosa non è una ricevuta di test.
- Lo script deve associare domanda, digest del suo contratto, stato fornito e CandidateRef
  canonico alla richiesta e alla risposta osservate. L'identità non è attestata dal modello.
- Selezionare un modello di frontiera realmente configurato e consentito. Non inventare un
  ID, non ripiegare silenziosamente su un modello diverso e non cambiare credenziali per
  rendere disponibile il judge. Il modello risolto deve essere nella ricevuta.
- Chiamata in-process non significa gratuita: conservare usage restituito, modello,
  tentativi/failure e costo noto o ignoto. Sommare a Pi/Jev lungo tutta la catena, senza
  azzerare al cambio di ruolo o candidato. Le delte documentate in SPJ-01 non includono
  automaticamente una completion annidata: il controller deve registrarla separatamente
  ed evitare doppio conteggio. Budget e autorità per future misure restano separati.
- Credenziali Jev restano nello script isolato, non nei prompt del builder o del judge.
  Permessi per ciascun destinatario e payload si verificano prima dell'invio. Nessuna copia
  di dati vietati a un altro provider come espediente di fallback.

## Primary Evidence and Feasibility Limit

- `ticket-driver/scripts/cascade.py`: `Cascade.batch`, `judge`, `_judge_answer` e `verdicts`
  mostrano domande canoniche, fallback storico fresco, esiti ammessi e gate umano.
- `ticket-driver/scripts/risk.py`: `assess` seleziona review per incertezza o hunk fuori
  bound; Jev non genera findings. `ticket-driver/policy.json` contiene i bound riportati.
- Nel pacchetto **installato** `pi-code`, `docs/goal.md`, `extensions/goal.ts` (`askEvaluator`,
  `evaluatorModel`) e `extensions/internal/model-complete.ts` (`completeText`) descrivono
  una completion in-process con `ModelRuntime.completeSimple`, prompt esplicito, usage e
  gestione degli errori. `model-lookup.ts` distingue override e modello della sessione.
- `pi-code/extensions/subagent/README.md`, `child.ts` (`agentInvocationArgs`) e `run.ts`
  (`spawnChild`) confermano invece un processo Pi figlio; il builtin senza pin non passa
  esplicitamente `ctx.model` al CLI. Non confondere questa estensione con l'esempio Pi.
- [SPJ-01](../research/solo-pi-jev-session-transport.md) raccomanda RPC per Python e distingue
  cronologia, sessione e processo. La completion deve essere esposta nel processo posseduto
  dal controller attraverso un adapter documentato e testabile: non esiste già nel driver.

Fonti installate sotto `C:/Users/CGS03/Projects/pi-personal-config/node_modules/pi-code`;
contratti del driver osservati sulla base `001d36229093e3b4d759d585a8406be5826dc47a`.
La lettura dimostra il meccanismo, non autenticazione, qualità, indipendenza causale o
funzionamento del futuro adapter RPC. Il modello effettivo del futuro judge resta un
binding da verificare, non una scelta di ID dedotta dal lotto Opus.

## Alternatives and Trade-offs

- Gate umano immediato: semplice e senza ulteriore inference, ma meno autonomo; non scelto
  come primo fallback delle domande semantiche.
- Analisi nello stesso Pi seguita da un nuovo Jev: mantiene il contesto del builder e non
  risolve Jev indisponibile. Analisi condivisa scelta soltanto per handoff dopo judge fallito.
- Subagent dell'estensione: contesto agente separato e strumenti possibili, ma processo Pi
  aggiuntivo e binding del CLI; scelta iniziale sostituita dopo verifica del meccanismo.
- Completion dedicata in-process: conserva un processo e un prompt separato, ma richiede
  prove preparate dallo script, risposta rigorosa, accounting ed error handling. Non può
  raccogliere autonomamente prove mancanti e non è la review condivisa di SPJ-03.

## Verification Strategy and Remaining Work

Walkthrough documentale dei rami della tabella. Dopo SPJ-03/04, SPJ-05 deve provare con fake
positivi/negativi, tutti i rami non decisi, permessi separati, payload fuori bound, risposta
malformata, modello non disponibile, prova insufficiente e consumo cumulativo. Contare
separatamente processo/sessione principale e completion judge; nessuna foglia nascosta.

L'adapter reale, API/provider, modello/autenticazione, costo e qualità restano non testati.
I fake non provano questi aspetti. Questa spec non autorizza implementazione di produzione,
nuovi benchmark, uso di Sonnet VOID come baseline, pubblicazione, installazione o reload.
Conservare copie e risultati storici immutati; non aggiungere compatibilità o shim impliciti.
