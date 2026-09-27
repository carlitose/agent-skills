# delivery-bench — misura completa: catene da 1, 3 e 8

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-results`
- Role: `research`
- Parent: [DB-08 — Misura completa: catene da 3 e 8](../tickets/delivery-bench/done/08-full-measurement.md)

## Stato
Output di DB-08 (2026-09-26/27): la tabella braccio × lunghezza × scenario e la raccomandazione
operativa promesse dalla [mappa](../specs/delivery-bench-wayfinder.md). Lotto `db07-pilot`: le
45 celle del [pilota](delivery-bench-pilot.md) sono state **proseguite** fino alla richiesta 3,
e la ripetizione 1 fino all'8 (contratto §9). La regola di TBA-03 ha poi chiesto la ripetizione 2
della catena da 8 per `bare`, skills-only, Autopilot e c1a. Bracci su `openai-codex/gpt-6-sol`
con `--thinking high`. Record di cella, giudizi e ledger stanno nel repo privato dell'oracolo
(`results/db07-pilot/`, fuori da Git); qui ci sono solo aggregati, senza nomi di controlli,
trappole o difetti.

**Aggiornamento del 2026-09-27, TJV-02.** Le righe `driver-c3a` di questo report misurano il
driver prima delle correzioni TJV-01 e TJV-03. Il c3a corretto è stato rimisurato nel lotto
`c3a-observed` e confrontato con gli altri bracci in
[delivery-bench-c3a-corrected.md](delivery-bench-c3a-corrected.md): 9/9, 25/27 e 45/48,
indistinguibile da `bare` a ogni lunghezza, fermo al cancello in 2 run su 57. La lettura 9 e la
voce su c3a in *Da non usare* valgono solo per il driver originale.

## Autorizzazione e provenienza
- **Autorizzazione**: l'obiettivo di sessione dell'utente («esegui tutti i ticket per creare il
  benchmark e poi esegui tutti i bracci sul benchmark», senza fermarsi a chiedere conferma).
  Non c'è stato un nuovo messaggio esplicito dopo il pilota, né una revisione interattiva fra
  pilota e misura: la richiesta di DB-08 («nuova autorizzazione esplicita») è coperta da quella
  frase, e lo si dichiara. L'autorità del lotto (sha256 `058edf26…`) copre già lunghezza 8, 3
  ripetizioni e spesa Jev. Il verbale di DB-08 (`results/db08-authorization.json`) la cita per
  hash, con il tetto di tempo del contratto: 60 minuti per richiesta, 60 × L per catena,
  applicato dal runner.
- **Harness congelato** in un worktree dedicato, spostato solo fra due `run-lot`: pilota a
  `58a6bd3`, catene da 3 a `4e7c684` (PR #366), catene da 8 e ripetizioni extra a `b36f926`
  (PR #367). Il report e le correzioni di lettura sono in questa PR.
- **Suite nascoste** (sha256): `python-billing` `6ba6b3c0…`, `c-recq` `d87c157f…`,
  `ts-reservas` `42cdfc89…` → `1f8809bd…`. L'emendamento è a verbale nel lotto e nel ledger;
  vedi *Guasti dell'harness e correzioni*.
- **Esecuzione**: catene da 3, dalle 17:50 alle 20:06 UTC; catena da 8 r1, dalle 20:08 alle
  22:35; ripetizioni extra, dalle 22:54 alle 01:19. Sempre 4 celle in parallelo, sulla macchina e
  col provider dei lotti Terminal-Bench (tempi rumorosi). DB-08 ha fatto 225 tentativi, tutti
  del braccio (nessun guasto d'infrastruttura), per 119,10 $ stimati da Pi. Col pilota, il lotto
  fa 270 richieste giudicate, 134,63 $ e 0,0136 $ di Jev (105 chiamate). Nessun timeout: la
  richiesta più lunga è durata 853 s.

## Come si legge
- **Accettazione**: richieste accettate (tutte le feature della richiesta passano). Regola di
  TBA-03 appaiata con `bare`: McNemar esatto, Holm, differenza minima 3, pareggi al braccio più
  semplice. Legge un solo asse.
- **Robustezza e bussola sul repository finale** di ogni catena, perché sono cumulative.
  *Invarianti rotte* sono regressioni: il controllo era passato prima nella catena. `nd` conta
  le invarianti fallite di feature mai consegnate, che pesano già sull'accettazione. *Trappole
  violate/misurabili*: una trappola è misurabile solo finché la feature della sua richiesta di
  tentazione è in piedi; `nm` conta le altre. Il giudice è senza stato, quindi questa lettura
  lungo la catena è una correzione del report emersa in DB-08 (contratto §5).
- **Costo e tempo** sommati sulla catena: USD stimati da Pi (provider in abbonamento, non una
  fattura), Jev a parte, mediana del tempo per catena.
- **c3a**: quando il cancello semantico resta incerto, il run si ferma (`gated`) e aspetta un
  umano, che in un lotto AFK non si fabbrica. Il candidato fermo si giudica a parte
  (controfattuale) e non conta mai come accettazione.

## Risultati

### Catene da 1 (3 ripetizioni, 9 catene per braccio)
| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 9/9 | 37/39 | 0/36 | — | — | 0.74 | — | 128 | 0 | 0 (0.00) |
| skills-only | 9 | 9/9 | 36/39 | 0/36 | — | — | 1.60 | — | 169 | 0 | 0 (0.00) |
| autopilot | 9 | 9/9 | 36/39 | 0/36 | — | — | 8.26 | — | 617 | 0 | 0 (0.00) |
| driver-c1a | 9 | 9/9 | 36/39 | 0/36 | — | — | 1.92 | — | 193 | 0 | 0 (0.00) |
| driver-c3a | 9 | 2/9 | 13/39 | 0/36 | — | — | 3.01 | 0.0026 | 355 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| autopilot | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 9 | 2 | 9 | 0 | 7 | -7 | 0.01562 | 0.0625 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Catene da 3 (3 ripetizioni, 9 catene per braccio)
Robustness and compass are read on the final repository of each chain (they are cumulative); acceptance counts accepted requests; cost and time are summed over the chain.

| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 1.28 | — | 440 | 0 | 0 (0.00) |
| c-recq | skills-only | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 1.92 | — | 460 | 0 | 0 (0.00) |
| c-recq | autopilot | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 8.47 | — | 1628 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 2.64 | — | 736 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 3 | 0/9 | 3/24 | 0/39 (+27 nd) | — (+6 nm) | — | 3.36 | 0.0022 | 1186 | 0 | 0 (0.00) |
| python-billing | bare | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 0.71 | — | 267 | 0 | 0 (0.00) |
| python-billing | skills-only | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 1.27 | — | 333 | 0 | 0 (0.00) |
| python-billing | autopilot | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 7.55 | — | 1384 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 1.96 | — | 550 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 3 | 7/9 | 22/27 | 0/51 (+7 nd) | 0/4 (+2 nm) | — | 2.48 | 0.0039 | 898 | 0 | 0 (0.00) |
| ts-reservas | bare | 3 | 8/9 | 12/18 | 15/51 | 0/4 (+2 nm) | — | 1.59 | — | 667 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 3 | 9/9 | 18/18 | 1/51 | 0/6 | — | 4.79 | — | 1316 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 3 | 8/9 | 13/18 | 9/51 | 0/4 (+2 nm) | — | 12.31 | — | 1961 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 3 | 7/9 | 16/18 | 0/51 | 0/2 (+4 nm) | — | 3.30 | — | 1167 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 3 | 0/9 | 0/18 | 0/51 (+42 nd) | — (+6 nm) | — | 3.40 | 0.0027 | 1240 | 0 | 0 (0.00) |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 26/27 | 63/69 | 15/141 | 0/16 (+2 nm) | — | 3.58 | — | 440 | 0 | 0 (0.00) |
| skills-only | 9 | 27/27 | 69/69 | 1/141 | 0/18 | — | 7.98 | — | 460 | 0 | 0 (0.00) |
| autopilot | 9 | 26/27 | 64/69 | 9/141 | 0/16 (+2 nm) | — | 28.33 | — | 1628 | 0 | 0 (0.00) |
| driver-c1a | 9 | 25/27 | 67/69 | 0/141 | 0/14 (+4 nm) | — | 7.90 | — | 736 | 0 | 0 (0.00) |
| driver-c3a | 9 | 7/27 | 25/69 | 0/141 (+76 nd) | 0/4 (+14 nm) | — | 9.24 | 0.0088 | 1097 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 27 | 27 | 26 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| autopilot | 27 | 26 | 26 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 27 | 25 | 26 | 0 | 1 | -1 | 1 | 1 | indistinguishable |
| driver-c3a | 27 | 7 | 26 | 0 | 19 | -19 | 3.815e-06 | 1.526e-05 | worse |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Catene da 8 (ripetizione 1, più la 2 dove la regola di TBA-03 l'ha chiesta)
Dopo la r1 la regola chiedeva una ripetizione per skills-only e Autopilot (pari con `bare` a
24/24); dopo la r2 la chiedeva per c1a, che `bare` non superava più. Con la r2 di c1a la regola è
decisa. c3a, peggiore già alla r1, ha una ripetizione.

Robustness and compass are read on the final repository of each chain (they are cumulative); acceptance counts accepted requests; cost and time are summed over the chain.

| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 3.73 | — | 1367 | 0 | 0 (0.00) |
| c-recq | skills-only | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 5.23 | — | 1704 | 0 | 0 (0.00) |
| c-recq | autopilot | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 18.62 | — | 4183 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 2 | 16/16 | 31/32 | 0/76 | 0/18 | — | 4.94 | — | 2075 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 1 | 0/8 | 1/16 | 0/38 (+33 nd) | — (+9 nm) | — | 2.78 | 0.0019 | 2879 | 0 | 0 (0.00) |
| python-billing | bare | 2 | 16/16 | 34/36 | 0/74 | 0/18 | — | 2.40 | — | 906 | 0 | 0 (0.00) |
| python-billing | skills-only | 2 | 16/16 | 34/36 | 0/74 | 0/18 | — | 3.39 | — | 1185 | 0 | 0 (0.00) |
| python-billing | autopilot | 2 | 16/16 | 35/36 | 0/74 | 0/18 | — | 15.04 | — | 3573 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 2 | 16/16 | 35/36 | 0/74 | 0/18 | — | 4.26 | — | 1808 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 1 | 6/8 | 15/18 | 0/37 (+2 nd) | 0/4 (+5 nm) | — | 2.67 | 0.0036 | 2478 | 0 | 0 (0.00) |
| ts-reservas | bare | 2 | 10/16 | 12/24 | 15/70 (+15 nd) | 0/12 (+12 nm) | — | 4.34 | — | 1590 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 2 | 16/16 | 22/24 | 0/70 | 0/24 | — | 13.96 | — | 3635 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 2 | 11/16 | 15/24 | 9/70 (+8 nd) | 1/14 (+10 nm) | d6×1 | 23.26 | — | 5113 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 2 | 12/16 | 20/24 | 1/70 (+3 nd) | 0/12 (+12 nm) | — | 5.82 | — | 2784 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 1 | 0/8 | 0/12 | 0/35 (+32 nd) | — (+12 nm) | — | 2.80 | 0.0022 | 3204 | 0 | 0 (0.00) |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 6 | 42/48 | 78/92 | 15/220 (+15 nd) | 0/48 (+12 nm) | — | 10.48 | — | 1367 | 0 | 0 (0.00) |
| skills-only | 6 | 48/48 | 88/92 | 0/220 | 0/60 | — | 22.58 | — | 1704 | 0 | 0 (0.00) |
| autopilot | 6 | 43/48 | 82/92 | 9/220 (+8 nd) | 1/50 (+10 nm) | d6×1 | 56.92 | — | 4183 | 0 | 0 (0.00) |
| driver-c1a | 6 | 44/48 | 86/92 | 1/220 (+3 nd) | 0/48 (+12 nm) | — | 15.03 | — | 2075 | 0 | 0 (0.00) |
| driver-c3a | 3 | 6/24 | 16/46 | 0/110 (+67 nd) | 0/4 (+26 nm) | — | 8.25 | 0.0077 | 2879 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: convention×1; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 48 | 48 | 42 | 6 | 0 | +6 | 0.03125 | 0.09375 | indistinguishable |
| autopilot | 48 | 43 | 42 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| driver-c1a | 48 | 44 | 42 | 3 | 1 | +2 | 0.625 | 1 | indistinguishable |
| driver-c3a | 24 | 6 | 24 | 0 | 18 | -18 | 7.629e-06 | 3.052e-05 | worse |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Esiti del driver c3a
| Scenario | Catene da 3: run | Candidati fermi accettabili | Catena da 8 (r1): run | Candidati fermi accettabili |
|---|---|---:|---|---:|
| c-recq | `gated`×9 | 3/9 | `gated`×8 | 3/8 |
| python-billing | `integrated`×8, `gated`×1 | 1/1 | `integrated`×6, `gated`×2 | 2/2 |
| ts-reservas | `gated`×9 | 3/9 | `gated`×8 | 3/8 |

Alla prima richiesta, i candidati fermi erano tutti accettabili (7/7 nel pilota). Dopo il primo cancello,
il candidato parte da un `main` senza il lavoro precedente, quindi il controfattuale non dice più
molto.

## Letture

1. **Su C e Python il braccio non conta.** In `c-recq` e `python-billing`, `bare`, skills-only,
   Autopilot e c1a accettano tutte le richieste a ogni lunghezza (16/16 per scenario alla catena
   da 8), trovano quasi gli stessi latenti (31-32 su 32 in C, 34-35 su 36 in Python) e non rompono
   niente. Il costo in più
   degli altri bracci qui non compra nulla.
2. **Le differenze vengono tutte dal frontend (`ts-reservas`), e da un evento preciso.** Su 3
   catene per braccio, una catena di `bare` e una di Autopilot rompono l'app alla richiesta 3
   (15 e 9 regressioni) e non la riparano più nelle cinque richieste successive. La sessione
   esce sempre con successo. È il «tenere la rotta» che la mappa voleva vedere. skills-only non
   perde una richiesta in nessuna catena (16/16 alla catena da 8, 0 regressioni); c1a è in mezzo
   (12/16, una regressione). Le catene rotte sono state rigiudicate con esito identico, e i dettagli del giudice
   mostrano una rottura reale, non un artefatto dell'oracolo.
3. **L'accettazione, da sola, non separa nessuno dei quattro.** Alla catena da 8 skills-only
   fa 48/48 contro 42/48 di `bare` (+6, McNemar p = 0,031, Holm 0,094). La regola di TBA-03
   vuole Holm < 0,05, quindi è «indistinguibile», e le sei richieste perse da `bare` stanno
   tutte nella stessa catena. c1a +2 e Autopilot +1 sono rumore; c3a è peggiore (6/24,
   Holm 3·10⁻⁵).
4. **Robustezza e bussola vanno nella stessa direzione dell'evento del punto 2**: alla catena da
   8 skills-only trova 88/92 latenti, c1a 86, Autopilot 82, `bare` 78. Regressioni: 0, 1, 9, 15.
5. **Le trappole di memoria quasi non scattano.** Su tutte le trappole misurabili alla catena da
   8 c'è una sola violazione, di Autopilot: una convenzione a distanza 6. Con questo modello le
   regole piantate alle richieste 2-3 reggono fino all'8 in tutti i bracci. Il catalogo, a questa
   forza di modello, discrimina poco.
6. **La perdita di contesto è stata messa alla prova poco.** Alla catena da 8 la sessione di
   `bare` non è mai arrivata alla compaction (0 catene su 6), skills-only solo sul frontend
   (2 su 6), Autopilot una volta in ogni catena (6 su 6). A questa scala una catena da 8 entra
   nel contesto, e la memoria lunga resta quasi da misurare.
7. **Costo e tempo per catena da 8** (mediana del tempo): `bare` 1,75 $ e 23 min; c1a 2,51 $ e
   35 min; c3a 2,75 $ e 48 min; skills-only 3,76 $ e 28 min; Autopilot 9,49 $ e 70 min.
8. **L'osservazione dell'utente su Autopilot non è confermata.** Sui task piccoli Autopilot non
   è peggiore, è solo caro: alla catena da 1 accetta 9/9 come gli altri, a 11× il costo di
   `bare` e 5× il tempo. Sui task lunghi non tiene la rotta meglio di skills-only: 43/48 contro
   48/48, 9 regressioni contro 0, l'unica trappola violata, a 2,5× il costo e 2,5× il tempo.
9. **c3a non è un braccio AFK.** Il cancello semantico si ferma sull'incertezza e aspetta un
   umano. Così consegna 7/27 richieste alla catena da 3 e 6/24 alla catena da 8 (0/8 in C e nel
   frontend). Misurarlo con un umano al cancello è un'altra misura.

## Raccomandazione operativa
Per `openai-codex/gpt-6-sol` con `--thinking high` e task come questi (repo piccoli, richieste
di funzionalità in sequenza):

| Task | Usa | Perché | Cosa costa sceglierlo |
|---|---|---|---|
| 1 richiesta | **Pi nudo** | nessun braccio fa meglio su alcun asse | — |
| 3 richieste, backend (C, Python) | **Pi nudo** | tutti perfetti su ogni asse | — |
| 3 richieste, frontend | **skills-only** se una regressione costa più di tre volte i token, altrimenti Pi nudo | 9/9 contro 8/9; nessuna app rotta contro una catena rotta su 3 | 3× USD, 2× tempo |
| 8 richieste | **skills-only** | 48/48, 0 regressioni, più latenti; l'unico senza richieste perse | 2,2× USD, +25% tempo; l'accettazione da sola non lo distingue (Holm 0,094) |
| 8 richieste, solo backend | **Pi nudo** | stessi risultati di skills-only in C e Python | — |

Da non usare per task di queste dimensioni:
- **Autopilot**: non è davanti su nessun asse e costa 5,4× `bare` e 2,5× skills-only.
- **c3a originale in AFK**: si ferma in attesa di un umano. Il c3a corretto non è più escluso
  (vedi [c3a corretto](delivery-bench-c3a-corrected.md#raccomandazione-operativa-aggiornata)).

c1a costa meno di skills-only (1,4× `bare`), ma perde più richieste sul frontend.

## Limiti
- Un modello, un autore dell'oracolo (Claude Fable, famiglia diversa dai bracci), tre scenari
  con repo piccoli. La raccomandazione vale per questo, non per task di giorni.
- La catena da 8 ha 2 ripetizioni (1 per c3a). Il vantaggio di skills-only sul frontend
  poggia su una catena rotta di `bare` e una di Autopilot su 3: un evento raro visto una volta,
  non una frequenza.
- Le trappole non hanno discriminato e la compaction è scattata di rado: i due assi che la mappa
  voleva più vedere (memoria lunga, bussola) sono misurati in un regime in cui quasi non si
  sforzano.
- Tempi rumorosi (macchina e provider condivisi); USD stimati. Fra una richiesta e l'altra
  passano minuti o ore (il lotto prosegue celle esistenti), quindi la cache del provider può
  scadere: pesa sul costo, non sull'esito.
- Sulle catene frontend rotte, robustezza e bussola si leggono male: i latenti non si
  trovano e le trappole non sono misurabili perché l'app non si apre.
- Revisione umana: nessuna fra pilota e misura (vedi *Autorizzazione*).

## Guasti dell'harness e correzioni
- **Bussola letta richiesta per richiesta.** Il giudice, senza stato, contava come «invarianti
  rotte» le feature mai consegnate e come «trappole violate» quelle impossibili da misurare
  (c3a risultava con 6/6 trappole violate in C senza aver integrato niente). Corretto con la
  lettura lungo la catena in `profile_report.py` (contratto §5): i record non cambiano.
- **Difetto di una suite nascosta** (`ts-reservas`): un confronto dipendeva da un dettaglio che
  nessuna richiesta fissa, e consegne equivalenti fallivano. Otto
  giudizi erano falsi positivi, una regressione ciascuno, su due catene. La correzione:
  - suite corretta nel repo privato, fra due `run-lot`, e riverificata: riferimento, stub e
    trappole × 8 richieste, tutti come atteso;
  - rilegata al lotto con `runner.py amend-suite` (digest vecchio e nuovo, ragione, ora);
  - gli otto giudizi riclassificati esattamente, perché il confronto fallito era l'ultima
    asserzione del controllo; originali conservati;
  - tutti i 30 alberi `ts-reservas` ancora esistenti (progetto finale e istantanea prima
    dell'ultima richiesta di 15 celle) rigiudicati con la suite corretta: 30/30 identici al
    record, quindi nessun altro giudizio dipendeva dal difetto.
  Nessuna accettazione è cambiata. La procedura è nel contratto (§9).
- **Report e runner**: righe per catena, esclusione delle catene ancora in corso, regola di
  TBA-03 sui tassi (le ripetizioni extra coprono solo alcuni bracci), `run-lot --arm`
  (PR #367 e questa PR).
- Durante i 225 tentativi di DB-08: nessun guasto d'infrastruttura, errore del giudice, timeout,
  tetto di catena o riscontro dell'audit.

## Appendice: profilo per richiesta, catena da 8
Invariants broken are regressions (the check passed earlier in the chain); `nd` counts failed invariants whose feature was never delivered. Traps are violated/measurable: a trap is measurable while the feature of its tempting request is in place; `nm` counts the others.

| Scenario | Arm | Request | Accepted | Features | Latent found | Invariants broken | Traps violated | Distances | Tokens in / out / cache read | USD (Pi) | USD (Jev) | Median s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 1 | 2/2 | 8/8 | 10/10 | 0/8 | — | — | 46k / 10k / 129k | 0.22 | — | 132 | 0 | 0 (0.00) |
| c-recq | bare | 2 | 2/2 | 10/10 | 12/12 | 0/16 | — | — | 49k / 12k / 406k | 0.30 | — | 163 | 0 | 0 (0.00) |
| c-recq | bare | 3 | 2/2 | 12/12 | 16/16 | 0/26 | 0/4 | — | 41k / 12k / 676k | 0.34 | — | 157 | 0 | 0 (0.00) |
| c-recq | bare | 4 | 2/2 | 10/10 | 18/18 | 0/38 | 0/4 | — | 97k / 15k / 1106k | 0.56 | — | 170 | 0 | 0 (0.00) |
| c-recq | bare | 5 | 2/2 | 6/6 | 22/22 | 0/48 | 0/6 | — | 20k / 12k / 976k | 0.35 | — | 134 | 0 | 0 (0.00) |
| c-recq | bare | 6 | 2/2 | 14/14 | 26/26 | 0/54 | 0/10 | — | 55k / 28k / 2779k | 0.95 | — | 328 | 0 | 0 (0.00) |
| c-recq | bare | 7 | 2/2 | 8/8 | 28/28 | 0/68 | 0/14 | — | 35k / 8k / 1245k | 0.40 | — | 100 | 0 | 0 (0.00) |
| c-recq | bare | 8 | 2/2 | 6/6 | 32/32 | 0/76 | 0/18 | — | 26k / 15k / 2082k | 0.62 | — | 183 | 0 | 0 (0.00) |
| c-recq | skills-only | 1 | 2/2 | 8/8 | 10/10 | 0/8 | — | — | 54k / 12k / 495k | 0.33 | — | 163 | 0 | 0 (0.00) |
| c-recq | skills-only | 2 | 2/2 | 10/10 | 12/12 | 0/16 | — | — | 41k / 16k / 1236k | 0.49 | — | 228 | 0 | 0 (0.00) |
| c-recq | skills-only | 3 | 2/2 | 12/12 | 16/16 | 0/26 | 0/4 | — | 33k / 15k / 1490k | 0.51 | — | 189 | 0 | 0 (0.00) |
| c-recq | skills-only | 4 | 2/2 | 10/10 | 18/18 | 0/38 | 0/4 | — | 95k / 17k / 1917k | 0.74 | — | 206 | 0 | 0 (0.00) |
| c-recq | skills-only | 5 | 2/2 | 6/6 | 22/22 | 0/48 | 0/6 | — | 25k / 12k / 1658k | 0.51 | — | 148 | 0 | 0 (0.00) |
| c-recq | skills-only | 6 | 2/2 | 14/14 | 26/26 | 0/54 | 0/10 | — | 58k / 34k / 3864k | 1.23 | — | 398 | 0 | 0 (0.00) |
| c-recq | skills-only | 7 | 2/2 | 8/8 | 28/28 | 0/68 | 0/14 | — | 40k / 10k / 1762k | 0.53 | — | 139 | 0 | 0 (0.00) |
| c-recq | skills-only | 8 | 2/2 | 6/6 | 32/32 | 0/76 | 0/18 | — | 31k / 17k / 3322k | 0.90 | — | 234 | 0 | 0 (0.00) |
| c-recq | autopilot | 1 | 2/2 | 8/8 | 10/10 | 0/8 | — | — | 167k / 28k / 6730k | 1.96 | — | 644 | 0 | 0 (0.00) |
| c-recq | autopilot | 2 | 2/2 | 10/10 | 12/12 | 0/16 | — | — | 62k / 25k / 6307k | 1.63 | — | 529 | 0 | 0 (0.00) |
| c-recq | autopilot | 3 | 2/2 | 12/12 | 16/16 | 0/26 | 0/4 | — | 71k / 27k / 9628k | 2.34 | — | 507 | 0 | 0 (0.00) |
| c-recq | autopilot | 4 | 2/2 | 10/10 | 18/18 | 0/38 | 0/4 | — | 499k / 36k / 14445k | 4.24 | — | 568 | 0 | 0 (0.00) |
| c-recq | autopilot | 5 | 2/2 | 6/6 | 22/22 | 0/48 | 0/6 | — | 52k / 22k / 11689k | 2.66 | — | 424 | 0 | 0 (0.00) |
| c-recq | autopilot | 6 | 2/2 | 14/14 | 26/26 | 0/54 | 0/10 | — | 237k / 45k / 8470k | 2.62 | — | 683 | 0 | 0 (0.00) |
| c-recq | autopilot | 7 | 2/2 | 8/8 | 28/28 | 0/68 | 0/14 | — | 55k / 23k / 5234k | 1.39 | — | 372 | 0 | 0 (0.00) |
| c-recq | autopilot | 8 | 2/2 | 6/6 | 32/32 | 0/76 | 0/18 | — | 61k / 32k / 6676k | 1.78 | — | 454 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 1 | 2/2 | 8/8 | 10/10 | 0/8 | — | — | 68k / 15k / 783k | 0.44 | — | 247 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 2 | 2/2 | 10/10 | 12/12 | 0/16 | — | — | 96k / 18k / 1151k | 0.61 | — | 255 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 3 | 2/2 | 12/12 | 16/16 | 0/26 | 0/4 | — | 115k / 19k / 1535k | 0.73 | — | 314 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 4 | 2/2 | 10/10 | 17/18 | 0/38 | 0/4 | — | 98k / 22k / 1950k | 0.81 | — | 306 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 5 | 2/2 | 6/6 | 21/22 | 0/48 | 0/6 | — | 61k / 13k / 849k | 0.43 | — | 178 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 6 | 2/2 | 14/14 | 25/26 | 0/54 | 0/10 | — | 90k / 23k / 1560k | 0.72 | — | 281 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 7 | 2/2 | 8/8 | 27/28 | 0/68 | 0/14 | — | 78k / 17k / 1167k | 0.56 | — | 246 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 8 | 2/2 | 6/6 | 31/32 | 0/76 | 0/18 | — | 85k / 19k / 1444k | 0.65 | — | 248 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 1 | 0/1 | 0/4 | 1/5 | 0/4 | — | — | 66k / 11k / 689k | 0.38 | 0.0003 | 361 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 2 | 0/1 | 0/5 | 1/6 | 0/8 (+4 nd) | — | — | 63k / 11k / 531k | 0.34 | 0.0002 | 414 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 3 | 0/1 | 1/6 | 1/8 | 0/13 (+9 nd) | — (+2 nm) | — | 77k / 13k / 684k | 0.42 | 0.0002 | 436 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 4 | 0/1 | 0/5 | 1/9 | 0/19 (+14 nd) | — (+2 nm) | — | 45k / 9k / 624k | 0.31 | 0.0002 | 337 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 5 | 0/1 | 0/3 | 1/11 | 0/24 (+19 nd) | — (+3 nm) | — | 52k / 7k / 296k | 0.24 | 0.0002 | 258 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 6 | 0/1 | 0/7 | 1/13 | 0/27 (+22 nd) | — (+5 nm) | — | 64k / 17k / 809k | 0.46 | 0.0003 | 473 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 7 | 0/1 | 0/4 | 1/14 | 0/34 (+29 nd) | — (+7 nm) | — | 66k / 8k / 421k | 0.29 | 0.0002 | 258 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 8 | 0/1 | 0/3 | 1/16 | 0/38 (+33 nd) | — (+9 nm) | — | 74k / 11k / 495k | 0.35 | 0.0003 | 342 | 0 | 0 (0.00) |
| python-billing | bare | 1 | 2/2 | 16/16 | 10/10 | 0/10 | — | — | 34k / 6k / 80k | 0.14 | — | 89 | 0 | 0 (0.00) |
| python-billing | bare | 2 | 2/2 | 8/8 | 16/16 | 0/26 | — | — | 50k / 8k / 298k | 0.23 | — | 117 | 0 | 0 (0.00) |
| python-billing | bare | 3 | 2/2 | 6/6 | 18/18 | 0/34 | 0/4 | — | 16k / 5k / 314k | 0.14 | — | 63 | 0 | 0 (0.00) |
| python-billing | bare | 4 | 2/2 | 10/10 | 24/24 | 0/40 | 0/6 | — | 61k / 7k / 492k | 0.30 | — | 97 | 0 | 0 (0.00) |
| python-billing | bare | 5 | 2/2 | 10/10 | 28/28 | 0/50 | 0/6 | — | 51k / 12k / 817k | 0.39 | — | 140 | 0 | 0 (0.00) |
| python-billing | bare | 6 | 2/2 | 10/10 | 30/30 | 0/60 | 0/8 | — | 37k / 7k / 772k | 0.30 | — | 88 | 0 | 0 (0.00) |
| python-billing | bare | 7 | 2/2 | 4/4 | 32/34 | 0/70 | 0/14 | — | 28k / 11k / 1034k | 0.37 | — | 135 | 0 | 0 (0.00) |
| python-billing | bare | 8 | 2/2 | 10/10 | 34/36 | 0/74 | 0/18 | — | 39k / 16k / 1489k | 0.53 | — | 177 | 0 | 0 (0.00) |
| python-billing | skills-only | 1 | 2/2 | 16/16 | 10/10 | 0/10 | — | — | 35k / 7k / 266k | 0.19 | — | 103 | 0 | 0 (0.00) |
| python-billing | skills-only | 2 | 2/2 | 8/8 | 16/16 | 0/26 | — | — | 72k / 8k / 592k | 0.35 | — | 151 | 0 | 0 (0.00) |
| python-billing | skills-only | 3 | 2/2 | 6/6 | 18/18 | 0/34 | 0/4 | — | 28k / 5k / 504k | 0.21 | — | 77 | 0 | 0 (0.00) |
| python-billing | skills-only | 4 | 2/2 | 10/10 | 24/24 | 0/40 | 0/6 | — | 80k / 8k / 927k | 0.43 | — | 122 | 0 | 0 (0.00) |
| python-billing | skills-only | 5 | 2/2 | 10/10 | 28/28 | 0/50 | 0/6 | — | 82k / 16k / 1749k | 0.67 | — | 270 | 0 | 0 (0.00) |
| python-billing | skills-only | 6 | 2/2 | 10/10 | 30/30 | 0/60 | 0/8 | — | 25k / 10k / 1540k | 0.45 | — | 130 | 0 | 0 (0.00) |
| python-billing | skills-only | 7 | 2/2 | 4/4 | 32/34 | 0/70 | 0/14 | — | 19k / 10k / 1130k | 0.36 | — | 122 | 0 | 0 (0.00) |
| python-billing | skills-only | 8 | 2/2 | 10/10 | 34/36 | 0/74 | 0/18 | — | 33k / 18k / 2405k | 0.72 | — | 210 | 0 | 0 (0.00) |
| python-billing | autopilot | 1 | 2/2 | 16/16 | 10/10 | 0/10 | — | — | 153k / 25k / 5285k | 1.61 | — | 705 | 0 | 0 (0.00) |
| python-billing | autopilot | 2 | 2/2 | 8/8 | 16/16 | 0/26 | — | — | 66k / 20k / 5765k | 1.49 | — | 406 | 0 | 0 (0.00) |
| python-billing | autopilot | 3 | 2/2 | 6/6 | 18/18 | 0/34 | 0/4 | — | 66k / 18k / 6811k | 1.67 | — | 332 | 0 | 0 (0.00) |
| python-billing | autopilot | 4 | 2/2 | 10/10 | 24/24 | 0/40 | 0/6 | — | 326k / 23k / 8921k | 2.66 | — | 420 | 0 | 0 (0.00) |
| python-billing | autopilot | 5 | 2/2 | 10/10 | 28/28 | 0/50 | 0/6 | — | 117k / 29k / 11119k | 2.75 | — | 495 | 0 | 0 (0.00) |
| python-billing | autopilot | 6 | 2/2 | 10/10 | 30/30 | 0/60 | 0/8 | — | 171k / 24k / 6637k | 1.91 | — | 442 | 0 | 0 (0.00) |
| python-billing | autopilot | 7 | 2/2 | 4/4 | 33/34 | 0/70 | 0/14 | — | 57k / 20k / 4476k | 1.21 | — | 351 | 0 | 0 (0.00) |
| python-billing | autopilot | 8 | 2/2 | 10/10 | 35/36 | 0/74 | 0/18 | — | 70k / 28k / 6556k | 1.73 | — | 422 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 1 | 2/2 | 16/16 | 10/10 | 0/10 | — | — | 60k / 15k / 929k | 0.45 | — | 214 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 2 | 2/2 | 8/8 | 16/16 | 0/26 | — | — | 79k / 15k / 1130k | 0.54 | — | 235 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 3 | 2/2 | 6/6 | 18/18 | 0/34 | 0/4 | — | 82k / 11k / 633k | 0.40 | — | 150 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 4 | 2/2 | 10/10 | 24/24 | 0/40 | 0/6 | — | 88k / 14k / 1000k | 0.52 | — | 207 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 5 | 2/2 | 10/10 | 28/28 | 0/50 | 0/6 | — | 73k / 17k / 1276k | 0.57 | — | 297 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 6 | 2/2 | 10/10 | 30/30 | 0/60 | 0/8 | — | 76k / 12k / 930k | 0.46 | — | 234 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 7 | 2/2 | 4/4 | 33/34 | 0/70 | 0/14 | — | 129k / 15k / 1003k | 0.61 | — | 211 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 8 | 2/2 | 10/10 | 35/36 | 0/74 | 0/18 | — | 91k / 21k / 1653k | 0.72 | — | 260 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 1 | 1/1 | 8/8 | 5/5 | 0/5 | — | — | 43k / 9k / 434k | 0.26 | 0.0005 | 291 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 2 | 1/1 | 4/4 | 8/8 | 0/13 | — | — | 53k / 10k / 628k | 0.33 | 0.0004 | 352 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 3 | 1/1 | 3/3 | 9/9 | 0/17 | 0/2 | — | 46k / 8k / 543k | 0.28 | 0.0004 | 255 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 4 | 1/1 | 5/5 | 12/12 | 0/20 | 0/3 | — | 72k / 8k / 608k | 0.35 | 0.0006 | 239 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 5 | 1/1 | 5/5 | 14/14 | 0/25 | 0/3 | — | 95k / 13k / 628k | 0.44 | 0.0007 | 355 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 6 | 1/1 | 5/5 | 15/15 | 0/30 | 0/4 | — | 72k / 9k / 579k | 0.35 | 0.0005 | 432 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 7 | 0/1 | 0/2 | 15/17 | 0/35 | 0/4 (+3 nm) | — | 43k / 8k / 390k | 0.24 | 0.0002 | 211 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 8 | 0/1 | 0/5 | 15/18 | 0/37 (+2 nd) | 0/4 (+5 nm) | — | 62k / 14k / 782k | 0.42 | 0.0003 | 342 | 0 | 0 (0.00) |
| ts-reservas | bare | 1 | 2/2 | 10/10 | 5/6 | 0/6 | — | — | 23k / 8k / 114k | 0.15 | — | 143 | 0 | 0 (0.00) |
| ts-reservas | bare | 2 | 2/2 | 18/18 | 9/10 | 0/16 | — | — | 41k / 16k / 661k | 0.37 | — | 220 | 0 | 0 (0.00) |
| ts-reservas | bare | 3 | 1/2 | 7/12 | 6/12 | 15/34 | 0/2 (+2 nm) | — | 38k / 20k / 1430k | 0.56 | — | 290 | 0 | 0 (0.00) |
| ts-reservas | bare | 4 | 1/2 | 5/6 | 8/14 | 15/46 (+5 nd) | 0/2 (+2 nm) | — | 104k / 10k / 1245k | 0.56 | — | 143 | 0 | 0 (0.00) |
| ts-reservas | bare | 5 | 1/2 | 3/6 | 9/16 | 15/52 (+6 nd) | 0/5 (+5 nm) | — | 29k / 13k / 1532k | 0.50 | — | 171 | 0 | 0 (0.00) |
| ts-reservas | bare | 6 | 1/2 | 3/6 | 10/18 | 15/58 (+9 nd) | 0/6 (+6 nm) | — | 29k / 15k / 2320k | 0.67 | — | 207 | 0 | 0 (0.00) |
| ts-reservas | bare | 7 | 1/2 | 3/6 | 10/20 | 15/64 (+12 nd) | 0/8 (+8 nm) | — | 37k / 17k / 2692k | 0.78 | — | 204 | 0 | 0 (0.00) |
| ts-reservas | bare | 8 | 1/2 | 5/8 | 12/24 | 15/70 (+15 nd) | 0/12 (+12 nm) | — | 28k / 17k / 2632k | 0.75 | — | 212 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 1 | 2/2 | 10/10 | 4/6 | 0/6 | — | — | 77k / 20k / 1434k | 0.64 | — | 380 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 2 | 2/2 | 18/18 | 8/10 | 0/16 | — | — | 102k / 35k / 3570k | 1.27 | — | 521 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 3 | 2/2 | 12/12 | 12/12 | 0/34 | 0/4 | — | 75k / 38k / 6742k | 1.88 | — | 603 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 4 | 2/2 | 6/6 | 14/14 | 0/46 | 0/4 | — | 256k / 26k / 6762k | 2.12 | — | 373 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 5 | 2/2 | 6/6 | 16/16 | 0/52 | 0/10 | — | 53k / 23k / 6868k | 1.71 | — | 335 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 6 | 2/2 | 6/6 | 18/18 | 0/58 | 0/12 | — | 70k / 38k / 12771k | 3.07 | — | 629 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 7 | 2/2 | 6/6 | 19/20 | 0/64 | 0/16 | — | 112k / 28k / 8416k | 2.19 | — | 393 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 8 | 2/2 | 8/8 | 22/24 | 0/70 | 0/24 | — | 90k / 30k / 2997k | 1.08 | — | 403 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 1 | 2/2 | 10/10 | 4/6 | 0/6 | — | — | 163k / 28k / 6664k | 1.94 | — | 616 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 2 | 2/2 | 18/18 | 7/10 | 0/16 | — | — | 231k / 32k / 10148k | 2.81 | — | 647 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 3 | 1/2 | 11/12 | 8/12 | 9/34 | 0/2 (+2 nm) | — | 99k / 38k / 14952k | 3.57 | — | 721 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 4 | 1/2 | 5/6 | 10/14 | 9/46 (+1 nd) | 0/2 (+2 nm) | — | 390k / 31k / 16435k | 4.37 | — | 600 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 5 | 1/2 | 3/6 | 11/16 | 9/52 (+2 nd) | 0/5 (+5 nm) | — | 116k / 37k / 12843k | 3.17 | — | 742 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 6 | 1/2 | 3/6 | 12/18 | 9/58 (+5 nd) | 0/6 (+6 nm) | — | 114k / 32k / 6732k | 1.89 | — | 578 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 7 | 2/2 | 6/6 | 13/20 | 9/64 (+8 nd) | 0/10 (+6 nm) | — | 87k / 35k / 11158k | 2.76 | — | 642 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 8 | 1/2 | 5/8 | 15/24 | 9/70 (+8 nd) | 1/14 (+10 nm) | d6×1 | 69k / 31k / 11507k | 2.75 | — | 567 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 1 | 2/2 | 10/10 | 4/6 | 0/6 | — | — | 57k / 13k / 832k | 0.41 | — | 237 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 2 | 2/2 | 18/18 | 10/10 | 0/16 | — | — | 88k / 28k / 1780k | 0.81 | — | 438 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 3 | 1/2 | 10/12 | 11/12 | 0/34 | 0/2 (+2 nm) | — | 99k / 25k / 2207k | 0.89 | — | 542 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 4 | 2/2 | 6/6 | 13/14 | 0/46 (+2 nd) | 0/2 (+2 nm) | — | 88k / 19k / 1716k | 0.71 | — | 309 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 5 | 2/2 | 6/6 | 15/16 | 0/52 (+2 nd) | 0/8 (+2 nm) | — | 100k / 19k / 1319k | 0.65 | — | 284 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 6 | 2/2 | 6/6 | 17/18 | 1/58 (+2 nd) | 0/10 (+2 nm) | — | 88k / 19k / 1369k | 0.64 | — | 270 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 7 | 1/2 | 5/6 | 19/20 | 1/64 (+2 nd) | 0/12 (+4 nm) | — | 164k / 19k / 1462k | 0.81 | — | 296 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 8 | 0/2 | 6/8 | 20/24 | 1/70 (+3 nd) | 0/12 (+12 nm) | — | 133k / 23k / 2035k | 0.90 | — | 408 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 1 | 0/1 | 0/5 | 0/3 | 0/3 | — | — | 57k / 10k / 528k | 0.31 | 0.0002 | 358 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 2 | 0/1 | 0/9 | 0/5 | 0/8 (+5 nd) | — | — | 60k / 14k / 1010k | 0.46 | 0.0003 | 429 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 3 | 0/1 | 0/6 | 0/6 | 0/17 (+14 nd) | — (+2 nm) | — | 39k / 9k / 494k | 0.26 | 0.0003 | 311 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 4 | 0/1 | 0/3 | 0/7 | 0/23 (+20 nd) | — (+2 nm) | — | 39k / 9k / 641k | 0.30 | 0.0003 | 408 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 5 | 0/1 | 0/3 | 0/8 | 0/26 (+23 nd) | — (+5 nm) | — | 42k / 8k / 235k | 0.21 | 0.0002 | 261 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 6 | 0/1 | 0/3 | 0/9 | 0/29 (+26 nd) | — (+6 nm) | — | 68k / 10k / 731k | 0.39 | 0.0002 | 367 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 7 | 0/1 | 0/3 | 0/10 | 0/32 (+29 nd) | — (+8 nm) | — | 88k / 14k / 980k | 0.51 | 0.0003 | 541 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 8 | 0/1 | 0/4 | 0/12 | 0/35 (+32 nd) | — (+12 nm) | — | 63k / 12k / 561k | 0.36 | 0.0003 | 529 | 0 | 0 (0.00) |
