# delivery-bench — pilota: catena da 1, cinque bracci, tre scenari

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-pilot`
- Role: `research`
- Parent: [DB-07 — Pilota: catena da 1, cinque bracci, tre scenari](../tickets/delivery-bench/done/07-pilot-chain-1-all-arms.md)

## Stato
Output di DB-07 (2026-09-26). Lotto `db07-pilot`: 45 celle (3 scenari × 5 bracci × 3
ripetizioni), catena da 1, `openai-codex/gpt-6-sol` con `--thinking high`. DB-08 prosegue
queste stesse celle (contratto §9). I record di cella, i giudizi e il ledger stanno nel repo
privato dell'oracolo (`results/db07-pilot/`, ignorato da Git); qui ci sono solo gli aggregati,
senza nomi di controlli nascosti.

## Provenienza
- Autorità: `results/db07-pilot-authority.json`, sha256 `058edf26ce020f10…`, dall'obiettivo di
  sessione («esegui tutti i ticket per creare il benchmark e poi esegui tutti i bracci sul
  benchmark»); copre i cinque bracci, i tre scenari, 3 ripetizioni, lunghezza fino a 8, spesa
  Jev per `driver-c3a`.
- Runner: `benchmarks/delivery-bench/runner.py` al merge `58a6bd3`, congelato in un worktree
  dedicato; la cella sonda (`python-billing.bare.r1`) è partita dal commit `89615b4`, con lo
  stesso file byte per byte. Giudizio controfattuale e report: questa PR.
- Suite nascoste (sha256): `python-billing` `6ba6b3c0…`, `c-recq` `d87c157f…`, `ts-reservas`
  `42cdfc89…`; copie del driver: `leaf.py` `d4577316…`, `arbiter.py` `5f8ba799…`,
  `policy.json` per scenario (`6cdc2817…`, `59909923…`, `676a728d…`).
- Esecuzione: 2026-09-26 16:22-17:32 UTC, 4 celle in parallelo, sulla stessa macchina e con lo
  stesso provider dei lotti Terminal-Bench in corso (i tempi sono rumorosi).

## Risultati (generati da `profile_report.py`)

### Profile per request

| Scenario | Arm | Request | Accepted | Features | Latent found | Invariants broken | Traps violated | Distances | Tokens in / out / cache read | USD (Pi) | USD (Jev) | Median s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 1 | 3/3 | 12/12 | 15/15 | 0/12 | — | — | 64k / 15k / 197k | 0.32 | — | 133 | 0 | 0 (0.00) |
| c-recq | skills-only | 1 | 3/3 | 12/12 | 15/15 | 0/12 | — | — | 93k / 18k / 726k | 0.51 | — | 164 | 0 | 0 (0.00) |
| c-recq | autopilot | 1 | 3/3 | 12/12 | 15/15 | 0/12 | — | — | 265k / 41k / 9208k | 2.78 | — | 624 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 1 | 3/3 | 12/12 | 15/15 | 0/12 | — | — | 95k / 23k / 1235k | 0.66 | — | 192 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 1 | 0/3 | 0/12 | 3/15 | 0/12 | — | — | 223k / 34k / 2023k | 1.19 | 0.0007 | 361 | 0 | 0 (0.00) |
| python-billing | bare | 1 | 3/3 | 24/24 | 15/15 | 0/15 | — | — | 44k / 9k / 127k | 0.20 | — | 86 | 0 | 0 (0.00) |
| python-billing | skills-only | 1 | 3/3 | 24/24 | 15/15 | 0/15 | — | — | 56k / 11k / 464k | 0.31 | — | 103 | 0 | 0 (0.00) |
| python-billing | autopilot | 1 | 3/3 | 24/24 | 15/15 | 0/15 | — | — | 235k / 39k / 8345k | 2.53 | — | 642 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 1 | 3/3 | 24/24 | 15/15 | 0/15 | — | — | 88k / 21k / 1297k | 0.64 | — | 187 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 1 | 2/3 | 17/24 | 10/15 | 0/15 | — | — | 126k / 27k / 1205k | 0.76 | 0.0012 | 354 | 0 | 0 (0.00) |
| ts-reservas | bare | 1 | 3/3 | 15/15 | 7/9 | 0/9 | — | — | 34k / 13k / 150k | 0.23 | — | 132 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 1 | 3/3 | 15/15 | 6/9 | 0/9 | — | — | 99k / 26k / 1593k | 0.77 | — | 324 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 1 | 3/3 | 15/15 | 6/9 | 0/9 | — | — | 253k / 42k / 10157k | 2.95 | — | 615 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 1 | 3/3 | 15/15 | 6/9 | 0/9 | — | — | 83k / 21k / 1187k | 0.61 | — | 245 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 1 | 0/3 | 0/15 | 0/9 | 0/9 | — | — | 175k / 31k / 1991k | 1.05 | 0.0007 | 358 | 0 | 0 (0.00) |

### Per arm, all scenarios and requests

| Arm | Accepted | Features | Latent found | Invariants broken | Traps violated | Distances | Tokens in / out / cache read | USD (Pi) | USD (Jev) | Median s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9/9 | 51/51 | 37/39 | 0/36 | — | — | 143k / 36k / 473k | 0.74 | — | 128 | 0 | 0 (0.00) |
| skills-only | 9/9 | 51/51 | 36/39 | 0/36 | — | — | 247k / 54k / 2783k | 1.60 | — | 169 | 0 | 0 (0.00) |
| autopilot | 9/9 | 51/51 | 36/39 | 0/36 | — | — | 753k / 122k / 27709k | 8.26 | — | 617 | 0 | 0 (0.00) |
| driver-c1a | 9/9 | 51/51 | 36/39 | 0/36 | — | — | 267k / 64k / 3720k | 1.92 | — | 193 | 0 | 0 (0.00) |
| driver-c3a | 2/9 | 17/51 | 13/39 | 0/36 | — | — | 523k / 92k / 5219k | 3.01 | 0.0026 | 355 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: —.

### Acceptance paired with `bare`

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| autopilot | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 9 | 2 | 9 | 0 | 7 | -7 | 0.01562 | 0.0625 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Driver outcomes

A `gated` run stopped on an uncertain semantic gate and waits for a human; nothing is integrated. Its candidate is judged apart (counterfactual, never counted as acceptance).

| Scenario | Arm | Request | Runs by status | Gated candidates accepted |
|---|---|---:|---|---:|
| c-recq | driver-c1a | 1 | integrated×3 | — |
| c-recq | driver-c3a | 1 | gated×3 | 3/3 |
| python-billing | driver-c1a | 1 | integrated×3 | — |
| python-billing | driver-c3a | 1 | gated×1, integrated×2 | 1/1 |
| ts-reservas | driver-c1a | 1 | integrated×3 | — |
| ts-reservas | driver-c3a | 1 | gated×3 | 3/3 |

### Harness and validity

- Infrastructure attempts by class: {}
- Cells invalidated by the audit: none
- Cells stopped by an error: none
- Cells that hit the chain time cap: none

## Letture

1. **Alla catena da 1 l'accettazione è al soffitto.** Bare, skills-only, Autopilot e c1a
   accettano 9/9 con 51/51 controlli di funzionalità; nessuna coppia discorde, quindi la regola
   di TBA-03 non distingue nessuno e l'asse dell'accettazione, da solo, indica il braccio più
   semplice. È lo stesso quadro di Terminal-Bench, non quello di bench38: con questo modello Pi
   nudo trova 15/15 dei latenti Python (bench38, con Sonnet 4.6 medium: 0/5).
2. **Robustezza**: 37/39 latenti per bare e 36/39 per skills-only, Autopilot e c1a (la
   differenza è un solo latente del frontend: troppo poco per leggerci qualcosa); c3a 13/39,
   per i run bloccati che non consegnano.
3. **Bussola**: nessuna invariante rotta; nessuna trappola è attiva alla richiesta 1 per
   costruzione (le tentazioni arrivano dalla 2), quindi questo asse si legge solo in DB-08.
4. **Costo e tempo** (totale di 9 celle, stima USD di Pi): bare 0,74 $, skills-only 1,60 $
   (2,2×), c1a 1,92 $ (2,6×), c3a 3,01 $ (4,1×), Autopilot 8,26 $ (11,2×); mediana del tempo per
   richiesta 128 s, 169 s, 193 s, 355 s, 617 s. Jev costa in tutto 0,0026 $.
5. **c3a in AFK misura il suo cancello, non il suo lavoro.** Sette run su nove si fermano in
   `gated`: Jev risponde (nessun guasto), la cascata aggiunge tre foglie giudice e una domanda
   resta incerta (per esempio `qa.evidence_class` con confidenza 0,51-0,54 contro 0,75). Il run
   aspetta allora un'approvazione umana, che in un lotto AFK non si fabbrica. I sette candidati
   bloccati, giudicati a parte, sarebbero stati accettati tutti (7/7). In una catena, la
   richiesta successiva parte da un `main` senza quel lavoro: è il modo naturale del braccio e
   resta così in DB-08, con il controfattuale riportato accanto.
6. **Ogni braccio ha lavorato nel suo modo naturale.** Autopilot ha usato il runner in 9 celle
   su 9 (un run, un ramo, integrazione in `main` da parte del braccio, albero pulito); bare e
   skills-only lasciano il lavoro nel working tree, che è ciò che si giudica; skills-only ha
   scritto spec e ticket solo in 2 celle frontend su 9.

## Guasti dell'harness e correzioni
- Durante il lotto: nessun guasto d'infrastruttura (45 tentativi, tutti `agent`), nessun errore
  del giudice, nessun timeout, nessun riscontro dell'audit; tempo massimo di una richiesta 770 s.
- Emersi preparando il lotto e corretti in DB-06 (PR #365): comando di test TypeScript del
  contratto (`scripts/test.mjs` non esiste: `cmd /c npm test`), nome dell'immagine C, codifica
  dell'output del report su Windows.
- Emersi dal pilota, corretti in questa PR: (a) il report non mostrava gli esiti dei run del
  driver né distingueva un cancello da un lavoro sbagliato → sezione *Driver outcomes* e
  `runner.py judge-gated` (giudizio controfattuale del candidato bloccato, mai contato come
  accettazione); (b) `run-lot` non sapeva limitarsi a una ripetizione, e la catena da 8 gira solo
  sulla r1 → `--rep`; (c) DB-08 deve ripetere la catena da 8 «solo dove la regola di TBA-03 lo
  richiede» → `profile_report.py --through L --rep R` e la regola del vincitore (vincitore
  provvisorio e bracci che richiedono un'altra ripetizione).

## Limiti
- I tempi condividono macchina e provider con Terminal-Bench; gli USD sono la stima di Pi per un
  provider in abbonamento, non una fattura.
- Una sola lunghezza: il pilota dice che i bracci sono confrontabili e che l'harness regge, non
  quale braccio conviene.
- Revisione dell'utente: l'obiettivo di sessione autorizza DB-07 e DB-08 senza fermarsi; questo
  report è il punto di revisione e la misura completa parte con la stessa autorizzazione.
