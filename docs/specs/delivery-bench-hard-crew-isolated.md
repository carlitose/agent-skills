# Crew che funziona: worker isolati, compiti interi, skills-only

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

## Decisions (utente, 2026-10-08: «mi va bene tutto però devono anche poter usare skill only in crew»)
1. Si sistema prima nel banco, dove i test nascosti dicono se funziona; poi le stesse regole
   valgono nei progetti veri.
2. **Isolamento:** ogni worker lavora in una propria copia del progetto (`git worktree` su un
   proprio branch). Il coordinatore integra il lavoro in `main` della cartella del progetto e fa
   girare i test sul risultato integrato.
3. **Compiti interi:** al massimo 2 compiti per worker per richiesta. Un compito è una parte
   intera della richiesta, chiusa con i suoi test; due compiti in parallelo non toccano gli stessi
   file. Un compito bloccato non si spezza ancora: lo riprende il coordinatore.
4. **Regole in una skill** di `agent-skills` (`crew-delivery`), non solo nel prompt del braccio.
5. **Skills-only nella Crew:** coordinatore e worker vedono le skill installate e lavorano nella
   corsia skills-only. Il coordinatore usa `to-spec` e `to-tickets` per ricavare i compiti dalla
   richiesta; ogni compito della Crew è un ticket; ogni worker lo porta a termine con
   `execute-ticket` inline nel suo worktree. Nessun runner, scheduler o driver di Autopilot.
6. **Misura:** un braccio nuovo `crew-3` (coordinatore che lavora anche lui + 2 worker), catene da
   4, 3 ripetizioni × 3 scenari, stesso modello, confronto con `pi-tools` (`dbh-luna3d`) e
   `crew-2` (`dbh-crew`).
7. **Soglia:** la Crew «funziona» se `crew-3` accetta almeno quanto `pi-tools` (30/36) e il suo
   tempo mediano per catena è al massimo 1,5 volte quello di `pi-tools`.

## Target behavior
1. **Skill `crew-delivery`.** Una skill corta per chi coordina e per chi fa il worker:
   - coordinatore: legge la richiesta, la porta in spec e ticket (skills-only), sceglie al più
     2 ticket per worker con file disgiunti, crea un compito per ticket con il ticket allegato,
     lancia i worker; quando un worker consegna, integra il suo branch in `main` (merge o
     rebase), fa girare i test del repository sul risultato integrato e risolve lui i conflitti;
     un compito `blocked` lo finisce lui, senza spezzarlo; «fatto» vale solo con i test verdi sul
     risultato integrato;
   - worker: crea il proprio worktree e branch dal `main` attuale, lavora solo lì, porta il ticket
     a termine con `execute-ticket` (test inclusi), fa commit sul suo branch e consegna il nome del
     branch; non tocca la cartella principale né i worktree degli altri; se si blocca, consegna lo
     stato e il motivo invece di riprovare in piccolo.
   La skill vive in `agent-skills`, si installa con le altre ed è instradabile da `ask-skills`.
2. **Braccio `crew-3`.** Come `pi-full` (estensione obbligatoria e skill visibili) più la copia di
   `pi-messenger` dei bracci Crew; 2 worker; il coordinatore lavora anche lui. I worker caricano
   le skill e l'estensione obbligatoria (non `--no-skills`), senza `/goal`. I worktree stanno
   dentro la cartella del braccio, fuori da `project/`, così il giudice vede solo il risultato
   integrato e l'audit resta valido.
3. **Registrazione:** come `crew-1`/`crew-2` (costo principale e worker a parte, sessioni worker,
   giri di `/goal`), più compiti creati, completati e bloccati per richiesta e worktree creati.
4. **Report:** accettazione, latenti, costo, tempo mediano per catena e compiti per `crew-3`
   accanto a `pi-tools` e `crew-2`, con la soglia della decisione 7; poi il giudizio di qualità
   come per DBH-32.

## Non-goals
- Cambiare `crew-1`, `crew-2` o i lotti già misurati.
- Planner o reviewer automatici di `pi-messenger`.
- Applicare la skill ai progetti fuori dal banco in questa spec: viene dopo, se la soglia regge.

## Failure modes
- Un worker scrive nella cartella principale: la skill lo vieta e il report conta i commit su
  `main` fatti fuori dall'integrazione del coordinatore.
- Conflitti di merge: li risolve il coordinatore; il report conta le integrazioni con conflitti.
- Worktree rimasti a fine richiesta: il coordinatore li rimuove dopo l'integrazione; il runner
  non li giudica (sono fuori da `project/`).
- `pi-messenger` su Windows (EINVAL allo spawn): già risolto dalla copia patchata (DBH-33).

## Verification
- Test della skill nel grafo delle skill (`ask-skills` la instrada, limiti di righe rispettati).
- Unit test del runner per `crew-3`: profilo, skill visibili a coordinatore e worker, argv dei
  worker, registrazione dei compiti.
- Preflight senza lotto di `crew-3` con un compito reale fatto da un worker nel suo worktree e
  integrato dal coordinatore.
- A fine lotto: ledger, celle e report completi, confronto con la soglia.

## Gates
Risposte dell'utente del 2026-10-08 («mi va bene tutto», più skills-only nella Crew).
- Tentativo: per DBH-40 e DBH-41 una PR con CI verde; per DBH-42 un lotto `dbh-crew3` completo
  (`crew-3` × 3 scenari × 3 ripetizioni, catene da 4).
- Budget per tentativo: nessun tetto (abbonamento ChatGPT a canone fisso via OAuth); la spesa a
  prezzo di listino resta nel report.
- Tempo per tentativo: 24 ore. Tentativi massimi: 2.
- Approvazioni: l'agente fa il merge delle PR con CI verde e `--match-head-commit`. Installare la
  skill (pin in `pi-personal-config`, `update:personal`) è autorizzato, ma solo tra due lotti.
  Nessun deploy né pubblicazione.
- Versione esatta: nessuna; il lotto lega skill ed estensioni installate al suo avvio.
- Blocchi esistenti cercati (runner, lotti, memorie):
  - un solo lotto alla volta: `dbh-crew3` parte dopo `dbh-chain12` e `dbh-vague`;
  - durante un lotto il checkout principale di `agent-skills` non si aggiorna e niente
    `update:personal`;
  - Docker Desktop deve essere avviato.
