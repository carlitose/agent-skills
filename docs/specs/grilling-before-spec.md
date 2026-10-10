# Grilling prima della spec quando mancano requisiti

## Artifact Graph
- Artifact ID: `artifact:grilling-before-spec`
- Role: `spec`
- Standalone: true

### Children
- [GBS-01](../tickets/grilling-before-spec/01-route-open-requirements.md)

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
