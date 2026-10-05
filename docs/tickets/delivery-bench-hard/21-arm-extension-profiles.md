---
ticket_schema: 1
ticket_id: "DBH-21"
execution_mode: AFK
blocked_by: []
---

# DBH-21 — Profili di estensioni per braccio, legati al lotto, e preflight

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:21`
- Role: `ticket`
- Parent: [delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md)

## Parent Spec
[delivery-bench-hard-luna-three-arms.md](../../specs/delivery-bench-hard-luna-three-arms.md),
sezioni *Obiettivo* e *Comportamento atteso* 1–3.

## What to Build
Due bracci nuovi nel runner di delivery-bench, `pi-tools` e `pi-full`, che caricano con `-e` un
elenco chiuso di estensioni dalla copia installata di pi-personal-config, legato al lotto con un
digest per estensione. Un comando `preflight` verifica, con una richiesta minima fuori dal lotto,
che ogni braccio veda i tool e le skill previsti e che `code` scriva un file in `-p` senza
approvazione umana.

## Acceptance Criteria
- [ ] `ARMS` contiene `pi-tools` e `pi-full`; `bare`, `skills-only`, `autopilot` e `driver-*`
      restano invariati, con argv identico a prima.
- [ ] `pi-tools`: `--no-skills`, `-e` per `pi-code-tool`, `todo.ts`, `plan-mode`, `web.ts`, nessun
      suffisso. `pi-full`: skill attive, gli stessi `-e` più `mandatory-agent-skills.ts`, nessun
      suffisso.
- [ ] `init-lot` registra per braccio `[{path, sha256}]`; un'estensione mancante fa fallire
      `init-lot`; una cambiata o sparita fa fallire `load-lot`. Ogni tentativo registra l'elenco
      con cui parte.
- [ ] L'autorità deve coprire i bracci nuovi come gli altri; i lotti esistenti si caricano ancora.
- [ ] `preflight --lot-free` lancia una richiesta per braccio in una cartella temporanea e
      riporta tool attivi, skill caricate e l'esito di una scrittura con `code`; esce con codice
      non zero se un braccio non corrisponde al suo profilo.
- [ ] Test unitari nuovi in `benchmarks/delivery-bench/test_runner.py` passano; i test esistenti
      del runner passano.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Definire i profili (nomi, percorsi relativi alla radice installata di pi-personal-config) in
   `runner.py`; risolvere la radice dall'installazione, non dal checkout di sviluppo.
2. Estendere `init_lot`/`load_lot` con il campo `arm_extensions`, digest della cartella come
   `bind_extension` (DBH-18).
3. Estendere `arm_argv` e la registrazione del tentativo.
4. Aggiungere il sottocomando `preflight`, che legge la sessione JSONL prodotta per verificare
   tool, skill e scrittura.
5. Test unitari con estensioni finte in una cartella temporanea.

## Testing Plan
- Unitari: argv per ciascun braccio (vecchi e nuovi), digest, rifiuto di estensione
  mancante/cambiata, caricamento di un `lot.json` senza `arm_extensions`.
- Il preflight reale si esegue in DBH-23 (spende pochi centesimi); qui si testa con un comando Pi
  finto.

## Out of Scope
- Il viewer (DBH-22) e la misura (DBH-23).
- Cambiare le estensioni stesse o il pin di pi-personal-config.
