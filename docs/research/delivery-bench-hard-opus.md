# delivery-bench difficile — Opus 5.5: catene da 1, 4 e 12

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-opus`
- Role: `research`
- Parent: [DBH-20 — Misurare con Opus 5.5](../tickets/delivery-bench-hard/done/20-measure-opus.md)

## Stato
Output di DBH-20 (2026-09-30/10-01). Il protocollo di [DBH-09](delivery-bench-hard-results.md) è
ripetuto con `anthropic/claude-opus-5-5` a `--thinking medium` invece di luna: cinque bracci,
tre sistemi maturi (`lua-vm`, `sql-engine`, `crdt-yjs`), le stesse suite nascoste. Lotto
`dbh-opus`. Record di cella, giudizi e ledger stanno nel repo privato dell'oracolo
(`results/dbh-opus/`). Qui ci sono solo aggregati, senza nomi di controlli, trappole, richieste
o difetti.

In breve:
- **Opus esce dal pavimento; le catene brevi arrivano al soffitto.** Alla catena da 4
  `bare`, skills-only, Autopilot e c1a accettano 36 richieste su 36, contro 1-9/36 di luna.
  Alla richiesta 1 i cinque bracci accettano complessivamente 44 richieste su 45.
- **La regola sceglie `bare` a ogni lunghezza**, per il pareggio al braccio più semplice
  fra quelli non esclusi. Alla catena da 4 c3a è significativamente peggiore. A L12 i bracci
  non-driver accettano 63, 64 e 65/72; i driver 30 e 23/36.
- **I driver perdono consegne anche per arresti e cancelli.** Il limite della foglia è
  1800 s. c3a si ferma al cancello 12 volte; 11 candidati superano il giudizio separato,
  senza diventare consegne effettive. Anche alcuni run integrati non sono accettati.
- **Tre difetti trovati e corretti nel sorgente**, uno dell'harness e due del driver
  (DBH-19, TDL-01, TDC-01). L'harness tocca anche altri bracci. La differenza significativa
  di c3a alla catena da 4 non resta significativa escludendo le coppie interessate: è
  sensibilità descrittiva, non una rimisura del driver corretto.
- **Nessuna compaction osservata**. Nessuna trappola violata nei bracci non-driver entro
  le verifiche misurabili; questo non dimostra sicurezza generale.
- Spesa: 792,09 $ di listino Pi più 0,040505 $ stimati per Jev.

## Autorizzazione e provenienza
- **Autorità del lotto**: `results/dbh-opus-authority.json` (sha256 `47527a02…`). Dopo il report
  di DBH-16 l'agente aveva proposto una misura con un modello più forte, stimando circa 490 $
  per Opus, e l'utente ha risposto: «Aggiorniamo pi personal config e le skills e poi facciamo
  con opus 5-5». Il tetto iniziale era di 500 $ a prezzo di listino. Dopo il pilota l'agente ha
  visto che il piano l'avrebbe superato, e ha fatto girare le catene da 4 una ripetizione alla
  volta. L'utente ha poi scritto «metti budget a 1000 euro». L'emendamento
  `results/dbh-opus-authority-amendment-1.json` (sha256 `473fdca6…`) porta il tetto a 1000 $ di
  listino e cita l'autorità originale per hash, senza modificarla.
- **Modello e fornitore**: Opus 5.5 attraverso l'estensione OAuth di Claude Pro/Max
  (`pi-wierd-stuff` `8126047`, cartella `3ad096fc…`), legata al lotto e caricata con `-e` da ogni
  braccio e da ogni foglia del driver
  ([DBH-18](../tickets/delivery-bench-hard/done/18-bind-pi-extension.md)). Le richieste si pagano
  con il piano Claude; gli USD sono il prezzo di listino stimato da Pi (4 $ per milione di token
  in ingresso, 20 in uscita, 0,2 in lettura di cache).
- **Legami uguali a `dbh`**, verificati prima di partire: seed e suite nascoste dei tre scenari
  (`lua-vm` `f90869af…`, `sql-engine` `5b029cb4…`, `crdt-yjs` `be281cb4…`), bracci, comando dei
  test del driver, tetto di 5400 s per richiesta.
- **Skill installate**: quelle di agent-skills `6a1f84d`, installate da pi-personal-config
  (ASP-08, #48) e legate al lotto (manifest `9f2dd817…`,
  [DBH-17](../tickets/delivery-bench-hard/done/17-bind-installed-skills.md)). Nessun
  aggiornamento durante il lotto. Pi 0.99.1.
- **Harness**, spostato solo fra due `run-lot` (contratto §9):
  - catene da 1 e da 4 a `ea96bea` (DBH-18, #400);
  - catena da 12 a `3426d7e` (DBH-19, #402), che cambia solo il runner e i suoi test.
  Le copie del driver vengono da un checkout pulito di `ea96bea` (`prepare-drivers --source`) e
  non sono mai cambiate. Non contengono quindi le correzioni di TDL-01 e TDC-01 (vedi *Guasti*).
- **Esecuzione**, 4 celle in parallelo:
  - catene da 1 il 30/09, dalle 07:45 alle 10:31 UTC;
  - catene da 4 dalle 10:32 alle 18:35, prima la ripetizione 1 e poi le ripetizioni 2 e 3
    insieme;
  - catena da 12, ripetizione 1, dalle 18:36 al 01/10 alle 02:49;
  - catena da 12, ripetizione 2 dei tre bracci non-driver, il 01/10 dalle 03:47 alle
    08:13 UTC. La regola non richiede altre ripetizioni.
  Il lotto ha 372 richieste giudicate e 390 tentativi: 372 dei bracci e 18 guasti
  d'infrastruttura (vedi *Guasti*), nessuno esaurito. Un timeout, nessun tetto di catena, nessuna
  cella invalidata dall'audit, nessun errore del giudice. Poi `judge-gated` ha giudicato a parte
  i 12 candidati fermi di c3a.
- **Spesa**: 792,09 $ di listino Pi, inclusi i retry d'infrastruttura; 79,63 $ per la
  posizione 1, 232,50 $ per le posizioni 2-4 e 479,96 $ per le posizioni 5-12. Jev costa
  separatamente 0,040505 $ stimati. Le tabelle sono prefissi delle stesse catene e non
  vanno sommate fra livelli. È una stima di listino, non una fattura Claude né una conversione
  del budget espresso in euro. Il totale resta sotto il tetto operativo emendato di 1000 $.

## Come si legge
Come nel [report di DBH-09](delivery-bench-hard-results.md#come-si-legge): stesse letture lungo
la catena, stessa regola di TBA-03, appaiata con `bare` per (scenario, ripetizione, richiesta),
con la famiglia di Holm di quattro confronti. Il confronto fra modelli usa per luna i bracci di
`dbh` e i driver corretti di [`dbh-drivers2`](delivery-bench-hard-drivers.md). Alla catena da 12
usa solo la ripetizione 1, l'unica misurata per tutti i bracci in tutti e due i lotti.

## Risultati

### Opus e luna a confronto
Accettate, latenti trovati, invarianti rotte e spesa sono sommati per braccio. *Contro `bare`* è
la decisione della regola nel lotto del modello; alla catena da 12, con una sola ripetizione, la
regola può chiedere ripetizioni (`repeat`) quando l'evidenza è ancora insufficiente.

### L1

| Modello | Braccio | Catene | Accettate | Latenti | Invarianti rotte | USD | Mediana catena min | Contro `bare` |
|---|---|---:|---:|---:|---:|---:|---:|---|
| luna medium | bare | 9 | 0/9 | 3/30 | 0/9 | 0.04 | 2 | base |
| luna medium | skills-only | 9 | 1/9 | 4/30 | 0/9 | 0.06 | 1 | indistinguishable |
| luna medium | autopilot | 9 | 0/9 | 0/30 | 0/9 | 0.05 | 1 | indistinguishable |
| luna medium | driver-c1a | 9 | 0/9 | 1/30 | 0/9 | 0.05 | 1 | indistinguishable |
| luna medium | driver-c3a | 9 | 0/9 | 0/30 | 0/9 | 0.07 | 1 | indistinguishable |
| luna medium | *regola* | | **bare** | | | | | ripetere: — |
| Opus 5.5 medium | bare | 9 | 9/9 | 26/30 | 0/9 | 8.63 | 7 | base |
| Opus 5.5 medium | skills-only | 9 | 9/9 | 27/30 | 0/9 | 9.78 | 6 | indistinguishable |
| Opus 5.5 medium | autopilot | 9 | 9/9 | 27/30 | 0/9 | 35.60 | 19 | indistinguishable |
| Opus 5.5 medium | driver-c1a | 9 | 9/9 | 27/30 | 0/9 | 11.89 | 6 | indistinguishable |
| Opus 5.5 medium | driver-c3a | 9 | 8/9 | 23/30 | 0/9 | 13.71 | 9 | indistinguishable |
| Opus 5.5 medium | *regola* | | **bare** | | | | | ripetere: — |

### L4

| Modello | Braccio | Catene | Accettate | Latenti | Invarianti rotte | USD | Mediana catena min | Contro `bare` |
|---|---|---:|---:|---:|---:|---:|---:|---|
| luna medium | bare | 9 | 1/36 | 25/99 | 0/126 | 0.27 | 10 | base |
| luna medium | skills-only | 9 | 9/36 | 35/99 | 0/126 | 0.78 | 15 | better |
| luna medium | autopilot | 9 | 6/36 | 38/99 | 0/126 | 1.62 | 24 | indistinguishable |
| luna medium | driver-c1a | 9 | 1/36 | 32/99 | 0/126 | 0.24 | 8 | indistinguishable |
| luna medium | driver-c3a | 9 | 0/36 | 4/99 | 0/126 | 0.31 | 10 | indistinguishable |
| luna medium | *regola* | | **skills-only** | | | | | ripetere: — |
| Opus 5.5 medium | bare | 9 | 36/36 | 87/99 | 0/126 | 37.25 | 29 | base |
| Opus 5.5 medium | skills-only | 9 | 36/36 | 88/99 | 0/126 | 40.75 | 25 | indistinguishable |
| Opus 5.5 medium | autopilot | 9 | 36/36 | 91/99 | 0/126 | 132.96 | 73 | indistinguishable |
| Opus 5.5 medium | driver-c1a | 9 | 36/36 | 90/99 | 0/126 | 48.19 | 37 | indistinguishable |
| Opus 5.5 medium | driver-c3a | 9 | 26/36 | 63/99 | 0/126 | 52.95 | 41 | worse |
| Opus 5.5 medium | *regola* | | **bare** | | | | | ripetere: — |

### L12 (ripetizione 1)

| Modello | Braccio | Catene | Accettate | Latenti | Invarianti rotte | USD | Mediana catena min | Contro `bare` |
|---|---|---:|---:|---:|---:|---:|---:|---|
| luna medium | bare | 3 | 8/36 | 38/89 | 1/127 | 1.02 | 46 | base |
| luna medium | skills-only | 3 | 11/36 | 45/89 | 3/127 | 1.82 | 113 | repeat |
| luna medium | autopilot | 3 | 7/36 | 40/89 | 7/127 | 4.64 | 232 | repeat |
| luna medium | driver-c1a | 3 | 3/36 | 23/89 | 0/127 | 0.23 | 23 | repeat |
| luna medium | driver-c3a | 3 | 0/36 | 1/89 | 0/127 | 0.29 | 26 | worse |
| luna medium | *regola* | | **indecisa** | | | | | ripetere: skills-only |
| Opus 5.5 medium | bare | 3 | 31/36 | 71/89 | 0/127 | 54.37 | 88 | base |
| Opus 5.5 medium | skills-only | 3 | 32/36 | 72/89 | 0/127 | 60.53 | 95 | repeat |
| Opus 5.5 medium | autopilot | 3 | 32/36 | 76/89 | 0/127 | 143.88 | 251 | repeat |
| Opus 5.5 medium | driver-c1a | 3 | 30/36 | 74/89 | 0/127 | 66.24 | 157 | repeat |
| Opus 5.5 medium | driver-c3a | 3 | 23/36 | 51/89 | 0/127 | 71.49 | 162 | repeat |
| Opus 5.5 medium | *regola* | | **indecisa** | | | | | ripetere: skills-only, autopilot |

### Catene da 1 (3 ripetizioni, 9 catene per braccio)
| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 9/9 | 26/30 | 0/9 | — | — | 8.63 | — | 402 | 0 | 6 (0.02) | 0 |
| skills-only | 9 | 9/9 | 27/30 | 0/9 | — | — | 9.78 | — | 364 | 0 | 0 (0.00) | 0 |
| autopilot | 9 | 9/9 | 27/30 | 0/9 | — | — | 35.60 | — | 1147 | 0 | 0 (0.00) | 0 |
| driver-c1a | 9 | 9/9 | 27/30 | 0/9 | — | — | 11.89 | — | 370 | 0 | 0 (0.00) | 0 |
| driver-c3a | 9 | 8/9 | 23/30 | 0/9 | — | — | 13.71 | 0.0078 | 522 | 0 | 0 (0.00) | 0 |

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| autopilot | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 9 | 8 | 9 | 0 | 1 | -1 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Catene da 4 (3 ripetizioni, 9 catene per braccio)
| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 3 | 12/12 | 24/27 | 0/39 | — | — | 11.55 | — | 1818 | 0 | 0 (0.00) | 0 |
| crdt-yjs | skills-only | 3 | 12/12 | 24/27 | 0/39 | — | — | 10.83 | — | 1431 | 0 | 0 (0.00) | 0 |
| crdt-yjs | autopilot | 3 | 12/12 | 24/27 | 0/39 | — | — | 42.01 | — | 4104 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c1a | 3 | 12/12 | 23/27 | 0/39 | — | — | 13.67 | — | 2243 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 3 | 10/12 | 19/27 | 0/39 (+6 nd) | — | — | 14.50 | 0.0079 | 2341 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 3 | 12/12 | 24/30 | 0/48 | — | — | 9.70 | — | 1395 | 0 | 6 (0.02) | 0 |
| lua-vm | skills-only | 3 | 12/12 | 25/30 | 0/48 | — | — | 12.23 | — | 1415 | 0 | 0 (0.00) | 0 |
| lua-vm | autopilot | 3 | 12/12 | 27/30 | 0/48 | — | — | 44.70 | — | 3776 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c1a | 3 | 12/12 | 27/30 | 0/48 | — | — | 12.06 | — | 1902 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 3 | 12/12 | 26/30 | 0/48 | — | — | 13.63 | 0.0092 | 2161 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 3 | 12/12 | 39/42 | 0/39 | — | — | 16.01 | — | 1963 | 0 | 3 (0.00) | 0 |
| sql-engine | skills-only | 3 | 12/12 | 39/42 | 0/39 | — | — | 17.69 | — | 2208 | 0 | 0 (0.00) | 0 |
| sql-engine | autopilot | 3 | 12/12 | 40/42 | 0/39 | — | — | 46.25 | — | 5455 | 0 | 3 (0.00) | 0 |
| sql-engine | driver-c1a | 3 | 12/12 | 40/42 | 0/39 | — | — | 22.46 | — | 3511 | 0 | 3 (0.00) | 0 |
| sql-engine | driver-c3a | 3 | 4/12 | 18/42 | 0/39 (+20 nd) | — | — | 24.83 | 0.0077 | 3903 | 0 | 3 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 36/36 | 87/99 | 0/126 | — | — | 37.25 | — | 1744 | 0 | 9 (0.02) | 0 |
| skills-only | 9 | 36/36 | 88/99 | 0/126 | — | — | 40.75 | — | 1514 | 0 | 0 (0.00) | 0 |
| autopilot | 9 | 36/36 | 91/99 | 0/126 | — | — | 132.96 | — | 4369 | 0 | 3 (0.00) | 0 |
| driver-c1a | 9 | 36/36 | 90/99 | 0/126 | — | — | 48.19 | — | 2243 | 0 | 3 (0.00) | 0 |
| driver-c3a | 9 | 26/36 | 63/99 | 0/126 (+26 nd) | — | — | 52.95 | 0.0248 | 2463 | 0 | 3 (0.00) | 0 |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 36 | 36 | 36 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| autopilot | 36 | 36 | 36 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 36 | 36 | 36 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 36 | 26 | 36 | 0 | 10 | -10 | 0.001953 | 0.007812 | worse |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

**Sensibilità.** Delle 10 richieste che solo `bare` accetta contro c3a, 6 sono toccate da un
difetto: 3 sessioni chiuse dal fornitore dopo l'output e giudicate così (DBH-19), e 3 run fermi
perché il revisore diretto non è partito (TDL-01). Togliendo le coppie dei tagli c3a fa 0 contro
7, Holm 0,0625. Togliendo anche quelle del revisore fa 0 contro 4, Holm 0,5. In tutti e due i
casi c3a non si distingue da `bare`. Gli altri tre bracci restano indistinguibili in ogni
variante.

### Catene da 12 (2 ripetizioni per i bracci non-driver; 1 per i driver)
| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 2 | 22/24 | 38/48 | 0/88 (+2 nd) | 0/10 (+4 nm) | — | 43.79 | — | 8347 | 0 | 0 (0.00) | 0 |
| crdt-yjs | skills-only | 2 | 22/24 | 38/48 | 0/88 (+2 nd) | 0/10 (+4 nm) | — | 41.11 | — | 6211 | 0 | 0 (0.00) | 0 |
| crdt-yjs | autopilot | 2 | 22/24 | 38/48 | 0/88 (+2 nd) | 0/10 (+4 nm) | — | 109.70 | — | 13417 | 1 | 0 (0.00) | 0 |
| crdt-yjs | driver-c1a | 1 | 9/12 | 17/24 | 0/44 (+13 nd) | 0/4 (+3 nm) | — | 22.87 | — | 9432 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 1 | 7/12 | 14/24 | 0/44 (+21 nd) | 0/3 (+4 nm) | — | 24.02 | 0.0066 | 9704 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 2 | 22/24 | 44/54 | 0/84 (+2 nd) | 0/14 | — | 29.03 | — | 3986 | 0 | 6 (0.02) | 0 |
| lua-vm | skills-only | 2 | 22/24 | 44/54 | 0/84 (+2 nd) | 0/14 | — | 35.37 | — | 4267 | 0 | 0 (0.00) | 0 |
| lua-vm | autopilot | 2 | 22/24 | 48/54 | 0/84 (+2 nd) | 0/14 | — | 89.39 | — | 10783 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c1a | 1 | 11/12 | 24/27 | 0/42 (+1 nd) | 2/7 | d5×1, d8×1 | 14.60 | — | 5655 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 1 | 11/12 | 23/27 | 0/42 (+1 nd) | 0/7 | — | 15.91 | 0.0096 | 6542 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 2 | 19/24 | 60/76 | 1/82 (+5 nd) | 0/10 (+4 nm) | — | 35.26 | — | 6092 | 0 | 0 (0.00) | 0 |
| sql-engine | skills-only | 2 | 20/24 | 62/76 | 0/82 (+4 nd) | 0/12 (+2 nm) | — | 44.67 | — | 7477 | 0 | 0 (0.00) | 0 |
| sql-engine | autopilot | 2 | 21/24 | 67/76 | 1/82 (+1 nd) | 0/11 (+3 nm) | — | 94.39 | — | 15470 | 0 | 3 (0.00) | 0 |
| sql-engine | driver-c1a | 1 | 10/12 | 33/38 | 0/41 (+2 nd) | 0/6 (+1 nm) | — | 28.77 | — | 13542 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c3a | 1 | 5/12 | 14/38 | 0/41 (+20 nd) | 0/4 (+3 nm) | — | 31.55 | 0.0077 | 14408 | 0 | 0 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 6 | 63/72 | 142/178 | 1/254 (+9 nd) | 0/34 (+8 nm) | — | 108.07 | — | 6022 | 0 | 6 (0.02) | 0 |
| skills-only | 6 | 64/72 | 144/178 | 0/254 (+8 nd) | 0/36 (+6 nm) | — | 121.15 | — | 6211 | 0 | 0 (0.00) | 0 |
| autopilot | 6 | 65/72 | 153/178 | 1/254 (+5 nd) | 0/35 (+7 nm) | — | 293.48 | — | 13702 | 1 | 3 (0.00) | 0 |
| driver-c1a | 3 | 30/36 | 74/89 | 0/127 (+16 nd) | 2/17 (+4 nm) | d5×1, d8×1 | 66.24 | — | 9432 | 0 | 0 (0.00) | 0 |
| driver-c3a | 3 | 23/36 | 51/89 | 0/127 (+42 nd) | 0/14 (+7 nm) | — | 71.49 | 0.0239 | 9704 | 0 | 0 (0.00) | 0 |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: contract×2; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 72 | 64 | 63 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| autopilot | 72 | 65 | 63 | 2 | 0 | +2 | 0.5 | 1 | indistinguishable |
| driver-c1a | 36 | 30 | 31 | 1 | 2 | -1 | 1 | 1 | repeat |
| driver-c3a | 36 | 23 | 31 | 1 | 9 | -8 | 0.02148 | 0.08594 | repeat |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

La prima ripetizione lasciava `skills-only` e Autopilot nella lista `repeat_needed`;
la seconda è stata eseguita per i tre bracci non-driver, conservando l'appaiamento con
`bare`. Dopo questa, `repeat_needed` è vuota e la regola sceglie `bare`. La dicitura
`repeat` nelle righe dei driver segnala che hanno una sola ripetizione; non prova
un'equivalenza con `bare` e non autorizza una nuova misura. Escludendo la coppia residua
colpita da DBH-19 (Autopilot, ripetizione 2), le conclusioni non cambiano.

### Esiti del driver e motivi dei cancelli
Alla catena da 12 i driver girano solo nella ripetizione 1, come in DBH-09: 60 run ciascuno in
tutto il lotto.
- **c1a**: 56 run integrati, e 53 sono accettati; gli altri 3 passano una parte dei controlli
  nascosti della richiesta. 4 run falliscono: 3 perché il builder supera il tempo massimo della
  foglia (1800 s) e 1 per la sessione chiusa dal fornitore (DBH-19). I 3 timeout cadono sulle
  stesse tre richieste di `crdt-yjs` dove cadono quelli di c3a. Alla catena da 12 le 2 richieste
  che solo `bare` accetta contro c1a sono due di queste. Una richiesta è accettata anche se il
  run fallisce: il lavoro delle richieste prima la soddisfaceva già.
- **c3a**: 43 run integrati, e 39 sono accettati. 12 run si fermano al cancello e 5 falliscono:
  3 per il tempo massimo della foglia, sulle stesse richieste di c1a, e 2 per la sessione chiusa
  dal fornitore. Alla catena da 12, delle 9 richieste che solo `bare` accetta, 6 sono fermate al
  cancello, 2 sono timeout della foglia e una segue lavoro fermato prima. Come per c1a, una
  richiesta è accettata anche se il run si ferma al cancello.
- **Test**: 111 esecuzioni della suite nei due bracci. Una sola non arriva in fondo: su
  `sql-engine` il contenitore della suite è stato ucciso dopo 121 s (codice 137), e la causa non
  è registrata.

I 12 cancelli di c3a e i loro candidati, giudicati a parte con `judge-gated`:

| Cancello | Run | Candidato fermo accettato |
|---|---:|---:|
| `review.scope_complete` indeterminato | 5 | 5 |
| revisore diretto non partito (TDL-01) | 4 | 3 |
| revisore diretto con una cache di pytest (TDC-01) | 1 | 1 |
| `retry.recoverable` indeterminato, dopo la suite uccisa | 1 | 1 |
| `qa.evidence_class` senza giudice: il processo è morto all'avvio | 1 | 1 |
| **Totale** | **12** | **11** |

Verdetti del giudice fresco sulle 103 escalation:

| Domanda | Verdetti |
|---|---|
| `review.scope_complete` | sì×25, indeterminato×5 |
| `review.findings_block` | no×9 |
| `qa.evidence_class` | integration×31, unit×7, senza giudice×1 |
| `verify.claim_supported` | sì×24 |
| `retry.recoverable` | indeterminato×1 |

*Senza giudice*: il processo di Pi del giudice è uscito dopo 2 s con il codice `0xC0000409` di
Windows, senza uscita. Il driver lo conta come indeterminato.

## Letture
1. **Con Opus quattro bracci raggiungono il soffitto sulle catene brevi.** Alla catena da 4
   accettano 36/36 contro 1-9/36 con luna; c3a resta a 26/36. In quel livello non si osservano
   invarianti rotte né trappole violate fuori dai driver; i quattro bracci trovano fra 87 e 91
   latenti su 99. Alla catena da 12 restano richieste non accettate: non è un soffitto generale.
2. **Non si osserva un vantaggio significativo di accettazione per la struttura.**
   skills-only e Autopilot pareggiano con `bare` a L1/L4. A L12 i piccoli scarti osservati
   (+1 e +2/72) non sono significativi; indistinguibilità non significa equivalenza.
3. **Autopilot costa e impiega più tempo nel lotto.** A L4 costa 132,96 $ contro
   37,25 $ di `bare` e 40,75 $ di skills-only; la mediana è 73 minuti contro 29 e 25.
   A L12 costa 293,48 $ contro 108,07 $ e 121,15 $, con mediana 228 minuti contro
   100 e 104. Sono tempi di catena, non durata totale dell'esperimento.
4. **Arresti e cancelli contribuiscono alle mancate consegne dei driver.** I run integrati
   accettati sono 53/56 per c1a e 39/43 per c3a: restano anche difetti nel lavoro integrato.
   I record documentano timeout e cancelli, ma non isolano causalmente il costo delle
   sessioni nuove rispetto ad altre differenze fra bracci.
5. **Il giudizio separato accetta 11 candidati fermi su 12.** Non dimostra che ogni cancello
   fosse ingiustificato rispetto al contratto di review. Cinque arresti vengono dai difetti
   TDL-01 e TDC-01, due da guasti dell'ambiente e cinque da completezza indeterminata.
6. **Il controfattuale non è una catena con intervento umano.** Sostituendo solo gli esiti
   fermati con i giudizi separati, c3a passerebbe aritmeticamente da 23 a 29/36 a L12,
   contro 31 di `bare`. Non è una misura di integrazione: le richieste successive partono
   senza quel lavoro e non sono ricostruibili con questa sostituzione.

## Raccomandazione operativa
Per questo regime e modello la regola di accettazione favorisce `bare`: nessun vantaggio
significativo di skills-only o Autopilot, con costo maggiore soprattutto per Autopilot.
Questo non rende inutili le skill per obiettivi non misurati qui (tracciabilità, consenso,
qualità documentale). Prima di giudicare un driver corretto o «solo Pi + Jev», risolvere
le decisioni di progetto e produrre un candidato nuovo: non dedurlo dai run storici.
Non avviare ulteriori benchmark senza autorità e budget nuovi.

## Limiti
- **Un solo modello forte, un solo thinking.** Opus 5.5 a `medium`; altri modelli o livelli non
  sono misurati qui. `dbh-sonnet` è annullato (VOID): dati e spesa restano conservati, ma
  quel lotto non è completato e non entra in confronti o conclusioni.
- **Oracolo e braccio della stessa famiglia.** Richieste, suite e trappole sono state scritte da
  un modello Claude. Con luna l'autore era di un'altra famiglia; qui il braccio è un modello
  Claude anche lui, e una vicinanza di stile fra chi scrive le richieste e chi le esegue non si
  può escludere.
- **Il soffitto riduce il potere della regola.** Con quasi tutte le richieste accettate le
  coppie discordanti sono poche, e nessun braccio può risultare «meglio».
- **Lotti diversi, a due giorni di distanza.** `dbh` è girato dal 28 al 29/09, `dbh-opus` dal 30/09
  al 01/10. Suite, seed e protocollo sono gli stessi. Le skill installate e la versione di Pi no:
  agent-skills `6a1f84d` e Pi 0.99.1 qui. In `dbh` Pi era 0.87.1 e il manifest iniziale
  era del 24/09, con deriva delle skill il 29/09 documentata in DBH-17. Quindi il confronto
  non attribuisce l'intera differenza al solo modello.
- **Driver diversi da quelli misurati con luna.** Le copie vengono da `ea96bea`, che contiene le
  correzioni del driver di DBH-16 e quelle successive. Non contengono TDL-01 e TDC-01, trovate in
  questo lotto.
- **Il piano Claude ha un limite d'uso.** Il 30/09 fra le 16:35 e le 17:02 UTC le richieste hanno
  ricevuto 429. Le attese di DBH-14 e DBH-15 le hanno coperte, ma 5 sessioni chiuse dopo
  l'output sono state giudicate come esito del braccio (vedi *Sensibilità* e *Guasti*).
- **I tempi dei driver dipendono dal tempo massimo della foglia.** 1800 s bastavano a luna; con
  Opus 6 run su 120 lo superano.

## Guasti dell'harness e del driver, e correzioni
- **Rifiuti del fornitore**: 6 tentativi di `bare` sulla prima richiesta di `lua-vm` sono stati
  bloccati prima di ogni output dal classificatore di Anthropic sui contenuti informatici
  (`stop_reason: refusal`). Sono guasti d'infrastruttura per
  [DBH-18](../tickets/delivery-bench-hard/done/18-bind-pi-extension.md): ogni catena è ripartita
  ed è stata accettata. Gli altri bracci, con prompt diversi, non li hanno avuti.
- **Limite d'uso del piano**: 12 tentativi hanno ricevuto 429 prima dell'output, e sono stati
  ripetuti dopo le attese.
- **Sessioni chiuse dopo l'output**: 5 richieste delle catene da 4, nelle ripetizioni 2 e 3, sono
  state chiuse dal fornitore (429 o sovraccarico) mentre il modello lavorava, e sono state
  giudicate sul lavoro a metà: 3 accettate comunque, 2 no. Corretto nel runner in
  [DBH-19](../tickets/delivery-bench-hard/done/19-provider-cut-after-work.md) (#402), prima della
  catena da 12. Le richieste giudicate non si rieseguono; la *Sensibilità* le toglie. Lo stesso
  difetto aveva toccato 2 richieste di `dbh`, e il report di DBH-09 riporta la correzione.
- **Revisore diretto non partito**: c3a passa a Pi il prompt del revisore diretto come argomento
  della riga di comando. Con molti hunk a rischio il prompt supera i 32 767 caratteri di Windows
  e il processo non parte: 4 run fermi. Corretto nel driver in
  [TDL-01](../tickets/ticket-driver-long-prompt/done/01-prompt-in-a-session-file.md) (#403): oltre
  il limite il prompt passa da un file della sessione.
- **Cache di pytest del revisore**: il revisore diretto ha lanciato pytest dalla sua cartella, e
  la cache è stata contata come una scrittura fuori dall'artefatto: 1 run fermo. Corretto in
  [TDC-01](../tickets/ticket-driver-reviewer-tool-caches/done/01-tool-caches-are-not-writes.md)
  (#404).
- **Timeout**: una richiesta di Autopilot su `crdt-yjs` è arrivata al tetto di 5400 s. Un suo
  ciclo di prove ripetute è durato 40 minuti, fino al tempo massimo del suo strumento. È un esito
  del braccio, non un guasto.
- **L'harness** è cambiato solo fra due `run-lot`. Le copie misurate del driver sono rimaste
  congelate; TDL-01 e TDC-01 nel sorgente valgono soltanto per futuri candidati.

## Seguiti possibili (non fatti)
- Portare il tempo massimo della foglia del driver vicino al tetto per richiesta, o renderlo
  proporzionale al modello: con Opus è il primo motivo per cui c1a perde richieste.
- Esplorare una sessione Pi di catena con Jev per rischio e domande, quando possibile.
  Il benchmark non misura questa configurazione. Restano decisioni HITL su fallback,
  review condivisa e ownership di worktree/test/integrazione: una review nella sessione
  builder non è indipendente. Un futuro confronto richiede candidato congelato,
  protocollo e nuove autorità e budget; nessuna nuova misura è avviata da questo report.
- Il driver potrebbe ripetere una volta un giudice morto all'avvio, prima di contarlo come
  indeterminato.
- Una futura misura con un modello intermedio potrebbe cercare un regime meno saturo.
  Non riprendere `dbh-sonnet` VOID né usare i suoi risultati parziali: servono un lotto
  nuovo, autorità e budget nuovi.
