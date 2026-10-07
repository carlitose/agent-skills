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
- Parent: [delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md)

## Parent Spec
[delivery-bench-hard-vague-requests.md](../../specs/delivery-bench-hard-vague-requests.md), Target behavior 1 e Failure modes.

## What to Build
Le versioni vaghe delle richieste 1–4 di `lua-vm`, `sql-engine` e `crdt-yjs`, nel repo privato
accanto alle richieste precise (`requests-vague/NN.md`): 2–5 frasi in spagnolo, con l'obiettivo
e senza i dettagli, come le scriverebbe l'utente. Le precise restano il brief del simulato.

## Acceptance Criteria
- [ ] 12 file, uno per scenario e richiesta, ciascuno di 2–5 frasi e senza messaggi d'errore
      esatti, nomi di test o canary.
- [ ] Ogni versione vaga chiede la stessa cosa della precisa: nessun obiettivo nuovo o mancante.
- [ ] L'utente ha approvato le 12 versioni, con le sue correzioni.

## Frontier
Pronto.

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
