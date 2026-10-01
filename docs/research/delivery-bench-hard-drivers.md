# delivery-bench difficile — i driver corretti: catene da 1, 4 e 12

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-drivers`
- Role: `research`
- Parent: [DBH-16 — Rimisurare i driver corretti](../tickets/delivery-bench-hard/done/16-remeasure-fixed-drivers.md)

## Stato
Output di DBH-16 (2026-09-29). Nella [misura completa](delivery-bench-hard-results.md) (DBH-09)
i due driver non avevano nessuna richiesta accettata. Dopo quella misura sono stati corretti
cinque difetti del driver. Qui `driver-c1a` e `driver-c3a` sono rimisurati nel lotto
`dbh-drivers2`, che contiene solo loro: stesso modello, stessi scenari, stesse suite e stesso
protocollo di DBH-09. La regola di TBA-03 li confronta con i bracci registrati di `dbh`
(`profile_report.py --arm-from`). Record, giudizi e ledger stanno nel repo privato dell'oracolo
(`results/dbh-drivers2/`). Qui ci sono solo aggregati, senza nomi di controlli, trappole,
richieste o difetti.

In breve:
- **Le correzioni funzionano su quello che toccano.** Nessun builder si ferma più per protocollo
  (prima 28 volte), e nessuna suite di test viene più uccisa (prima 17). c1a integra 32 run su 60
  invece di 9, e tocca il codice in tutte le 9 catene.
- **c1a arriva al livello di `bare` alla catena da 4**: 1/36 ciascuno. Alla catena da 12 accetta
  3/36, contro le 8 di `bare` sulle stesse coppie: resta sotto, senza distinguersi (Holm 0,19).
- **Integrare non basta.** Dei 32 run integrati di c1a, 28 non passano tutti i controlli nascosti
  della richiesta. I test del builder passano, ma non coprono quello che la richiesta chiede.
- **c3a si ferma al cancello** in 28 run su 60 e resta a 0 accettate: alla catena da 12 è
  ancora «peggio» di `bare`. Dei 28 candidati fermi, giudicati a parte, 5 sarebbero stati
  accettati.
- **La regola non chiede altre ripetizioni**, e i vincitori di DBH-09 non cambiano:
  skills-only alla catena da 4, `bare` alla catena da 12.
- Spesa: 0,88 $ di Pi e 0,0065 $ di Jev, in 3 ore di parete.

## Autorizzazione e provenienza
- **Autorizzazione**: gli obiettivi di sessione dell'utente, «arriva a finire tutti i benchmark di
  tutti i bracci» e poi «finisci tutti i todos», e i suoi messaggi dopo il report di DBH-09 («se
  c* son buggati bisogna fixarli»). L'autorità del lotto (`results/dbh-drivers2-authority.json`,
  sha256 `cbe05e22…`) copre solo i due driver, gli stessi tre scenari, le catene da 4 e da 12 e
  la regola di TBA-03, con tetti di 30 $ e 36 ore. Dice anche che `dbh` e `dbh-drivers` non si
  emendano e non si rieseguono. Il precedente è il lotto `c3a-observed` del
  [c3a corretto](delivery-bench-c3a-corrected.md).
- **Driver**: `prepare-drivers --source` l'ha copiato dal checkout pulito di `36aebf7`, che
  contiene le cinque correzioni (albero `0e0b92a5…`, registrato nel lotto per ogni scenario).
  L'installazione globale della skill non è stata toccata.
  **Correzione (DBH-17)**: le skill installate non sono quelle del 24/09 di `dbh`, come diceva
  questo report. Il 29/09 alle 11:22 UTC, prima di questo lotto, un aggiornamento di
  pi-personal-config ha installato quelle di `a4190bc`, e sono cambiate `ask-skills`,
  `llm-wiki` e `ticket-autopilot`. I driver hanno copie proprie di `ticket-driver` e
  `ticket-autopilot`, mentre i loro builder vedono le altre skill installate. Il runner non le
  registrava; ora le lega al lotto
  ([DBH-17](../tickets/delivery-bench-hard/done/17-bind-installed-skills.md)).
- **Legami uguali a `dbh`**, verificati prima di partire: seed e suite nascoste dei tre scenari
  (`lua-vm` `f90869af…`, `sql-engine` `5b029cb4…`, `crdt-yjs` `be281cb4…`), fornitore e
  modello (`openai-codex/gpt-6-luna` con `--thinking medium`), comando Pi e tetto di 5400 s per
  richiesta.
- **Harness congelato** a `36aebf7` in un checkout dedicato per tutto il lotto. Rispetto
  all'ultimo harness di `dbh` cambiano solo le attese fra i tentativi falliti per
  l'infrastruttura (DBH-14, DBH-15), e in questo lotto non ce n'è stato nessuno.
- **Esecuzione**: il 29/09 dalle 18:16 alle 21:21 UTC, 4 celle in parallelo come in `dbh`. Prima
  le catene da 4 (3 ripetizioni), poi la ripetizione 1 fino alla 12. Il lotto ha 120 richieste
  giudicate e 120 tentativi, tutti dei bracci. Poi `judge-gated` ha giudicato a parte i 28
  candidati fermi al cancello.
- **Lotto annullato**: `dbh-drivers`, il primo tentativo di questa rimisura, è stato fermato dopo
  la catena da 4, con 70 richieste giudicate su 72, 0 accettate e 0,43 $ spesi. Aveva trovato un
  altro difetto del driver e uno del runner (vedi *Guasti*). Resta registrato con una nota di
  annullamento e non entra in nessuna tabella.

## Cosa è cambiato nel driver
Le cause sono spiegate nel [report di DBH-09](delivery-bench-hard-results.md#esiti-del-driver) e
nelle spec delle correzioni. In sintesi:
- **Il builder non si ferma per protocollo** (TBP-01, #391): il task in prosa è tutto
  l'incarico, e l'assenza di un ticket canonico non è un motivo per fermarsi.
- **I test rossi mostrano la fine di ogni stream** (RTO-01, #390), dove le suite scrivono l'esito.
- **Le suite verbose restano vive** (RTO-02, #392): il limite d'uscita dei test passa da 64 KiB a
  8 MiB.
- **La domanda sul tipo di test vede la fine dell'uscita** e riconosce la cartella dei test di Lua
  (QAO-01, #394).
- **Le suite lente hanno il tempo di finire** (RTO-03, #396): il tempo massimo dei test passa da
  180 a 600 s.
- Invariati: domande, soglie, ordine della cascata, fase di rischio, tempo massimo della foglia e
  una sessione nuova per ogni richiesta.

## Come si legge
Come nel [report di DBH-09](delivery-bench-hard-results.md#come-si-legge): stesse letture lungo
la catena, stessa regola di TBA-03, appaiata con `bare` per (scenario, ripetizione, richiesta).
Le righe dei driver vengono da `dbh-drivers2`, le altre da `dbh`. La famiglia di Holm resta di
quattro confronti. Cambiando il p dei driver cambia anche il p corretto degli altri, ma le loro
decisioni non cambiano.

## Risultati

### I driver prima e dopo
| | c1a in `dbh` | c1a corretto | c3a in `dbh` | c3a corretto |
|---|---:|---:|---:|---:|
| Accettate, catena da 4 | 0/36 | **1/36** | 0/36 | 0/36 |
| Accettate, catena da 12 | 0/36 | **3/36** | 0/36 | 0/36 |
| Run integrati | 9/60 | **32/60** | 0/60 | 2/60 |
| Run fermi al cancello | — | — | 15/60 | 28/60 |
| Candidati vuoti | 36 | 18 | 36 | 22 |
| di cui fermi per protocollo | 15 | **0** | 13 | **0** |
| Suite uccise (uscita o tempo) | 9 | **0** | 8 | **0** |
| Catene finite identiche al seme | 4/9 | **0/9** | 9/9 | 7/9 |
| Latenti trovati, catena da 12 | 3/89 | 23/89 | 1/89 | 1/89 |
| Mediana per richiesta | 67 s | 98 s | 77 s | 147 s |

### Catene da 1 (3 ripetizioni, 9 catene per braccio)
| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 0/9 | 3/30 | 0/9 | — | — | 0.04 | — | 105 | 0 | 0 (0.00) | 0 |
| skills-only | 9 | 1/9 | 4/30 | 0/9 | — | — | 0.06 | — | 71 | 0 | 0 (0.00) | 0 |
| autopilot | 9 | 0/9 | 0/30 | 0/9 | — | — | 0.05 | — | 88 | 0 | 0 (0.00) | 0 |
| driver-c1a | 9 | 0/9 | 1/30 | 0/9 | — | — | 0.05 | — | 73 | 0 | 0 (0.00) | 0 |
| driver-c3a | 9 | 0/9 | 0/30 | 0/9 | — | — | 0.07 | 0.0014 | 63 | 0 | 0 (0.00) | 0 |

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
| crdt-yjs | driver-c1a | 3 | 0/12 | 9/27 | 0/39 (+26 nd) | — | — | 0.08 | — | 508 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 3 | 0/12 | 0/27 | 0/39 (+36 nd) | — | — | 0.09 | 0.0017 | 590 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 3 | 0/12 | 7/30 | 0/48 (+31 nd) | — | — | 0.07 | — | 307 | 0 | 0 (0.00) | 0 |
| lua-vm | skills-only | 3 | 4/12 | 13/30 | 0/48 (+28 nd) | — | — | 0.24 | — | 620 | 0 | 0 (0.00) | 0 |
| lua-vm | autopilot | 3 | 3/12 | 16/30 | 0/48 (+24 nd) | — | — | 0.93 | — | 3493 | 0 | 0 (0.00) | 3 |
| lua-vm | driver-c1a | 3 | 0/12 | 4/30 | 0/48 (+40 nd) | — | — | 0.07 | — | 310 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 3 | 0/12 | 0/30 | 0/48 (+42 nd) | — | — | 0.09 | 0.0010 | 469 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 3 | 0/12 | 8/42 | 0/39 (+30 nd) | — | — | 0.08 | — | 1110 | 0 | 0 (0.00) | 0 |
| sql-engine | skills-only | 3 | 0/12 | 11/42 | 0/39 (+28 nd) | — | — | 0.13 | — | 837 | 0 | 0 (0.00) | 0 |
| sql-engine | autopilot | 3 | 0/12 | 12/42 | 0/39 (+29 nd) | — | — | 0.24 | — | 1426 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c1a | 3 | 1/12 | 19/42 | 0/39 (+22 nd) | — | — | 0.09 | — | 698 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c3a | 3 | 0/12 | 4/42 | 0/39 (+34 nd) | — | — | 0.12 | 0.0018 | 1333 | 0 | 0 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 9 | 1/36 | 25/99 | 0/126 (+77 nd) | — | — | 0.27 | — | 575 | 0 | 0 (0.00) | 0 |
| skills-only | 9 | 9/36 | 35/99 | 0/126 (+67 nd) | — | — | 0.78 | — | 887 | 0 | 0 (0.00) | 1 |
| autopilot | 9 | 6/36 | 38/99 | 0/126 (+71 nd) | — | — | 1.65 | — | 1426 | 0 | 0 (0.00) | 4 |
| driver-c1a | 9 | 1/36 | 32/99 | 0/126 (+88 nd) | — | — | 0.24 | — | 508 | 0 | 0 (0.00) | 0 |
| driver-c3a | 9 | 0/36 | 4/99 | 0/126 (+112 nd) | — | — | 0.31 | 0.0044 | 590 | 0 | 0 (0.00) | 0 |

Violated trap types per arm: bare: —; skills-only: —; autopilot: —; driver-c1a: —; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 36 | 9 | 1 | 8 | 0 | +8 | 0.007812 | 0.03125 | better |
| autopilot | 36 | 6 | 1 | 6 | 1 | +5 | 0.125 | 0.375 | indistinguishable |
| driver-c1a | 36 | 1 | 1 | 1 | 1 | +0 | 1 | 1 | indistinguishable |
| driver-c3a | 36 | 0 | 1 | 0 | 1 | -1 | 1 | 1 | indistinguishable |

Acceptance rule of TBA-03 (ties to the simpler arm): **skills-only**. It reads one axis; the choice of an arm reads all five.

### Catene da 12 (ripetizione 1 per i driver)
- La regola non chiede altre ripetizioni. c1a ha una sola ripetizione e la decisione aperta
  («repeat»), ma il suo tasso (0,083) è sotto quello del vincitore provvisorio `bare` (0,181), e
  la regola ripete solo un braccio che potrebbe superarlo.
- c3a è «peggio» già con la ripetizione 1, come in DBH-09.
- Le righe di `bare`, skills-only e Autopilot hanno 2 ripetizioni. Sulla sola ripetizione 1,
  quella dei driver, `bare` accetta 8/36 e trova 38/89 latenti.

| Scenario | Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| crdt-yjs | bare | 2 | 5/24 | 23/48 | 1/88 (+41 nd) | 1/4 (+10 nm) | d10×1 | 0.43 | — | 2395 | 0 | 0 (0.00) | 1 |
| crdt-yjs | skills-only | 2 | 8/24 | 24/48 | 1/88 (+34 nd) | 0/3 (+11 nm) | — | 0.97 | — | 4603 | 0 | 0 (0.00) | 6 |
| crdt-yjs | autopilot | 2 | 8/24 | 23/48 | 6/88 (+34 nd) | 0/5 (+9 nm) | — | 2.62 | — | 11589 | 0 | 0 (0.00) | 15 |
| crdt-yjs | driver-c1a | 1 | 1/12 | 11/24 | 0/44 (+30 nd) | — (+7 nm) | — | 0.07 | — | 1368 | 0 | 0 (0.00) | 0 |
| crdt-yjs | driver-c3a | 1 | 0/12 | 1/24 | 0/44 (+43 nd) | — (+7 nm) | — | 0.08 | 0.0013 | 1572 | 0 | 0 (0.00) | 0 |
| lua-vm | bare | 2 | 5/24 | 19/54 | 0/84 (+48 nd) | 0/3 (+11 nm) | — | 0.61 | — | 2580 | 0 | 0 (0.00) | 1 |
| lua-vm | skills-only | 2 | 10/24 | 22/54 | 2/84 (+32 nd) | 2/5 (+9 nm) | d7×2 | 1.77 | — | 7446 | 0 | 0 (0.00) | 6 |
| lua-vm | autopilot | 2 | 10/24 | 32/54 | 1/84 (+19 nd) | 4/8 (+6 nm) | d5×1, d7×2, d8×1 | 4.29 | — | 17440 | 0 | 0 (0.00) | 23 |
| lua-vm | driver-c1a | 1 | 1/12 | 0/27 | 0/42 (+36 nd) | — (+7 nm) | — | 0.06 | — | 797 | 0 | 0 (0.00) | 0 |
| lua-vm | driver-c3a | 1 | 0/12 | 0/27 | 0/42 (+38 nd) | — (+7 nm) | — | 0.07 | 0.0006 | 1102 | 0 | 0 (0.00) | 0 |
| sql-engine | bare | 2 | 3/24 | 31/76 | 0/82 (+38 nd) | 3/4 (+10 nm) | d7×3 | 0.81 | — | 5936 | 0 | 0 (0.00) | 2 |
| sql-engine | skills-only | 2 | 3/24 | 34/76 | 1/82 (+34 nd) | 2/4 (+10 nm) | d7×2 | 1.16 | — | 6280 | 0 | 2 (0.00) | 3 |
| sql-engine | autopilot | 2 | 4/24 | 33/76 | 1/82 (+34 nd) | 2/2 (+12 nm) | d7×2 | 3.81 | — | 18161 | 0 | 2 (0.00) | 19 |
| sql-engine | driver-c1a | 1 | 1/12 | 12/38 | 0/41 (+30 nd) | 1/1 (+6 nm) | d7×1 | 0.10 | — | 2021 | 0 | 0 (0.00) | 0 |
| sql-engine | driver-c3a | 1 | 0/12 | 0/38 | 0/41 (+40 nd) | — (+7 nm) | — | 0.14 | 0.0015 | 4267 | 0 | 0 (0.00) | 0 |

| Arm | Cells | Accepted requests | Latent found (end) | Invariants broken (end) | Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts | Infra retries (USD) | Compactions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bare | 6 | 13/72 | 73/178 | 1/254 (+127 nd) | 4/11 (+31 nm) | d7×3, d10×1 | 1.85 | — | 2690 | 0 | 0 (0.00) | 4 |
| skills-only | 6 | 21/72 | 80/178 | 4/254 (+100 nd) | 4/12 (+30 nm) | d7×4 | 3.90 | — | 6280 | 0 | 2 (0.00) | 15 |
| autopilot | 6 | 22/72 | 88/178 | 8/254 (+87 nd) | 6/15 (+27 nm) | d5×1, d7×4, d8×1 | 10.72 | — | 16654 | 0 | 2 (0.00) | 57 |
| driver-c1a | 3 | 3/36 | 23/89 | 0/127 (+96 nd) | 1/1 (+20 nm) | d7×1 | 0.23 | — | 1368 | 0 | 0 (0.00) | 0 |
| driver-c3a | 3 | 0/36 | 1/89 | 0/127 (+121 nd) | — (+21 nm) | — | 0.29 | 0.0034 | 1572 | 0 | 0 (0.00) | 0 |

Violated trap types per arm: bare: contract×2, convention×1, deprecated×1; skills-only: architecture×2, contract×2; autopilot: architecture×2, contract×4; driver-c1a: contract×1; driver-c3a: —.

| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference | McNemar p | Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| skills-only | 72 | 21 | 13 | 14 | 6 | +8 | 0.1153 | 0.1875 | indistinguishable |
| autopilot | 72 | 22 | 13 | 15 | 6 | +9 | 0.07835 | 0.1875 | indistinguishable |
| driver-c1a | 36 | 3 | 8 | 0 | 5 | -5 | 0.0625 | 0.1875 | repeat |
| driver-c3a | 36 | 0 | 8 | 0 | 8 | -8 | 0.007812 | 0.03125 | worse |

Acceptance rule of TBA-03 (ties to the simpler arm): **bare**. It reads one axis; the choice of an arm reads all five.

### Esiti del driver e motivi dei cancelli
- **c1a**: 60 run, 32 integrati e 28 falliti. I falliti sono 18 candidati vuoti (16 rinunce
  senza modifiche e 2 modifiche che non lasciano niente) e 10 con i test rossi. Dei 32 integrati,
  4 sono accettati. Degli altri 28, 20 passano una parte dei controlli nascosti della richiesta
  e 8 nessuno.
- **c3a**: 60 run, 2 integrati, 28 fermi al cancello, 28 falliti e 2 fermati. I falliti sono 22
  candidati vuoti (19 rinunce e 3 modifiche senza risultato) e 6 con i test rossi. I 2 fermati
  hanno ancora i test rossi dopo il retry chiesto dalla cascata. I 2 integrati passano una parte
  dei controlli, non tutti.
- **Test**: 88 esecuzioni della suite nei due bracci, nessuna uccisa per l'uscita o per il tempo.
  Le più lunghe, su `sql-engine`, durano fino a 217 s.

I 28 cancelli di c3a e i loro candidati, giudicati a parte con `judge-gated`:

| Cancello | Run | Candidato fermo accettato |
|---|---:|---:|
| `review.scope_complete` indeterminato | 9 | 2 |
| `review.findings_block` indeterminato | 9 | 3 |
| `retry.recoverable` indeterminato, dopo test rossi | 6 | 0 |
| verdetti negativi decisi anche dopo il retry | 4 | 0 |
| **Totale** | **28** | **5** |

Dei 5, 4 cadono nella catena da 12 e 2 nelle catene da 4. Uno sta in entrambe, perché la catena
da 12 prosegue la ripetizione 1.
Verdetti del giudice fresco sulle 63 escalation:

| Domanda | Verdetti |
|---|---|
| `review.findings_block` | sì×12, no×8, indeterminato×8, senza risposta×1 |
| `review.scope_complete` | sì×3, no×6, indeterminato×8, senza risposta×1 |
| `retry.recoverable` | correzione sul posto×1, indeterminato×6 |
| `qa.evidence_class` | integration×3, unit×2, unknown×1 |
| `verify.claim_supported` | sì×3 |

*Senza risposta*: il giudice ha scritto il verdetto nell'uscita invece che nel file, e il driver
lo conta come assente. In tutti e due i casi il verdetto era «indeterminato», quindi il cancello
è lo stesso.

## Letture
1. **Le correzioni hanno tolto i guasti che dovevano togliere.** Nessuno stop per protocollo,
   nessuna suite uccisa, nessun candidato di crdt-yjs escluso in partenza. c1a ora tocca il
   codice in ogni catena, e trova più latenti di `bare` alla catena da 4 (32/99 contro 25/99).
2. **c1a corretto sta vicino a `bare` alla catena da 4 e sotto alla catena da 12.** 1/36 contro
   1/36, poi 3/36 contro 8/36 sulle stesse coppie. Le 5 richieste che solo `bare` accetta non
   bastano per dire «peggio» con una sola ripetizione (Holm 0,19).
3. **Il limite di c1a adesso è il suo cancello, non un guasto.** c1a integra quando passano i test
   del progetto, compresi quelli che il builder scrive. In 28 integrati su 32 quei test passano e
   la richiesta no. Senza una revisione, niente controlla che il lavoro copra la richiesta.
4. **c3a si ferma dove c1a integra.** Il giudice (lo stesso luna) è spesso indeterminato: 24
   escalation su 63, contro 1 su 126 del [c3a corretto con sol](delivery-bench-c3a-corrected.md).
   I cancelli sui test rossi (6) e quelli con verdetti negativi decisi (4) fermano candidati che
   la suite nascosta boccia. Dei 18 cancelli indeterminati della revisione, 5 fermano un
   candidato buono.
5. **Con un umano al cancello c3a avrebbe consegnato qualcosa, ma poco.** Anche contando i 4
   candidati fermi e buoni della catena da 12, c3a arriverebbe a 4/36, sotto le 8 di `bare`. Le
   richieste successive, che qui sono partite senza quel lavoro, non si possono ricostruire.
6. **Resta la rinuncia del builder.** 16 run di c1a e 19 di c3a finiscono senza modifiche, con il
   builder che scrive di non riuscire a completare il task. Su crdt-yjs alcune rinunce dipendono
   da una richiesta precedente mai consegnata: il builder non trova il codice da estendere. Ogni
   run parte da una sessione nuova, mentre `bare` e skills-only continuano la stessa sessione e
   accumulano conoscenza del codice.
7. **Costo e tempo per catena da 12** (mediana del tempo): c1a 0,08 $ e 23 minuti, c3a 0,10 $ e
   26 minuti, contro `bare` 0,31 $ e 45 minuti. I driver costano meno perché lavorano meno:
   sessioni brevi e nessuna compaction.

## Raccomandazione operativa, aggiornata
La tabella di [DBH-09](delivery-bench-hard-results.md#raccomandazione-operativa) non cambia:
skills-only per catene da 2-4 richieste, skills-only o Pi nudo per catene da 12.

Cambia la riga *Da non usare* sui driver, che adesso vale anche per la versione corretta:
- **c1a** con luna su sistemi maturi accetta meno di `bare` alla catena da 12, 3/36 contro 8/36.
  Costa un quarto e impiega metà del tempo, ma consegna lavoro che passa i propri test e non
  quelli della richiesta.
- **c3a** si ferma al cancello in metà dei run, e senza un umano non consegna. Con un umano al
  cancello consegnerebbe comunque meno di `bare`.

## Limiti del confronto fra lotti
- **Lotti diversi, a poche ore di distanza.** `dbh` è girato dal 28/09 alle 16:51 al 29/09 alle
  12:26 UTC, `dbh-drivers2` il 29/09 dalle 18:16 alle 21:21. Modello, fornitore, seed e suite sono
  gli stessi, ma cambiamenti lato fornitore non si possono escludere.
- **Solo i driver sono corretti.** Gli altri bracci restano come misurati in `dbh`, con le skill
  installate del 24/09. I builder dei driver vedono invece le skill di `a4190bc` (vedi la
  correzione in *Autorizzazione e provenienza*). Il replay di TBP-01 è girato con le stesse
  skill, e lì è il prompt vecchio a fermare il builder per protocollo.
- **Una sola ripetizione alla catena da 12** per i driver, come in DBH-09. Con tassi così bassi
  poche richieste spostano la regola.
- **Tetti invariati**: il tempo massimo della foglia (1800 s) e il tetto per richiesta non sono
  stati toccati, e nessuna richiesta li ha raggiunti.
- **I conteggi delle cause in `dbh`** (fermi per protocollo, suite uccise) vengono dalla
  rilettura delle sessioni e delle ricevute del report di DBH-09.

## Guasti dell'harness e correzioni
- **Durante `dbh-drivers2`**: nessun guasto d'infrastruttura (120 tentativi, tutti dei bracci),
  nessun timeout, nessun tetto di catena, nessun riscontro dell'audit, nessun errore di
  `judge-gated`.
- **`dbh-drivers`**, annullato dopo la catena da 4, con i driver a `ad4769a`:
  - il tempo massimo dei test del driver era 180 s. In `dbh` la suite di `sql-engine` durava da
    71 a 136 s, ma con quattro celle `sql-engine` insieme 9 esecuzioni su 11 sono andate oltre e
    il driver le ha contate come test rossi. Corretto in
    [RTO-03](../tickets/ticket-driver-red-test-observation/done/03-give-a-mature-suite-time.md)
    (#396).
  - Un buco di rete di 42 minuti, dalle 16:02 alle 16:45 UTC, ha esaurito le ripetizioni di 10
    richieste: le attese di DBH-14 coprivano circa 11 minuti. Corretto in
    [DBH-15](../tickets/delivery-bench-hard/done/15-long-outage-wait.md) (#395).
- **Harness e driver** sono cambiati solo fra i due lotti, mai fra due `run-lot` dello stesso
  lotto.

## Seguiti possibili (non fatti)
- Il driver potrebbe leggere il verdetto del giudice anche dalla sua uscita, quando il giudice
  non scrive il file. Qui non avrebbe cambiato nessun cancello.
- Su crdt-yjs la suite scrive il dettaglio del test fallito a metà dell'uscita, e alla fine solo
  il conteggio. Lo stato della domanda sul retry potrebbe portare le righe del fallimento.
- Al termine di questo lotto un modello più forte sugli stessi scenari non era misurato.
  Opus 5.5 è stato misurato dopo, con autorità e budget nuovi, in
  [DBH-20](delivery-bench-hard-opus.md).
