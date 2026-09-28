---
ticket_schema: 1
ticket_id: "DBH-12"
execution_mode: AFK
blocked_by:
  - "DBH-02"
---

# DBH-12 — Un file con nome di dispositivo nell'istantanea di una cella

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:12`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Un difetto del runner trovato durante la misura completa (DBH-09). Prima di ogni richiesta il
runner copia la cartella del braccio in un'istantanea, e la rimette al suo posto dopo un guasto
d'infrastruttura.
- **Osservato**: in una cella di un driver, un builder ha rediretto l'output di una build su
  `NUL` da una shell POSIX. Nel worktree del driver è rimasto un file chiamato `NUL`.
  All'istantanea della richiesta 3 la copia fallisce con `WinError 87`, e la catena si ferma
  alla richiesta 2 con un errore di cella. Le altre celle vanno avanti.
- **Causa**: su Windows `NUL`, `CON`, `AUX` e simili sono nomi di dispositivo. Con i percorsi
  normali la copia e la cancellazione non raggiungono un file con quel nome. Lo raggiungono solo
  i percorsi estesi (`\\?\`). `snapshot`, `restore` e `rmtree` usavano i percorsi normali.

Il comportamento atteso: l'istantanea e il ripristino copiano e cancellano anche un file con
nome di dispositivo, e la catena prosegue.

## Acceptance Criteria
- [x] Un test fa lasciare al braccio finto un file `NUL` nel progetto e nel worktree del driver,
  poi fa cadere la richiesta successiva. Prima della correzione fallisce con lo stesso
  `WinError 87` della misura.
- [x] Dopo la correzione la richiesta è ripetuta e accettata, i residui del tentativo caduto
  spariscono, e i due file `NUL` ci sono ancora, con il loro contenuto.
- [x] Fuori da Windows i percorsi non cambiano.

## Outcome
2026-09-28. Il test nuovo di `test_runner.py` fallisce prima della correzione con `WinError 87`
sull'istantanea, come nella misura. Dopo la correzione passa, insieme agli altri test di
`test_runner.py`, `test_judge.py` e `test_profile_report.py` (51, 2 saltati).
- `native_path` dà la forma estesa di un percorso su Windows, in modo lessicale. `abspath`
  trasformerebbe un percorso che finisce in `NUL` nel dispositivo `\\.\NUL`. Fuori da Windows
  resta `abspath`.
- `snapshot`, `restore` e `rmtree` usano quella forma.
- I record salvati non cambiano.

**Correzione.** Questo ticket dichiarava che la cella ferma sarebbe ripartita dalla richiesta
3 al `run-lot` successivo, ma nessun test lo provava. Non è successo: il task della richiesta
era già stato registrato con un commit, e il secondo commit falliva. Il difetto è corretto in
[DBH-13](13-resume-after-task-delivery.md).

## Frontier
Chiuso. Le celle ferme riprendono dopo DBH-13.

## Step-by-Step Implementation Plan
1. Test RED in `test_runner.py`: un braccio finto che lascia un file `NUL`, poi un guasto.
2. `native_path` e percorsi estesi in `snapshot`, `restore` e `rmtree`.

## Testing Plan
Test offline di `test_runner.py` con il braccio finto. Poi la ripresa vera della cella nel lotto
`dbh`.

## Out of Scope
- Impedire ai bracci di creare file con nomi di dispositivo.
- Il giudice: il file stava fuori dal progetto giudicato.
- Riscrivere i record già salvati.
