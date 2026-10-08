# Crew che funziona: un team con ruoli, worktree separati, skills-only

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-hard-crew-isolated`
- Role: `spec`
- Parent: [`artifact:delivery-bench-hard-wayfinder`](delivery-bench-hard-wayfinder.md)

### Children
- [DBH-40](../tickets/delivery-bench-hard/done/40-crew-delivery-skill.md)
- [DBH-41](../tickets/delivery-bench-hard/41-crew-3-arm.md)
- [DBH-42](../tickets/delivery-bench-hard/42-crew-3-lot.md)

## Type
Feature (skill e braccio del banco) più misura.

## Problem
Nel lotto `dbh-crew` (catene da 4, `gpt-6-luna` medium) la Crew non ha reso più di un Pi solo:
`pi-tools` 30/36 in 67 minuti mediani per catena; `crew-1` 24/36; `crew-2` 30/36 in 173 minuti
con 423 sessioni worker. I compiti salvati dicono perché:

- `crew-1` ha usato il worker in 11 richieste su 36 (22 compiti): in pratica lavora da solo.
- `crew-2` ha creato 350 compiti, fino a 25 per richiesta; 86 sono finiti `blocked`. Motivi
  scritti dai worker: sovrapposizione con un altro compito in corso (22), suite rossa per il
  lavoro a metà del collega (23), compito troppo piccolo per un cambiamento che tocca tutto
  («serve riprogettare», 23), altro (18).

È lo stesso schema visto fuori dal banco con più Pi sullo stesso progetto: tutti «pronti», nessuno
chiude, il coordinatore smista invece di integrare.

## Decisions
Dell'utente, 2026-10-08: «mi va bene tutto però devono anche poter usare skill only in crew»;
poi «come gli umani sullo stesso repo» (PM, developer, code review, merge, QA del ciclo) e
«ok a tutto» sulle sei proposte.

1. Si sistema prima nel banco, dove i test nascosti dicono se funziona; poi le stesse regole
   valgono nei progetti veri.
2. **Ruoli come un team umano**:
   - un **PM** scrive spec e ticket (`to-spec`, `to-tickets`), assegna i ticket e gestisce la
     coda di merge, senza scrivere codice di prodotto;
   - **2 developer** fanno un ticket alla volta con `execute-ticket` (corsia skills-only) senza la
     propria review;
   - **1 reviewer** fa `code-review` di ogni branch, da un contesto separato, e il QA del ciclo.
3. **Il principale non lo tocca nessuno.** Ognuno lavora nel suo `git worktree` su un suo branch.
   Un hook `pre-commit` rifiuta i commit sul branch `main`. Il report conta ogni violazione.
4. **Coda di merge (Q1)**: un passo fisso del PM, un branch alla volta:
   - `rebase` sul principale; con un conflitto il ticket torna al suo developer;
   - test sul branch aggiornato;
   - merge solo fast-forward;
   - rimozione del worktree.
5. **Compiti interi**: al più 2 ticket per developer per richiesta, uno alla volta, con file
   disgiunti. Un ticket bloccato il PM non lo finisce: lo riscrive più chiaro o lo unisce a un
   altro e lo riassegna. Al secondo blocco sullo stesso ticket la richiesta si ferma, con il
   motivo registrato.
6. **QA del ciclo**: quando tutti i ticket della richiesta sono uniti, il reviewer fa
   `qa-test-plan` e i test completi sul principale; ogni problema diventa un ticket nuovo. La
   richiesta è finita solo con il QA verde sul principale.
7. **Regole in una skill** di `agent-skills` (`crew-delivery`); nessun runner, scheduler o driver
   di Autopilot.
8. **Misura:** un braccio nuovo `crew-3`, con PM + 2 developer + 1 reviewer:
   - catene da 4, 3 ripetizioni × 3 scenari, stesso modello;
   - confronto con `pi-tools` (`dbh-luna3d`) e `crew-2` (`dbh-crew`).
9. **Soglia:** la Crew «funziona» se valgono entrambe:
   - `crew-3` accetta almeno quanto `pi-tools` (30/36);
   - il suo tempo mediano per catena è al massimo 1,5 volte quello di `pi-tools`.

## Target behavior
1. **Skill `crew-delivery`**: i ruoli, il giro del ticket, la coda di merge, l'hook e il QA del
   ciclo come nelle decisioni 2–6. Si installa con le altre skill e `ask-skills` la instrada
   quando la Crew esiste già. Non crea deleghe da sola.
2. **Braccio `crew-3`**:
   - profilo come `pi-full` (estensione obbligatoria e skill visibili) più la copia di
     `pi-messenger` dei bracci Crew;
   - il coordinatore fa il PM;
   - i worker fanno da developer o da reviewer secondo il compito;
   - i worker caricano le skill e l'estensione obbligatoria, senza `/goal`;
   - prima della prima richiesta, il runner installa l'hook `pre-commit` nel progetto;
   - i worktree stanno nella cartella del braccio, fuori da `project/`, così il giudice vede
     solo il principale e l'audit resta valido.
3. **Registrazione**:
   - come `crew-1` e `crew-2`: costo del principale e dei worker a parte, sessioni worker, giri
     di `/goal`;
   - in più, per ogni richiesta: ticket creati, uniti e bloccati; review con verdetto; giri di QA;
     worktree creati; commit sul principale fuori dalla coda (violazioni).
4. **Report**:
   - accettazione, latenti, costo, tempo mediano per catena e ticket per `crew-3`, accanto a
     `pi-tools` e `crew-2`;
   - il verdetto sulla soglia della decisione 9;
   - poi il giudizio di qualità, come per DBH-32.

## Non-goals
- Cambiare `crew-1`, `crew-2` o i lotti già misurati.
- Planner o reviewer automatici di `pi-messenger`: i ruoli li dà la skill.
- Applicare la skill ai progetti fuori dal banco in questa spec: viene dopo, se la soglia regge.

## Failure modes
- **Qualcuno scrive nel principale.** L'hook ferma i commit; le modifiche non salvate nel
  principale e i commit fuori dalla coda finiscono nel report come violazioni.
- **Conflitti**: il ticket torna al suo developer. Il report conta i ritorni.
- **Review che rimbalza all'infinito.** Ogni rimando conta come blocco: dal secondo sullo stesso
  ticket vale la decisione 5.
- **Worktree rimasti**: li rimuove la coda di merge. Il runner non li giudica, perché sono fuori
  da `project/`.
- **`pi-messenger` su Windows** (EINVAL allo spawn): già risolto dalla copia patchata (DBH-33).

## Verification
- Test della skill e del grafo delle skill: `ask-skills` la instrada e i limiti di righe sono
  rispettati.
- Unit test del runner per `crew-3`:
  - profilo e skill visibili a PM e worker;
  - argv dei worker;
  - hook installato;
  - registrazione di ticket, review e violazioni.
- Preflight senza lotto di `crew-3`, con un ticket reale:
  - fatto da un developer nel suo worktree;
  - approvato dal reviewer;
  - unito dalla coda.
- A fine lotto: ledger, celle e report completi, confronto con la soglia.

## Gates
Risposte dell'utente del 2026-10-08 («mi va bene tutto», skills-only nella Crew, «ok a tutto»).
- **Tentativo**:
  - per DBH-40 e DBH-41: una PR con CI verde;
  - per DBH-42: un lotto `dbh-crew3` completo (`crew-3` × 3 scenari × 3 ripetizioni, catene
    da 4).
- **Budget per tentativo**: nessun tetto (abbonamento ChatGPT a canone fisso via OAuth). La
  spesa a prezzo di listino resta nel report.
- **Tempo per tentativo**: 24 ore. **Tentativi massimi**: 2.
- **Approvazioni**:
  - l'agente fa il merge delle PR con CI verde e `--match-head-commit`;
  - installare la skill (pin in `pi-personal-config`, `update:personal`) è autorizzato, ma solo
    tra due lotti;
  - nessun deploy né pubblicazione.
- **Versione esatta**: nessuna. Il lotto lega skill ed estensioni installate al suo avvio.
- **Blocchi esistenti cercati** (runner, lotti, memorie):
  - un solo lotto alla volta: `dbh-crew3` parte dopo `dbh-chain12` e `dbh-vague`;
  - durante un lotto il checkout principale di `agent-skills` non si aggiorna, e niente
    `update:personal`;
  - Docker Desktop deve essere avviato.
