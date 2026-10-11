# TODO

- [ ] 1. Aggiungi a `config_v2.json` il campo `"retry_limit": 3`.
- [ ] 2. Aggiungi `Worker.pending()`, che restituisce la lista dei job ancora in coda.
- [ ] 3. Aggiungi `Worker.switch_config(path)`: passa alla config nuova mentre il worker gira, senza
      perdere job e senza chiuderne uno due volte. Un job iniziato con la config vecchia si chiude
      con quella; i job iniziati dopo il passaggio usano la nuova. Non esiste una procedura documentata di pausa e settlement: va progettata.

Verifica: `python check_todo.py`.
