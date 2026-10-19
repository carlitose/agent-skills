---
type: source
title: "Grilling prima della spec quando mancano requisiti"
identity_key: artifact:grilling-before-spec
identity_strength: stable
source_path: docs/specs/grilling-before-spec.md
source_digest: sha256:07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-10
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Grilling prima della spec quando mancano requisiti

Compiled from `docs/specs/grilling-before-spec.md`. Identity is `artifact:grilling-before-spec`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-10** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-grilling-before-spec-gbs-01]]
- Child source: [[sources/ticket-grilling-before-spec-gbs-02]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[5],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-grilling-before-spec.md","payload_bytes":3543,"payload_sha256":"07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee"}],"payload_bytes":3543,"payload_sha256":"07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee","schema":1,"source_digest":"sha256:07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee","source_identity":"artifact:grilling-before-spec","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 8: Non-goals |
| decisions | 5: Decision |
| invariants | no matching section identified in the source; complete source retained |
| verification | 9: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3543,"payload_sha256":"07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee","schema":1,"source_digest":"sha256:07cabbef751dcba95ede46107a21e0270330ceeb7e85300e98925f3bbd6307ee","source_identity":"artifact:grilling-before-spec"} -->
```markdown
# Grilling prima della spec quando mancano requisiti

## Artifact Graph
- Artifact ID: `artifact:grilling-before-spec`
- Role: `spec`
- Standalone: true

### Children
- [GBS-01](../tickets/grilling-before-spec/done/01-route-open-requirements.md)
- [GBS-02](../tickets/grilling-before-spec/done/02-concrete-trigger.md)

## Type
Decision.

## Problem
Nel lotto `dbh-vague` (DBH-39) le richieste corte lasciano aperti requisiti che i test nascosti
controllano. pi-full va da `ask-skills` a `to-spec` in 6 sessioni su 6 e scrive la spec senza
chiedere quei dettagli. Le sue 37 domande sono quasi tutte sul processo (28 su gate e tentativi,
prima di GQ-01) e nessuna sui requisiti che mancano. Risultato: 5/36 accettate, contro 29/36 con le
richieste precise; la richiesta 4 è 0/9 in tutti i bracci.

## Decision
Utente, 2026-10-10: «non dovrebbe far partire wayfinder ma il grilling prima di to-spec». Tra
grilling prima di `to-spec` (A) e poche domande dentro `to-spec` (B) ha scelto **A**.
- `ask-skills`: una richiesta con requisiti aperti che cambierebbero il risultato o i suoi test,
  quando qualcuno può rispondere, va per `grilling -> to-spec`. Una richiesta completa va dritta a
  `to-spec`, come prima.
- `grilling`, nuova sezione *Before a spec*:
  - domande solo sui requisiti, mai su processo, gate, tentativi, budget o strumenti;
  - nessuna domanda su ciò che richiesta, repository o documenti dicono già, né su ciò che non
    cambierebbe codice o test;
  - si chiede col canale che la sessione offre; senza risposta vale la risposta raccomandata,
    segnata come assunzione;
  - ci si ferma quando nessun requisito aperto cambierebbe il risultato; le risposte dell'ultimo
    giro valgono come conferma, senza un giro a parte.
- Wayfinder no: il lavoro è chiaro, mancano solo decisioni dell'utente.

## Correzione (GBS-02, 2026-10-10)
La prima versione non scattava. Nel lotto `dbh-vague2` (annullato dopo 30 minuti) pi-full in 5 sessioni
su 5 è andato dritto a `to-spec`: ha giudicato da solo che i requisiti non erano aperti («la
semantica naturale… senza decisione umana in sospeso») e ha fatto 1 domanda in tutto. La condizione
diventa concreta: se si può chiedere all'utente e la richiesta non dice il comportamento esatto, si
passa per `grilling`; una lettura «naturale» è un'ipotesi, non un requisito. Scelta dell'utente: «2»
(fermare il lotto, correggere, rilanciare).

## Misura (dbh-vague3)
pi-full sulle richieste vaghe: **12/36** accettate (prima 5/36), richiesta 4 da 0/9 a 3/9, `grilling` in 9
celle su 9, domande solo sui requisiti. Costo e tempo quasi uguali (8.05 $ contro 7.35 $). Le
richieste precise fanno 29/36: il divario resta grande.

## Non-goals
- Cambiare `to-spec`, i gate (GQ-01) o i bracci del benchmark.

## Verification
- Test in `ticket-autopilot/tests/test_skill_graph.py` sulla rotta e sulla sezione; CI.
- Misura (fuori da questa consegna, solo quando l'utente lo dice): rifare `dbh-vague` per pi-full
  con le skill installate e confrontare accettate e tipo di domande.

## Gates
- **Attempt:** il lavoro fino alla merge e all'installazione. **Budget, tempo, tentativi:** nessuno
  fissato.
- **Approvals:** merge con CI verde da parte dell'agente; pin in `pi-personal-config`,
  `update:personal` e reload (regola di sincronizzazione dopo ogni passo integrato). Nessun lotto.
- **Exact version:** nessuna.
- **Existing blocks:** nessun lotto in corso. `ask-skills/SKILL.md` è al limite di 94 righe di
  `scripts/check_file_limits.py`: la modifica resta entro il limite.

```
