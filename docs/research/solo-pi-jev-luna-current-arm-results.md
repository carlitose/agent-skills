# Benchmark Luna con il braccio Pi + Jev corrente

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-luna-current-arm-results`
- Role: `research`
- Parent: [SPB-14](../tickets/solo-pi-jev-luna-pilot/14-current-arm-benchmark.md)

## Risultato, in parole semplici
**Nessuno dei tre primi lavori è stato completato e consegnato.**
Sono stati provati tre progetti diversi, non soltanto Yjs. In ogni progetto il primo
lavoro è stato tentato con il ciclo di correzione previsto, poi il sistema si è fermato.
I tre lavori successivi dipendevano dal primo e non sono stati tentati.

| Progetto | Consegne accettate | Lavori tentati | Non tentati |
|---|---:|---:|---:|
| Lua VM | 0/4 | 1 | 3 |
| SQL engine | 0/4 | 1 | 3 |
| Yjs | 0/4 | 1 | 3 |
| Totale | **0/12** | **3** | **9** |

0/12 è il punteggio di consegna della catena, NON dodici fallimenti indipendenti.
Successo fra i lavori realmente tentati: 0/3. In ogni scenario R1 ha tre fallimenti
finali di qualità; in questa coorte non sono osservati gate tecnici o di budget.
I test ordinari passavano sui candidati finali: non bastavano a dimostrare la nuova funzione.

## Perché si è fermato
- **Lua:** Luna ha dichiarato di non riuscire a implementare la modifica in sicurezza,
  senza cambiare file. Il parser non aveva gli operatori di assegnazione composta richiesti.
  Review blocker concreto, candidato=seed, test originali verdi ma funzione nuova assente.
  Non è stata richiesta una decisione Jev/judge perché il blocker impediva l'accettazione.
- **SQL:** ha prodotto codice, ma review trova problemi nelle window functions con aggregati
  e ordinamento di NULL. Jev dà NO sulle prime coperture; sul candidato finale c'è fallback
  al judge che dà NO. Anche il candidato finale non passa la verifica privata del benchmark.
  Jev ha inoltre valutato realmente il rischio di alcune funzioni Python.
- **Yjs:** test ordinari verdi e review «No findings.»; la decisione finale del judge è NO,
  e la verifica privata respinge il candidato. È la r5 già osservata, riusata senza rilancio.
  Il judge non conserva una spiegazione dettagliata del NO: non la inventiamo.

## Che cosa abbiamo davvero valutato
Un solo braccio `pi-jev-persistent`, stesso `openai-codex/gpt-6-luna` medium,
runtime congelato SPB-12 `1d35fbe2938a08d89bef9cb40aba92a8de66b77e` per tutti e tre.
Lua e SQL sono due nuove celle seriali; Yjs riusa r5 con la sua identità/tempo originali.
Un processo/sessione per cella, shutdown exit0, tentativi/candidati/consegnati conservati.
È osservato il percorso di rifiuto, incluso risk Python/NO diretto Jev e fallback judge SQL;
non la consegna positiva, i lavori R2-R4 o l'accuratezza generale dei giudici.
Questa combinazione non porta a casa nessuna prima consegna nel piccolo lotto osservato.
Non possiamo dedurre un miglioramento rispetto a Luna da solo: nessun nuovo bare appaiato.

## Benchmark invariato, storico separato
Task/seed/richieste/suite/oracle/test command/modello/SDK/skills/settings/argv/question/policy
validati contro primarie e manifest; immagini Docker già presenti. Nessun criterio di
accettazione o score cambiato, nessun hidden feedback o intervento manuale sul prodotto.
Le vecchie versioni del braccio, compresa r4 precedente alla riparazione SPB-12, non vengono
ricalcolate, rinominate o mescolate. Lo stesso braccio rimane invariato tra questi scenari.
Riuso Yjs è esplicito, non una replica nuova o un risultato scelto dopo ulteriori lanci.

## Provenienza e tempi
- Lua: `spj-luna-current-arm-l4/cells/lua-vm.pi-jev-persistent.r1`, PID35460,
  session01a0fdc8-a88e-7034-a5ad-a512f2c99e95, 278.063s.
- SQL: `spj-luna-current-arm-l4/cells/sql-engine.pi-jev-persistent.r1`, PID16292,
  session01a0fdcd-6803-7185-9dce-4a2448fb39ff, 942.546s.
- Yjs riusato: `spj-luna-corrected-l4-5/cell`, PID28344,
  session01a0fd6c-fa1d-7395-833b-e3dd24a7b90d, 423.437s.
Dati privati sotto `C:/Users/CGS03/dbench-private/results/`; tempi includono oracle e non
sono una misura comparativa di velocità fra bracci o del solo modello.

## Costi e limiti
Checkpoint: esperimenti cumulativi $0.233689834, operatore $29.971153600,
totale stimato SDK $30.204843434 = circa €26.7347 al FX contabile originale1.1298.
Le due nuove celle Lua/SQL aggiungono $0.022275836 di esperimento, non il costo totale.
Consumi cumulativi **14 launch,79 reservation,19 semantic call,487 charge**, gate=null.
Budget originale €1000 invariato; nessun reset o nuova fattura/cap provider dedotto.
Uso operatore dopo checkpoint non incluso/non zero, invoice e FX finale ignoti.

Un tentativo iniziale di preparazione Lua confrontava erroneamente una directory Git
(incluso .git) con il seed senza .git: fermato prima di qualsiasi lancio. Record conservato;
corretto il solo confronto metadata su file seed/byte, riprese risorse vuote, zero replay.
Anche l'assert del generatore caller prima della scrittura è un errore di setup, non trial.
Nessun nuovo bug del braccio dimostrato in queste due celle; questo non è prova di assenza
di bug altrove. Nessuna suite runtime invariata ripetuta. Review/QA/audit inline shared-context;
release profile/exact-head CI/integrazione/installazione non eseguiti. Nessun runner/delega,
commit/push/PR/merge/install/reload/wiki sync. I risultati negativi non autorizzano altri lanci.
