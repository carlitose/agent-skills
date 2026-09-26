# delivery-bench — misurare come si consegna software, non solo se

## Artifact Graph
- Artifact ID: `artifact:delivery-bench`
- Role: `wayfinder`
- Standalone: true

### Children
- [DB-01](../tickets/delivery-bench/done/01-oracle-contract-and-run-protocol.md)
- [DB-02](../tickets/delivery-bench/done/02-trap-catalog-review.md)
- [DB-03](../tickets/delivery-bench/done/03-python-scenario-bench38-chain.md)
- [DB-04](../tickets/delivery-bench/done/04-c-scenario.md)
- [DB-05](../tickets/delivery-bench/done/05-typescript-frontend-scenario.md)
- [DB-06](../tickets/delivery-bench/done/06-runner-and-profile-report.md)
- [DB-07](../tickets/delivery-bench/done/07-pilot-chain-1-all-arms.md)
- [DB-08](../tickets/delivery-bench/08-full-measurement.md)

## Type
Wayfinding spec

## Status
Active. Decisa in un'intervista (grilling) il 2026-09-26. Pilota eseguito (DB-07,
[risultati](../research/delivery-bench-pilot.md)); misura completa in corso (DB-08).

## Destination
Un benchmark nostro, privato, che per ogni **braccio** (modo di lavorare) dice **quando conviene**:
un profilo a cinque assi, senza pesi, su catene di richieste di lunghezza 1, 3 e 8 in tre
scenari (Python, C, frontend TypeScript). Deve far emergere ciò che né Terminal-Bench né
bench38 vedono: sui task lunghi, chi tiene la rotta e a che costo. Risultato atteso: una tabella
braccio × lunghezza × scenario con accettazione, robustezza, bussola, costo, tempo, e la
raccomandazione operativa che ne segue ("per task da N richieste usa X").

## Perché non basta quello che c'è
- **Terminal-Bench 4.0** (63 task originali, una ripetizione): Pi nudo 15/63, skills-only 16/61,
  differenza +1, p = 1. I task sono problemi tecnici da risolvere in un colpo: il braccio non
  cambia il risultato. Vedi [terminal-bench-best-arm](terminal-bench-best-arm.md).
- **bench38** (una consegna Python con 5 difetti latenti di arrotondamento): Pi nudo 0/5,
  skills-only 3/5, Autopilot 0-3/5 a 20× il costo. Il braccio conta, ma è **una** consegna
  corta: non dice nulla sui task lunghi né sulla perdita di contesto. Vedi
  [ticket-driver](ticket-driver.md).
- Osservazione dell'utente da confermare con dati: Autopilot completo «è una schifezza per
  piccoli task, ma su task lunghi non perde il contesto rispetto a skills-only».

## Decisions So Far
Tutte prese dall'utente nell'intervista del 2026-09-26; il record durevole è questa mappa.

