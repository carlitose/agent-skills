# Richieste vaghe con un utente simulato

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-vague-requests`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-37](../tickets/delivery-bench-hard/done/37-vague-requests.md)
- [DBH-38](../tickets/delivery-bench-hard/done/38-ask-user-simulator.md)
- [DBH-39](../tickets/delivery-bench-hard/done/39-vague-lot.md)

## Type
Feature del banco più misura.

## Problem
Le richieste di delivery-bench-hard sono specifiche chiuse e precise: circa 200 parole, con i
messaggi d'errore esatti e i casi limite. Misurano quanto bene un braccio esegue, non quanto bene
chiarisce. Una persona vera scrive richieste corte e incomplete. Le skill di `pi-full` (routing,
spec, grilling) dovrebbero servire proprio lì: chiedere prima di scrivere codice. Il banco oggi
non lo può vedere.

## Decisions (utente, 2026-10-07: «ok tutto», poi «l'agente utente sa che ruolo ha e sa che deve
rispondere uguale a tutti i bracci»)
1. **Scenari:** gli stessi tre (`lua-vm`, `sql-engine`, `crdt-yjs`), con le richieste riscritte in
   forma vaga. I test nascosti non cambiano e restano il giudice ufficiale.
2. **Utente simulato:** `openai-codex/gpt-6-sol`, tramite l'abbonamento ChatGPT. Ha la richiesta
   completa e risponde solo a ciò che gli chiedono, senza aggiungere dettagli di sua iniziativa.
3. **Domande:** lo strumento `ask_user`. L'agente scrive una domanda e riceve subito la risposta,
   senza fermare il lavoro. Tutti i bracci hanno lo strumento.
4. **Limite:** al massimo 10 domande per richiesta. Nel report il numero di domande è una colonna
   a parte; chi non fa domande non viene penalizzato.
5. **Bracci:** `pi-tools`, `pi-full`, `bare-goal`.
6. **Catene:** 4 richieste, 3 ripetizioni, per il confronto diretto con `dbh-luna3d` e
   `dbh-luna3e`, che usano le richieste precise.
7. **Ruolo del simulato:** sa di essere l'utente che ha chiesto il lavoro e risponde allo stesso
   modo a tutti i bracci.

## Target behavior
1. **Richieste vaghe.** Per ogni scenario, le richieste 1–4 hanno una versione vaga: 2–5 frasi
   scritte come le scriverebbe l'utente, con l'obiettivo e senza i dettagli. Esempio: al posto
   delle regole complete di `table.freeze` resta «vorrei poter congelare le tabelle, così nessuno
   le modifica per sbaglio». La versione precisa resta il brief del simulato. Le versioni vaghe
   stanno nel repo privato accanto alle richieste precise e sono fissate nel lotto con il loro
   sha256, come le suite.
2. **Strumento `ask_user`.** È un'estensione Pi caricata in tutti e tre i bracci. Ha un solo
   parametro, `question`, e la descrizione «Pregunta al usuario que hizo el encargo». Il prompt
   del banco non cambia. Dopo la decima domanda lo strumento risponde, senza chiamare il
   simulato, che le domande per questo encargo sono finite.
3. **Simulato.** Il runner chiama `gpt-6-sol` in una sessione separata, con istruzioni fisse:
   - sei l'utente che ha chiesto il lavoro; il brief è la richiesta precisa (più le precedenti
     della catena, che l'utente ricorda);
   - rispondi solo a ciò che è chiesto, in modo breve, con i dati del brief; non dare codice, non
     rivelare test, non suggerire soluzioni non chieste; se il brief non lo dice, rispondi «no lo
     sé, decide tú»;
   - rispondi allo stesso modo a chiunque chieda.
   Il simulato non vede il nome del braccio, il ledger o il codice dell'agente: riceve solo il
   brief e la domanda.
4. **Stessa domanda, stessa risposta.** Le risposte sono salvate per scenario e richiesta. La
   stessa domanda, normalizzata (minuscole, spazi compressi), riceve la stessa risposta in ogni
   braccio e ripetizione, senza nuova chiamata al modello.
5. **Registrazione.** Ogni domanda e risposta va nel tentativo: testo, ora, se viene dalla cache,
   costo. Il costo del simulato è riportato a parte e non entra nel costo del braccio.
6. **Valutatore di `/goal`.** Valuta come oggi il testo di `TASK.md`, che ora è la versione vaga.
   Il risultato ufficiale resta quello dei test nascosti.
7. **Report.** Accettazione per braccio confrontata con la stessa posizione nelle catene precise;
   domande per richiesta (media, massimo, quante dalla cache); poi il giudizio di qualità come
   per DBH-32.

## Non-goals
- Cambiare le richieste precise, le suite o i lotti già misurati.
- Valutare la qualità delle domande con un giudice: si contano soltanto.
- Bracci Crew o catene da 12 su richieste vaghe.

## Failure modes
- Il simulato rivela più del brief, per esempio codice o nomi dei test: le istruzioni lo
  vietano, e un controllo del runner rifiuta risposte che contengono nomi di file dei test
  nascosti o il canary dello scenario.
- Il simulato dà risposte diverse a domande uguali: la cache lo impedisce.
- Il provider del simulato non risponde: il tentativo è infrastrutturale e il runner ripete, come
  per il modello del braccio.
- Una richiesta vaga è troppo vaga anche per un umano: l'utente rivede tutte le versioni vaghe
  prima del lotto (DBH-37).

## Verification
- Unit test del runner: la cache restituisce la stessa risposta; il limite di 10; il simulato non
  riceve il nome del braccio; le risposte con nomi di test o canary vengono rifiutate; il costo
  del simulato è separato.
- Preflight senza lotto dei tre bracci, con una domanda vera a `gpt-6-sol`.
- A fine lotto: ledger, celle e report completi.

## Gates
Risposte dell'utente del 2026-10-07 («ok tutto» alla proposta di gate).
- Tentativo: per DBH-37 un set di 12 richieste vaghe nel repo privato, approvato dall'utente;
  per DBH-38 una PR con CI 8/8; per DBH-39 un lotto `dbh-vague` completo, 3
  bracci × 3 scenari × 3 ripetizioni, catene da 4.
- Budget per tentativo: nessun tetto. Braccio e simulato passano dall'abbonamento ChatGPT a
  canone fisso tramite OAuth; la spesa a prezzo di listino resta nel report.
- Tempo per tentativo: 24 ore. Tentativi massimi: 2.
- Approvazioni: l'agente fa il merge delle PR con CI 8/8 e `--match-head-commit`. L'utente
  approva le richieste vaghe prima del lotto. Nessun deploy né pubblicazione.
- Versione esatta: nessuna. Il lotto lega le skill e le estensioni installate quando parte.
- Blocchi esistenti cercati (runner, lotti, memorie):
  - un solo lotto alla volta: `dbh-vague` parte dopo `dbh-chain12`;
  - durante un lotto il checkout principale di `agent-skills` non si aggiorna, e niente
    `update:personal`;
  - Docker Desktop deve essere avviato.
