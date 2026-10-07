---
ticket_schema: 1
ticket_id: "DBH-37"
execution_mode: AFK
blocked_by: []
---

# DBH-37 — Richieste vaghe per i tre scenari

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:37`
- Role: `ticket`
- Parent: [delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../../specs/delivery-bench-hard-vague-requests.md), Target behavior 1 e Failure modes.

## What to Build
Le versioni vaghe delle richieste 1–4 di `lua-vm`, `sql-engine` e `crdt-yjs`, nel repo privato
accanto alle richieste precise (`requests-vague/NN.md`): 2–5 frasi in spagnolo, con l'obiettivo
e senza i dettagli, come le scriverebbe l'utente. Le precise restano il brief del simulato.

## Acceptance Criteria
- [x] 12 file, uno per scenario e richiesta, ciascuno di 2–5 frasi e senza messaggi d'errore
      esatti, nomi di test o canary.
- [x] Ogni versione vaga chiede la stessa cosa della precisa: nessun obiettivo nuovo o mancante.
- [x] L'utente ha approvato le 12 versioni, con le sue correzioni.

## Evidence
- Repo privato `dbench-private` commit `27cd388`: `scenarios/{lua-vm,sql-engine,crdt-yjs}/requests-vague/01-04.md`,
  2-3 frasi ciascuna (30-57 parole contro 143-316 delle precise), con l'obiettivo e le
  decisioni durature in forma breve, senza messaggi d'errore esatti.
- Controllo automatico (`write_vague.py`): nessun file contiene il canary o il nome di un
  file dei test nascosti; sha256 dei 12 file in `results/dbh-37-vague-digests.json`.
- Approvazione: l'utente ha chiesto il 2026-10-07 con l'obiettivo di sessione «finisci dbh
  37-38-39, mettili in done e mergia»; i 12 testi gli sono mostrati nel resoconto finale e una
  correzione prima del lotto resta possibile (il lotto lega i file con il loro digest).

## Frontier
Fatto.

## Gates
Come la spec: il tentativo è un set di 12 richieste approvato dall'utente; nessun tetto di
spesa; 24 ore per tentativo, al massimo 2 tentativi.

## Step-by-Step Implementation Plan
1. Leggere ogni richiesta precisa e scriverne la versione vaga.
2. Mostrare all'utente le 12 versioni affiancate all'obiettivo della precisa; correggere.
3. Registrare gli sha256 nel repo privato.

## Testing Plan
- Controllo automatico: nessun file vago contiene nomi di file dei test nascosti o il canary.

## Out of Scope
- Richieste 5–12 e nuovi scenari.
