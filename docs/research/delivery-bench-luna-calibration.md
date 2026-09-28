# delivery-bench — calibrazione di luna sugli scenari vecchi

## Artifact Graph
- Artifact ID: `artifact:delivery-bench-luna-calibration`
- Role: `research`
- Parent: [DBH-03 — Calibrazione di luna sugli scenari vecchi](../tickets/delivery-bench-hard/done/03-luna-calibration.md)

## Stato
Output di DBH-03 (2026-09-27). Il lotto `luna-calib` fa girare `bare` e skills-only con
`openai-codex/gpt-6-luna` e `--thinking medium` sui tre scenari della prima misura: catene da 3,
3 ripetizioni, 18 celle. Il riferimento sono le stesse celle di `db07-pilot`, cioè gli stessi
bracci con `gpt-6-sol` e `--thinking high`, tagliate alla richiesta 3.

**È un confronto fra due regimi di modello, non fra bracci.** Cambiano insieme il modello e il
livello di thinking. Record, giudizi e ledger stanno nel repo privato dell'oracolo
(`results/luna-calib/`). Qui ci sono solo aggregati, senza nomi di controlli, trappole o difetti.

In breve: luna medium stacca i due bracci dal soffitto, ma poco e non abbastanza per separarli.
Alla catena da 3 le richieste accettate scendono da 26/27 a 22/27 (`bare`) e da 27/27 a 20/27
(skills-only). Compaiono violazioni di trappole (2 per braccio, erano 0). La regola di TBA-03
resta «indistinguibile». Il costo scende di 40-60 volte, il tempo di 2-3 volte.

## Autorizzazione e provenienza
- **Autorità del lotto**: `results/luna-calib-authority.json` (sha256 `352fae74…`). Il file dice
  che il goal di sessione valeva come conferma di DBH-01, e questa era un'inferenza. La conferma
  vera l'ha data l'utente dopo, una domanda alla volta: scenari, lunghezze, tetti e budget alle
  21:46 UTC del 27/09, le altre decisioni della mappa alle 07:14 UTC del 28/09. È registrata in `results/dbh-01-confirmation.json` (sha256
  `b2aa1f31…`). L'autorità resta byte per byte uguale perché il lotto è legato al suo digest.
- **Legami uguali a `db07-pilot`**, verificati prima di partire: seed e suite nascoste dei tre
  scenari (`python-billing` `6ba6b3c0…`, `c-recq` `d87c157f…`, `ts-reservas` `1f8809bd…`, cioè la
  suite emendata in DB-08), canarini, comando Pi. `db07-pilot` non è stato toccato.
- **Harness**: `061a445` (DBH-02) per 17 celle e per il primo tentativo della richiesta 3
  dell'ultima; `04ec469` (DBH-10) per la ripresa di quella richiesta. Fra i due cambia solo il
  percorso di ripresa.
- **Esecuzione**: il 27/09, dalle 21:02 alle 21:25 UTC con 4 celle in parallelo; ripresa
  dell'ultima richiesta dalle 22:03 alle 22:07. Tetto di 60 minuti per richiesta, mai raggiunto.
