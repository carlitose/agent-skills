# delivery-bench difficile — pilota: catena da 1

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-pilot`
- Role: `research`
- Parent: [DBH-08 — Pilota: catena da 1](../tickets/delivery-bench-hard/done/08-pilot.md)

## Stato
Output di DBH-08 (2026-09-28). Il lotto `dbh` fa girare i cinque bracci sui tre scenari nuovi
(`lua-vm`, `sql-engine`, `crdt-yjs`) con `openai-codex/gpt-6-luna` e `--thinking medium`: 3
ripetizioni fino alla richiesta 1, 45 celle. Record, giudizi e ledger stanno nel repo privato
dell'oracolo (`results/dbh/`). Qui ci sono solo aggregati, senza nomi di controlli, trappole,
richieste o difetti.

In breve: il regime nuovo non sta più al soffitto, sta al pavimento. Una sola richiesta accettata
su 45. In 37 celle su 45 la cartella consegnata è identica al seme: il braccio legge, dichiara il
lavoro troppo grande o bloccato, e si ferma senza toccare il codice. Una richiesta dura da 33 a
329 s, contro un tetto di 5400 s. La regola di TBA-03 dà «indistinguibile» per tutti i bracci.
La spesa è di 0,25 $.

## Autorizzazione e provenienza
- **Autorità del lotto**: `results/dbh-authority.json` (sha256 `52597cbf…`), letta con la
  conferma di DBH-01 (`results/dbh-01-confirmation.json`, sha256 `b2aa1f31…`). Copre pilota e
  misura completa, i cinque bracci, i tre scenari e 3 ripetizioni. Nomina modello e thinking, e
  il lotto li registra.
- **Scenari**: quelli verificati in DBH-05/06/07. Le suite nascoste del lotto sono le stesse dei
  report di verifica: `lua-vm` `f90869af…`, `sql-engine` `5b029cb4…`, `crdt-yjs` `be281cb4…`.
  Prima del lancio i tre `scenario.json` hanno avuto il comando di test dei driver
  (`driver_test_command`, `python dev.py test`). Senza, il runner avrebbe dato ai driver il
  comando di default del linguaggio, che su questi semi non è il comando di test.
- **Harness e driver**: runner di `main` `b22b985` (DBH-11). Le copie del driver vengono da un
  checkout pulito dello stesso commit con `prepare-drivers --source`, che registra commit e
  albero. Pi 0.87.1. Le skill installate, usate da skills-only e Autopilot, sono quelle del
  manifest del 24/09, le stesse di `luna-calib`. Non sono state aggiornate apposta, perché i
  bracci restino uguali fra pilota e misura completa.
- **Primo lancio annullato**: il primo `run-lot` è partito con il tetto di 5400 s, che la
  cattura dei processi rifiutava. Le prime 4 celle hanno fatto 12 tentativi, tutti
  `infra:harness`, in 0 s e senza spesa. Il lotto è stato fermato a mano e archiviato a parte
  nel repo privato. Il difetto è stato corretto fra due `run-lot` (DBH-11, #382), e il lotto
  `dbh` è stato riaperto da capo.
- **Esecuzione**: il 28/09 dalle 16:02 alle 16:42 UTC, con 4 celle in parallelo. 45 tentativi,
  nessun retry d'infrastruttura, nessun timeout, nessuna cella invalidata dall'audit, nessuna
  compaction. `judge-gated` non ha trovato candidati fermi a un cancello.
- **Spesa**: 0,248 $ stimati da Pi, contro un tetto di 40 $. Jev non è stato chiamato: nessun
  candidato di c3a è arrivato alla revisione. Tempo di parete 40 minuti, contro 12 ore.
- **Rigiudizio di controllo**: 4 celle, una o due per scenario, scelte fra quelle con più
  controlli passati. Il secondo giudizio dà lo stesso albero, la stessa suite, lo stesso esito
  su ogni controllo e gli stessi assi.

## Risultati

### Per braccio (3 scenari × 3 ripetizioni, 9 celle)
| Braccio | Accettate | Feature passate | Latenti trovati | Invarianti rotti | Celle senza modifiche | USD (Pi) | Mediana s |
|---|---:|---:|---:|---:|---:|---:|---:|
| bare | 0/9 | 8/45 | 3/30 | 0/9 | 6/9 | 0,04 | 105 |
| skills-only | 1/9 | 9/45 | 4/30 | 0/9 | 5/9 | 0,06 | 71 |
| autopilot | 0/9 | 0/45 | 0/30 | 0/9 | 9/9 | 0,05 | 88 |
| driver-c1a | 0/9 | 4/45 | 1/30 | 0/9 | 8/9 | 0,05 | 65 |
| driver-c3a | 0/9 | 0/45 | 0/30 | 0/9 | 9/9 | 0,04 | 62 |

Alla richiesta 1 non ci sono trappole misurabili: le tentazioni arrivano dalla richiesta 8.

### Per scenario
| Scenario | Accettate | Feature passate | Latenti trovati | Celle senza modifiche |
|---|---:|---:|---:|---:|
| `crdt-yjs` | 1/15 | 17/75 | 7/45 | 9/15 |
| `lua-vm` | 0/15 | 4/90 | 1/45 | 14/15 |
| `sql-engine` | 0/15 | 0/60 | 0/60 | 14/15 |

Il lavoro che c'è si concentra su `crdt-yjs`, con `bare` e skills-only: 6 delle 8 celle che
toccano il codice. Lì due celle restano a una feature dall'accettazione, e una la raggiunge.

### Regola di TBA-03 (accettazione appaiata con `bare`)
| Braccio | Coppie | Braccio | bare | Solo braccio | Solo bare | Differenza | Holm p | Decisione |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 1 | 0 | 1 | 0 | +1 | 1 | indistinguishable |
| autopilot | 9 | 0 | 0 | 0 | 0 | +0 | 1 | indistinguishable |
| driver-c1a | 9 | 0 | 0 | 0 | 0 | +0 | 1 | indistinguishable |
| driver-c3a | 9 | 0 | 0 | 0 | 0 | +0 | 1 | indistinguishable |

Vince `bare` per il pareggio al braccio più semplice.

### Esiti del driver
- **c1a**: 8 run falliti con candidato vuoto (il builder non ha lasciato modifiche), uno
  integrato, non accettato.
- **c3a**: 9 run falliti con candidato vuoto.
- Nessun run fermo a un cancello, quindi niente da giudicare a parte.

### Autopilot
In 9 celle su 9 l'orchestratore non arriva a un'implementazione. Dal suo resoconto finale si fermano
tutte prima del lavoro, su vincoli del suo protocollo: la richiesta non è un ticket nel formato
che il runner accetta, il repository non ha un provider che riconosce, o il worktree andrebbe
fuori dalla cartella della cella. È il braccio nel suo modo naturale, come nella prima misura.

### Durata delle richieste
45 richieste, un tentativo ciascuna: minimo 33 s, mediana 82 s, 90° percentile 216 s, massimo
329 s (tempo di parete massimo 332 s). Il tetto di 5400 s non si avvicina mai: i bracci si
fermano da soli.

## Tetti per la misura completa
- **Per richiesta: 5400 s, invariato.** La durata osservata arriva a 329 s, un sedicesimo del
  tetto, quindi il tetto non taglia niente e non costa niente. Abbassarlo toccherebbe solo i
  tentativi lunghi e rari, che sono proprio quelli da osservare nelle catene lunghe, dove il
  contesto cresce.
- **Per catena: tetto per richiesta × lunghezza**, come nell'autorità.
- **Spesa e parete**: al ritmo osservato le catene da 4 (3 ripetizioni) e da 12 (ripetizione 1)
  valgono circa 255 richieste nuove. Stimo pochi dollari e poche ore, contro 250 $ e 72 ore.

## Lettura
1. **Il regime è passato dal soffitto al pavimento.** Con sol sugli scenari facili i bracci
   accettavano quasi tutto. Con luna sui sistemi maturi, alla richiesta 1 ne accettano una su 45.
2. **Il limite è la disponibilità a provare, prima della capacità.** In 37 celle su 45 il braccio
   non tocca il codice. Quando ci prova, su `crdt-yjs`, arriva vicino all'accettazione in 3 celle
   su 6. Luna medium, messa davanti a un sistema grande, tende a dichiarare il lavoro troppo
   grande e a fermarsi dopo un minuto o due.
3. **La struttura non aiuta qui.** Autopilot e i due driver non consegnano niente in 26 celle su
   27. I loro protocolli si fermano prima (Autopilot) o il builder non produce un candidato
   (driver). skills-only e `bare` sono gli unici che a volte ci provano.
4. **Per la misura completa il rischio è l'opposto della prima misura.** Allora i bracci erano
   tutti al soffitto, ora sono quasi tutti al pavimento. La regola può restare «indistinguibile»
   per mancanza di eventi. Il piano resta quello deciso dall'utente in DBH-01: la misura
   completa dirà se le richieste successive, e la memoria di una catena, cambiano il quadro.

## Limiti
- Solo la richiesta 1, 3 ripetizioni per braccio e scenario.
- Modello e thinking sono fissati dall'utente: la nota non separa l'effetto di luna da quello di
  `medium`.
- I bracci usano le skill installate il 24/09, non quelle di `main`.
- L'esito di Autopilot riflette anche l'incontro fra il suo protocollo e una cella di benchmark
  (ticket, provider, worktree). Come nella prima misura, non è stato adattato.
