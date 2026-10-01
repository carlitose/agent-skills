---
ticket_schema: 1
ticket_id: "SPJ-03"
execution_mode: HITL
blocked_by:
  - "SPJ-02"
---

# SPJ-03 — Confermare il contratto della review nel contesto condiviso

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spj-03`
- Role: `ticket`
- Parent: [Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md)

## Parent Spec
[Solo Pi + Jev](../../specs/solo-pi-jev-wayfinder.md): Decisions So Far, Current Evidence, Not Yet Specified 3.

## Question / Outcome
Che cosa significa review diretta se builder e reviewer sono turni dello stesso Pi? Confermare ruolo, scritture, lettura dei findings e claims di qualità senza chiamare indipendente una review condivisa.

## Evidence
Partire da `risk.py` (`directed_review`), `driver.py` (`risk_phase`, `_record_candidate`) e `findings.py`. Oggi il revisore ha un contesto fresco e una scratch distinta, con controllo delle scritture e del candidato. Leggere l'esito e la prova di conferma di SPJ-02; l'emissione del ticket non ne completa la dipendenza.

## Produces
Decisione confermata tramite `to-spec` in `docs/specs/solo-pi-jev-review-decision.md`, Artifact ID `artifact:solo-pi-jev-review-decision`, Role `spec`, Parent a questo ticket e link Children reciproco qui, aggiunti alla creazione. Aggiornamento della relativa edge nella mappa; nessun risultato preesistente.

## Acceptance Criteria
- [ ] Dipendenza SPJ-02 verificata su decisione e conferma attribuibili, non su una checkbox o un piano.
- [ ] Invocata `grilling`, una domanda per volta, e ottenuta conferma reale: mantenere, modificare o omettere il turno di review, con garanzie perse dichiarate.
- [ ] Distinti cambio di ruolo, separazione delle scritture e indipendenza del contesto; il solo prompt di reviewer, una scratch o Jev non rendono indipendente il giudizio dello stesso Pi.
- [ ] Specificati quando fare review, input per funzione, formato/lettura dei findings, owner del giudizio, blocker/retry/stop e scritture permesse. Eventuali modifiche al prodotto richiedono nuovo candidato e rivalutazione delle evidenze interessate.
- [ ] Spec tramite `to-spec` con prova della conferma e conseguenze rispetto al contratto storico; grafo reciproco e mappa aggiornati senza implementare o risolvere SPJ-04 per inferenza.

## Frontier
Dependency-blocked da SPJ-02 e HITL per una scelta umana. Il risultato non è «indipendente» e il ticket resta aperto se la conferma manca. Una variazione materiale della destinazione richiede il destination gate Wayfinder prima di modifiche durevoli.

## Step-by-Step Implementation Plan
1. Verificare SPJ-02, leggere i confini attuali e la skill `grilling`.
2. Intervistare su ruolo, indipendenza e mutazioni; confrontare claims ammessi e garanzie perse. Completion criterion: contratto e compromessi confermati realmente, o edge ancora aperta.
3. Salvare la decisione attraverso `to-spec`, collegare i grafi e rimuovere solo l'unknown risolta dalla mappa.

## Testing Plan
Walkthrough di findings puliti, blocker, formato non leggibile e review che cambia l'albero; verificare quali evidenze decadono e che nessuno stato finga indipendenza. Controlli documentali e di grafo, senza provider o benchmark.

## Out of Scope
Policy Jev nuova, worktree/test/integrazione definitivi, implementazione, nuovo revisore Pi, chiamate live, lotti storici, CLI/scheduler Autopilot, delivery/wiki impliciti. Consegna skills-only inline; nessuna delega.
