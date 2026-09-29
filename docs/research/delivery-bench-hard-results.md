# delivery-bench difficile — misura completa: catene da 1, 4 e 12

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-results`
- Role: `research`
- Parent: [DBH-09 — Misura completa: catene da 4 e 12](../tickets/delivery-bench-hard/done/09-full-measurement.md)

## Stato
Output di DBH-09 (2026-09-28/29): la tabella braccio × lunghezza × scenario, la regola di TBA-03
e la raccomandazione operativa promesse dalla [mappa](../specs/delivery-bench-hard-wayfinder.md).
Lotto `dbh`: le 45 celle del [pilota](delivery-bench-hard-pilot.md) sono state **proseguite**
fino alla richiesta 4 (3 ripetizioni), e la ripetizione 1 fino alla 12 (contratto §9). La regola
ha poi chiesto la ripetizione 2 della catena da 12, prima per skills-only e poi per Autopilot.
Bracci su `openai-codex/gpt-6-luna` con `--thinking medium`, su tre sistemi reali maturi
(`lua-vm`, `sql-engine`, `crdt-yjs`). Record di cella, giudizi e ledger stanno nel repo privato
dell'oracolo (`results/dbh/`). Qui ci sono solo aggregati, senza nomi di controlli, trappole,
richieste o difetti.

In breve:
- **Il regime sta al pavimento.** Alla richiesta 1 passa una richiesta su 45. Alla catena da 12
  il braccio migliore accetta 22 richieste su 72.
- **Alla catena da 4 skills-only è «meglio» di `bare` per la regola** (9/36 contro 1/36,
  Holm 0,031). È la prima volta in delivery-bench che un braccio strutturato stacca `bare`.
- **Alla catena da 12 non si distingue più.** skills-only fa 21/72 e Autopilot 22/72, contro
  13/72 di `bare`, con Holm 0,157. Vince `bare` per il pareggio al braccio più semplice.
- **I due driver non ottengono nessuna accettazione**: 0 su 60 ciascuno, e alla catena da 12
  sono «peggio» di `bare`. Dopo la misura sono emersi due difetti del driver, ora corretti, che
  pesano su questo risultato (vedi *Esiti del driver*). La
  [rimisura dei driver corretti](delivery-bench-hard-drivers.md) (DBH-16) porta c1a a 3/36 alla
  catena da 12, e c3a resta a 0.
- **Le trappole ora scattano**, 14 violazioni su 38 misurabili alla catena da 12, in
  proporzioni simili nei tre bracci che consegnano.
- **La compaction arriva**, con 4, 15 e 57 compaction per `bare`, skills-only e Autopilot.
- Spesa: 17,71 $ per tutto il lotto, contro i 250 $ del tetto.

## Autorizzazione e provenienza
- **Autorità del lotto**: `results/dbh-authority.json` (sha256 `52597cbf…`), la stessa del
  pilota. Copre pilota e misura completa, i cinque bracci, i tre scenari, 3 ripetizioni e la
  lunghezza 12, e lega modello e thinking. La conferma dell'utente è in DBH-01
  (`results/dbh-01-confirmation.json`, sha256 `b2aa1f31…`). Il piano della misura (catene da 4,
  poi da 12, poi le ripetizioni chieste dalla regola) è quello di quella conferma.
- **Scenari**: le suite nascoste sono quelle verificate in DBH-05/06/07 e registrate dal lotto:
  `lua-vm` `f90869af…`, `sql-engine` `5b029cb4…`, `crdt-yjs` `be281cb4…`. Nessuna suite è
  stata emendata durante la misura.
- **Harness congelato** in un checkout dedicato, spostato solo fra due `run-lot`:
  - pilota e prima passata delle catene da 4 a `b22b985`;
  - catena da 12, ripetizione 1, a `7e05a39` (DBH-12, #384);
  - ripresa delle due celle ferme e ripetizioni 2 della catena da 12 a `833b908` (DBH-13, #385).
  Le copie del driver restano quelle del pilota, da un checkout pulito di `b22b985`
  (`prepare-drivers --source`): le correzioni toccano solo il runner. Pi 0.87.1. Le skill
  installate sono quelle del manifest del 24/09, le stesse del pilota e di `luna-calib`.
  **Correzione (DBH-17)**: non per tutto il lotto. Il 29/09 alle 11:22 UTC un aggiornamento
  di pi-personal-config ha installato le skill di `a4190bc`, e sono cambiate `ask-skills`,
  `llm-wiki` e `ticket-autopilot`. Dopo sono partite 2 richieste di Autopilot, la 12 di due
  catene, e la 11 delle stesse catene era in corso. Delle 4, una è accettata. Togliendo le 4
  coppie la regola non cambia: alla catena da 12 Autopilot resta indistinguibile (Holm
  0,083). Il runner non registrava le skill installate; ora le lega al lotto
  ([DBH-17](../tickets/delivery-bench-hard/done/17-bind-installed-skills.md)).
- **Esecuzione**: dal 28/09 alle 16:51 UTC al 29/09 alle 12:26 UTC, 4 celle in parallelo (2-3
  nelle ultime riprese). Col pilota il lotto ha 372 richieste giudicate e 376 tentativi: 370 dei
  bracci e 6 guasti d'infrastruttura (vedi *Guasti*). Nessun timeout, nessun tetto di catena,
  nessuna cella invalidata dall'audit, nessun errore del giudice.
- **Spesa**: 17,71 $ stimati da Pi per tutto il lotto, di cui 17,46 $ per DBH-09, e 0,0035 $ di
  Jev. Tempo di parete di DBH-09: 19,6 ore, contro 72.
- **Rigiudizio di controllo**: 5 celle, catene da 12 nei tre scenari e una da 4, giudicate di
  nuovo sull'ultima richiesta. Danno lo stesso albero, la stessa suite, lo stesso esito su ogni
  controllo e gli stessi assi.

## Come si legge
Come nella [prima misura](delivery-bench-results.md#come-si-legge).
- **Accettazione**: richieste accettate. La regola di TBA-03 è appaiata con `bare` (McNemar
  esatto, Holm, differenza minima 3, pareggi al braccio più semplice) e legge un solo asse.
- **Robustezza e bussola** si leggono sul repository finale di ogni catena. *Invarianti rotte*
  sono regressioni; `nd` conta le invarianti di feature mai consegnate. *Trappole
  violate/misurabili*: una trappola è misurabile solo finché la sua feature è in piedi, e `nm`
  conta le altre.
- **Costo e tempo** sono sommati sulla catena. **Compaction**: quante volte Pi ha riassunto una
  sessione per liberare contesto (DBH-02), con il loro costo dentro gli USD.
- **c3a**: un run fermo al cancello semantico aspetta un umano. Il suo candidato si giudica a
  parte (controfattuale) e non conta mai come accettazione.

## Risultati

### Catene da 1 (3 ripetizioni, 9 catene per braccio)
È il pilota: il dettaglio è nel [report del pilota](delivery-bench-hard-pilot.md).

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 0/9 | 3/30 | 0/9 | — | — | 0.04 | — | 105 | 0 | 0 (0.00) | 0 |
| skills-only | 9 | 1/9 | 4/30 | 0/9 | — | — | 0.06 | — | 71 | 0 | 0 (0.00) | 0 |
| autopilot | 9 | 0/9 | 0/30 | 0/9 | — | — | 0.05 | — | 88 | 0 | 0 (0.00) | 0 |
| driver-c1a | 9 | 0/9 | 1/30 | 0/9 | — | — | 0.05 | — | 65 | 0 | 0 (0.00) | 0 |
| driver-c3a | 9 | 0/9 | 0/30 | 0/9 | — | — | 0.04 | — | 62 | 0 | 0 (0.00) | 0 |

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 1 | 0 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| autopilot | 9 | 0 | 0 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 9 | 0 | 0 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 9 | 0 | 0 | 0 | 0 | +0 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Catene da 4 (3 ripetizioni, 9 catene per braccio)
| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 3 | 1/12 | 10/27 | 0/39 (+16 nd) | — | — | 0.12 | — | 545 | 0 | 0 (0.00) | 0 |
| crdt-yjs | skills-only | 3 | 5/12 | 11/27 | 0/39 (+11 nd) | — | — | 0.41 | — | 1489 | 0 | 0 (0.00) | 1 |
| crdt-yjs | autopilot | 3 | 3/12 | 10/27 | 0/39 (+18 nd) | — | — | 0.49 | — | 845 | 0 | 0 (0.00) | 1 |
| crdt-yjs | driver-c1a | 3 | 0/12 | 0/27 | 0/39 (+36 nd) | — | — | 0.10 | — | 592 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 3 | 0/12 | 0/27 | 0/39 (+36 nd) | — | — | 0.10 | 0.0005 | 547 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 3 | 0/12 | 7/30 | 0/48 (+31 nd) | — | — | 0.07 | — | 307 | 0 | 0 (0.00) | 0 |
| lua-vm | skills-only | 3 | 4/12 | 13/30 | 0/48 (+28 nd) | — | — | 0.24 | — | 620 | 0 | 0 (0.00) | 0 |
| lua-vm | autopilot | 3 | 3/12 | 16/30 | 0/48 (+24 nd) | — | — | 0.93 | — | 3493 | 0 | 0 (0.00) | 3 |
| lua-vm | driver-c1a | 3 | 0/12 | 1/30 | 0/48 (+38 nd) | — | — | 0.06 | — | 236 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 3 | 0/12 | 0/30 | 0/48 (+42 nd) | — | — | 0.08 | 0.0007 | 290 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 3 | 0/12 | 8/42 | 0/39 (+30 nd) | — | — | 0.08 | — | 1110 | 0 | 0 (0.00) | 0 |
| sql-engine | skills-only | 3 | 0/12 | 11/42 | 0/39 (+28 nd) | — | — | 0.13 | — | 837 | 0 | 0 (0.00) | 0 |
| sql-engine | autopilot | 3 | 0/12 | 12/42 | 0/39 (+29 nd) | — | — | 0.24 | — | 1426 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c1a | 3 | 0/12 | 9/42 | 0/39 (+26 nd) | — | — | 0.09 | — | 444 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c3a | 3 | 0/12 | 0/42 | 0/39 (+36 nd) | — | — | 0.10 | 0.0010 | 756 | 0 | 0 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 1/36 | 25/99 | 0/126 (+77 nd) | — | — | 0.27 | — | 575 | 0 | 0 (0.00) | 0 |
| skills-only | 9 | 9/36 | 35/99 | 0/126 (+67 nd) | — | — | 0.78 | — | 887 | 0 | 0 (0.00) | 1 |
| autopilot | 9 | 6/36 | 38/99 | 0/126 (+71 nd) | — | — | 1.65 | — | 1426 | 0 | 0 (0.00) | 4 |
| driver-c1a | 9 | 0/36 | 10/99 | 0/126 (+100 nd) | — | — | 0.25 | — | 444 | 0 | 0 (0.00) | 0 |
| driver-c3a | 9 | 0/36 | 0/99 | 0/126 (+114 nd) | — | — | 0.28 | 0.0022 | 655 | 0 | 0 (0.00) | 0 |

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 36 | 9 | 1 | 8 | 0 | +8 | 0.007812 | 0.03125 | better |
| autopilot | 36 | 6 | 1 | 6 | 1 | +5 | 0.125 | 0.375 | indistinguishable |
| driver-c1a | 36 | 0 | 1 | 0 | 1 | -1 | 1 | 1 | indistinguishable |
| driver-c3a | 36 | 0 | 1 | 0 | 1 | -1 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **skills-only**. It reads one axis; the choice of an arm reads all five.

### Catene da 12 (ripetizione 1, più la 2 dove la regola l'ha chiesta)
- Dopo la ripetizione 1 la regola chiedeva una ripetizione per skills-only, con un tasso sopra
  `bare` e la decisione aperta. La ripetizione 2 è girata per skills-only e per `bare`, che è la
  base delle coppie.
- Dopo quella, la chiedeva per Autopilot, arrivato a un tasso pari a quello di `bare`.
- Con la ripetizione 2 di Autopilot la regola è decisa. I due driver, già «peggio» alla
  ripetizione 1, ne hanno una.

| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 2 | 5/24 | 23/48 | 1/88 (+41 nd) | 1/4 (+10 nm) | d10×1 | 0.43 | — | 2395 | 0 | 0 (0.00) | 1 |
| crdt-yjs | skills-only | 2 | 8/24 | 24/48 | 1/88 (+34 nd) | 0/3 (+11 nm) | — | 0.97 | — | 4603 | 0 | 0 (0.00) | 6 |
| crdt-yjs | autopilot | 2 | 8/24 | 23/48 | 6/88 (+34 nd) | 0/5 (+9 nm) | — | 2.62 | — | 11589 | 0 | 0 (0.00) | 15 |
| crdt-yjs | driver-c1a | 1 | 0/12 | 1/24 | 0/44 (+43 nd) | — (+7 nm) | — | 0.09 | — | 1512 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 1 | 0/12 | 1/24 | 0/44 (+43 nd) | — (+7 nm) | — | 0.09 | 0.0006 | 1567 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 2 | 5/24 | 19/54 | 0/84 (+48 nd) | 0/3 (+11 nm) | — | 0.61 | — | 2580 | 0 | 0 (0.00) | 1 |
| lua-vm | skills-only | 2 | 10/24 | 22/54 | 2/84 (+32 nd) | 2/5 (+9 nm) | d7×2 | 1.77 | — | 7446 | 0 | 0 (0.00) | 6 |
| lua-vm | autopilot | 2 | 10/24 | 32/54 | 1/84 (+19 nd) | 4/8 (+6 nm) | d5×1, d7×2, d8×1 | 4.29 | — | 17440 | 0 | 0 (0.00) | 23 |
| lua-vm | driver-c1a | 1 | 0/12 | 0/27 | 0/42 (+38 nd) | — (+7 nm) | — | 0.05 | — | 585 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 1 | 0/12 | 0/27 | 0/42 (+38 nd) | — (+7 nm) | — | 0.08 | 0.0010 | 1137 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 2 | 3/24 | 31/76 | 0/82 (+38 nd) | 3/4 (+10 nm) | d7×3 | 0.81 | — | 5936 | 0 | 0 (0.00) | 2 |
| sql-engine | skills-only | 2 | 3/24 | 34/76 | 1/82 (+34 nd) | 2/4 (+10 nm) | d7×2 | 1.16 | — | 6280 | 0 | 2 (0.00) | 3 |
| sql-engine | autopilot | 2 | 4/24 | 33/76 | 1/82 (+34 nd) | 2/2 (+12 nm) | d7×2 | 3.81 | — | 18161 | 0 | 2 (0.00) | 19 |
| sql-engine | driver-c1a | 1 | 0/12 | 2/38 | 0/41 (+39 nd) | — (+7 nm) | — | 0.09 | — | 1055 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c3a | 1 | 0/12 | 0/38 | 0/41 (+40 nd) | — (+7 nm) | — | 0.10 | 0.0008 | 1892 | 0 | 0 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 6 | 13/72 | 73/178 | 1/254 (+127 nd) | 4/11 (+31 nm) | d7×3, d10×1 | 1.85 | — | 2690 | 0 | 0 (0.00) | 4 |
| skills-only | 6 | 21/72 | 80/178 | 4/254 (+100 nd) | 4/12 (+30 nm) | d7×4 | 3.90 | — | 6280 | 0 | 2 (0.00) | 15 |
| autopilot | 6 | 22/72 | 88/178 | 8/254 (+87 nd) | 6/15 (+27 nm) | d5×1, d7×4, d8×1 | 10.72 | — | 16654 | 0 | 2 (0.00) | 57 |
| driver-c1a | 3 | 0/36 | 3/89 | 0/127 (+120 nd) | — (+21 nm) | — | 0.22 | — | 1055 | 0 | 0 (0.00) | 0 |
| driver-c3a | 3 | 0/36 | 1/89 | 0/127 (+121 nd) | — (+21 nm) | — | 0.27 | 0.0024 | 1567 | 0 | 0 (0.00) | 0 |

Violated trap types per arm: bare: contract×2, convention×1, deprecated×1; skills-only: architecture×2, contract×2; autopilot: architecture×2, contract×4; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 72 | 21 | 13 | 14 | 6 | +8 | 0.1153 | 0.1567 | indistinguishable |
| autopilot | 72 | 22 | 13 | 15 | 6 | +9 | 0.07835 | 0.1567 | indistinguishable |
| driver-c1a | 36 | 0 | 8 | 0 | 8 | -8 | 0.007812 | 0.03125 | worse |
| driver-c3a | 36 | 0 | 8 | 0 | 8 | -8 | 0.007812 | 0.03125 | worse |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Accettazione lungo la catena
Catene da 12 di `bare`, skills-only e Autopilot (6 per braccio), per posizione della richiesta:

| Braccio | Richiesta 1 | 2-4 | 5-8 | 9-12 |
|---|---:|---:|---:|---:|
| bare | 0/6 | 1/18 | 3/24 | 9/24 |
| skills-only | 1/6 | 5/18 | 6/24 | 9/24 |
| autopilot | 0/6 | 4/18 | 9/24 | 9/24 |

L'accettazione cresce lungo la catena in tutti e tre. Alla fine delle catene ogni braccio senza
driver ha toccato il codice in ogni catena. Alla richiesta 1 invece 37 celle su 45 lasciavano
la cartella identica al seme.

### Esiti del driver
- **c1a**: 60 run, 51 falliti e 9 integrati, 0 accettati. 36 run falliscono con un candidato
  vuoto, cioè il builder non lascia modifiche; 15 per i test.
- **c3a**: 60 run, 44 falliti, 15 fermi al cancello e 1 fermato. 36 run falliscono con un
  candidato vuoto. Dei 15 candidati fermi, giudicati a parte con `judge-gated`, 4 sarebbero
  stati accettati: con un umano al cancello c3a avrebbe consegnato qualcosa.
- In 13 catene di driver su 18 la cartella finale è ancora identica al seme.

**Perché i driver non consegnano.** Dopo la misura sono state rilette le sessioni del builder e
le ricevute dei test dei 120 run. Due difetti del driver, non del modello, pesano sul risultato.
Sono corretti dopo la misura, e questa misura è girata senza le correzioni.
- **Il builder si fermava per protocollo**, corretto in #391:
  [TBP-01](../tickets/ticket-driver-builder-prompt/done/01-let-the-builder-implement-a-prose-task.md).
  In 28 dei 72 candidati vuoti (15 di c1a, 13 di c3a) il builder non tocca niente. Il prompt gli
  chiedeva il giro `to-spec -> to-tickets -> execute-ticket`, e luna, davanti a un task in prosa
  invece che a un ticket canonico, si fermava. skills-only, con lo stesso modello, le stesse
  skill e le stesse richieste, non si è mai fermato così. Rigiocati 4 di quei run su copie, il
  prompt vecchio si ferma 2 volte per protocollo e quello nuovo nessuna.
- **Le suite verbose venivano uccise**, corretto in #392:
  [RTO-02](../tickets/ticket-driver-red-test-observation/done/02-keep-a-verbose-suite-alive.md).
  Il driver interrompeva i test oltre 64 KiB di uscita, e contava l'interruzione come test
  rossi. La suite di crdt-yjs passa al seme ma stampa circa 87 KB. Così sono stati uccisi 16 dei
  18 run di crdt-yjs arrivati ai test, più uno di sql-engine: nessun candidato dei driver su
  crdt-yjs poteva essere integrato.
  Fra questi 17 ci sono i 6 run di c3a fermi al cancello sulla domanda di retry.
- **Il resto viene dal modello o dal disegno del driver:**
  - 36 candidati vuoti sono rinunce: il builder scrive che non riesce a completare il task, e
    non modifica niente;
  - altri 8 modificano file ma non lasciano niente;
  - i 9 integrati di c1a passano i test del driver, ma non tutti i controlli della richiesta;
  - degli altri 9 cancelli di c3a, 3 chiedono di che tipo sono i test e 6 riguardano la
    revisione del contenuto;
  - ogni run del driver parte da una sessione nuova, mentre `bare`, skills-only e Autopilot
    continuano la stessa sessione lungo la catena. È il disegno del driver, e spiega le 0
    compaction.

### Durata delle richieste e compaction
| Braccio | Richieste | Mediana s | Massimo s | Oltre 900 s |
|---|---:|---:|---:|---:|
| bare | 84 | 218 | 883 | 0 |
| skills-only | 84 | 339 | 2329 | 12 |
| autopilot | 84 | 1189 | 3642 | 45 |
| driver-c1a | 60 | 67 | 425 | 0 |
| driver-c3a | 60 | 77 | 457 | 0 |

Il tetto di 5400 s non è mai stato toccato. Alle catene da 12 le compaction sono:
- `bare` 4, una in 4 catene su 6;
- skills-only 15 e Autopilot 57, in tutte e 6 le catene;
- i driver 0.

## Letture
1. **Luna medium su questi sistemi sta al pavimento.** Da solo non risolve quasi niente (1/45
   alla richiesta 1). Nelle catene va un po' meglio, ma il migliore resta sotto un terzo delle
   richieste (22/72). Il livello assoluto è basso, e le differenze fra bracci si leggono su pochi
   eventi.
2. **Alla catena da 4 skills-only è l'unico braccio «meglio» di `bare`**: 8 richieste che solo
   lui accetta, nessuna che solo `bare` accetta, Holm 0,031. Autopilot è sopra di 5, senza
   distinguersi.
3. **Alla catena da 12 il vantaggio c'è ma non si distingue.** skills-only +8 e Autopilot +9 su
   72 coppie, entrambi con Holm 0,157. Le richieste che solo `bare` accetta (6) diluiscono
   il segnale. A questa scala e con 2 ripetizioni la regola dà `bare`.
4. **Gli altri assi non ribaltano la lettura, ma costano.** Alla catena da 12 Autopilot trova più
   latenti (88/178 contro 80 e 73) e rompe più invarianti (8 contro 4 e 1). Viola anche più
   trappole (6/15 contro 4/12 e 4/11).
5. **Il catalogo v2 morde, ma non separa i bracci.** Alla catena da 8 della prima misura le
   trappole violate erano una. Qui sono 14 su 38 misurabili alla catena da 12, a distanza da 5 a 10,
   in proporzioni simili per `bare`, skills-only e Autopilot.
6. **La memoria lunga ora è messa alla prova.** Autopilot compatta di continuo (57 volte in 6
   catene), skills-only spesso (15), `bare` di rado (4). La compaction non si traduce in una
   perdita visibile sulle regole: i tre bracci violano trappole in proporzioni simili.
7. **Costo e tempo per catena da 12** (mediana del tempo): `bare` 0,31 $ e 45 minuti,
   skills-only 0,65 $ e 1 ora e 45, Autopilot 1,79 $ e 4 ore e 38.
8. **Autopilot parte peggio e finisce meglio.** Alla richiesta 1 si ferma sempre sul suo
   protocollo (0/9). Più avanti lavora, e alla catena da 12 accetta più di tutti, a 5,8 volte il
   costo di `bare` e 6 volte il tempo.
9. **I driver, com'erano, non sono bracci per questo modello.** Con luna il builder di c1a e di
   c3a quasi sempre non produce un candidato, e su crdt-yjs nessun candidato poteva passare i
   test del driver. Due di queste cause erano difetti del driver, ora corretti: la misura non
   dice come andrebbe il driver corretto. c3a in più si ferma al cancello: 4 dei suoi candidati
   fermi sarebbero stati accettati.

## Raccomandazione operativa
Per `openai-codex/gpt-6-luna` con `--thinking medium` e task come questi (sistemi reali maturi,
una funzionalità per richiesta, catene fino a 12):

| Task | Usa | Perché | Cosa costa sceglierlo |
|---|---|---|---|
| 1 richiesta | **un modello più forte** | nessun braccio consegna: 1/45 | — |
| 2-4 richieste | **skills-only** | 9/36 contro 1/36, l'unico «meglio» per la regola | 2,9× USD, 1,5× tempo |
| 12 richieste | **skills-only** se conta l'accettazione, altrimenti Pi nudo | 21/72 contro 13/72, non distinguibile (Holm 0,157); più latenti; regressioni 4 contro 1 | 2,1× USD, 2,3× tempo |

Da non usare per task di queste dimensioni con questo modello:
- **driver c1a e c3a**, nella versione misurata: 0 richieste accettate su 60 ciascuno. La
  versione corretta, misurata dopo in [DBH-16](delivery-bench-hard-drivers.md), resta sotto `bare`:
  c1a 3/36 alla catena da 12, c3a 0/36.
- **Autopilot**: accetta quanto skills-only alla catena da 12 (22 contro 21), ma costa 2,7 volte
  skills-only e ci mette 2,7 volte il tempo. Rompe anche più invarianti, e alla richiesta 1 non
  lavora.

La regola, da sola, non decide niente alla catena da 12. La scelta di skills-only legge anche gli
altri assi e la catena da 4.

## Confronto con la prima misura e con la calibrazione
| Misura | Modello e scenari | Accettazione | Regola di TBA-03 |
|---|---|---|---|
| [Prima misura](delivery-bench-results.md) | sol high, app piccole, catene da 8 | 42-48/48 per i quattro bracci senza cancello | tutti indistinguibili, c3a originale peggio |
| [Calibrazione](delivery-bench-luna-calibration.md) (DBH-03) | luna medium, app piccole, catene da 3 | `bare` 22/27, skills-only 20/27 | indistinguibile |
| Questa misura | luna medium, sistemi maturi, catene da 12 | `bare` 13/72, skills-only 21/72, Autopilot 22/72, driver 0/36 | `bare`; skills-only meglio alla catena da 4 |

- **Dal soffitto al pavimento.** La prima misura stava al soffitto e le differenze venivano da un
  evento raro. Qui i bracci accettano poco, e la regola trova una differenza vera soltanto alla
  catena da 4.
- **skills-only resta la scelta più solida.** Era l'unico senza richieste perse alla catena
  da 8 della prima misura. Qui è l'unico «meglio» alla catena da 4, e alla catena da 12
  costa meno della metà di Autopilot.
- **Autopilot cambia ruolo.** Prima non era davanti su nessun asse e costava 5,4 volte `bare`.
  Qui alla catena da 12 accetta più di tutti, ma sempre a un costo di circa 6 volte.
- **I driver crollano.** c1a era alla pari di `bare` nella prima misura, e il c3a corretto era
  indistinguibile ([c3a corretto](delivery-bench-c3a-corrected.md)). Con luna non ottengono
  nessuna accettazione. Nel c3a corretto, con sol e lo stesso prompt del builder, 55 run su 57
  erano integrati, e le suite di quelle app erano piccole. Qui i due difetti sono venuti fuori.
- **Trappole e compaction** diventano misurabili. Alla catena da 12 le violazioni sono 14,
  contro una sola alla catena da 8 della prima misura. La compaction arriva in tutte le
  catene da 12 di skills-only e Autopilot.

## Limiti
- **Un solo modello**, fissato dall'utente, con modello e thinking insieme. La misura non dice
  come andrebbe un modello più forte sugli stessi scenari: sol sugli scenari difficili non è
  misurato.
- **Poche ripetizioni**: 2 per la catena da 12 di `bare`, skills-only e Autopilot, 1 per i
  driver. Con tassi così bassi, poche richieste spostano la regola.
- **Oracolo scritto da un modello Claude**, di famiglia diversa dai bracci, come nella prima
  misura. Richieste, suite e trappole dei tre scenari sono dello stesso autore; gli scenari li
  ha confermati l'utente (DBH-01).
- **L'accettazione cresce lungo la catena**, ma la misura non separa la difficoltà delle
  richieste dall'effetto di conoscere già la codebase.
- **Tempi rumorosi**: la macchina e il provider erano condivisi, e gli USD sono stime di Pi. Fra
  una richiesta e l'altra passano minuti o ore, quindi la cache del provider può scadere.
- **Due richieste perse per la rete** (vedi *Guasti*): contano come non accettate, come vuole il
  contratto. Togliendo le due coppie, la regola non cambia.
- **I bracci usano le skill installate il 24/09**, non quelle di `main`, tranne 4 richieste di
  Autopilot alla fine del lotto (vedi la correzione in *Autorizzazione e provenienza*).
- **I driver misurati hanno due difetti**, corretti dopo la misura (vedi *Esiti del driver*). Il
  loro risultato non vale per il driver corretto, misurato in
  [DBH-16](delivery-bench-hard-drivers.md).
- **Autopilot alla richiesta 1** misura anche l'incontro fra il suo protocollo e una cella di
  benchmark (ticket, provider, worktree). Come nella prima misura, non è stato adattato.

## Guasti dell'harness e correzioni
- **Tetto oltre l'ora** (DBH-11, #382): trovato al lancio del pilota, prima di questa misura.
- **File con nome di dispositivo** (DBH-12, #384): un builder di c3a e un'istanza di Autopilot
  hanno lasciato un file chiamato `NUL`. Su Windows l'istantanea della cella falliva, e due
  catene si sono fermate alla richiesta 2. Il difetto è stato corretto fra due `run-lot`, con un
  test scritto prima della correzione.
- **Ripresa dopo la consegna del task** (DBH-13, #385): la ripresa di quelle due catene falliva
  di nuovo, perché il task della richiesta era già stato registrato. DBH-12 dichiarava una
  ripresa che nessun test provava, e il ticket ha una nota di correzione. Anche questo è stato
  corretto fra due `run-lot`. Le due catene sono riprese dalla richiesta 3 e sono arrivate alla
  loro lunghezza.
- **Buco di rete** il 29/09 fra le 06:33 e le 06:42 UTC. Alla richiesta 12 di due celle
  `sql-engine` Pi è uscito con `fetch failed` tre volte, in circa 17 s ciascuna e senza spesa.
  I retry si sono esauriti, e le due richieste contano come non accettate (contratto §9).
  I retry non aspettavano fra un tentativo e l'altro, quindi un'interruzione di qualche minuto
  li esauriva. Il difetto è corretto dopo la misura, in
  [DBH-14](../tickets/delivery-bench-hard/done/14-infra-retry-wait.md): questa misura è
  girata senza la correzione.
- **Difetti del driver**, trovati dopo la misura rileggendo i suoi run: il prompt del builder
  (TBP-01, #391) e il limite d'uscita dei test (RTO-02, #392), descritti in *Esiti del driver*.
  Le copie del driver di questo lotto restano quelle del pilota.
- Nessun errore del giudice, timeout, tetto di catena o riscontro dell'audit.

## Appendice: profilo per richiesta, catena da 12
Invariants broken are regressions (the check passed earlier in the chain); `nd` counts failed invariants whose feature was never delivered. Traps are violated/measurable: a trap is measurable while the feature of its tempting request is in place; `nm` counts the others.

| Scenario | Arm | Request | Accepted | Features | Latent found | Invariants broken | Traps violated | Distances | Tokens in / out / cache read | USD (Pi) | USD (Jev) | Median s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 1 | 0/2 | 6/10 | 3/6 | 0/2 | — | — | 76k / 4k / 414k | 0.01 | — | 114 | 0 | 0 (0.00) |
| crdt-yjs | bare | 2 | 0/2 | 2/6 | 5/12 | 0/12 (+2 nd) | — | — | 41k / 3k / 694k | 0.01 | — | 106 | 0 | 0 (0.00) |
| crdt-yjs | bare | 3 | 0/2 | 3/8 | 2/14 | 5/18 (+5 nd) | — | — | 67k / 7k / 2043k | 0.03 | — | 170 | 0 | 0 (0.00) |
| crdt-yjs | bare | 4 | 1/2 | 3/6 | 7/18 | 0/26 (+10 nd) | — | — | 48k / 6k / 2406k | 0.03 | — | 160 | 0 | 0 (0.00) |
| crdt-yjs | bare | 5 | 0/2 | 3/10 | 8/24 | 0/32 (+13 nd) | — | — | 174k / 4k / 1695k | 0.04 | — | 145 | 0 | 0 (0.00) |
| crdt-yjs | bare | 6 | 1/2 | 3/6 | 8/26 | 0/42 (+20 nd) | — | — | 64k / 6k / 2570k | 0.03 | — | 146 | 0 | 0 (0.00) |
| crdt-yjs | bare | 7 | 0/2 | 2/8 | 10/30 | 0/48 (+23 nd) | — | — | 98k / 11k / 6445k | 0.08 | — | 329 | 0 | 0 (0.00) |
| crdt-yjs | bare | 8 | 0/2 | 2/8 | 9/32 | 1/56 (+29 nd) | — (+4 nm) | — | 32k / 5k / 818k | 0.01 | — | 157 | 0 | 0 (0.00) |
| crdt-yjs | bare | 9 | 1/2 | 4/8 | 11/36 | 1/64 (+35 nd) | 0/1 (+5 nm) | — | 28k / 4k / 695k | 0.01 | — | 93 | 0 | 0 (0.00) |
| crdt-yjs | bare | 10 | 0/2 | 6/8 | 12/38 | 1/72 (+37 nd) | 0/1 (+7 nm) | — | 57k / 15k / 2605k | 0.04 | — | 289 | 0 | 0 (0.00) |
| crdt-yjs | bare | 11 | 1/2 | 4/8 | 15/42 | 1/80 (+37 nd) | 0/2 (+8 nm) | — | 63k / 22k / 4315k | 0.06 | — | 371 | 0 | 0 (0.00) |
| crdt-yjs | bare | 12 | 1/2 | 5/6 | 23/48 | 1/88 (+41 nd) | 1/4 (+10 nm) | d10×1 | 62k / 16k / 4991k | 0.06 | — | 315 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 1 | 1/2 | 9/10 | 4/6 | 0/2 | — | — | 111k / 7k / 1299k | 0.03 | — | 203 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 2 | 0/2 | 2/6 | 4/12 | 0/12 (+1 nd) | — | — | 157k / 11k / 3432k | 0.06 | — | 363 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 3 | 1/2 | 4/8 | 4/14 | 0/18 (+5 nd) | — | — | 205k / 19k / 9635k | 0.13 | — | 559 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 4 | 2/2 | 6/6 | 7/18 | 0/26 (+8 nd) | — | — | 104k / 12k / 4029k | 0.06 | — | 333 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 5 | 0/2 | 3/10 | 8/24 | 0/32 (+8 nd) | — | — | 303k / 14k / 2540k | 0.06 | — | 261 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 6 | 1/2 | 3/6 | 9/26 | 0/42 (+13 nd) | — | — | 203k / 30k / 8026k | 0.12 | — | 629 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 7 | 0/2 | 0/8 | 11/30 | 0/48 (+16 nd) | — | — | 124k / 14k / 3111k | 0.05 | — | 317 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 8 | 0/2 | 2/8 | 11/32 | 1/56 (+24 nd) | — (+4 nm) | — | 132k / 24k / 6841k | 0.09 | — | 483 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 9 | 2/2 | 8/8 | 15/36 | 1/64 (+30 nd) | 0/2 (+4 nm) | — | 95k / 10k / 6269k | 0.08 | — | 258 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 10 | 0/2 | 6/8 | 16/38 | 1/72 (+28 nd) | 0/2 (+6 nm) | — | 222k / 9k / 2874k | 0.06 | — | 214 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 11 | 1/2 | 4/8 | 18/42 | 1/80 (+30 nd) | 0/3 (+7 nm) | — | 229k / 23k / 10904k | 0.14 | — | 609 | 0 | 0 (0.00) |
| crdt-yjs | skills-only | 12 | 0/2 | 4/6 | 24/48 | 1/88 (+34 nd) | 0/3 (+11 nm) | — | 144k / 16k / 5067k | 0.07 | — | 375 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 1 | 0/2 | 0/10 | 0/6 | 0/2 | — | — | 53k / 3k / 306k | 0.01 | — | 90 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 2 | 0/2 | 1/6 | 3/12 | 0/12 (+5 nd) | — | — | 119k / 11k / 3415k | 0.05 | — | 316 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 3 | 1/2 | 4/8 | 4/14 | 0/18 (+8 nd) | — | — | 312k / 49k / 16050k | 0.22 | — | 1221 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 4 | 1/2 | 3/6 | 6/18 | 0/26 (+12 nd) | — | — | 166k / 20k / 8824k | 0.11 | — | 447 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 5 | 0/2 | 0/10 | 6/24 | 0/32 (+15 nd) | — | — | 307k / 11k / 2577k | 0.06 | — | 271 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 6 | 1/2 | 3/6 | 6/26 | 0/42 (+25 nd) | — | — | 290k / 34k / 13689k | 0.18 | — | 754 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 7 | 1/2 | 6/8 | 9/30 | 0/48 (+24 nd) | — | — | 807k / 109k / 40913k | 0.54 | — | 2312 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 8 | 1/2 | 4/8 | 9/32 | 1/56 (+26 nd) | 0/2 (+2 nm) | — | 403k / 56k / 18842k | 0.26 | — | 1300 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 9 | 2/2 | 8/8 | 13/36 | 1/64 (+30 nd) | 0/4 (+2 nm) | — | 503k / 56k / 21900k | 0.30 | — | 1385 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 10 | 0/2 | 3/8 | 14/38 | 1/72 (+28 nd) | 0/4 (+4 nm) | — | 188k / 21k / 7469k | 0.10 | — | 480 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 11 | 1/2 | 7/8 | 17/42 | 6/80 (+33 nd) | 0/5 (+5 nm) | — | 675k / 61k / 22859k | 0.33 | — | 1393 | 0 | 0 (0.00) |
| crdt-yjs | autopilot | 12 | 0/2 | 4/6 | 23/48 | 6/88 (+34 nd) | 0/5 (+9 nm) | — | 589k / 79k / 25487k | 0.35 | — | 1620 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 1 | 0/1 | 0/5 | 0/3 | 0/1 | — | — | 33k / 1k / 111k | 0.00 | — | 64 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 2 | 0/1 | 0/3 | 0/6 | 0/6 (+5 nd) | — | — | 49k / 3k / 489k | 0.01 | — | 260 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 3 | 0/1 | 0/4 | 0/7 | 0/9 (+8 nd) | — | — | 56k / 3k / 606k | 0.01 | — | 218 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 4 | 0/1 | 0/3 | 0/9 | 0/13 (+12 nd) | — | — | 14k / 1k / 83k | 0.00 | — | 43 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 5 | 0/1 | 0/5 | 0/12 | 0/16 (+15 nd) | — | — | 20k / 1k / 39k | 0.00 | — | 31 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 6 | 0/1 | 0/3 | 0/13 | 0/21 (+20 nd) | — | — | 44k / 6k / 629k | 0.01 | — | 251 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 7 | 0/1 | 0/4 | 1/15 | 0/24 (+23 nd) | — | — | 26k / 1k / 219k | 0.01 | — | 56 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 8 | 0/1 | 0/4 | 1/16 | 0/28 (+27 nd) | — (+2 nm) | — | 14k / 1k / 60k | 0.00 | — | 43 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 9 | 0/1 | 0/4 | 1/18 | 0/32 (+31 nd) | — (+3 nm) | — | 44k / 2k / 374k | 0.01 | — | 131 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 10 | 0/1 | 0/4 | 1/19 | 0/36 (+35 nd) | — (+4 nm) | — | 22k / 1k / 148k | 0.00 | — | 62 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 11 | 0/1 | 0/4 | 1/21 | 0/40 (+39 nd) | — (+5 nm) | — | 21k / 1k / 187k | 0.00 | — | 64 | 0 | 0 (0.00) |
| crdt-yjs | driver-c1a | 12 | 0/1 | 0/3 | 1/24 | 0/44 (+43 nd) | — (+7 nm) | — | 57k / 5k / 659k | 0.01 | — | 288 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 1 | 0/1 | 0/5 | 0/3 | 0/1 | — | — | 43k / 1k / 80k | 0.01 | — | 41 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 2 | 0/1 | 0/3 | 0/6 | 0/6 (+5 nd) | — | — | 42k / 3k / 432k | 0.01 | 0.0001 | 224 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 3 | 0/1 | 0/4 | 0/7 | 0/9 (+8 nd) | — | — | 52k / 3k / 534k | 0.01 | 0.0001 | 225 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 4 | 0/1 | 0/3 | 0/9 | 0/13 (+12 nd) | — | — | 15k / 1k / 60k | 0.00 | — | 36 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 5 | 0/1 | 0/5 | 0/12 | 0/16 (+15 nd) | — | — | 16k / 1k / 82k | 0.00 | — | 54 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 6 | 0/1 | 0/3 | 0/13 | 0/21 (+20 nd) | — | — | 61k / 7k / 634k | 0.02 | 0.0001 | 283 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 7 | 0/1 | 0/4 | 1/15 | 0/24 (+23 nd) | — | — | 31k / 3k / 302k | 0.01 | 0.0001 | 185 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 8 | 0/1 | 0/4 | 1/16 | 0/28 (+27 nd) | — (+2 nm) | — | 26k / 1k / 102k | 0.00 | — | 39 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 9 | 0/1 | 0/4 | 1/18 | 0/32 (+31 nd) | — (+3 nm) | — | 63k / 4k / 535k | 0.01 | 0.0001 | 235 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 10 | 0/1 | 0/4 | 1/19 | 0/36 (+35 nd) | — (+4 nm) | — | 19k / 1k / 96k | 0.00 | — | 41 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 11 | 0/1 | 0/4 | 1/21 | 0/40 (+39 nd) | — (+5 nm) | — | 18k / 1k / 114k | 0.00 | — | 40 | 0 | 0 (0.00) |
| crdt-yjs | driver-c3a | 12 | 0/1 | 0/3 | 1/24 | 0/44 (+43 nd) | — (+7 nm) | — | 39k / 3k / 398k | 0.01 | 0.0001 | 163 | 0 | 0 (0.00) |
| lua-vm | bare | 1 | 0/2 | 0/12 | 0/6 | 0/2 | — | — | 29k / 1k / 72k | 0.00 | — | 51 | 0 | 0 (0.00) |
| lua-vm | bare | 2 | 0/2 | 2/12 | 2/10 | 0/14 (+7 nd) | — | — | 67k / 6k / 566k | 0.02 | — | 133 | 0 | 0 (0.00) |
| lua-vm | bare | 3 | 0/2 | 2/6 | 5/16 | 0/26 (+14 nd) | — | — | 54k / 9k / 1807k | 0.03 | — | 180 | 0 | 0 (0.00) |
| lua-vm | bare | 4 | 0/2 | 1/4 | 7/20 | 0/32 (+17 nd) | — | — | 20k / 3k / 699k | 0.01 | — | 78 | 0 | 0 (0.00) |
| lua-vm | bare | 5 | 2/2 | 6/6 | 9/22 | 0/36 (+20 nd) | — | — | 122k / 6k / 995k | 0.03 | — | 110 | 0 | 0 (0.00) |
| lua-vm | bare | 6 | 0/2 | 0/8 | 9/26 | 0/42 (+20 nd) | — | — | 65k / 11k / 3407k | 0.05 | — | 190 | 0 | 0 (0.00) |
| lua-vm | bare | 7 | 0/2 | 0/8 | 9/30 | 0/50 (+27 nd) | — | — | 43k / 6k / 1289k | 0.02 | — | 118 | 0 | 0 (0.00) |
| lua-vm | bare | 8 | 0/2 | 1/8 | 9/34 | 0/58 (+35 nd) | — (+4 nm) | — | 69k / 11k / 3437k | 0.05 | — | 221 | 0 | 0 (0.00) |
| lua-vm | bare | 9 | 0/2 | 1/6 | 9/36 | 0/66 (+42 nd) | — (+6 nm) | — | 94k / 26k / 8618k | 0.11 | — | 458 | 0 | 0 (0.00) |
| lua-vm | bare | 10 | 0/2 | 4/6 | 14/42 | 0/72 (+47 nd) | — (+10 nm) | — | 102k / 16k / 7857k | 0.10 | — | 294 | 0 | 0 (0.00) |
| lua-vm | bare | 11 | 1/2 | 5/6 | 15/46 | 0/78 (+47 nd) | 0/1 (+11 nm) | — | 130k / 25k / 10341k | 0.13 | — | 447 | 0 | 0 (0.00) |
| lua-vm | bare | 12 | 2/2 | 6/6 | 19/54 | 0/84 (+48 nd) | 0/3 (+11 nm) | — | 68k / 16k / 5263k | 0.07 | — | 301 | 0 | 0 (0.00) |
| lua-vm | skills-only | 1 | 0/2 | 0/12 | 0/6 | 0/2 | — | — | 54k / 2k / 321k | 0.01 | — | 67 | 0 | 0 (0.00) |
| lua-vm | skills-only | 2 | 1/2 | 7/12 | 0/10 | 0/14 (+12 nd) | — | — | 95k / 11k / 2408k | 0.04 | — | 305 | 0 | 0 (0.00) |
| lua-vm | skills-only | 3 | 1/2 | 5/6 | 4/16 | 0/26 (+17 nd) | — | — | 160k / 20k / 7182k | 0.10 | — | 386 | 0 | 0 (0.00) |
| lua-vm | skills-only | 4 | 0/2 | 2/4 | 8/20 | 0/32 (+18 nd) | — | — | 58k / 7k / 2910k | 0.04 | — | 145 | 0 | 0 (0.00) |
| lua-vm | skills-only | 5 | 2/2 | 6/6 | 10/22 | 0/36 (+20 nd) | — | — | 197k / 13k / 5776k | 0.08 | — | 237 | 0 | 0 (0.00) |
| lua-vm | skills-only | 6 | 2/2 | 8/8 | 12/26 | 0/42 (+20 nd) | — | — | 362k / 51k / 19572k | 0.26 | — | 941 | 0 | 0 (0.00) |
| lua-vm | skills-only | 7 | 1/2 | 4/8 | 13/30 | 0/50 (+20 nd) | — | — | 227k / 43k / 19002k | 0.23 | — | 780 | 0 | 0 (0.00) |
| lua-vm | skills-only | 8 | 0/2 | 4/8 | 14/34 | 0/58 (+24 nd) | — (+4 nm) | — | 466k / 44k / 9611k | 0.16 | — | 816 | 0 | 0 (0.00) |
| lua-vm | skills-only | 9 | 0/2 | 2/6 | 15/36 | 2/66 (+27 nd) | — (+6 nm) | — | 304k / 81k / 22002k | 0.29 | — | 1474 | 0 | 0 (0.00) |
| lua-vm | skills-only | 10 | 2/2 | 6/6 | 19/42 | 2/72 (+31 nd) | 2/4 (+6 nm) | d7×2 | 318k / 61k / 14044k | 0.20 | — | 1070 | 0 | 0 (0.00) |
| lua-vm | skills-only | 11 | 1/2 | 4/6 | 19/46 | 2/78 (+31 nd) | 2/5 (+7 nm) | d7×2 | 272k / 33k / 9601k | 0.14 | — | 523 | 0 | 0 (0.00) |
| lua-vm | skills-only | 12 | 0/2 | 4/6 | 22/54 | 2/84 (+32 nd) | 2/5 (+9 nm) | d7×2 | 211k / 37k / 12165k | 0.16 | — | 701 | 0 | 0 (0.00) |
| lua-vm | autopilot | 1 | 0/2 | 0/12 | 0/6 | 0/2 | — | — | 84k / 3k / 588k | 0.02 | — | 109 | 0 | 0 (0.00) |
| lua-vm | autopilot | 2 | 0/2 | 2/12 | 2/10 | 0/14 (+6 nd) | — | — | 92k / 15k / 2848k | 0.05 | — | 401 | 0 | 0 (0.00) |
| lua-vm | autopilot | 3 | 0/2 | 4/6 | 6/16 | 0/26 (+16 nd) | — | — | 285k / 35k / 15573k | 0.20 | — | 853 | 0 | 0 (0.00) |
| lua-vm | autopilot | 4 | 2/2 | 4/4 | 10/20 | 0/32 (+18 nd) | — | — | 272k / 33k / 12049k | 0.16 | — | 759 | 0 | 0 (0.00) |
| lua-vm | autopilot | 5 | 2/2 | 6/6 | 12/22 | 0/36 (+18 nd) | — | — | 729k / 42k / 13721k | 0.23 | — | 878 | 0 | 0 (0.00) |
| lua-vm | autopilot | 6 | 1/2 | 6/8 | 15/26 | 0/42 (+18 nd) | — | — | 592k / 86k / 31583k | 0.42 | — | 1517 | 0 | 0 (0.00) |
| lua-vm | autopilot | 7 | 0/2 | 6/8 | 18/30 | 0/50 (+20 nd) | — | — | 890k / 136k / 44747k | 0.60 | — | 2402 | 0 | 0 (0.00) |
| lua-vm | autopilot | 8 | 1/2 | 7/8 | 21/34 | 1/58 (+14 nd) | 1/2 (+2 nm) | d5×1 | 1017k / 156k / 43354k | 0.61 | — | 2636 | 0 | 0 (0.00) |
| lua-vm | autopilot | 9 | 0/2 | 3/6 | 21/36 | 1/66 (+15 nd) | 1/2 (+4 nm) | d5×1 | 905k / 170k / 42355k | 0.60 | — | 2699 | 0 | 0 (0.00) |
| lua-vm | autopilot | 10 | 2/2 | 6/6 | 25/42 | 1/72 (+18 nd) | 3/6 (+4 nm) | d5×1, d7×2 | 754k / 104k / 33583k | 0.46 | — | 1837 | 0 | 0 (0.00) |
| lua-vm | autopilot | 11 | 1/2 | 5/6 | 27/46 | 1/78 (+18 nd) | 4/7 (+5 nm) | d5×1, d7×2, d8×1 | 690k / 97k / 23980k | 0.36 | — | 1539 | 0 | 0 (0.00) |
| lua-vm | autopilot | 12 | 1/2 | 5/6 | 32/54 | 1/84 (+19 nd) | 4/8 (+6 nm) | d5×1, d7×2, d8×1 | 640k / 98k / 30643k | 0.42 | — | 1811 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 1 | 0/1 | 0/6 | 0/3 | 0/1 | — | — | 24k / 1k / 82k | 0.00 | — | 49 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 2 | 0/1 | 1/6 | 0/5 | 0/7 (+6 nd) | — | — | 17k / 1k / 126k | 0.00 | — | 50 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 3 | 0/1 | 0/3 | 0/8 | 0/13 (+11 nd) | — | — | 41k / 1k / 123k | 0.01 | — | 69 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 4 | 0/1 | 0/2 | 0/10 | 0/16 (+14 nd) | — | — | 15k / 1k / 86k | 0.00 | — | 43 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 5 | 0/1 | 1/3 | 0/11 | 0/18 (+16 nd) | — | — | 32k / 1k / 254k | 0.01 | — | 44 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 6 | 0/1 | 0/4 | 0/13 | 0/21 (+18 nd) | — | — | 25k / 1k / 140k | 0.00 | — | 47 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 7 | 0/1 | 0/4 | 0/15 | 0/25 (+22 nd) | — | — | 20k / 1k / 59k | 0.00 | — | 34 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 8 | 0/1 | 0/4 | 0/17 | 0/29 (+26 nd) | — (+2 nm) | — | 19k / 1k / 110k | 0.00 | — | 49 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 9 | 0/1 | 1/3 | 0/18 | 0/33 (+30 nd) | — (+3 nm) | — | 23k / 1k / 77k | 0.00 | — | 37 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 10 | 0/1 | 0/3 | 0/21 | 0/36 (+32 nd) | — (+5 nm) | — | 24k / 1k / 181k | 0.00 | — | 53 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 11 | 0/1 | 0/3 | 0/23 | 0/39 (+35 nd) | — (+6 nm) | — | 12k / 1k / 89k | 0.00 | — | 46 | 0 | 0 (0.00) |
| lua-vm | driver-c1a | 12 | 0/1 | 0/3 | 0/27 | 0/42 (+38 nd) | — (+7 nm) | — | 21k / 1k / 137k | 0.00 | — | 63 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 1 | 0/1 | 0/6 | 0/3 | 0/1 | — | — | 32k / 1k / 176k | 0.01 | — | 82 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 2 | 0/1 | 1/6 | 0/5 | 0/7 (+6 nd) | — | — | 79k / 4k / 647k | 0.02 | 0.0005 | 350 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 3 | 0/1 | 0/3 | 0/8 | 0/13 (+11 nd) | — | — | 51k / 4k / 633k | 0.01 | 0.0002 | 178 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 4 | 0/1 | 0/2 | 0/10 | 0/16 (+14 nd) | — | — | 25k / 1k / 177k | 0.00 | — | 61 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 5 | 0/1 | 1/3 | 0/11 | 0/18 (+16 nd) | — | — | 56k / 4k / 330k | 0.01 | 0.0004 | 144 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 6 | 0/1 | 0/4 | 0/13 | 0/21 (+18 nd) | — | — | 18k / 1k / 93k | 0.00 | — | 44 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 7 | 0/1 | 0/4 | 0/15 | 0/25 (+22 nd) | — | — | 22k / 1k / 90k | 0.00 | — | 34 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 8 | 0/1 | 0/4 | 0/17 | 0/29 (+26 nd) | — (+2 nm) | — | 28k / 1k / 188k | 0.01 | — | 49 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 9 | 0/1 | 1/3 | 0/18 | 0/33 (+30 nd) | — (+3 nm) | — | 24k / 1k / 213k | 0.00 | — | 54 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 10 | 0/1 | 0/3 | 0/21 | 0/36 (+32 nd) | — (+5 nm) | — | 14k / 1k / 121k | 0.00 | — | 49 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 11 | 0/1 | 0/3 | 0/23 | 0/39 (+35 nd) | — (+6 nm) | — | 14k / 1k / 87k | 0.00 | — | 38 | 0 | 0 (0.00) |
| lua-vm | driver-c3a | 12 | 0/1 | 0/3 | 0/27 | 0/42 (+38 nd) | — (+7 nm) | — | 23k / 1k / 157k | 0.00 | — | 53 | 0 | 0 (0.00) |
| sql-engine | bare | 1 | 0/2 | 0/8 | 0/8 | 0/2 | — | — | 47k / 1k / 65k | 0.01 | — | 113 | 0 | 0 (0.00) |
| sql-engine | bare | 2 | 0/2 | 0/8 | 0/18 | 0/10 (+8 nd) | — | — | 76k / 6k / 809k | 0.02 | — | 264 | 0 | 0 (0.00) |
| sql-engine | bare | 3 | 0/2 | 0/8 | 2/22 | 0/18 (+15 nd) | — | — | 13k / 3k / 487k | 0.01 | — | 148 | 0 | 0 (0.00) |
| sql-engine | bare | 4 | 0/2 | 3/8 | 5/28 | 0/26 (+21 nd) | — | — | 45k / 8k / 1730k | 0.03 | — | 386 | 0 | 0 (0.00) |
| sql-engine | bare | 5 | 0/2 | 1/10 | 6/34 | 0/34 (+26 nd) | — | — | 100k / 10k / 2486k | 0.04 | — | 317 | 0 | 0 (0.00) |
| sql-engine | bare | 6 | 0/2 | 3/8 | 13/42 | 0/44 (+28 nd) | — | — | 72k / 15k / 4161k | 0.06 | — | 582 | 0 | 0 (0.00) |
| sql-engine | bare | 7 | 0/2 | 2/8 | 13/48 | 0/52 (+33 nd) | — | — | 180k / 25k / 4681k | 0.08 | — | 724 | 0 | 0 (0.00) |
| sql-engine | bare | 8 | 0/2 | 6/8 | 15/56 | 0/60 (+39 nd) | — (+2 nm) | — | 92k / 31k / 8195k | 0.11 | — | 682 | 0 | 0 (0.00) |
| sql-engine | bare | 9 | 0/2 | 1/4 | 17/62 | 0/68 (+40 nd) | — (+6 nm) | — | 146k / 21k / 7725k | 0.10 | — | 790 | 0 | 0 (0.00) |
| sql-engine | bare | 10 | 2/2 | 2/2 | 21/66 | 0/72 (+43 nd) | 2/2 (+6 nm) | d7×2 | 28k / 12k / 3107k | 0.04 | — | 427 | 0 | 0 (0.00) |
| sql-engine | bare | 11 | 1/2 | 6/8 | 25/72 | 0/74 (+43 nd) | 3/4 (+8 nm) | d7×3 | 109k / 34k / 13174k | 0.16 | — | 670 | 0 | 0 (0.00) |
| sql-engine | bare | 12 | 0/2 | 5/8 | 31/76 | 0/82 (+38 nd) | 3/4 (+10 nm) | d7×3 | 199k / 39k / 10863k | 0.15 | — | 832 | 0 | 0 (0.00) |
| sql-engine | skills-only | 1 | 0/2 | 0/8 | 0/8 | 0/2 | — | — | 46k / 2k / 228k | 0.01 | — | 59 | 0 | 0 (0.00) |
| sql-engine | skills-only | 2 | 0/2 | 3/8 | 3/18 | 0/10 (+8 nd) | — | — | 43k / 5k / 558k | 0.01 | — | 141 | 0 | 0 (0.00) |
| sql-engine | skills-only | 3 | 0/2 | 2/8 | 5/22 | 0/18 (+13 nd) | — | — | 38k / 7k / 987k | 0.02 | — | 265 | 0 | 0 (0.00) |
| sql-engine | skills-only | 4 | 0/2 | 6/8 | 10/28 | 0/26 (+19 nd) | — | — | 72k / 12k / 2716k | 0.04 | — | 301 | 0 | 0 (0.00) |
| sql-engine | skills-only | 5 | 0/2 | 7/10 | 14/34 | 0/34 (+21 nd) | — | — | 143k / 27k / 4846k | 0.08 | — | 474 | 0 | 0 (0.00) |
| sql-engine | skills-only | 6 | 0/2 | 3/8 | 20/42 | 0/44 (+18 nd) | — | — | 127k / 38k / 9366k | 0.13 | — | 710 | 0 | 0 (0.00) |
| sql-engine | skills-only | 7 | 0/2 | 3/8 | 21/48 | 1/52 (+23 nd) | — | — | 138k / 39k / 12910k | 0.16 | — | 660 | 0 | 0 (0.00) |
| sql-engine | skills-only | 8 | 0/2 | 6/8 | 22/56 | 1/60 (+28 nd) | — (+2 nm) | — | 164k / 47k / 13586k | 0.18 | — | 829 | 0 | 0 (0.00) |
| sql-engine | skills-only | 9 | 1/2 | 2/4 | 25/62 | 1/68 (+30 nd) | 0/2 (+4 nm) | — | 278k / 31k / 7781k | 0.12 | — | 582 | 0 | 0 (0.00) |
| sql-engine | skills-only | 10 | 2/2 | 2/2 | 27/66 | 1/72 (+32 nd) | 2/4 (+4 nm) | d7×2 | 106k / 37k / 4961k | 0.08 | — | 681 | 0 | 0 (0.00) |
| sql-engine | skills-only | 11 | 0/2 | 6/8 | 32/72 | 1/74 (+32 nd) | 2/4 (+8 nm) | d7×2 | 197k / 58k / 16133k | 0.21 | — | 1114 | 0 | 0 (0.00) |
| sql-engine | skills-only | 12 | 0/2 | 2/8 | 34/76 | 1/82 (+34 nd) | 2/4 (+10 nm) | d7×2 | 125k / 29k / 8324k | 0.11 | — | 464 | 0 | 2 (0.00) |
| sql-engine | autopilot | 1 | 0/2 | 0/8 | 0/8 | 0/2 | — | — | 60k / 3k / 356k | 0.01 | — | 88 | 0 | 0 (0.00) |
| sql-engine | autopilot | 2 | 0/2 | 0/8 | 0/18 | 0/10 (+8 nd) | — | — | 38k / 4k / 537k | 0.01 | — | 98 | 0 | 0 (0.00) |
| sql-engine | autopilot | 3 | 0/2 | 2/8 | 2/22 | 0/18 (+16 nd) | — | — | 81k / 10k / 1706k | 0.03 | — | 295 | 0 | 0 (0.00) |
| sql-engine | autopilot | 4 | 0/2 | 3/8 | 8/28 | 0/26 (+19 nd) | — | — | 176k / 37k / 9226k | 0.13 | — | 1038 | 0 | 0 (0.00) |
| sql-engine | autopilot | 5 | 0/2 | 6/10 | 10/34 | 0/34 (+24 nd) | — | — | 455k / 71k / 24719k | 0.33 | — | 1744 | 0 | 0 (0.00) |
| sql-engine | autopilot | 6 | 2/2 | 8/8 | 19/42 | 0/44 (+23 nd) | — | — | 552k / 92k / 23133k | 0.33 | — | 1714 | 0 | 0 (0.00) |
| sql-engine | autopilot | 7 | 0/2 | 3/8 | 20/48 | 1/52 (+23 nd) | — | — | 877k / 182k / 42572k | 0.60 | — | 2635 | 0 | 0 (0.00) |
| sql-engine | autopilot | 8 | 0/2 | 6/8 | 21/56 | 2/60 (+28 nd) | — (+2 nm) | — | 468k / 100k / 30414k | 0.40 | — | 1581 | 0 | 0 (0.00) |
| sql-engine | autopilot | 9 | 0/2 | 2/4 | 24/62 | 2/68 (+30 nd) | — (+6 nm) | — | 665k / 173k / 37575k | 0.53 | — | 2484 | 0 | 0 (0.00) |
| sql-engine | autopilot | 10 | 2/2 | 2/2 | 27/66 | 1/72 (+32 nd) | 2/2 (+6 nm) | d7×2 | 1181k / 157k / 44455k | 0.64 | — | 3217 | 0 | 0 (0.00) |
| sql-engine | autopilot | 11 | 0/2 | 3/8 | 30/72 | 1/74 (+32 nd) | 2/2 (+10 nm) | d7×2 | 702k / 123k / 34243k | 0.47 | — | 2515 | 0 | 0 (0.00) |
| sql-engine | autopilot | 12 | 0/2 | 2/8 | 33/76 | 1/82 (+34 nd) | 2/2 (+12 nm) | d7×2 | 312k / 40k / 12773k | 0.18 | — | 754 | 0 | 2 (0.00) |
| sql-engine | driver-c1a | 1 | 0/1 | 0/4 | 0/4 | 0/1 | — | — | 23k / 1k / 88k | 0.00 | — | 103 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 2 | 0/1 | 0/4 | 0/9 | 0/5 (+4 nd) | — | — | 32k / 4k / 368k | 0.01 | — | 174 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 3 | 0/1 | 0/4 | 0/11 | 0/9 (+8 nd) | — | — | 35k / 3k / 407k | 0.01 | — | 89 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 4 | 0/1 | 0/4 | 0/14 | 0/13 (+12 nd) | — | — | 31k / 2k / 287k | 0.01 | — | 95 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 5 | 0/1 | 0/5 | 0/17 | 0/17 (+16 nd) | — | — | 32k / 2k / 377k | 0.01 | — | 85 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 6 | 0/1 | 0/4 | 0/21 | 0/22 (+21 nd) | — | — | 16k / 1k / 49k | 0.00 | — | 25 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 7 | 0/1 | 1/4 | 0/24 | 0/26 (+25 nd) | — | — | 41k / 2k / 376k | 0.01 | — | 80 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 8 | 0/1 | 0/4 | 0/28 | 0/30 (+28 nd) | — (+1 nm) | — | 26k / 1k / 164k | 0.00 | — | 52 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 9 | 0/1 | 0/2 | 1/31 | 0/34 (+32 nd) | — (+3 nm) | — | 28k / 2k / 298k | 0.01 | — | 71 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 10 | 0/1 | 0/1 | 2/33 | 0/36 (+34 nd) | — (+4 nm) | — | 49k / 3k / 629k | 0.01 | — | 121 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 11 | 0/1 | 0/4 | 2/36 | 0/37 (+35 nd) | — (+6 nm) | — | 36k / 3k / 426k | 0.01 | — | 102 | 0 | 0 (0.00) |
| sql-engine | driver-c1a | 12 | 0/1 | 0/4 | 2/38 | 0/41 (+39 nd) | — (+7 nm) | — | 19k / 1k / 110k | 0.00 | — | 59 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 1 | 0/1 | 0/4 | 0/4 | 0/1 | — | — | 22k / 2k / 122k | 0.00 | — | 112 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 2 | 0/1 | 0/4 | 0/9 | 0/5 (+4 nd) | — | — | 33k / 3k / 339k | 0.01 | 0.0001 | 227 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 3 | 0/1 | 0/4 | 0/11 | 0/9 (+8 nd) | — | — | 45k / 2k / 624k | 0.01 | 0.0001 | 101 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 4 | 0/1 | 0/4 | 0/14 | 0/13 (+12 nd) | — | — | 47k / 4k / 532k | 0.01 | 0.0000 | 337 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 5 | 0/1 | 0/5 | 0/17 | 0/17 (+16 nd) | — | — | 29k / 1k / 179k | 0.01 | — | 42 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 6 | 0/1 | 0/4 | 0/21 | 0/22 (+21 nd) | — | — | 25k / 1k / 196k | 0.01 | — | 51 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 7 | 0/1 | 0/4 | 0/24 | 0/26 (+25 nd) | — | — | 77k / 7k / 462k | 0.02 | 0.0004 | 457 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 8 | 0/1 | 0/4 | 0/28 | 0/30 (+29 nd) | — (+1 nm) | — | 28k / 2k / 301k | 0.01 | — | 84 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 9 | 0/1 | 0/2 | 0/31 | 0/34 (+33 nd) | — (+3 nm) | — | 38k / 2k / 361k | 0.01 | — | 65 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 10 | 0/1 | 0/1 | 0/33 | 0/36 (+35 nd) | — (+4 nm) | — | 85k / 7k / 660k | 0.02 | 0.0001 | 324 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 11 | 0/1 | 0/4 | 0/36 | 0/37 (+36 nd) | — (+6 nm) | — | 21k / 1k / 144k | 0.00 | — | 40 | 0 | 0 (0.00) |
| sql-engine | driver-c3a | 12 | 0/1 | 0/4 | 0/38 | 0/41 (+40 nd) | — (+7 nm) | — | 18k / 1k / 98k | 0.00 | — | 53 | 0 | 0 (0.00) |
