# Catene da 12: pi-tools, pi-full e bare-goal su richieste lunghe

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-chain-12`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-36](../tickets/delivery-bench-hard/36-chain-12-lot.md)

## Type
Misura (decisione di lotto), senza codice nuovo.

## Problem
Con le catene da 4 (`dbh-luna3d`, `dbh-luna3e`) i tre bracci con `/goal` sono vicini:
`pi-tools` 30/36, `pi-full` 29/36, `bare-goal` 25/36. La richiesta 4 è 9/9 per tutti e gli
errori si concentrano su poche richieste. Le catene da 4 non dicono nulla sul lavoro lungo:
compattazioni, contesto che cresce, regressioni sulle richieste precedenti. Le catene da 12
servono a questo.

## Decisions (utente)
1. Bracci `pi-tools`, `pi-full` e `bare-goal`. `bare` resta fuori (0/36 con le catene da 4).
2. Stesso modello e thinking di `dbh-luna3d`: `openai-codex/gpt-6-luna`, `medium`.
3. Stessi tre scenari e le stesse suite, 3 ripetizioni.
4. Il lotto parte dopo il giudizio di qualità (finito) e dopo il lotto Crew.

## Target behavior
1. Un lotto nuovo `dbh-chain12` con le skill e le estensioni installate al momento dell'avvio.
   Non si estende `dbh-luna3d`: il lotto lega le skill installate, che sono cambiate da allora
   (gate espliciti, disciplina delle corsie, `/loop`).
2. `run-lot --through 12 --jobs 9`, avvio visibile con il watcher, come i lotti precedenti.
3. Ogni tentativo registra già i giri di `/goal` (DBH-34): il report li riporta per braccio.
4. Report a confronto con le catene da 4, poi il giudizio di qualità sulle unità del lotto, come
   per DBH-32.

## Stima
Con le catene da 4 ogni posizione di richiesta è costata 0,5–1,6 $ per braccio sulle 9 catene,
più il valutatore di `/goal` (fino a +25%). Per 12 richieste: circa 15–25 $ per braccio, cioè
45–65 $ in totale. Il tetto può arrivare prima della fine. Tempo: circa 27 catene × 3,5–5,5 ore
su 9 posti, quindi 12–18 ore.

## Non-goals
- Bracci Crew sulle catene da 12.
- Cambiare runner, giudici o lotti già misurati.

## Failure modes
- Spesa proiettata oltre il tetto: l'agente ferma il lotto prima di superarlo e registra il
  motivo. Le richieste giudicate restano valide.
- Docker fermo, oppure il provider non risponde: il runner aspetta, come nei lotti precedenti.

## Verification
- Preflight senza lotto dei tre bracci prima di `init-lot`.
- A fine lotto: ledger e celle completi, report per braccio e per scenario.

## Gates
Risposte dell'utente del 2026-10-06 («VA BENE») e del 2026-10-07 («fai catene da 12 e le crew»).
- Tentativo: un lotto `dbh-chain12` completo, catene da 12, 3 bracci × 3 scenari × 3 ripetizioni.
- Budget per tentativo: 60 $ a prezzo di listino, riportato da Pi e pagato con l'abbonamento
  ChatGPT tramite OAuth. Il runner non lo impone: l'agente ferma il lotto prima del tetto.
- Tempo per tentativo: 24 ore.
- Tentativi massimi: 2.
- Approvazioni: nessun merge di codice. Questo documento passa con CI 8/8 e
  `--match-head-commit`. Nessun deploy né pubblicazione.
- Versione esatta: nessuna. Il lotto lega le skill e le estensioni installate quando parte.
- Blocchi esistenti cercati (runner, lotti, memorie):
  - un solo lotto alla volta. Ordine: giudizio di qualità (finito), poi Crew, poi questo;
  - durante il lotto il checkout principale di `agent-skills` non si aggiorna, e niente
    `update:personal`;
  - Docker Desktop deve essere avviato (lotto `dbh-luna3`, annullato).
