---
ticket_schema: 1
ticket_id: "SPB-03"
execution_mode: AFK
blocked_by:
  - "SPB-02"
---

# SPB-03 — Riparare i confini di osservazione dopo il pilota Luna

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-03`
- Role: `ticket`
- Parent: [Pilota Luna e riparazioni](../../specs/solo-pi-jev-luna-pilot.md)

## Parent Spec
[Pilota Luna](../../specs/solo-pi-jev-luna-pilot.md): Post-pilot Repairs — SPB-03.

## What to Build
Riparare i difetti propri del flusso: findings multilingua e gate di formato distinti da
fallimenti di codice, test process-owned forniti a fix/review, errori infrastrutturali e
diff non UTF-8 conservati, clone LF stabile e contabilità sperimentale/operatore distinta.
Fonte locale baseline SPB-02 tree 6fca3cd863db87e0db1e19d405a47980640f5200. Non alterare
pilota, copie/suite/ledger privati originali, sorgente congelata o capacità del modello.

## Acceptance Criteria
- [ ] Review C/JS/TS/Python interpretata senza perdere severity/path/line/prosa; Python regressions preservate. Unparsed apre gate, conserva prosa, non approva e non incrementa final failures.
- [ ] Fix e review ricevono candidate-bound test observations (argv/exit/failure/stdout/stderr); preview bounded/troncamenti dichiarati e receipt integrali/hash conservati; test-failing fixture diventa green grazie allo stderr, senza hidden inputs.
- [ ] Diff non UTF-8, errore turn/processo/cattura preservano candidato/cause/inflight/receipt e gate infrastrutturale, senza retry o addebito come failure modello. Tre fallimenti reali e blocchi delle dipendenze invariati.
- [ ] Helper per clone owned nuovo forza LF prima del checkout; tree seed/clone uguali sotto autocrlf ereditato; originale immutato e nessun overwrite.
- [ ] Cost report distingue componenti e ignoti; operator estimates cumulative/source-bound/idempotenti, nessun reset; reserve/launch includono costo operatore e rifiutano componente ignota; nessun ledger storico riscritto.
- [ ] Test causali locali, packaging/graph, review/QA/audit canonico sul candidato esatto. Source/SDK/runtime osservati nel pilota non rinominati come prova dei fix; nessuna nuova spesa live o delivery.

## Frontier
Ready dopo validazione del handoff SPB-02 implementation-complete/release-blocked. Il
mandato è una riparazione locale, non permesso di riaprire la misura Lua o altri lotti.
Contabilità operatore live non nota: non fornire uno zero sintetico per autorizzare spesa.

## Step-by-Step Implementation Plan
1. Congelare input/contesto e verificare dependency, target/base e scope; validare spec/ticket/graph con owner canonici senza runner.
2. Repro RED di ciascun confine con Git/subprocess reali e peer/classifier finti, accounting dei tentativi e source refs.
3. GREEN nel reader, controllore e adapter; niente AST C/JS, nuove soglie Jev o approvazione implicita.
4. Verifiche causali/compatibilità e limiti; cleanup focalizzato, freeze e review shared-context.
5. QA fattibile locale e audit canonico; handoff release-blocked con costi/tentativi/gate senza provider mutation.

## Testing Plan
Unittest mirati findings/controller/adapter e caller fixtures. Solo processi locali e API
simulate: niente credenziali/model/providers/Docker hidden/replay del pilota. Salvare RED,
GREEN, durate e source fingerprints; niente suite Autopilot completa seriale. Le fixture
operatore a costo zero sono fittizie e dichiarate, mai prove di costo live.

## Out of Scope
Benchmark live, rep extra/L12/tuning/modello alternativo, Sonnet, soglie/risk AST non Python,
independent/delegated review, pubblicazione, commit/push/PR/merge, install/reload, wiki sync,
GC, editing dei lotti/suite/copiedi storici o attivazione di runner/scheduler/driver.