1. **Scopo**: scegliere il modo di lavorare per consegne software reali (non misurare la
   capacità generale dell'agente, per cui esiste Terminal-Bench).
2. **Input uguale per tutti**: la richiesta grezza e il repo com'è in quel momento. Ogni braccio
   scompone a modo suo: Pi nudo parte a lavorare; skills-only scrive la spec, la divide in ticket
   e li esegue; il driver esegue i ticket nel driver; Autopilot li manda al runner. **Mai** una
   catena di ticket precotta: la scomposizione è parte del braccio misurato.
3. **Giudizio solo sul repo finale**, con una suite nascosta che nessun braccio vede mai.
4. **Lunghezza = richieste in sequenza**: la richiesta N+1 arriva solo a consegna avvenuta della
   N e dipende da scelte prese prima. Catene da 1, 3 e 8, ognuna **prefisso** della successiva;
   la catena da 1 dello scenario Python è bench38 così com'è.
5. **Scenari**: Python (bench38 esteso), **C** (programma piccolo con parser, memoria e limiti:
   i latenti sono overflow, off-by-one, ownership), **frontend TypeScript** (Svelte, API finte,
   verifier Playwright deterministico: comportamento, stato, accessibilità; mai pixel). Niente
   .NET, per scelta dell'utente.
6. **Bracci, ciascuno nel suo modo naturale**: Pi nudo (una sessione per tutta la catena);
   skills-only (una sessione, spec → ticket → esecuzione inline); driver c1a; driver c3a con
   giudizi Jev; Autopilot completo (spec → ticket → runner → merge). Non si forza la stessa
   memoria: la differenza di memoria è ciò che si misura.
7. **Profilo a cinque assi, senza pesi**: accettazione (test nascosti per richiesta);
   robustezza (difetti latenti trovati); **bussola** (invarianti trasversali violate lungo la
   catena, comprese le trappole di memoria); costo (token e USD stimati, Jev a parte); tempo
   (dal primo all'ultimo evento). Nessun numero unico.
8. **Trappole di memoria**: regole piantate nelle richieste 2-3 che le richieste 6-8 tentano di
   violare. Catalogo: deprecato (nuovi usi di un simbolo deprecato = 0, controllo statico);
   decisione architetturale (es. importi in centesimi interi, mai float); bug chiuso che non
   deve tornare; contratto di output che non cambia quando viene esteso; convenzione di nomi,
   cartelle, errori. Per ogni trappola si registra la **distanza in richieste** tra regola e
   tentazione, così si vede dove il braccio si perde, non solo se.
9. **Ripetizioni**: 3 sulle catene da 1 e 3, 1 sulla catena da 8; si ripete la 8 solo dove serve
   a decidere. Regola statistica di TBA-03 (McNemar appaiato, differenza minima 3) per l'asse
   accettazione; gli altri assi si leggono in modo descrittivo.
10. **Oracolo**: **Claude Fable (questa istanza Pi)** scrive richieste, suite nascoste e
    trappole in un repo privato del benchmark e in sessioni separate; i bracci girano su
    `openai-codex/gpt-6-sol`. Famiglie di modello diverse tra chi scrive e chi è misurato: il
    limite di bench38 (stessa famiglia) non si applica. L'utente rivede solo il catalogo delle
    trappole e i punti in cui sono piantate, non il codice nascosto.
11. **Regole di isolamento**: il braccio riceve solo la richiesta corrente e il repo pubblico di
    quel momento; mai la suite nascosta, mai le richieste future, mai questa mappa. La suite
    nascosta vive fuori da ogni checkout che il braccio può leggere.

## Not Yet Specified
- Il contratto esatto dell'oracolo: formato della richiesta, formato della suite nascosta,
  come si esegue la suite su un repo consegnato (container per scenario), come si registra
  il profilo (DB-01).
- Il catalogo concreto delle trappole per scenario, con distanze (DB-02, revisione umana).
- Come Autopilot riceve la richiesta grezza: la spec la scrive il braccio con `to-spec`, i
  ticket con `to-tickets`, poi `ticket-autopilot`; il merge avviene nel repo del benchmark.
  Da confermare in DB-01 che il runner accetti un repo effimero senza provider remoto, o quale
  provider locale usare.
- Un tetto di tempo per catena (le catene da 8 con Autopilot possono durare ore).

## Out of Scope
- Leaderboard pubblici, confronto con altri modelli, .NET.
- Migliorare i bracci mentre si misura: lo sviluppo del vincitore resta in
  [terminal-bench-best-arm](terminal-bench-best-arm.md) (TBA-04), e in seguito qui, ma non
  nello stesso lotto della misura.
- TBA-05 (benchmark privato «condizionale») è **superato** da questa mappa: va chiuso come
  sostituito con `change-status-ticket`, non eseguito.

## Frontier / Blocking Edges
- **Contratto dell'oracolo** (DB-01): blocca tutto; si sblocca con un documento di contratto e
  un runner minimo che esegue una suite nascosta su un repo consegnato.
- **Catalogo trappole approvato** (DB-02): blocca gli scenari; si sblocca con la revisione
  dell'utente.
- **Tre scenari con suite nascoste e latenti seminati** (DB-03/04/05): bloccano il runner
  completo; si sbloccano quando la soluzione di riferimento passa tutto e uno stub fallisce.
- **Pilota sulla catena da 1** (DB-07): blocca la misura completa; si sblocca quando i cinque
  bracci producono un profilo confrontabile senza guasti dell'harness.

## Ticket Plan
| ID | Tipo | Modo | Bloccato da | Titolo | Output atteso |
|---|---|---|---|---|---|
| DB-01 | research | AFK | — | Contratto dell'oracolo e protocollo di esecuzione | `docs/research/delivery-bench-oracle-contract.md` |
| DB-02 | grilling | HITL | DB-01 | Catalogo delle trappole, revisione umana | catalogo approvato per scenario |
| DB-03 | task | AFK | DB-02 | Scenario Python: catena da 8 su bench38 | repo privato con richieste 1-8, suite nascosta, latenti |
| DB-04 | task | AFK | DB-02 | Scenario C | idem |
| DB-05 | task | AFK | DB-02 | Scenario frontend TypeScript | idem, verifier Playwright |
| DB-06 | task | AFK | DB-01 | Runner e report a profilo | comando unico per braccio × scenario × lunghezza |
| DB-07 | task | HITL | DB-03, DB-04, DB-05, DB-06 | Pilota: catena da 1, cinque bracci | profilo a 5 assi × 3 scenari, guasti dell'harness |
| DB-08 | task | HITL | DB-07 | Misura completa | tabella finale e raccomandazione operativa |

## Next Review
- Dopo DB-01: il contratto risponde alle domande in *Not Yet Specified*? Il runner minimo
  esegue una suite nascosta su un repo consegnato senza toccarlo?
- Dopo DB-07: i cinque bracci hanno profili confrontabili? Quali guasti dell'harness sono
  emersi e sono stati ripetuti?
