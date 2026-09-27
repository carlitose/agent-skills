# delivery-bench — c3a corretto: catene da 1, 3 e 8

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-c3a-corrected`
- Role: `research`
- Parent: [TJV-02 — measure the corrected c3a on delivery-bench](../tickets/ticket-driver-judge-verdicts/done/02-measure-corrected-c3a.md)

## Stato
Output di TJV-02 (2026-09-27). Il braccio `driver-c3a` è stato rimisurato dopo le correzioni
del driver TJV-01 (#369) e TJV-03 (#371), nel lotto `c3a-observed`, che contiene solo questo
braccio. Il protocollo è quello degli altri bracci in `db07-pilot`: 3 ripetizioni fino alla
richiesta 3 e la ripetizione 1 fino all'8, più le ripetizioni che la regola di TBA-03 chiede. La
regola ha chiesto la r2 della catena da 8, e con la r2 la regola è decisa. c3a è confrontato con
i bracci registrati di `db07-pilot` (`profile_report.py --arm-from`, #372). Record, giudizi e
ledger stanno nel repo privato dell'oracolo (`results/c3a-observed/`); qui ci sono solo
aggregati, senza nomi di controlli, trappole o difetti.

In breve, c3a ora completa il benchmark. Si è fermato in 2 run su 57 (prima 31 su 42) e accetta
9/9, 25/27 e 45/48 alle tre lunghezze (prima 2/9, 7/27 e 6/24). A ogni lunghezza è
indistinguibile da `bare`.

## Autorizzazione e provenienza
- **Autorizzazione**: l'obiettivo di sessione dell'utente, «Fai in modo che c3a completi il
  benchmark», che autorizza anche la spesa di modello e Jev. L'autorità del lotto
  (`results/c3a-observed-authority.json`, sha256 `91af2cb0…`) copre solo `driver-c3a`, gli stessi
  tre scenari, le lunghezze 3 e 8 e la regola di TBA-03. Dice anche che `db07-pilot` non si
  emenda e non si riesegue.
- **Driver**: `prepare-drivers --source` (#370) l'ha copiato dal checkout pulito del merge di
  TJV-03, `8fa9ca6`, che contiene anche TJV-01 (albero `20c6c8d3…`, registrato nel lotto per ogni
  scenario). Rispetto alle copie di `db07-pilot` differiscono solo `SKILL.md`,
  `prompts/judge.md`, `scripts/cascade.py`, `scripts/driver.py` e `scripts/state.py`. La policy,
  la foglia e l'arbitro hanno gli stessi digest. L'installazione globale della skill non è stata
  toccata.
- **Legami uguali a `db07-pilot`**, verificati prima di partire: seed, suite nascoste e canarini
  dei tre scenari (`python-billing` `6ba6b3c0…`, `c-recq` `d87c157f…`, `ts-reservas`
  `1f8809bd…`, cioè la suite già emendata in DB-08), provider, modello `openai-codex/gpt-6-sol`
  con `--thinking high`, comando Pi e tetti di tempo.
- **Harness congelato** a `8fa9ca6` in un worktree dedicato per tutto il lotto. Il report usa
  `profile_report.py` a `1d78f31` (#372), che aggiunge solo la lettura di un braccio da un
  altro lotto.
- **Esecuzione**: il 27/09 dalle 16:18 alle 18:30 UTC. Catene da 3 con 5 celle in parallelo,
  catene da 8 con 3; stessa macchina e stesso provider dei lotti Terminal-Bench. Il lotto fa 57
  richieste giudicate, 57 tentativi (tutti del braccio), 22,31 $ stimati da Pi e 0,0326 $ di Jev
  (201 chiamate).
- **Lotto fermato**: `c3a-verdicts` ha usato il driver con il solo TJV-01 ed è stato fermato
  apposta dopo 14 run (vedi *Guasti*). Resta registrato come misura di TJV-01 e non entra in
  nessuna tabella.

## Cosa è cambiato nel driver
Le cause sono nella [spec](../specs/ticket-driver-judge-verdicts.md). In sintesi:
- **TJV-01**: il giudice fresco chiude con una riga `Answer:` presa dall'elenco dei verdetti
  della domanda. Senza quella riga il verdetto vale «incerto». Lo stato della review riceve la
  ricevuta del test osservata dal driver, e un negativo deciso della review provoca un retry
  del builder invece di un cancello.
- **TJV-03**: lo stato arriva al giudice come file con hash, non sulla riga di comando. Lo stato
  QA contiene i sorgenti dei test eseguiti, e lo stato di verifica contiene la ricevuta del test
  come oggetto unico.
- Invariati: domande, soglie, ordine della cascata e fase di rischio.

## Come si legge
Gli assi sono quelli del [report di DB-08](delivery-bench-results.md#come-si-legge): stesse
letture lungo la catena, stessa regola di TBA-03, appaiata con `bare` per (scenario, ripetizione,
richiesta). Le righe `driver-c3a` vengono da `c3a-observed`, le altre da `db07-pilot`. La
famiglia di Holm resta di quattro confronti, ma cambiando il p di c3a cambia anche il p corretto
degli altri; le decisioni degli altri bracci non cambiano.

## Risultati

### c3a prima e dopo
| Catena | Richieste accettate | Run fermi al cancello | USD (Pi) per catena | USD (Jev) per catena | Mediana per catena |
|---|---:|---:|---:|---:|---:|
| da 1 (3 rip.) | 2/9 → **9/9** | 7/9 → **0/9** | 0,33 → 0,38 | 0,0003 → 0,0005 | 355 → 352 s |
| da 3 (3 rip.) | 7/27 → **25/27** | 19/27 → **2/27** | 1,03 → 1,16 | 0,0010 → 0,0016 | 1097 → 1071 s |
| da 8 (1 → 2 rip.) | 6/24 → **45/48** | 31/42 → **2/57** (tutto il lotto) | 2,75 → 3,15 | 0,0026 → 0,0046 | 2879 → 3040 s |

Il costo per catena cresce poco perché adesso il lavoro si integra e le richieste successive
partono da un `main` che lo contiene.

### Catene da 1 (3 ripetizioni, 9 catene per braccio)
| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 9/9 | 37/39 | 0/36 | — | — | 0.74 | — | 128 | 0 | 0 (0.00) |
| skills-only | 9 | 9/9 | 36/39 | 0/36 | — | — | 1.60 | — | 169 | 0 | 0 (0.00) |
| autopilot | 9 | 9/9 | 36/39 | 0/36 | — | — | 8.26 | — | 617 | 0 | 0 (0.00) |
| driver-c1a | 9 | 9/9 | 36/39 | 0/36 | — | — | 1.92 | — | 193 | 0 | 0 (0.00) |
| driver-c3a | 9 | 9/9 | 36/39 | 0/36 | — | — | 3.38 | 0.0046 | 352 | 0 | 0 (0.00) |

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| autopilot | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 9 | 9 | 9 | 0 | 0 | +0 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**.

### Catene da 3 (3 ripetizioni, 9 catene per braccio)
| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 1.28 | — | 440 | 0 | 0 (0.00) |
| c-recq | skills-only | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 1.92 | — | 460 | 0 | 0 (0.00) |
| c-recq | autopilot | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 8.47 | — | 1628 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 2.64 | — | 736 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 3 | 9/9 | 24/24 | 0/39 | 0/6 | — | 3.39 | 0.0037 | 1071 | 0 | 0 (0.00) |
| python-billing | bare | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 0.71 | — | 267 | 0 | 0 (0.00) |
| python-billing | skills-only | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 1.27 | — | 333 | 0 | 0 (0.00) |
| python-billing | autopilot | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 7.55 | — | 1384 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 3 | 9/9 | 27/27 | 0/51 | 0/6 | — | 1.96 | — | 550 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 3 | 8/9 | 24/27 | 0/51 (+4 nd) | 1/6 | d1×1 | 2.81 | 0.0057 | 770 | 0 | 0 (0.00) |
| ts-reservas | bare | 3 | 8/9 | 12/18 | 15/51 | 0/4 (+2 nm) | — | 1.59 | — | 667 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 3 | 9/9 | 18/18 | 1/51 | 0/6 | — | 4.79 | — | 1316 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 3 | 8/9 | 13/18 | 9/51 | 0/4 (+2 nm) | — | 12.31 | — | 1961 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 3 | 7/9 | 16/18 | 0/51 | 0/2 (+4 nm) | — | 3.30 | — | 1167 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 3 | 8/9 | 17/18 | 0/51 | 0/4 (+2 nm) | — | 4.26 | 0.0047 | 1351 | 0 | 0 (0.00) |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 26/27 | 63/69 | 15/141 | 0/16 (+2 nm) | — | 3.58 | — | 440 | 0 | 0 (0.00) |
| skills-only | 9 | 27/27 | 69/69 | 1/141 | 0/18 | — | 7.98 | — | 460 | 0 | 0 (0.00) |
| autopilot | 9 | 26/27 | 64/69 | 9/141 | 0/16 (+2 nm) | — | 28.33 | — | 1628 | 0 | 0 (0.00) |
| driver-c1a | 9 | 25/27 | 67/69 | 0/141 | 0/14 (+4 nm) | — | 7.90 | — | 736 | 0 | 0 (0.00) |
| driver-c3a | 9 | 25/27 | 65/69 | 0/141 (+4 nd) | 1/16 (+2 nm) | d1×1 | 10.46 | 0.0142 | 1071 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: convention×1.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 27 | 27 | 26 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| autopilot | 27 | 26 | 26 | 0 | 0 | +0 | 1 | 1 | indistinguishable |
| driver-c1a | 27 | 25 | 26 | 0 | 1 | -1 | 1 | 1 | indistinguishable |
| driver-c3a | 27 | 25 | 26 | 1 | 2 | -1 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**.

### Catene da 8 (2 ripetizioni per braccio)
Dopo la r1 c3a accettava 22/24. Il suo tasso (0,917) era sopra quello del vincitore provvisorio
`bare` (0,875) e c'era una sola ripetizione, quindi la regola ha chiesto la r2, come in DB-08
per gli altri bracci. Con la r2 la regola è decisa.

| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| c-recq | bare | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 3.73 | — | 1367 | 0 | 0 (0.00) |
| c-recq | skills-only | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 5.23 | — | 1704 | 0 | 0 (0.00) |
| c-recq | autopilot | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 18.62 | — | 4183 | 0 | 0 (0.00) |
| c-recq | driver-c1a | 2 | 16/16 | 31/32 | 0/76 | 0/18 | — | 4.94 | — | 2075 | 0 | 0 (0.00) |
| c-recq | driver-c3a | 2 | 16/16 | 32/32 | 0/76 | 0/18 | — | 6.46 | 0.0075 | 3212 | 0 | 0 (0.00) |
| python-billing | bare | 2 | 16/16 | 34/36 | 0/74 | 0/18 | — | 2.40 | — | 906 | 0 | 0 (0.00) |
| python-billing | skills-only | 2 | 16/16 | 34/36 | 0/74 | 0/18 | — | 3.39 | — | 1185 | 0 | 0 (0.00) |
| python-billing | autopilot | 2 | 16/16 | 35/36 | 0/74 | 0/18 | — | 15.04 | — | 3573 | 0 | 0 (0.00) |
| python-billing | driver-c1a | 2 | 16/16 | 35/36 | 0/74 | 0/18 | — | 4.26 | — | 1808 | 0 | 0 (0.00) |
| python-billing | driver-c3a | 2 | 15/16 | 32/36 | 0/74 (+4 nd) | 2/18 | d1×1, d5×1 | 6.01 | 0.0122 | 2708 | 0 | 0 (0.00) |
| ts-reservas | bare | 2 | 10/16 | 12/24 | 15/70 (+15 nd) | 0/12 (+12 nm) | — | 4.34 | — | 1590 | 0 | 0 (0.00) |
| ts-reservas | skills-only | 2 | 16/16 | 22/24 | 0/70 | 0/24 | — | 13.96 | — | 3635 | 0 | 0 (0.00) |
| ts-reservas | autopilot | 2 | 11/16 | 15/24 | 9/70 (+8 nd) | 1/14 (+10 nm) | d6×1 | 23.26 | — | 5113 | 0 | 0 (0.00) |
| ts-reservas | driver-c1a | 2 | 12/16 | 20/24 | 1/70 (+3 nd) | 0/12 (+12 nm) | — | 5.82 | — | 2784 | 0 | 0 (0.00) |
| ts-reservas | driver-c3a | 2 | 14/16 | 21/24 | 0/70 (+1 nd) | 2/20 (+4 nm) | d6×2 | 6.44 | 0.0081 | 3195 | 0 | 0 (0.00) |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 6 | 42/48 | 78/92 | 15/220 (+15 nd) | 0/48 (+12 nm) | — | 10.48 | — | 1367 | 0 | 0 (0.00) |
| skills-only | 6 | 48/48 | 88/92 | 0/220 | 0/60 | — | 22.58 | — | 1704 | 0 | 0 (0.00) |
| autopilot | 6 | 43/48 | 82/92 | 9/220 (+8 nd) | 1/50 (+10 nm) | d6×1 | 56.92 | — | 4183 | 0 | 0 (0.00) |
| driver-c1a | 6 | 44/48 | 86/92 | 1/220 (+3 nd) | 0/48 (+12 nm) | — | 15.03 | — | 2075 | 0 | 0 (0.00) |
| driver-c3a | 6 | 45/48 | 85/92 | 0/220 (+5 nd) | 4/56 (+4 nm) | d1×1, d5×1, d6×2 | 18.90 | 0.0278 | 3040 | 0 | 0 (0.00) |

Violated trap types per arm: bare: —; skills-only: —; autopilot: convention×1; driver-c1a: —; driver-c3a: contract×1, convention×3.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 48 | 48 | 42 | 6 | 0 | +6 | 0.03125 | 0.125 | indistinguishable |
| autopilot | 48 | 43 | 42 | 1 | 0 | +1 | 1 | 1 | indistinguishable |
| driver-c1a | 48 | 44 | 42 | 3 | 1 | +2 | 0.625 | 1 | indistinguishable |
| driver-c3a | 48 | 45 | 42 | 6 | 3 | +3 | 0.5078 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. Nel report di DB-08 il Holm di
skills-only era 0,094; qui è 0,125 perché il p di c3a è cambiato. La decisione non cambia.

### Esiti del driver e motivi dei cancelli
In 57 run: 55 `integrated`, 2 `gated`; nessun `no-summary`, nessun errore della foglia giudice.
Ci sono stati 5 retry del builder: 2 dopo un negativo deciso della review (uno poi integrato,
l'altro fermo) e 3 nella fase di rischio, tutti poi integrati.

Verdetti del giudice fresco sulle escalation:

| Domanda | Verdetti |
|---|---|
| `review.findings_block` | no×30, sì×3 |
| `review.scope_complete` | sì×17, indeterminato×1 |
| `qa.evidence_class` | integration×36, unit×3, simulated×1 |
| `verify.claim_supported` | sì×35 |

Nel lotto originale lo stesso giudice aveva risolto `qa.evidence_class` 0 volte su 15.

| Cancello | Motivo | Candidato fermo, giudicato a parte |
|---|---|---:|
| `python-billing`, r2, richiesta 2 | `review.scope_complete` indeterminato: due criteri riguardano codice che il diff non tocca, e lo stato del giudice contiene il diff, non il resto del repository | accettato (1/1) |
| `ts-reservas`, r3, richiesta 3 | `review.findings_block` = sì due volte: il retry ha corretto il primo difetto, il secondo giudice ne ha trovato un altro, concreto, che si vede nel codice del candidato (verificato a parte); nessun test visibile lo esercita | accettato (1/1) |

Entrambi i candidati fermi sarebbero stati accettati dalla suite nascosta. Il primo cancello è
un'incertezza vera, perché lo stato non decide la domanda. Il secondo ferma un difetto reale che
l'oracolo non misura.

## Letture
1. **c3a ora completa il benchmark.** Fino all'8 si ferma 2 volte su 57, e ogni volta con una
   ragione scritta. Accetta quanto gli altri bracci su C e Python, e sul frontend a catena lunga
   14/16, secondo solo a skills-only (16/16) e sopra c1a (12/16), Autopilot (11/16) e `bare`
   (10/16).
2. **L'accettazione, da sola, non lo separa da nessuno.** c3a +3 su `bare` alla catena da 8
   (Holm 1), come c1a +2 e Autopilot +1. Il vincitore della regola resta `bare` a ogni
   lunghezza.
3. **Robustezza: nessuna regressione.** 0/220 invarianti rotte alla catena da 8, come
   skills-only; `bare` 15, Autopilot 9, c1a 1. Nel frontend l'app non si è mai rotta in nessuna
   delle catene di c3a. Latenti 85/92, fra c1a (86) e Autopilot (82).
4. **Bussola: c3a viola più trappole di tutti, 4 su 56 misurabili**, contro l'unica di Autopilot.
   Vanno lette in due gruppi:
   - 2 (convenzione, distanze 1 e 5, `python-billing` r2) vengono da una regola della richiesta
     fermata al cancello. Quel lavoro non è mai arrivato in `main`, quindi le richieste dopo non
     potevano conoscere la regola. È un costo del cancello in AFK, non una dimenticanza.
   - 2 (convenzione e contratto, distanza 6, `ts-reservas` r2) vengono da una regola integrata e
     accettata alla richiesta 2 e violata alla richiesta 8. Qui è memoria lunga. Il builder del
     driver parte da una sessione nuova a ogni richiesta e vede le regole precedenti solo
     attraverso il repository. Nella r1 le stesse trappole non sono misurabili, perché la
     feature della richiesta 8 non è stata accettata.
5. **Costo e tempo per catena da 8** (mediana del tempo): c3a 3,15 $ e 51 min, contro `bare`
   1,75 $ e 23 min, c1a 2,51 $ e 35 min, skills-only 3,76 $ e 28 min, Autopilot 9,49 $ e 70 min.
   Jev costa 0,005 $ per catena. c3a costa meno di skills-only ma impiega quasi il doppio del
   tempo.

## Raccomandazione operativa, aggiornata
La tabella di [DB-08](delivery-bench-results.md#raccomandazione-operativa) non cambia:
Pi nudo per task brevi e backend, skills-only per 8 richieste o per il frontend. c3a non la
supera su nessun asse misurato: meno richieste e latenti di skills-only, 4 trappole violate
contro 0, quasi il doppio del tempo.

Cambia invece la riga *Da non usare*: **c3a non è più escluso in AFK.** Ha senso quando si vuole
che il run si fermi con una ragione scritta invece di integrare un difetto che la review vede,
e si accetta di pagarlo in tempo e, in AFK, con le richieste che partono senza il lavoro fermo.
Costa 0,84× skills-only e 1,8× `bare`, e impiega 1,8× il tempo di skills-only.

## Limiti del confronto fra lotti
- **Lotti diversi, giorni diversi.** Gli altri bracci sono stati misurati il 26-27/09 in
  `db07-pilot`, c3a il 27/09 pomeriggio in `c3a-observed`. Modello, provider, seed e suite sono
  gli stessi, ma cambiamenti lato provider in quelle ore non si possono escludere. Le coppie di
  McNemar appaiano la stessa richiesta della stessa catena, non esecuzioni contemporanee.
- **Solo c3a ha il driver nuovo.** Gli altri bracci restano nella versione con cui sono stati
  misurati. Per c1a questo non conta: il suo percorso (builder, test, integrazione) non passa
  per la cascata, i cancelli semantici o la fase di rischio, che sono le parti cambiate. Le righe
  di c3a in `db07-pilot` restano la misura del driver originale.
- **Suite di `ts-reservas`**: `c3a-observed` è giudicato fin dall'inizio con la suite emendata
  in DB-08; per gli altri bracci gli otto giudizi toccati erano stati riclassificati in modo
  esatto (contratto §9).
- **Parallelismo** di 5 e poi 3 celle, contro 4 in DB-08: pesa sui tempi, non sugli esiti. I
  tempi restano rumorosi e gli USD sono stime di Pi.
- **Stesse misure piccole di DB-08**: 2 ripetizioni alla catena da 8. Le 2 trappole a distanza
  6 sono un evento in una catena, non una frequenza.

## Guasti dell'harness e correzioni
- **Durante `c3a-observed`**: nessun guasto d'infrastruttura (57 tentativi, tutti `agent`),
  nessun timeout, nessun tetto di catena, nessun riscontro dell'audit.
- **`c3a-verdicts`** (solo TJV-01) è stato fermato apposta dopo 14 run del driver, quando si è
  visto che due giudici non ricevevano le osservazioni che la loro domanda chiede. Lì una
  richiesta è finita con il driver uscito a codice 0, senza output e senza riepilogo, mentre
  lanciava un giudice. La causa non è spiegata, ed è registrata come evento d'infrastruttura. Il
  trasporto dello stato su file di TJV-03 elimina il rischio vicino (riga di comando oltre il
  limite di Windows), che però produce un errore visibile, non un'uscita muta.
- **Harness**: `prepare-drivers --source` (#370) prima del lotto, `profile_report.py --arm-from`
  (#372) dopo. Nessuna modifica fra due `run-lot` di questo lotto.

## Seguiti possibili (non fatti)
- `review.scope_complete` non può decidere criteri su codice non modificato guardando un diff:
  il giudice potrebbe ricevere una vista limitata e con hash del repository.
- Memoria lunga del builder del driver: le regole delle richieste precedenti arrivano solo dal
  repository. È da misurare con catene più lunghe o trappole più dure, come già chiede la
  [mappa](../specs/delivery-bench-wayfinder.md#next-review).