- **Interruzione**: il lotto è stato fermato apposta con 17 celle su 18 finite, per
  riconciliare la provenienza di DBH-01 prima di spendere ancora. Una richiesta era nel giudizio.
  La ripresa ha trovato un difetto del runner (la richiesta interrotta non si riprendeva se era
  l'ultima della catena), corretto in DBH-10 (#376). La richiesta è stata rifatta dallo
  snapshot. Il tentativo superato resta nel record e il suo costo (0,005 $) è fra i retry
  d'infrastruttura.
- **Spesa**: 56 tentativi, 0,234 $ stimati da Pi in tutto, contro un tetto di 10 $. Jev non è
  stato usato. Somma dei tempi dei tentativi 4018 s (in parallelo, non è tempo di parete).

## Risultati

### Catene da 3 (3 ripetizioni, 9 catene per braccio)
Prima cifra: luna medium. Dopo la freccia: sol high (`db07-pilot`, stesse celle tagliate a 3).

| Braccio | Richieste accettate | Latenti trovati (fine) | Invarianti rotti (fine) | Trappole violate (fine) | USD (Pi) | Mediana per catena |
|---|---:|---:|---:|---:|---:|---:|
| bare | 22/27 ← 26/27 | 61/69 ← 63/69 | 5/141 ← 15/141 | 2/10 ← 0/16 | 0,09 ← 3,58 | 161 ← 440 s |
| skills-only | 20/27 ← 27/27 | 53/69 ← 69/69 | 12/141 ← 1/141 | 2/8 ← 0/18 | 0,14 ← 7,98 | 214 ← 460 s |

Le trappole violate con luna sono di tipo architettura (3) e convenzione (1), a distanza 1 o 2.
Le trappole non misurabili, perché la feature della richiesta tentatrice non c'è, salgono a 8 e
10 (erano 2 e 0): con luna la feature manca più spesso.

| Scenario | bare: accettate | skills-only: accettate | bare: latenti | skills-only: latenti |
|---|---:|---:|---:|---:|
| `c-recq` (C) | 7/9 ← 9/9 | 6/9 ← 9/9 | 20/24 ← 24/24 | 21/24 ← 24/24 |
| `python-billing` | 9/9 ← 9/9 | 8/9 ← 9/9 | 27/27 ← 27/27 | 24/27 ← 27/27 |
| `ts-reservas` | 6/9 ← 8/9 | 6/9 ← 9/9 | 14/18 ← 12/18 | 8/18 ← 18/18 |

La maggior parte delle cadute (9 su 12) è alla richiesta 3: 1/3 e 1/3 su `c-recq`, 1/3 e 0/3
su `ts-reservas`. Alla richiesta 3 di `ts-reservas`, skills-only rompe 12 invarianti su 51.

### Catene da 1
Il soffitto regge: 9/9 per entrambi i bracci con luna come con sol. Latenti 36/39 per entrambi
(sol: 37/39 e 36/39). USD per braccio 0,02 e 0,04 (sol: 0,74 e 1,60), mediana 50 e 63 s (sol: 128
e 169 s).

### Regola di TBA-03 (accettazione appaiata con `bare`)
| Catena | Coppie | skills-only | bare | Solo skills-only | Solo bare | Differenza | Holm p | Decisione |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| da 1 | 9 | 9 | 9 | 0 | 0 | +0 | 1 | indistinguishable |
| da 3 | 27 | 20 | 22 | 2 | 4 | −2 | 0,6875 | indistinguishable |

Vince `bare` per il pareggio al braccio più semplice. Con sol la decisione era la stessa (+1,
p 1).

### Compaction
Zero compaction in tutte le 54 richieste con luna: su catene da 3 di questi scenari il contesto
non si riempie. Per sol non c'è il dato, perché i record di `db07-pilot` precedono il conteggio
introdotto in DBH-02.

## Lettura
1. **Luna medium basta a staccare i bracci dal soffitto, ma non a separarli.** L'accettazione a 3
   scende di 4 e 7 richieste, compaiono trappole violate e skills-only perde latenti. La
   differenza fra i bracci (−2) resta però sotto la soglia di 3, e il p resta lontano da 0,05.
2. **Il regime più difficile non premia skills-only su questi scenari.** Con luna skills-only
   perde più di `bare` in accettazione, latenti e invarianti, soprattutto su `ts-reservas`. Con
   27 coppie la differenza non è distinguibile dal caso. È un dato di contesto, non una
   classifica.
3. **Gli scenari nuovi restano necessari.** Già alla terza richiesta luna esce dal soffitto sugli
   scenari facili, quindi catene da 12 su sistemi reali dovrebbero dare differenze più ampie.
   Resta da verificarlo nel pilota (DBH-08).
4. **Costo.** Una catena da 3 costa circa 0,01 $ con luna, contro 0,40-0,90 $ con sol. Il tetto
   del pilota (40 $) e della misura (250 $) è largo per i bracci senza driver. Il costo reale di
   Autopilot e dei driver con luna lo misura il pilota.

## Limiti
- Modello e thinking cambiano insieme: la nota non attribuisce l'effetto a uno dei due.
- 3 ripetizioni per braccio e scenario, solo due bracci e solo catene da 3.
- Il riferimento `db07-pilot` gira in un orario diverso e con cache del provider diverse.
- Una richiesta è stata rifatta dopo un'interruzione voluta, con l'harness a un commit
  successivo che cambia solo la ripresa.
