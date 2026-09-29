---
ticket_schema: 1
ticket_id: "DBH-16"
execution_mode: AFK
blocked_by:
  - "DBH-09"
  - "DBH-15"
---

# DBH-16 — Rimisurare i driver corretti

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:16`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

### Produces
- [delivery-bench-hard-drivers.md](../../research/delivery-bench-hard-drivers.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
La misura completa (DBH-09) ha registrato 0 richieste accettate per `driver-c1a` e
`driver-c3a`. Dopo la misura sono emersi difetti del driver, corretti in TBP-01, RTO-01, RTO-02
e QAO-01. Questo ticket rimisura i due driver corretti, con lo stesso modello, gli stessi scenari
e le stesse suite, e li confronta con i bracci registrati di `dbh`.
- Un lotto nuovo con una sua autorità, solo per i due driver. `dbh` non si emenda e non si
  riesegue.
- Catene da 4 (3 ripetizioni) e da 12 (ripetizione 1), e altre ripetizioni solo se la regola di
  TBA-03 le chiede.
- Candidati fermi al cancello giudicati a parte (`judge-gated`).
- Un report solo con aggregati.

## Acceptance Criteria
- [x] Il lotto usa gli stessi seed, suite, modello, thinking, comando Pi e tetto per richiesta di
  `dbh`, verificati prima di partire.
- [x] Le copie del driver vengono da un checkout pulito con tutte le correzioni.
- [x] La regola di TBA-03 è applicata contro i bracci registrati di `dbh`.
- [x] Il report dice cosa cambia rispetto a DBH-09 e cosa resta, solo con aggregati.

## Outcome
2026-09-29. Il [report](../../research/delivery-bench-hard-drivers.md) ha i risultati. Il primo
lotto, `dbh-drivers`, è stato annullato dopo la catena da 4: aveva trovato un altro difetto del
driver (RTO-03, #396) e uno del runner (DBH-15, #395). Il lotto misurato è `dbh-drivers2`, con
driver e runner a `36aebf7`.
- c1a integra 32 run su 60 invece di 9, e accetta 1/36 alla catena da 4 e 3/36 alla catena
  da 12, contro 0 e 0.
- c3a si ferma al cancello in 28 run su 60, e resta a 0 accettate.
- La regola non chiede altre ripetizioni. Il vincitore resta `bare` alla catena da 12, e
  skills-only alla catena da 4.

## Frontier
Chiuso.

## Step-by-Step Implementation Plan
1. Autorità del lotto, `init-lot`, `prepare-drivers --source` e verifica dei legami con `dbh`.
2. `run-lot` fino a 4, poi fino a 12 per la ripetizione 1.
3. Regola di TBA-03 con `profile_report.py --arm-from`, poi `judge-gated`.
4. Report e mappa.

## Testing Plan
La verifica è la misura stessa: audit delle celle, ledger, regola e controllo dei legami.

## Out of Scope
- Un modello diverso o altri bracci.
- Modificare `dbh` o i suoi report, salvo un rimando alla rimisura.
- Nuove correzioni del driver durante il lotto.
