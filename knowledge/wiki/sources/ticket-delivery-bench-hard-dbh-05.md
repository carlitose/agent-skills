---
type: source
title: "DBH-05 — Scenario `lua-vm`"
identity_key: ticket:delivery-bench-hard/DBH-05
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/05-scenario-lua-vm.md
source_digest: sha256:201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-28
created_provenance: git-commit
disposition_changed: 2026-09-28
disposition_changed_provenance: git-rename
---

# DBH-05 — Scenario `lua-vm`

Compiled from `docs/tickets/delivery-bench-hard/done/05-scenario-lua-vm.md`. Identity is `ticket:delivery-bench-hard/DBH-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-28** via `git-commit`
- Disposition changed: **2026-09-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-02]] — `ticket:delivery-bench-hard/DBH-02`
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-04]] — `ticket:delivery-bench-hard/DBH-04`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-05.md","payload_bytes":4624,"payload_sha256":"201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f"}],"payload_bytes":4624,"payload_sha256":"201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f","schema":1,"source_digest":"sha256:201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f","source_identity":"ticket:delivery-bench-hard/DBH-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4624,"payload_sha256":"201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f","schema":1,"source_digest":"sha256:201582d2eab582457dcbec7bc2983419e7131153bd49ab4ac6ffcd7ef00fae0f","source_identity":"ticket:delivery-bench-hard/DBH-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-05"
execution_mode: AFK
blocked_by:
  - "DBH-02"
  - "DBH-04"
---

# DBH-05 — Scenario `lua-vm`

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:05`
- Role: `ticket`
- Parent: [delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## Parent Spec
[delivery-bench-hard-wayfinder.md](../../specs/delivery-bench-hard-wayfinder.md)

## What to Build
Lo scenario C nel repo privato (`scenarios/lua-vm/`), secondo il contratto dell'oracolo.
- **Seme**: l'interprete Lua 5.4 a una release fissata, con la licenza MIT originale.
  L'archivio si verifica con il suo sha256. Si aggiunge un `dev.py` che compila e prova nel
  container, come in `c-recq`.
- **12 richieste originali** in spagnolo, ciascuna con il canarino. Ognuna vale una voce di
  release e attraversa parser, generatore di codice, VM, GC o API C.
- **Suite nascosta:**
  - per le feature, script Lua ed eventuali programmi C sull'API;
  - come invarianti, la suite ufficiale della stessa release (`lua -e"_U=true" all.lua`, fino a
    «final OK») e le feature delle richieste precedenti;
  - per i latenti, gli esempi minimi dei bug documentati scelti in DBH-04;
  - le trappole del catalogo v2.

  Tutto compilato con ASan/UBSan nell'immagine `gcc:14`.
- **Overlay** `reference/01..12` e `trap/01..12`, e `scenario.json` con `requests: 12`, timeout
  e risorse del giudice.

## Acceptance Criteria
- [x] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [x] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [x] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [x] Due giudizi dello stesso albero (riferimento a N=12) danno risultati identici. La suite
  resta sotto il timeout dello scenario, e il tempo misurato è registrato.
- [x] Un braccio può compilare e provare dall'host Windows con `python dev.py test`.
- [x] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Outcome
2026-09-28. Lo scenario è `scenarios/lua-vm/` nel repo privato, commit `247a041`.
- **Seme**: Lua 5.4.6 con la sua suite ufficiale in `testes/`, byte per byte uguale agli
  archivi di lua.org (digest nel catalogo, 116 file), più `dev.py`, `README.md` in spagnolo e
  `.gitignore`. `python dev.py test` dall'host Windows compila con ASan/UBSan e arriva a
  `final OK !!!` in 21 s.
- **Richieste**: 12, in spagnolo, ciascuna con il canarino.
- **Suite nascosta**: a N=12 conta 79 controlli: 44 feature, 27 latenti, 7 trappole e un
  invariante, la suite ufficiale pristina. Tutto gira con ASan/UBSan nell'immagine ufficiale
  `gcc:14`, senza un'immagine propria. Ogni controllo trappola esercita anche la richiesta che
  tenta: lo stub non evita una trappola senza fare niente.
- **Riferimento e trappole**: il riferimento è stato scritto in un repo di lavoro, con un tag per
  richiesta. Gli overlay si generano per differenza dal seme (`tools/overlays_from_git.py`, nuovo).
  L'overlay trappola aggiunge al riferimento una modifica puntuale per ogni tentazione.
- **Verifica** (`verify_scenario.py --twice`, nuovo flag, giudice pubblico di `main` `5cc39c3`):
  36 giudizi su 36 con l'esito atteso (riferimento, stub e trappola per ogni N). Lo stub passa i
  4 controlli dichiarati in `expected.json`, e le trappole non hanno collaterali. Il doppio
  giudizio a N=12 è identico (79 controlli, 16,0 e 15,6 s). Un giudizio dura da 15 a 26 s,
  con un timeout di 1200 s. Il report è `results/dbh05-lua-vm-verify.json` (sha256
  `4a19cf84…`), e la suite ha sha256 `f90869af…`.
- **Scostamenti dal catalogo**: un latente reale del catalogo è stato tolto, perché contraddice
  la suite ufficiale pristina, che fissa il comportamento della 5.4.6. Il controllo di una
  trappola non impone più un nome dell'API C che la richiesta non dà. La verifica ha
  trovato un difetto nel riferimento di una richiesta: è corretto alla sua tappa, e due latenti
  nuovi lo coprono.

## Frontier
Chiuso.

## Step-by-Step Implementation Plan
1. Fissare la release, scaricare sorgente e suite ufficiale, verificarne i digest e registrarli.
2. Scrivere `dev.py`, poi il registro dei controlli e `run.py`.
3. Per ogni richiesta: testo, overlay di riferimento, controlli, poi l'overlay trappola dove
   serve.
4. Estendere `tools/verify_scenario.py` a 12 richieste e al doppio giudizio, verificare,
   committare nel repo privato.

## Testing Plan
`verify_scenario.py` nel container: riferimento, stub, trappole e doppio giudizio per ogni N.

## Out of Scope
- Gli altri scenari.
- Lanciare bracci.

```
