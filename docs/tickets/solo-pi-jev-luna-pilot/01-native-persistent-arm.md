---
ticket_schema: 1
ticket_id: "SPB-01"
execution_mode: AFK
blocked_by: []
---

# SPB-01 — Braccio persistente del benchmark e prova nativa Luna

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-01`
- Role: `ticket`
- Parent: [Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md)

## Parent Spec
[Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md): ingress/scope, persistent arm, budget,
observation e prova nativa. SPC-01/02/03 implementation-complete locali sono input validati.

## What to Build
Adapter di una cella esplicita per il benchmark che compone i moduli SPC, senza scheduler
né delivery. Nuova fonte/copia, prompt roles comprensibili, ticket canonici, directory
posseduta esplicitamente ammessa, reasoning judge medium esplicito, facts/costi/budget/gate.
Dopo RED/GREEN e verifica locale, provare trasporto/modello/Jev/judge reali nel mandato nuovo.

## Acceptance Criteria
- [ ] Ingress e mandato canonici/freschi, fonte e ambiente legati; due destinatari distinti, budget cumulativo EUR/USD e tentativi preservati; dato mancante non zero.
- [ ] Una cella/una sessione Pi lungo ticket/ruoli, nessun driver delivery/scheduler/folder selection; argv/model/thinking espliciti e Jev key esclusa dal child.
- [ ] Scope-directory solo su copia posseduta: nuove sorgenti/test nel root ammesso, mai path assoluti/parent/.git; regressione dei caller scope-file preservata.
- [ ] Nuovo contesto judge senza tools/transcript e reasoning medium vincolato in request/receipt; canonical Answer parser e stop/gate/usage restano invariati.
- [ ] Snapshot/prove/costo ad owner del benchmark, oracle separato non visibile al modello; fallito/gated non consegnato, tre fallimenti cumulativi, nessuna autoapprovazione.
- [ ] Prova nativa separata: due richieste sullo stesso pid/sessione più risposta Jev e judge attribuibili, backend/auth reali o gate esatto; non chiamare fake una prova live né viceversa.

## Frontier
Ready per adattatore locale: handoff SPC-03 e nuovo mandato umano disponibili. Avvio nativo
richiede binding di fonte/argv/model/ambiente/pricing/riserva e ammissione verificata, non merge.

## Step-by-Step Implementation Plan
1. Validare envelope/spec/grafo/base e tutti gli input/costi; ammettere scope di fonte controllato.
2. Fixture RED per directory-scope, reasoning, authority/usage/session/snapshot; implementare il solo adapter di cella e seams strettamente necessari.
3. Cleanup GREEN, review condivisa read-only, QA causale e record canonico; mantenere gate di release.
4. Congelare candidata/record privato del mandato, controllare binding e lanciare prova nativa limitata; conservare ogni launch/errore/spesa e stop su incertezza non riconciliata.

## Testing Plan
Test unit/simulated su adapter/authority/accounting e regressioni causali SPC; backend/peer fake
restano simulate. Prova nativa dopo gate locali sotto budget 1.000 EUR complessivo del lotto,
riserva e limiti finiti, modello già configurato, niente provider alternativo. No full profile
automatico né hosted CI prima di un PR non autorizzato.

## Out of Scope
Pilota L4 (SPB-02), L12, copie/risultati storici, ripartenza Sonnet, altre soglie/modelli,
runner/scheduler per implementare SPB, worker/delega, merge/PR/push, install/reload e GC.
