---
type: source-part
source_identity: artifact:delivery-bench-results
source_digest: sha256:c44878fd46efdcf867b411dfb63a161227ac41aeb5e5181be531affc4a634635
source_entry: wiki/sources/artifact-delivery-bench-results.md
---

# Preserved source — Part 1

Entry and provenance: [[sources/artifact-delivery-bench-results]]

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":20860,"payload_sha256":"677393209eaa493a7ff964c4bd538f42c0779e1913c9c611f74ac22560fd82e5","schema":1,"source_digest":"sha256:c44878fd46efdcf867b411dfb63a161227ac41aeb5e5181be531affc4a634635","source_identity":"artifact:delivery-bench-results"} -->
```markdown
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


```
