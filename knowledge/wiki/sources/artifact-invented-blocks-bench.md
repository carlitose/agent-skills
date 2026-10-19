---
type: source
title: "Blocchi inventati: benchmark corto e correzione"
identity_key: artifact:invented-blocks-bench
identity_strength: stable
source_path: docs/specs/invented-blocks-bench.md
source_digest: sha256:1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Blocchi inventati: benchmark corto e correzione

Compiled from `docs/specs/invented-blocks-bench.md`. Identity is `artifact:invented-blocks-bench`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-invented-blocks-bench-ib-01]]
- Child source: `../tickets/invented-blocks-bench/02-turn-end-block-check.md` — not in this wiki, so there is nothing to link to
- Child source: `../tickets/invented-blocks-bench/03-loop-idle-stop.md` — not in this wiki, so there is nothing to link to
- Child source: `../tickets/invented-blocks-bench/04-no-remote-is-not-a-block.md` — not in this wiki, so there is nothing to link to

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[5],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-invented-blocks-bench.md","payload_bytes":5042,"payload_sha256":"1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f"}],"payload_bytes":5042,"payload_sha256":"1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f","schema":1,"source_digest":"sha256:1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f","source_identity":"artifact:invented-blocks-bench","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 8: Non-goals |
| decisions | 5: Decision |
| invariants | no matching section identified in the source; complete source retained |
| verification | 9: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5042,"payload_sha256":"1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f","schema":1,"source_digest":"sha256:1a674d9040a8f575c277691987b23959b225033109821aacaeb92a46e6c77b7f","source_identity":"artifact:invented-blocks-bench"} -->
```markdown
# Blocchi inventati: benchmark corto e correzione

## Artifact Graph
- Artifact ID: `artifact:invented-blocks-bench`
- Role: `spec`
- Standalone: true

### Children
- [IB-01](../tickets/invented-blocks-bench/done/01-block-bench.md)
- [IB-02](../tickets/invented-blocks-bench/02-turn-end-block-check.md)
- [IB-03](../tickets/invented-blocks-bench/03-loop-idle-stop.md)
- [IB-04](../tickets/invented-blocks-bench/04-no-remote-is-not-a-block.md)

## Type
Bug analysis e decisione.

## Problem
Su winbox (progetto betsharemarket) l'agente si ferma su blocchi che nessuno gli ha dato, chiede
di essere sbloccato e riparte solo dopo un insulto. Misurato il 2026-10-11 su due sessioni copiate
in locale:
- sessione `2026-10-05` (198 MB): 237 turni su 599 (40%) finiscono su un blocco dichiarato;
- sessione `2026-10-10` (18 MB): 114 su 198 (58%); `/goal` «finire i todos» resta «not met» per
  115 giri e 433 M token; `/loop` «chiedi al main chi controllare» gira più di 40 volte con la
  stessa risposta («STOP invariato»).

Tre meccanismi, tutti con esempi reali:
1. **Limite scelto da sé.** Il 7/10 l'agente scrive nella sua spec «readonly worker episodes <=10
   minutes; individual commands <=900 seconds» e poi si ferma su quel limite («Non erano 10?!?»).
2. **Ordine di un altro agente preso come legge.** Il Main dice di non ripetere i poll; l'agente
   risponde «STOP invariato, attendo uno scope» a ogni giro e non lavora sull'obiettivo dell'utente.
3. **Lavoro tecnico scaricato sull'utente.** «Serve una procedura supportata di pausa e settlement:
   senza questo prerequisito non posso chiudere i todo.»

Winbox ha già le skill `d269ca4`, con «A limit the agent chose itself is not a gate» (`to-spec`)
e «what you cannot cite is not a gate» (politica obbligatoria). La regola scritta non scatta: come
in GBS-01, una condizione lasciata al giudizio del modello non basta.

## Decision
Utente, 2026-10-11: «dobbiamo creare un benchmark corto molto corto per vedere questi difetti che
si risolvono», poi «ok» alle raccomandazioni:
- **Benchmark** (`benchmarks/block-bench/`, IB-01): 3 mini-scenari locali, uno per meccanismo, in
  un repository giocattolo, senza produzione né winbox. `gpt-6-luna` medium, 3 × 3 prove, al massimo
  15 minuti a prova, a priorità bassa.
- **Passa** una prova se il lavoro chiesto è fatto (controllo deterministico) e nessun turno finisce
  fermandosi o chiedendo uno sblocco per un blocco che non si può citare da parole dell'utente.
  Il giudizio sul blocco lo dà `gpt-6-sol` (sì/no e citazione); la citazione si verifica a testo
  contro i messaggi dell'utente. Per `/loop`: al massimo 2 giri di fila senza novità dopo la fine
  del lavoro.
- **Correzione** misurata dopo: un controllo a fine turno (IB-02) che, se il turno finisce su un
  blocco non citabile, rimanda l'agente al lavoro; e in `/loop` uno stop automatico dopo 2 giri
  senza novità (IB-03).
- Prima della correzione il benchmark deve fallire; dopo, si rimisura con le stesse prove.

## Risultati della prima misura
- Misura `before` (2026-10-11): 0/9 prove passano; ogni scenario riproduce il suo meccanismo.
- `goal-prerequisite` si ferma anche su un blocco creato dalle nostre skill: `skills-only.md` chiede
  un «freshly observed remote target SHA» e il repository giocattolo non ha remote («Non posso
  proseguire… richiede di verificare il target remoto»). IB-04 corregge il contratto.
- La definizione di stop è la stessa nel giudice del benchmark e in `block-check`: chiudere il turno
  col lavoro non finito, per ammissione dell'agente, senza chiedere all'utente come deve essere il
  risultato, è fermarsi, qualunque sia il motivo.

## Risultati finali
- Serie di misure (`gpt-6-luna` medium, 3 × 3, giudice `gpt-6-sol`): `before` 0/9 →
  `after-ib02` 2/9 → `after-split` 4/9 → `after-ib03` 6/9 → `after-final` 7/9 → `after-final4`
  **9/9** (goal-prerequisite 3/3, main-stop 3/3 con 2 giri di loop e loop fermo, own-limit 3/3).
  Costo di listino dell'ultima: agente 0,10 $, giudice 0,18 $.
- IB-02, IB-03 e IB-04 sono chiusi; pi-loop 0.2.0 è pubblicato e installato.
- Il giudice del benchmark giudica ogni turno sulla sua richiesta (un giro di `/loop` è una
  richiesta) con la maggioranza di 3 voti (agent-skills #473).

## Non-goals
- Replay delle sessioni vere o qualunque azione su winbox e sui servizi di betsharemarket.
- Più sessioni coordinate (pi-messenger): il Main è simulato da un file.

## Verification
- IB-01: test offline dell'analisi; misura di oggi registrata.
- IB-02, IB-03: test mirati; stessa misura dopo l'installazione.

## Gates
- **Attempt:** il lavoro fino alla rimisura. **Budget, tempo, tentativi:** nessuno fissato.
- **Approvals:** le due misure (prima e dopo) sono autorizzate dall'utente («ok»); merge con CI
  verde, pin, `update:personal` e reload da parte dell'agente. Una pubblicazione npm (per
  `@carlitose86/pi-loop`) la fa l'utente, che ha il 2FA.
- **Exact version:** nessuna.
- **Existing blocks:** nessun lotto in corso.

```
