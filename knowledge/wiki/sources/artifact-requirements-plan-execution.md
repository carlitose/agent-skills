---
type: source
title: "Esecuzione da requisiti e piano, senza ticket intermedi"
identity_key: artifact:requirements-plan-execution
identity_strength: stable
source_path: docs/specs/requirements-plan-execution.md
source_digest: sha256:46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Esecuzione da requisiti e piano, senza ticket intermedi

Compiled from `docs/specs/requirements-plan-execution.md`. Identity is `artifact:requirements-plan-execution`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-requirements-plan-execution-plx-01]]
- Child source: [[sources/artifact-requirements-plan-execution-benchmark]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[10],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-requirements-plan-execution.md","payload_bytes":6039,"payload_sha256":"46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa"}],"payload_bytes":6039,"payload_sha256":"46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa","schema":1,"source_digest":"sha256:46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa","source_identity":"artifact:requirements-plan-execution","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 10: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6039,"payload_sha256":"46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa","schema":1,"source_digest":"sha256:46e1a905612d341851a9dfb7f9f2f388d2f0e934646694ffad9188247deccefa","source_identity":"artifact:requirements-plan-execution"} -->
```markdown
# Esecuzione da requisiti e piano, senza ticket intermedi

## Artifact Graph
- Artifact ID: `artifact:requirements-plan-execution`
- Role: `spec`
- Standalone: true

### Children
- [PLX-01 — Intake da piano e ciclo di qualità condiviso](../tickets/requirements-plan-execution/01-plan-intake.md)

### Produces
- [Benchmark del nuovo ingresso contro i bracci conservati](../research/requirements-plan-execution-benchmark.md)

## Type
Feature: accorciare l'ingresso nel ciclo di qualità skills-only, non ridurre i controlli.

## Goal and decisions
L'utente conferma «va bene» alla proposta: requisiti sufficienti -> un piano operativo ->
esecuzione con test, semplificazione, review e QA; spec per decisioni aperte e ticket per
consegne indipendenti. La scelta direct/skills-only esiste già: non aggiungere una quarta
corsia, un nuovo scheduler o una nuova skill per il medesimo ciclo di qualità.

Il lavoro viene sviluppato in checkout isolato. Nessuna installazione personale, benchmark,
commit, push, PR, merge o pubblicazione è autorizzata da questa conferma.

## Facts and current behavior
`ask-skills` e la policy iniettata impongono spec e ticket per tutto skills-only.
`execute-ticket` richiede envelope e CandidateRef anche quando il requisito originario
è già preciso. Review e QA ammettono già intake standalone da richiesta e diff.
L'analisi del lotto `spl-luna-1` suggerisce duplicazione documentale, ma non misura il
risparmio causale di questa modifica: non cambiare i risultati né promettere un guadagno.

## Target behavior
1. Skills-only accetta due ingressi nello stesso `execute-ticket`: ticket canonico, oppure
   requisiti e un piano per un unico incarico coeso senza decisioni materiali irrisolte.
   Il secondo ingresso non richiede spec, ticket, CandidateRef o Verification Record.
2. Il modello decide se l'intake è sufficiente in base a chiarezza dei requisiti, verificabilità
   e necessità di consegne indipendenti, non aggiungendo soglie di file/righe al percorso piano.
   Le soglie e le esclusioni della corsia direct restano invariate.
3. Riutilizzare richiesta/TASK.md/spec esistente come fonte. Un piano solo, nel contesto
   della sessione o in un documento esistente, contiene passi, criteri, scope, vincoli,
   verifiche e autorità/limiti applicabili. Non generare copie narrative o metadati fittizi.
4. Decisioni mancanti -> chiarimento/to-spec; consegne indipendenti, ticket esplicitamente
   richiesti o esistenti, runner e requisiti di Verification Record -> percorso canonico.
   Una spec sufficiente con una consegna sola non obbliga a produrre un ticket.
5. Entrambi gli ingressi usano lo stesso ciclo: baseline, criteri osservabili e test,
   implementazione, controlli ammessi, semplificazione dopo GREEN, review del diff congelato,
   QA con esiti distinti, ritorno alla fase interessata dopo difetti e handoff breve.
6. L'identità standalone è quella già usata da review/QA: checkout, base/head e manifest
   dei file modificati con hash, inclusi nuovi file. Il piano mantiene fonte e criteri.
   Cambi di requisiti o contenuto invalidano le prove pertinenti; non inventare ticket_digest.
7. Se serve un audit completo, promuovere esplicitamente gli input attraverso to-spec e
   to-tickets, senza relabeling delle prove precedenti. Nessuna modifica ai contratti macchina.

## Invariants and non-goals
- Stesse regole di test, review/QA, costo, sicurezza, autorità e claims; no bypass di gates.
- Un ticket canonico malformato o bloccato non diventa un piano per eludere il problema.
- Autopilot resta opt-in e una sospensione resta valida; no delegazione implicita.
- Nessun effetto Git/provider/installazione da execute-ticket; consegna separatamente autorizzata.
- Nessun claim di release/live/production/security attraverso il solo handoff da piano.
- Nessun cambio al benchmark, ai giudici, ai costi storici o alla configurazione Pi personale.
- Nessuna migrazione o compatibilità nuova: gli ingressi canonici esistenti restano invariati.

## Implementation slices
Un solo ticket end-to-end: aggiornare policy iniettata/router e istruzioni di esecuzione,
aggiungere un riferimento di intake da piano, chiarire l'identità standalone nei leaf,
allineare README e test di contratto/offline. Nessun nuovo algoritmo di classificazione:
la selezione semantica resta del modello e i test statici non pretendono di provarla live.

## Verification
- Prima dell'esecuzione: identità, scope, packaging/collegamenti e cost admission.
- Test Node mirati: policy prodotta, intake pubblicizzati, riferimenti presenti, esclusioni,
  qualità comune, gestione drift, promozione e preservazione delle altre corsie.
- Static: leggere scenari contrastanti (TASK chiaro, ambiguo, consegne separate, ticket
  bloccato, richiesta di audit, cambi dopo review). Non sono osservazioni di un modello live.
- Regressioni: profilo quick obbligatorio locale, file limits e Ruff applicabile.
- Esiti, errori e durate restano attribuiti alla versione realmente verificata. Nessuna
  ripetizione automatica del full o prova con modello; niente claim di risparmio misurato.

## Gates
- Attempt: implementazione locale fino all'handoff di PLX-01.
- Budget per attempt: nessun limite impostato; nessuna spesa modello/servizio autorizzata qui.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato.
- Approvals: «va bene» alla proposta di accorciare l'intake preservando il ciclo di qualità;
  modifiche locali e test offline autorizzati. Installazione, benchmark e delivery restano fuori scope.
- Exact version: nessuna versione di prodotto richiesta; base osservata `e9510a538cf37403ed89f9f5c4378750857b9bf7`.
- Existing blocks searched: policy/router, execute-ticket, leaf standalone, package/test-local,
  stato Git e remoto. Il checkout principale ha file estranei non tracciati: usare worktree
  isolato. Un precedente lotto riportava un fallimento quick CRLF; non trasferire quel
  risultato alla nuova versione né dichiararlo risolto senza osservazione.

```
