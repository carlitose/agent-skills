# Luna corretto — Yjs L4 e confronto storico

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-corrected-l4-results`
- Role: `research`
- Parent: [SPB-05](../tickets/solo-pi-jev-luna-pilot/05-run-corrected-l4.md)

## Esito della sola misura autorizzata

Una cella persistente Yjs L4, `openai-codex/gpt-6-luna`, medium, è stata eseguita
senza replay. Durata misurata dell'invocazione, oracle incluso: **396,453 s**.
Un solo processo/sessione nativi; chiusura osservata con exit 0. Exit 0 del trasporto
non significa successo del prodotto.

| Richiesta | Tentata | Esito del flusso | Snapshot consegnato accettato |
|---|---|---|---|
| R1 | sì | `human-gated`, copertura incerta | no |
| R2 | no | dipendenza bloccata | no |
| R3 | no | dipendenza bloccata | no |
| R4 | no | dipendenza bloccata | no |

**0/4 snapshot consegnati accettati; 1 richiesta tentata, 3 non tentate.** La catena
non è completata. I tre blocchi non sono tre fallimenti del modello. Il candidato R1
trattenuto è stato giudicato separatamente: anch'esso non accettato. Non è consegna.
I quattro snapshot consegnati sono rimasti sul tree valido iniziale.

Sorgente runtime congelato: SPB-03 tree
`6e78e725a4c3eee881c1d8b54a1a1abb4facf320`, distinto dal candidato documentale SPB-05.
Clone iniziale LF e tree seed uguale. Nessun cambiamento al source preparato o agli
input storici; nessun altro scenario, modello, replica o bare fresco.

## Il gate osservato, non un giudizio di Jev

R1 ha prodotto due candidati. Il primo test pubblico è uscito con codice 2; dopo una
correzione, il test pubblico è uscito con codice 0. Il review finale ha restituito
`No findings.`, correttamente parsato come `clean`. Questi segnali locali non dimostrano
che tutti i criteri funzionali siano implementati, come conferma l'oracle candidato.

Il controller ha poi inviato alla decisione di copertura le receipt **integrali**:
93.458 byte di JSON. Ricostruendo l'envelope esatto del secondo candidato e verificando
i digest dello stato e della domanda, l'input è **102.108 byte**, contro il limite
`data_bound` di **65.536 byte** in `DecisionEngine.decide`. Il ramo blocca sia Jev sia
il fallback judge **prima della chiamata**. Il motivo salvato è generico:
`insufficient/bound/forbidden/unavailable`; la ricostruzione identifica il bound.

Le preview bounded per fix/review introdotte in SPB-03 non coprono questo passaggio,
che usa ancora le receipt integrali. L'analisi readonly finale e il gate umano sono
stati conservati. Non è stato allargato il limite né interpretata l'incertezza come sì.

**Zero chiamate Jev/judge in questa cella**, pur con i port configurati. Il Pi nativo
ha eseguito builder, review, fix, review e analisi. Non è prova di una decisione live
Pi+Jev riuscita, di indisponibilità del provider o di esaurimento del budget monetario.
È un difetto locale del confine di input semantico, da correggere separatamente dalla
misura. Anche rimuoverlo non autorizza a dichiarare il candidato R1 corretto.

## Confronto più vicino: SPB-02 Yjs Luna

| Cella Yjs Luna | Snapshot accettati | Richieste tentate | Non tentate | Arresto |
|---|---:|---:|---:|---|
| SPB-02 bare | 1/4 | 4 | 0 | nessun gate di dipendenza persistente |
| SPB-02 persistente | 0/4 | 1 | 3 | R1 fallita dopo tre tentativi; review JS non parsata |
| SPB-05 persistente corretto | 0/4 | 1 | 3 | R1 human-gated dopo fix; input coverage oltre bound |

Il bare storico accetta solo R4: non dimostra una catena valida senza regressioni.
Il punteggio persistente non è migliorato. È cambiato il percorso osservato: il parser
arriva a `clean`, il fix riceve osservazioni pubbliche attribuite e il test finale è
verde, ma il confine coverage impedisce una decisione semantica. Non attribuiamo ai
vecchi risultati una causa nuova per deduzione dal solo punteggio.

SPB-02 resta immutato, compresi Lua non confrontabile e i nove blocchi complessivi.
Qui il confronto riguarda soltanto Yjs e le prime quattro richieste dello stesso Luna
medium. SPB-03 cambia il protocollo; non esiste un nuovo controllo bare appaiato.

## Altri vecchi Luna: contesto descrittivo DBH

Le righe seguenti sono le prime quattro richieste delle tre ripetizioni storiche,
**12 snapshot per braccio**, non dodici nuove richieste di questa cella. Sono prefissi
registrati di celle più lunghe, non un nuovo esperimento L4 appaiato.

| Lotto storico / braccio Yjs Luna | Accettati su R1-R4 × 3 | Richieste tentate nel prefisso |
|---|---:|---:|
| DBH / skills-only | 5/12 | 12 |
| DBH / autopilot | 3/12 | 12 |
| DBH / bare | 1/12 | 12 |
| DBH / driver-c1a | 0/12 | 12 |
| DBH / driver-c3a | 0/12 | 12 |
| DBH-drivers2 / driver-c1a | 0/12 | 12 |
| DBH-drivers2 / driver-c3a | 0/12 | 12 |

Provider/modello/thinking, seed e suite sono stati verificati nelle fonti primarie.
Per tutte le 84 richieste di queste righe, il `TASK.md` dell'esatto commit storico
per richiesta, nel repository prodotto conservato, ha lo stesso SHA-256 del task
pubblico preparato corrispondente. La prima ricerca nel contenitore anziché nel
repository `project` non trovava gli oggetti: è conservata come tentativo incompleto,
non come prova di input diversi; la verifica successiva copre ogni riga.

SDK, skill installate, lifecycle print/resume/persistente, policy e correzioni dei driver
non sono automaticamente identici. La deriva del manifest storico già documentata nei
report DBH non viene cancellata. I denominatori, repliche e protocolli diversi impediscono
inferenze causali o di superiorità: questa singola misura **non mostra un miglioramento
di consegna** e non classifica la capacità generale di Luna.

## Costi e consumo cumulativo

Checkpoint attribuito `spb05-report-operator`, successivo alla misura e al confronto:

| Componente | Stima USD |
|---|---:|
| Nuova cella sperimentale SPB-05 | 0,018405720 |
| Esperimento cumulativo, smoke e vecchio pilota inclusi | 0,152822706 |
| Operatore cumulativo dall'intento Luna originario | 16,844220500 |
| Totale dei due componenti al checkpoint | 16,997043206 |

Al cambio contabile originario di 1 EUR = 1,1298 USD: **€15,0443** stimati cumulativi,
**€984,9557** residui rispetto al tetto originale di €1.000. Non è una fattura, un cambio
finale né un hard cap del provider. L'uso operatore successivo al checkpoint resta da
prezzare, non zero. Le stime storiche precedenti mantengono la propria identità.

Consumo cumulativo conservato: **9 launch, 41 reservation, 7 semantic call, 310 charge**.
Rispetto allo storico: un launch e cinque reservation Pi aggiunti, zero semantic call
aggiunte; 268 charge storiche preservate e 42 nuove charge native attribuite. Il budget
residuo non autorizza una nuova replica; la singola authority live è consumata.

## Evidenza, limiti e prossimi gate

Le fonti private conservano authority, ammissione, costi prelaunch, SDK/skill/input hash,
turni e usage, checkpoint, receipt integrali, diff/candidati e snapshot delivered,
oracle immutabili e ricostruzione digest-bound del gate. Il rapporto contiene aggregati,
non sorgenti hidden, canary, credenziali o output grezzi dei test.

Review/QA del rapporto sono inline, seriali e shared-context: non indipendenti. Nessun
full-suite SPB-03 ripetuto per la sola modifica documentale; release profile, hosted CI
sull'head esatto e autorità di delivery restano gate separati. Nessun commit, push, PR,
merge, pubblicazione, installazione, runner, delega o wiki sync.

La diagnosi coverage resta una follow-up separata; i risultati SPB-05 non saranno
riscritti dopo una correzione locale. Qualunque nuova misura, anche sul fix, richiede
nuova authority di scope e ammissione cumulativa dei costi. Nessun replay implicito.
