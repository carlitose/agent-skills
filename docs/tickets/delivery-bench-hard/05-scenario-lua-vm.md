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
- [ ] Per ogni N da 1 a 12, il riferimento passa ogni controllo con `request <= N`.
- [ ] Il seme senza modifiche fallisce esattamente le feature e i latenti attesi.
- [ ] L'overlay trappola viola ciascuna trappola alla sua tentazione, con la distanza del
  catalogo.
- [ ] Due giudizi dello stesso albero (riferimento a N=12) danno risultati identici. La suite
  resta sotto il timeout dello scenario, e il tempo misurato è registrato.
- [ ] Un braccio può compilare e provare dall'host Windows con `python dev.py test`.
- [ ] Nel repo pubblico ci sono solo digest e conteggi aggregati.

## Frontier
Bloccato da DBH-02 (N richieste, risorse del giudice) e da DBH-04 (catalogo approvato).

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
