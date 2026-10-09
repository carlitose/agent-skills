# Comando `/loop`: ripetere un comando all'infinito

## Artifact Graph
- Artifact ID: `artifact:pi-code-loop-command`
- Role: `spec`
- Standalone: true

### Children
- [PCL-01](../tickets/pi-code-loop-command/done/01-loop-command.md)

## Type
Feature

Dal 2026-10-09 `/loop` vive solo nel pacchetto npm `@carlitose86/pi-loop`: vedi
[loop-moves-to-pi-loop](loop-moves-to-pi-loop.md).

## Problem
L'utente vuole un comando come `/goal`, ma senza condizione di arrivo: un `while (1)` che a
ogni giro ricorda all'agente cosa fare, con una pausa facoltativa tra un giro e l'altro.
`/goal` non basta: si ferma quando un valutatore dice "fatto" e ogni giro costa una chiamata
di valutazione. Oggi in Pi non esiste un comando che ripete un testo.

## Decisions (utente, 2026-10-06)
1. Ogni giro manda **lo stesso testo** che l'utente ha scritto dopo `/loop` («semplicemente gli
   ricorda cosa fare»).
2. **Pausa facoltativa in secondi** tra la fine di un giro e l'inizio del successivo; senza pausa
   il giro successivo parte subito.
3. Nessun limite di giri né di costo. Si ferma solo con `/loop stop`, con Esc, o da solo per un
   errore che ripetere non risolve.
4. Il comando è **un'estensione autonoma** del pacchetto Pi `carlitose-agent-skills-pi`
   (`extensions/loop.ts` in questo repository), condivisa con chi installa il pacchetto. Non dipende da pi-code; `/goal` resta invariato. (In un primo
   momento era previsto il fork di pi-code; l'utente ha chiesto l'estensione condivisa.)

## Target behavior
- `/loop [<n>s|<n>m|<n>h] <testo>`: avvia il ciclo (sostituisce uno già attivo) e manda subito
  il primo giro. L'intervallo è il primo token solo se ha l'unità (`30s`, `5m`, `1h`); un testo
  che comincia con un numero senza unità resta testo. Testo massimo 4.000 caratteri, come `/goal`.
- Ogni giro è un messaggio `loop` nella conversazione: `[loop, giro N] <testo>`, così il modello
  sa che è una ripetizione.
- A fine giro (turno concluso normalmente) parte il giro successivo: subito, oppure dopo la
  pausa. Se nel frattempo è iniziato un turno (l'utente ha scritto), il giro va in coda come
  follow-up.
- `/loop`: stato (testo, giri fatti, pausa, tempo trascorso), oppure `No loop set`.
- `/loop stop` (anche `clear`, `off`, `reset`, `none`, `cancel`): ferma il ciclo e annulla
  un'eventuale attesa.
- **Esc** su un giro ferma il ciclo, con un avviso.
- **Errori:** un errore irrecuperabile (autenticazione, credito, contesto troppo lungo, modello
  non disponibile, la stessa classificazione di `/goal`) ferma il ciclo con un avviso. Un
  errore transitorio (limiti di frequenza, rete) lascia il ciclo attivo e riprova dopo la pausa,
  almeno 30 secondi, per non girare a vuoto.
- Indicatore nel footer: `↻ loop N`.
- Headless (`pi -p "/loop ..."`): il comando tiene vivo il processo finché il ciclo non si ferma.
- Il ciclo non sopravvive a `/reload`, `--continue` o `/resume`: un ciclo infinito ripartito da
  solo sarebbe una sorpresa. Una nuova sessione lo azzera.

## Non-goals
- Condizioni di arrivo o valutatori: per quello c'è `/goal`.
- Modificare `/goal` o coordinare i due: usarli insieme è sconsigliato e documentato.
- Pianificazione a orario (cron) o cicli multipli contemporanei.

## Failure modes
- Pausa che scatta su una sessione chiusa: l'invio fallisce in silenzio, come in `/goal`.
- Turno che finisce mentre un'attesa è già armata: nessun secondo timer.

## Verification
- Unit (`node --test`, `extensions/loop.test.ts`): parsing dell'intervallo, primo giro immediato,
  giro successivo subito e dopo la pausa (timer finti), stato, stop che annulla l'attesa, Esc,
  errore irrecuperabile e transitorio, nessun ripristino alla nuova sessione, headless.
- `npm test` e `npm run lint` del repository; CI 8/8.
- Prova reale: `pi -p "/loop 2s ..."` su luna, fermata dopo 3 giri, pochi centesimi.

## Gates
Risposta dell'utente: «fallo con skill only», dopo la proposta con questi limiti.
- Tentativo: implementazione, PR e consegna (pin, installazione, reload).
- Budget per tentativo: nessuna spesa a pagamento tranne la prova reale, al massimo 0,10 $.
  Tempo: un giorno.
- Tentativi massimi: 2.
- Approvazioni: merge con CI 8/8 e `--match-head-commit`; pin aggiornato in `pi-personal-config`,
  poi `update:personal` e reload. Nessuna pubblicazione npm.
- Versione esatta: nessuna.
- Blocchi esistenti cercati (pacchetto, pin, benchmark):
  - nel Pi dell'utente il pacchetto è caricato dal checkout locale `~/.pi/agent/local/agent-skills`
    con tutte le sue `pi.extensions`, mentre `pi-personal-config` esclude le estensioni di questo
    pacchetto per non caricarle due volte. Basta quindi il pin: aggiungere `loop.ts` all'elenco
    di `pi-personal-config` registrerebbe `/loop` due volte;
  - il benchmark carica le estensioni con `--no-extensions` e `-e` espliciti, e il giudizio di
    qualità in corso fa lo stesso: la nuova estensione non lo tocca.
