---
type: source
title: "Superpowers su Pi: confronto con Luna medium"
identity_key: artifact:delivery-bench-superpowers-luna
identity_strength: stable
source_path: docs/specs/delivery-bench-superpowers-luna.md
source_digest: sha256:a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-11-07
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Superpowers su Pi: confronto con Luna medium

Compiled from `docs/specs/delivery-bench-superpowers-luna.md`. Identity is `artifact:delivery-bench-superpowers-luna`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-11-07** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-wayfinder]]
- Child source: [[sources/ticket-delivery-bench-superpowers-luna-spl-01]]
- Child source: [[sources/ticket-delivery-bench-superpowers-luna-spl-02]]
- Child source: [[sources/ticket-delivery-bench-superpowers-luna-spl-03]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[10],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-delivery-bench-superpowers-luna.md","payload_bytes":9490,"payload_sha256":"a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2"}],"payload_bytes":9490,"payload_sha256":"a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2","schema":1,"source_digest":"sha256:a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2","source_identity":"artifact:delivery-bench-superpowers-luna","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 10: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":9490,"payload_sha256":"a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2","schema":1,"source_digest":"sha256:a906f88e87bd20b0c32a54a49e946fb283799408dcb25680c86d3a1c820024e2","source_identity":"artifact:delivery-bench-superpowers-luna"} -->
```markdown
# Superpowers su Pi: confronto con Luna medium

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-superpowers-luna`
- Role: `spec`
- Parent: [delivery-bench-hard-wayfinder.md](delivery-bench-hard-wayfinder.md)

### Children
- [SPL-01 — Braccio isolato e controlli offline](../tickets/delivery-bench-superpowers-luna/01-superpowers-arm.md)
- [SPL-02 — Misura e report](../tickets/delivery-bench-superpowers-luna/02-measure-and-report.md)
- [SPL-03 — Recupero delle estensioni congelate](../tickets/delivery-bench-superpowers-luna/03-relocate-frozen-extension.md)

## Type
Feature e decisione di misura; corsia skills-only, senza Ticket Autopilot.

## Goal and decisions
L'utente vuole aggiungere `obra/superpowers` al confronto fra Pi nudo, Pi-tools e Pi-full,
senza Anthropic. Dopo aver verificato i modelli storici ha confermato «si facciamo cosi»:
`openai-codex/gpt-6-luna`, thinking `medium`, come il confronto Luna più recente.

Si prepara un lotto nuovo: `bare`, `pi-tools`, `pi-full`, `pi-superpowers`. Ogni braccio usa
lo stesso modello, thinking, scenari, richieste, ripetizioni e controlli nascosti. La misura
iniziale riprende il confronto citato: 4 richieste × 3 ripetizioni × 3 scenari (`lua-vm`,
`sql-engine`, `crdt-yjs`) × 4 bracci, cioè 144 posizioni di richiesta prima degli eventuali
retry infrastrutturali già previsti dal protocollo. Non si riavviano né modificano lotti storici.

## Evidence and current behavior
- [Luna e profili](delivery-bench-hard-luna-three-arms.md): strumenti separati dalle skill;
  `pi-tools` e `pi-full` usano anche `/goal`.
- [Catene da 12](delivery-bench-hard-chain-12.md): il confronto precedente sulle catene da 4
  riportava 30/36, 29/36 e 25/36 per Pi-tools, Pi-full e bare-goal. Non sono risultati nuovi.
- [Superpowers upstream](https://github.com/obra/superpowers#pi), osservato al commit
  `22f0b463e7a5e579904dd6211a520321035526f7`, versione `7.0.2`: pacchetto Pi nativo,
  skill in `skills/`, bootstrap `.pi/extensions/superpowers.ts`; nessuna dipendenza da Claude Code.
- Il bootstrap upstream è iniettato nel contesto provider e non salvato nella cronologia:
  l'elenco di skill in un JSONL non prova da solo che il modello abbia seguito il workflow.
- Gli scenari privati sono documentati in `C:/Users/CGS03/dbench-private`
  ([mappa](delivery-bench-hard-wayfinder.md)); quel percorso e
  `C:/Users/rdpuser/dbench-private` non esistono su questo host.

## Target behavior
1. `pi-superpowers` è un braccio Pi esplicito, non un alias di Pi-full. Ha lo stesso
   `TOOL_PROFILE`, `/goal` e condizioni di Pi-tools, più il bootstrap e soltanto le skill
   Superpowers selezionate esplicitamente. Nessuna nostra regola obbligatoria, skill personale,
   memoria, MCP, Telegram, subagent o pi-messenger viene aggiunta dal nuovo braccio.
2. `init-lot` e `preflight` accettano `--superpowers-root PATH`, un checkout/snapshot locale
   separato. Se il braccio è selezionato, il pacchetto ufficiale Pi deve avere manifest,
   bootstrap e skill utilizzabili. Non si esegue `pi install` e non si cambia la configurazione
   personale. Il runner non scarica o aggiorna il pacchetto.
3. Il lotto lega percorso, versione, impronta del pacchetto e nomi delle skill. Ogni caricamento
   del lotto e ogni tentativo verifica il legame prima di avviare Pi; una modifica a bootstrap,
   manifest, skill o riferimenti del pacchetto ferma il braccio. Le evidenze dei tentativi
   conservano il riferimento al pacchetto oltre ai normali profili degli strumenti.
4. Il preflight esige gli strumenti di Pi-tools, le sole skill del pacchetto e nessun routing
   `ask-skills`; verifica la scrittura con `code` come gli altri bracci. Non spaccia questi
   controlli per prova semantica che il modello abbia eseguito tutta la metodologia.
5. I report accettano il nuovo nome anche con `--arm-from`. Le cinque dimensioni e la
   statistica esistente non cambiano. Il pareggio preferisce Pi-tools alle varianti con skill;
   Pi-full precede Superpowers solo come ordine convenzionale dichiarato, non come risultato.
6. Senza capacità di subagent il braccio usa il fallback seriale upstream. La misura riguarda
   Superpowers su Pi con questa dotazione, non Claude Code e non il workflow con subagent.

## Non-goals and invariants
- Nessun Anthropic/Jev o giudice generativo Anthropic: i controlli nascosti restano il giudice
  della misura. Un giudizio qualitativo aggiuntivo è fuori da questo lotto.
- Nessuna installazione globale, reload, upgrade di Pi, modifica di provider o credenziali.
- Nessuna autorizzazione implicita a delegare, fare push/PR/merge o pubblicare risultati privati.
- Nessun nuovo scheduler di ticket; il runner di benchmark esistente resta il solo proprietario
  del protocollo sperimentale. Nessun cambiamento all'argv dei bracci esistenti, salvo il solo
  percorso fisico di un'estensione rilocata a byte identici tramite SPL-03, autorizzato con «1».
  Nomi, ordine, opzioni, prompt, modello, skill e impronta del contenuto non cambiano.
- Niente ranking diretto contro vecchi lotti con altri modelli, versioni o condizioni. Gli
  aggregati storici sono contesto; le conclusioni nuove richiedono controlli contemporanei.

## Recovery of frozen extensions
Il lotto `spl-luna1` conserva 99 giudizi; un aggiornamento di `pi-code-tool` ha fermato
12 celle. La precedente cartella è ricostruibile dal commit
`1129e282ed79fb385c885976f0983d1c731a3ada` con SHA-256
`5928b0c1ce16b89fc003392b98b1a9d6bd8f35508acd1ac36c3985ccd23c9f76`.
L'utente ha scelto il recupero isolato, non il rollback della propria installazione.

SPL-03 aggiunge `relocate-extension --lot DIR --source ENTRY --snapshot ENTRY --reason TEXT`.
L'operazione aggiorna solo un sidecar versionato e il ledger attraverso il runner esistente:
`lot.json`, risultati, snapshot delle richieste e tentativi precedenti restano immutati.
Il sidecar lega hash del manifesto originario, autorità originaria, percorso logico, nuova
posizione, stesso digest della cartella, motivo e data; conserva la cronologia delle rilocazioni.
Ogni caricamento applica soltanto destinazioni con lo stesso nome di entrypoint e lo stesso
contenuto congelato a tutti i bracci che referenziano quell'entrypoint. Il guard originale
continua a verificare cartella e import locali; deriva, metadati malformati, manifesto/autorità
stale, sorgente non legata o celle attive sono errori, non autorizzazioni a cambiare versione.
La pubblicazione del sidecar è atomica; il ledger distingue preparazione e applicazione.
Un errore di IO resta visibile senza eliminare il tentativo o il metadato già pubblicato.
Una ripetizione identica è un no-op validato, non una nuova autorizzazione.
La copia privata mantiene la risoluzione delle dipendenze senza installazioni o scritture
nella configurazione personale. Nessun nuovo scheduler, lotto o replay di giudizi completi.
## Implementation slices
- SPL-01: binding del pacchetto, isolamento argv, preflight, report, test offline e istruzioni.
- SPL-02: recuperare gli scenari senza leggere suite nascoste nel contesto dei partecipanti,
  verificare ambiente e accesso Luna, preparare autorità del lotto legata a questa conferma,
  eseguire il protocollo e produrre un report. Prima del preflight live registrare la stima
  corrente dei costi; nessuna stima numerica GPT-6.1 o di vecchi lotti vale come costo osservato.
- SPL-03: rilocazione verificata delle estensioni a contenuto invariato, test offline e
  documentazione; quindi ripresa di SPL-02 nello stesso lotto e nello stesso attempt di misura.

## Verification
SPL-01 usa fixture locali, Pi e giudice finti: binding/drift, argv, isolamento skill, preflight,
report e regressioni dei profili esistenti; lint e profilo quick obbligatorio del repository.
Il candidato e il grafo consegnato vengono congelati prima della review inline e del QA.
Le verifiche live sono distinte e non eseguite se mancano scenari o ambiente. I loro costi
sono sconosciuti, non zero. Un preflight di accesso non equivale a un punteggio di benchmark.

## Gates
- Attempt: implementazione attraverso handoff di SPL-01; SPL-02 è una successiva misura unica
  sul lotto nuovo, distinta dall'implementazione offline. SPL-03 ha un attempt di implementazione
  attraverso handoff; il successivo resume non azzera budget, consumi o storia di SPL-02.
- Budget per attempt: nessun limite impostato dall'utente; prima di spendere registrare costi
  stimati/osservati e tentativi. Non usare API a pagamento diverse dall'accesso OpenAI richiesto.
- Time per attempt: nessun limite impostato.
- Maximum attempts: nessun limite impostato; nessun retry implicito di un lotto completo.
- Approvals: l'utente autorizza questo confronto con Luna medium; non autorizza provider
  Anthropic, delegazione, installazione globale, pubblicazione o Git/provider delivery.
- Exact version: modello scelto `openai-codex/gpt-6-luna`, thinking `medium`; nessun pin umano
  di Superpowers. Il lotto congela il contenuto della versione upstream scelta prima della misura.
- Existing blocks searched: specifiche e report delivery-bench, CLI e codice del runner,
  configurazione/installazioni locali, checkout e remoto. Scenari privati assenti ai due percorsi
  sopra: gate di SPL-02. Accesso di generazione Luna e Docker non ancora provati per il lotto.
  Questi gate non bloccano SPL-01. Il checkout principale contiene modifiche estranee:
  SPL-01 lavora nel worktree isolato `agent-skills-superpowers-luna`, base `e9510a53`.

```
