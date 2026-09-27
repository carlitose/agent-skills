# delivery-bench difficile — luna medium su sistemi complessi, catene da 12

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [Candidati e oracoli](../research/delivery-bench-hard-candidates.md)
- [DBH-01](../tickets/delivery-bench-hard/done/01-confirm-scenarios-and-budget.md)
- [DBH-02](../tickets/delivery-bench-hard/done/02-harness-model-length-compaction.md)
- [DBH-03](../tickets/delivery-bench-hard/03-luna-calibration.md)
- [DBH-04](../tickets/delivery-bench-hard/04-trap-catalog-v2.md)
- [DBH-05](../tickets/delivery-bench-hard/05-scenario-lua-vm.md)
- [DBH-06](../tickets/delivery-bench-hard/06-scenario-sql-engine.md)
- [DBH-07](../tickets/delivery-bench-hard/07-scenario-crdt-yjs.md)
- [DBH-08](../tickets/delivery-bench-hard/08-pilot.md)
- [DBH-09](../tickets/delivery-bench-hard/09-full-measurement.md)

## Type
Wayfinding spec

## Status
Active (2026-09-27).
- **Decisioni 1 e 2**: sono dell'utente.
- **Decisioni 3-11**: vengono dalla [ricerca](../research/delivery-bench-hard-candidates.md). DBH-01
  le conferma con il goal di sessione dell'utente, «finisci di aggiornare il benchmark ed esegui di
  nuovo tutti i bracci», dato senza fermarsi a chiedere.
- **Autorità** nel repo privato: `results/dbh-authority.json` (sha256 `52597cbf…`) e
  `results/luna-calib-authority.json` (sha256 `352fae74…`).
- **Harness**: pronto (DBH-02).

## Destination
Una seconda misura di delivery-bench in un regime dove i bracci non arrivano tutti al soffitto:
- modello `openai-codex/gpt-6-luna` con `--thinking medium`;
- tre sistemi reali molto complessi al posto delle app;
- catene da 12 richieste e trappole più dure.

L'output è come nella [prima misura](../research/delivery-bench-results.md): una tabella
braccio × lunghezza × scenario sui cinque assi, con in più la compaction. Contiene la regola di
TBA-03 e una raccomandazione operativa valida per questo regime. Mostra anche come cambia la
risposta rispetto al regime facile (`gpt-6-sol`, app piccole).

## Perché serve
- **Il regime facile sta al soffitto.** Alla catena da 8 i bracci accettano fra 42 e 48 richieste
  su 48. Su C e Python i quattro bracci senza cancello accettano 16/16. I latenti trovati vanno
  dall'85% al 96%, le trappole violate sono 5 in tutto e `bare` non arriva mai alla compaction.
  Le differenze vengono da uno o due eventi, e la regola dà «indistinguibile» ovunque.
- **Fuori da qui, ciò che separa agenti e modelli è l'evoluzione lunga di codebase mature**, con
  un verificatore quasi perfetto (SWE-EVO, DeepSWE, Carlini: vedi la ricerca).

## Decisions So Far
1. **Modello** (utente, 2026-09-27): `openai-codex/gpt-6-luna`, thinking `medium`, per tutti i
   bracci e per le foglie del driver. Nel catalogo di Pi ha contesto di 272K e reasoning, e la
   stima di costo è 0,1 $ per milione di token in input e 0,5 $ in output (sol: 2 $ e 10 $).
2. **Problema** (utente): estremamente complesso, niente app semplici, cercato anche in rete.
3. **Scenari** (proposta): `lua-vm` (C), `sql-engine` (Python, executor di sqlglot) e `crdt-yjs`
   (JavaScript con tipi JSDoc/tsc). Il seme di ciascuno è una release fissata del progetto reale,
   con licenza MIT. Motivi e alternative scartate sono nella ricerca.
4. **Catene da 12 richieste**, lette a 1, 4 e 12: ciascuna è un prefisso della successiva.
   - Le richieste sono originali, mai copiate da release note upstream, in spagnolo come prima.
   - Ognuna vale circa una voce di release: una funzionalità che attraversa più moduli.
5. **Oracolo esterno e deterministico per scenario**, oltre ai controlli scritti da noi.
   - `lua-vm`: la suite ufficiale della stessa release (`_U`) e ASan/UBSan.
   - `sql-engine`: un confronto differenziale con SQLite/DuckDB. I risultati si calcolano una
     volta e si congelano, come in sqllogictest.
   - `crdt-yjs`: convergenza su test casuali con seed fissi e decodifica dei documenti prodotti
     alle richieste precedenti.
   - Contratto invariato: il riferimento passa, lo stub fallisce, la soluzione trappola cade in
     ciascuna trappola. In più, due giudizi dello stesso albero devono essere identici.
6. **Latenti reali**: bug documentati della release fissata. Per Lua sono le voci di lua.org/bugs
   con l'esempio minimo, per gli altri i fix upstream successivi con il loro test. Si scelgono
   dove le richieste passano davvero.
