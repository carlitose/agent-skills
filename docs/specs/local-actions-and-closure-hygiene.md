# Azioni necessarie e pulizia in chiusura

## Artifact Graph
- Artifact ID: `spec:local-actions-and-closure-hygiene`
- Role: `spec`
- Standalone: true

### Related
- [Retenzione prima della pulizia dei worktree](worktree-cleanup-retention.md)
- [GC dei worktree del runner](ticket-autopilot-orphan-worktree-garbage-collection.md)
- [Revisione del piano](plan-review-checkpoint.md)

## Tipo e fonte
Decisione di workflow, da attuare come istruzioni agli agenti, non come cancellatore automatico.
Fonte: nella sessione Pi `01a1d44a-0296-77b2-947c-36d3861c371c`, il 2026-11-13,
l'utente ha risposto «Q1 si, Q2 si Q3 si Q4 si Q5 si» alle cinque domande.
Q5 è la riparazione separata [#488](https://github.com/carlitose/agent-skills/pull/488).
Questa spec attua Q1–Q4 senza riaprire quelle decisioni.

## Problema e obiettivo
Gli agenti accumulano worktree, copie di sorgenti e ambienti dentro la directory Git;
la pulizia del runner copre soltanto le risorse di cui il runner dimostra la proprietà.
Inoltre chiedono conferme per passaggi già necessari alla consegna richiesta.

Obiettivo: eseguire le azioni necessarie già coperte dal mandato e, in chiusura,
rimuovere il materiale dell'agente recuperabile senza perdere lavoro unico.
Le regole valgono in tutte le lane; non selezionano Autopilot e non alterano i suoi gate.

## Decisioni approvate
### Q1 — Chiusura
Dopo merge/chiusura di una PR e alla fine della sessione, inventariare risorse e spazio.
Rimuovere senza una nuova domanda solo risorse attribuibili al lavoro dell'agente,
non più in uso e recuperabili: worktree, branch locali con remoto scomparso, temporanei,
cartelle di lavoro create dall'agente dentro la directory Git.
Una PR ancora aperta o un handoff attivo richiedono di conservare il checkout necessario.

Prima di rimuovere lavoro non presente su `main` o sul remoto, salvare e verificare
una copia recuperabile fuori dal bersaglio: patch binaria con base identificata per le
modifiche, copia dei file non tracciati e, se necessario, bundle dei commit unici.
Una patch vuota non salva commit unici; una patch del diff non salva file non tracciati.
Se la recuperabilità non è verificabile, conservare e riportare il motivo.
Il nome della cartella e il marcatore `[gone]` non provano proprietà o integrazione.

Non toccare dati dell'utente, `.git/private`, `node_modules` e `.venv` del checkout
principale. Non seguire symlink/junction fuori dal bersaglio. Conservare risorse altrui,
risorse attive, prove uniche, lock e operazioni Git interrotte. Nessun `reset --hard`,
`clean -fdx`, rimozione forzata o cancellazione ricorsiva indiscriminata.
I worktree del runner passano dai controlli e dalle ricevute già esistenti, non da un
percorso alternativo. Una copia di recupero non annulla un loro rifiuto.

### Q2 — Allarme spazio
Misurare la directory Git comune effettiva, anche da un worktree con `.git` file.
Sopra 1 GB (`1,000,000,000` byte), riportare le cinque sottocartelle immediate più
grandi, ordinate per byte senza contare due volte sottoalberi. Non leggere contenuti
privati né seguire link. Dichiarare misure parziali/errori, mai trasformarli in zero.
Pulire solo quanto ammesso da Q1/Q3; la soglia è un allarme, non autorità aggiuntiva.
Riportare spazio prima/dopo, rimosso e conservato con motivo.

### Q3 — Run integrati
Per run tutti durabilmente integrati da più di 14 giorni, conservare ledger, storia,
manifeste, ricevute e prove uniche. I 14 giorni sono l'età minima prima della pulizia
dei materiali pesanti, non una scadenza per cancellare i registri piccoli.
Rimuovere soltanto copie rigenerabili: archivi/bundle di sorgenti, ambienti Python e
`node_modules` copiati. Usare la data di integrazione osservata, non mtime o nome.
Non basta l'estensione: un bundle che trattiene commit unici resta; un archivio referenziato
resta se la sua assenza rompe verifica, replay o recupero e non è rigenerabile esattamente.
Run attivi, non integrati, recenti, senza data certa o con riferimenti operativi restano.

### Q4 — Azioni necessarie
Un'azione necessaria al risultato richiesto, locale e reversibile non richiede un'altra
conferma. Sono coperti build/installazione di prova su telefono collegato o emulatore,
dipendenze di sviluppo, server di sviluppo, branch e commit; l'approvazione include
esplicitamente anche aprire PR nel repository dell'utente, pur essendo un effetto remoto.
Riportare le azioni nel resoconto. Non sostituire dati personali del telefono né esporre
il server pubblicamente per inferenza.

Restano decisioni esplicite: merge, pubblicazione su store/produzione, spese, credenziali
e account, cancellazione di dati non dell'agente e messaggi ad altri. L'eccezione PR non
si estende a messaggi, issue o altre pubblicazioni. La domanda «un no fermerebbe il lavoro?»
non è da sola una prova di autorizzazione. Restrizioni esplicite e rifiuti reali del runtime
restano validi; nessun bypass di permessi o consenso inventato.

## Invarianti e non-obiettivi
- Una sola fonte per la procedura dettagliata; puntatori dai default e dalla chiusura.
- Nessun nuovo scheduler, formato di grant, hook che cancella file, dipendenza o servizio.
- Non cambiare merge, deployment, credenziali, sincronizzazione Pi o reload.
- Non ripulire qui l'arretrato di betsharemarket/easylanguage/agent-skills: presentare prima
  una proposta per cartella; l'inventario precedente non autorizza quelle cancellazioni.
- Conservare le modifiche estranee nel checkout principale e lasciare le PR aperte.

## Piano unico di implementazione
1. Scrivere un riferimento operativo in `ask-skills/`, distinguendo azioni necessarie,
   chiusura, recuperabilità, allarme e materiali dei run.
2. Collegarlo dai default condivisi; rendere condizionata alla recuperabilità la pulizia
   post-PR nella policy iniettata e allineare i puntatori skills-only/worktree.
   Nessun nuovo hook o modifica del comportamento dei comandi del runner.
3. Aggiungere test strutturali per trigger, esclusioni, soglie e confini di autorità;
   aggiornare le fixture di contesto con misurazioni reali senza alzare il ceiling.
4. Eseguire controlli mirati, lint, graph/link check, review inline e QA. Consegnare
   separatamente dalla #488; non dichiarare che un test testuale provi obbedienza runtime.

## Accettazione e verifica
- La policy raggiunge il riferimento da ogni lane senza introdurre un secondo consenso.
- I test distinguono PR aperta da chiusa, `[gone]` da prova di ritenzione, archivio
  rigenerabile da unica copia; tutti i protetti di Q1 e Q3 sono espliciti.
- 1 GB e oltre 14 giorni sono letterali, con significato e confini non ambigui.
- La concessione PR non concede merge, messaggi, spesa o dati dell'utente.
- Link e Artifact Graph si validano; test e guida del context budget concordano con
  la misura e il ceiling esistente resta rispettato.
- Evidenza prevista: statica e test strutturali locali; nessuna cancellazione reale,
  build sul telefono o prova di enforcement del modello è dichiarata eseguita.

## Gates
- Attempt: dalla spec al relativo handoff di implementazione; precedenti tentativi CI
  della #488 restano separati, con identità e costi originali.
- Budget, tempo per attempt e massimo tentativi: nessun limite impostato.
- Versione esatta: nessuna richiesta.
- Approvazioni: Q1–Q4 concesse dalla risposta citata; commit e apertura PR inclusi in Q4.
  Merge, pubblicazione, spesa, sincronizzazione/reload Pi e pulizia dell'arretrato non concessi.
- Sequenza Q5: riparazione separata pronta nella #488, CI quick verde sul suo head;
  merge e CI full su `main` restano aperti. Questa modifica parte da quell'head in un
  worktree separato, senza dichiarare `main` riparata o usare quick come prova full.
- Limiti trovati: ceiling `176903` byte in `context-budget-ceilings-v1.json`; margine
  della #488 di 6 byte. Limiti di righe in `scripts/file-limits.json`; ownership e lock
  in `ticket-autopilot/references/worktrees.md`; autorità e handoff in `skills-only.md`.
  La #487 modifica la stessa closure e richiederà riconciliazione prima del merge.
- Blocchi ulteriori: nessuno trovato nella policy iniettata, nei default, nei contratti
  di worktree/skills-only e nelle configurazioni di controllo consultate. I gate aperti
  bloccano soltanto le rispettive operazioni; nessuna autorizzazione nuova è inferita.
