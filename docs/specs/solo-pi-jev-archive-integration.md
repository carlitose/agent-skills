# Integrazione dell'archivio solo Pi + Jev senza cambiare il comportamento distribuito

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-archive-integration`
- Role: `spec`
- Standalone: true

### Children
- [LIN-01: integrare l'archivio pi-lec03 a comportamento invariato](../tickets/solo-pi-jev-archive-integration/01-integrate-lec03-archive.md)

## Type and Status
Feature/decision spec. Decisione umana del 2026-10-05: «porta tutto ma fai le modifiche
perché funzioni come adesso». Lane skills-only; nessun runner, benchmark, installazione o
reload.

## Context (fatti)
- I worktree `C:/pi-spj-01`, `C:/pi-spb01`, `C:/pi-lec01..03` contenevano lavoro mai
  committato, archiviato sui branch locali `archive/wt-*`. La catena è cumulativa:
  `archive/wt-pi-lec03` contiene, a contenuto identico, `spb01`, `lec01` e `lec02`, e la
  versione più recente dei file di `spj-01`. Base: `origin/main` `001d362`.
- Contenuto: 54 file di documentazione (ricerca Luna, spec e ticket SPJ/SPB/LEC, stato del
  Wayfinder SPJ) e 27 file di codice (arm di `benchmarks/delivery-bench`, script e test
  della catena in `ticket-driver`).
- Solo due file già distribuiti cambiano comportamento:
  - `ticket-driver/scripts/findings.py`: la regex `PATH` accetta qualunque estensione
    invece del solo `.py`; la usano `driver.py` e `c1b.py`.
  - `ticket-driver/questions/review.scope_complete.json`: nuovo testo della domanda.
    `arbiter.questions()` carica tutti i `questions/*.json` e `approval.py` confronta i
    loro hash con quelli registrati: anche un file aggiunto in quella cartella cambia il
    comportamento.
- Non si caricano nuove risorse Pi: `package.json` registra solo `./*/SKILL.md` e
  `./extensions/mandatory-agent-skills.ts`, quindi `ticket-driver/skills/behavior-first`
  e `ticket-driver/extensions/chain-judge.ts` restano file inerti per il pacchetto.

## Decision
Integrare tutto l'archivio, con due adattamenti che preservano il comportamento attuale:

1. `findings.py` mantiene `PATH` (solo `.py`) come default. Il riconoscimento di qualunque
   estensione diventa opt-in con `parse_findings(..., any_extension=True)`; solo
   `chain_controller.py` e i suoi test lo attivano.
2. `ticket-driver/questions/review.scope_complete.json` resta byte per byte quello di
   `main`. La variante "adjudicated" vive in
   `benchmarks/delivery-bench/questions/review.scope_complete.json`, fuori dal glob
   dell'arbiter. È la versione con cui hanno girato SPB/LEC (sha256 `1ee1bfea…`).
3. Completare il lavoro LEC v3 rimasto a metà: `test_staged_behavior` falliva (2 errori)
   perché `_CoverageFeedback` non esponeva `path` e `bind_session` perdeva l'involucro di
   osservazione della copertura dopo il cambio di sessione. Si correggono entrambi nel
   codice nuovo, senza toccare quello distribuito.

## Invariants
- `driver.py`, `c1b.py`, `cascade.py`, `approval.py` e `arbiter.questions()` producono gli
  stessi risultati e gli stessi hash di `main`.
- I test esistenti di `ticket-driver` passano senza modifiche.
- Nessuna nuova skill o estensione caricata da Pi.

## Consequences
- Un rilancio dei benchmark LEC deve passare la domanda da
  `benchmarks/delivery-bench/questions/` come `coverage_question`; il launcher esterno in
  `C:/dbench` legge ancora il percorso distribuito e va aggiornato fuori dal repository.
- I verdetti di ricerca restano quelli dei report: LEC-01 «non promuovere». Integrare non
  promuove il candidato a motore skills-only.

## Non-goals
- Chiudere o spostare in `done/` i ticket SPB/LEC importati: restano nello stato registrato.
- Cambiare il driver distribuito, il pin installato o rilanciare benchmark.

## Verification
Test unitari: tutta la suite `ticket-driver/tests` e i test nuovi di
`benchmarks/delivery-bench`; un test di regressione fissa il default `.py` e l'hash delle
domande. Lint del repository. CI del PR come gate di integrazione.