7. **Trappole più dure**, con le stesse cinque tipologie del contratto: deprecato, architettura,
   bug chiuso, contratto, convenzione.
   - Le regole si piantano nelle richieste 2-4 e le tentazioni arrivano alle 8-12, quindi la
     distanza va da 4 a 10.
   - In ogni scenario almeno una tentazione ha come via più corta la rottura di un contratto:
     formato binario, API C, encoding o risultati di query già consegnati.
8. **Bracci**: gli stessi cinque, ciascuno nel suo modo naturale, con prompt e suffissi identici
   alla prima misura. c3a usa il driver corretto (TJV-01 e TJV-03). Jev resta nel driver c3a.
9. **Ripetizioni e regola**: 3 ripetizioni fino alla richiesta 4 e la ripetizione 1 fino alla
   12. Altre ripetizioni solo dove la regola di TBA-03 le chiede, confrontando i tassi.
10. **Compaction come dato misurato**: numero di compaction per catena e per sessione, per
    leggere la memoria lunga. È descrittivo e non entra nella regola.
11. **Isolamento e oracolo privato** come nella prima misura (contratto §2 e §8). Il repo
    privato è `C:/Users/CGS03/dbench-private`, con scenari nuovi e senza toccare quelli vecchi.

## Not Yet Specified
- **Conferma** di scenari, lunghezze, tetti di tempo e budget (DBH-01).
- **Catalogo delle trappole v2**: regole, tentazioni e distanze per scenario (DBH-04, revisione
  dell'utente).
- **Dettagli da fissare in ogni ticket di scenario:**
  - release esatte;
  - dimensione del seme e tempo della suite nel container;
  - dipendenze offline delle immagini;
  - come i bracci compilano e provano sull'host Windows.
- **Tempi reali** di una richiesta con luna medium su codebase così grandi: li misura il pilota
  (DBH-08) e fissano il tetto per la misura completa.

## Out of Scope
- **Classifiche di modelli.** Il confronto luna/sol di DBH-03 è solo contesto sul regime.
- **Modifiche ai lotti della prima misura** (`db07-pilot`, `c3a-observed`) e agli scenari vecchi.
- **App frontend, Maelstrom/Jepsen, compilatore da zero** (motivi nella ricerca).
- **Migliorare un braccio durante un lotto.** Una correzione fra due lotti è un lotto nuovo.

## Frontier / Blocking Edges
- **Decisioni e budget** (DBH-01): risolti il 2026-09-27 dal goal di sessione dell'utente.
- **Harness** (DBH-02): risolto il 2026-09-27. Modello, thinking e tetti ora vengono dal lotto,
  la lunghezza dallo scenario, e le compaction si registrano.
- **Catalogo v2** (DBH-04): blocca i tre scenari.
- **Scenari verificati** (DBH-05/06/07): bloccano il pilota. Uno scenario è verificato quando
  riferimento, stub e trappole danno l'esito atteso e due giudizi sono identici.
- **Pilota** (DBH-08): blocca la misura completa. Si sblocca quando i cinque bracci producono
  profili confrontabili entro i tetti.

## Ticket Plan
| ID | Tipo | Modo | Bloccato da | Titolo | Output atteso |
|---|---|---|---|---|---|
| DBH-01 | grilling | HITL | — | Conferma di scenari, lunghezze, tetti e budget | decisioni in questa mappa, autorità dei lotti |
| DBH-02 | task | AFK | — | Harness: modello dal lotto, N richieste, compaction | runner, report e contratto aggiornati, test offline |
| DBH-03 | task | AFK | DBH-01, DBH-02 | Calibrazione di luna sugli scenari vecchi | lotto `luna-calib` e nota di regime |
| DBH-04 | grilling | HITL | DBH-01 | Catalogo delle trappole v2 | catalogo approvato nel repo privato |
| DBH-05 | task | AFK | DBH-02, DBH-04 | Scenario `lua-vm` | seme, 12 richieste, suite, riferimento, trappole, immagine |
| DBH-06 | task | AFK | DBH-02, DBH-04 | Scenario `sql-engine` | idem |
| DBH-07 | task | AFK | DBH-02, DBH-04 | Scenario `crdt-yjs` | idem |
| DBH-08 | task | AFK | DBH-05, DBH-06, DBH-07 | Pilota: catena da 1 | lotto e report del pilota, tetti per la misura |
| DBH-09 | task | AFK | DBH-08 | Misura completa: catene da 4 e 12 | tabella, regola, raccomandazione |

## Next Review
- **Dopo DBH-01**: le decisioni 3-11 sono confermate o cambiate? Qual è il budget?
- **Dopo DBH-03**: luna medium basta, da solo, a staccare i bracci dal soffitto negli scenari
  facili?
- **Dopo DBH-05/06/07**: ogni scenario rispetta il contratto e dà due giudizi identici? Quanto
  dura la sua suite?
- **Dopo DBH-08**: durata delle richieste, compaction, guasti dell'harness, spesa rispetto ai
  tetti.
