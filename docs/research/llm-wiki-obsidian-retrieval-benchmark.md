# Disposable hybrid-retrieval benchmark over the Obsidian notes

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-obsidian-retrieval-benchmark`
- Role: `research`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

Produced by [OHR-02 — Benchmark disposable hybrid retrieval](../tickets/llm-wiki-obsidian-hybrid-retrieval/done/02-benchmark-disposable-hybrid-retrieval.md).

## Research question

On read-only copies of the three supplied notes, what quality, citation, latency, update/removal, and explicit-link behavior is observed for deterministic direct lookup, BM25 lexical ranking, BM25 plus a precisely named sparse lexical vector, and at most one-hop expansion—without installing or downloading a model, calling a provider, or mutating a durable wiki?

## Answer

No winner or production threshold is declared: this tiny corpus does not justify either. BM25 had the lowest observed unsupported-context rate (`0.366667`) and tied the fusion methods for macro MRR (`0.9`) and citation correctness (`0.9`). RRF over BM25 and sparse TF-IDF did not improve macro recall over either component (`0.783333`). Adding one real explicit-link hop raised macro Recall@5 from `0.783333` to `0.816667`, entirely through Q10, while leaving macro unsupported-context rate at `0.4` and adding visibly irrelevant expanded chunks on other questions. Q04 missed all three human-judged summary sections under every method, so cross-note synthesis remains an unsolved fixture rather than a claimed success.

The vector component was **sparse TF-IDF cosine lexical vector**, not a semantic embedding. No approved pre-existing semantic embedding model/runtime existed inside the declared standard-library, no-HTTP, no-install, no-download boundary. The observed environment had no `numpy`, `scipy`, `sklearn`, `sentence_transformers`, `torch`, or `transformers`; `qmd` was absent. An Ollama executable existed but was not invoked because an HTTP/model boundary was neither declared nor authorized. This limitation is measured, not relabeled as semantic evidence.

## Source and fixture identity

The exact-byte digest convention matches OHR-01 and remains distinct from `llm-wiki` universal-newline normalized text digests.

| ID | Original path | Bytes | Exact byte SHA-256 | Disposable copy |
|---|---|---:|---|---|
| S1 | `/Users/carlogiuseppesergi/Downloads/come-usiamo-obsidian.md` | 10,510 | `eecbb8aa6a187a68e2afaeea381c6a53cc80c3b5e9a0d98b01996de8b7b64b6f` | `/private/tmp/ohr-02-benchmark-20260901.9QPyUs/sources/S1.md` mode `0o444` before the controlled update/removal test |
| S2 | `/Users/carlogiuseppesergi/Downloads/obsidian-rag-ibrido-tecnologia.md` | 15,493 | `b4faac15f70ac9a0f96b040518fa5abea68810bdbf2d9792bcda2a9111b7c62c` | `/private/tmp/ohr-02-benchmark-20260901.9QPyUs/sources/S2.md` mode `0o444` before the controlled update/removal test |
| S3 | `/Users/carlogiuseppesergi/Downloads/obsidian-implementazione-tecnica.md` | 13,070 | `6f03b0e2867e60a0ab07aadda264f85ef5c13a3eac947e2b67e971d8ad25b9ff` | `/private/tmp/ohr-02-benchmark-20260901.9QPyUs/sources/S3.md` mode `0o444` before the controlled update/removal test |

- Fixture: `/private/tmp/ohr-02-benchmark-20260901.9QPyUs`; created before retrieval and deleted after the run.
- Human-readable question fixture: SHA-256 `838d0aa1997c6fb7685e9d2c3836542bddf23efdc5036c082646892885c9aa4b`, 10 questions, frozen at `2026-09-01T09:12:28.462579+00:00` with `retrieval_executed_before_freeze: false`.
- Harness: disposable `run_benchmark.py`, SHA-256 `4083539ba220fb89ecfae7e545359d9ba13b2f7b8d94e9f1b860b786f45347e0`; it imported only the Python standard library and contained no network client or subprocess execution seam.
- Transient result JSON: SHA-256 `c00741f861e08932c7d9bb04a1afa35b45e8300d7e10a2c41aa4c3dd287cd7a5`; its aggregate and per-question rows are reproduced below, then the file was deleted with the fixture.

## Benchmark contract

### Runtime and corpus

- Runtime: CPython 3.14.6 on `macOS-26.6.2-arm64-arm-64bit-Mach-O`; one process; standard library only.
- Corpus: 3 source copies, 57 deterministic chunks.
- Chunking: headings levels 1–4; at most 180 whitespace tokens per chunk; 30 token overlap; source title prepended. IDs are `source:tokenized-heading:two-digit-part`, with the heading slug truncated to 72 characters.
- Tokenization: Unicode/Italian-capable regex `[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+(?:-[A-Za-zÀ-ÖØ-öø-ÿ0-9_]+)*`, case-folding, no stemming. The complete sorted stopword set is: `a, ad, al, alla, alle, anche, and, c, che, chi, come, con, cosa, da, dal, dalla, davvero, delle, di, dove, e, ed, egrave, gli, ha, i, il, in, is, la, le, lo, ma, nel, nella, non, o, of, oggi, or, parte, per, piu, quale, quali, quando, resta, se, secondo, senza, solo, sono, su, the, to, tra, un, una, usa, viene`.
- Result depth: top 5. Ties use lexicographic chunk ID.
- Timing: `time.perf_counter_ns`; the reported **cold-per-question** value is the first invocation for that question in fixed Q01–Q10 order after one shared index build, so Q02 onward may benefit from process/cache warming. Warm is the median of the next 30 immediately repeated deterministic calls. Neither value is an OS-, process-, model-, or service-cold measurement; the sub-millisecond numbers are local comparative observations only.

### Methods

1. **`direct-token-lookup`** — no corpus statistic: title/heading matches receive 5× weight, body occurrences are capped at three per term, and an exact normalized query phrase adds 12.
2. **`bm25-lexical`** — BM25 with `k1=1.2`, `b=0.75`, corpus document frequency, and positive-score abstention.
3. **`sparse-tfidf-cosine-lexical-vector`** — raw term frequency × smoothed IDF `log((N+1)/(df+1))+1`, sparse cosine similarity, positive-score abstention. This is lexical, not semantic.
4. **`rrf-bm25-plus-sparse-tfidf`** — Reciprocal Rank Fusion over methods 2 and 3 using `k=60`; raw score scales are not mixed.
5. **`rrf-plus-one-hop-explicit-links`** — method 4 seeds its first three chunks, parses `[[target]]` by source title/stem and relative Markdown `.md` links by basename, follows only resolvable source edges once, records `expanded-from` and edge syntax, then fills to top five. No inferred edge or repeated hop exists.

### Measures

- `Recall@5`: fraction of independently frozen relevance entries represented by at least one top-five chunk. For Q09, an empty result is scored as correct recall.
- `Precision@3`: relevant fraction of the first three returned chunks. `Unsupported-context rate = 1 - Precision@3`.
- `MRR`: reciprocal rank of the first relevant chunk. For Q09, correct abstention is `1`.
- Citation correctness: top-ranked chunk is relevant, or the no-answer case returns no chunk. Every row retains source/chunk ID; expanded rows retain the seed edge.
- Macro summaries are the arithmetic mean of the ten per-question rows below.

## Frozen questions and judgments

| Q | Category | Question | Human-frozen relevance | Citation expectation |
|---|---|---|---|---|
| Q01 | `direct-fact` | Quale protocollo e porta usa davvero Local REST API e il percorso automatico lo usa oggi? | S1:Il plugin Local REST API: cosa fa davvero oggi; S3:2. Il plugin Obsidian Local REST API — configurazione reale | Cite S1 Local REST API and/or S3 section 2; distinguish HTTPS 27124 from the unused automatic path. |
| Q02 | `direct-fact` | Quante note contiene il vault e come sono distribuite tra Procedure Entita e MOC? | S1:La struttura del vault | Cite S1 vault structure with 39 total, 27 Procedure, 11 Entita, and 1 MOC. |
| Q03 | `terminology` | Che differenza c'e tra embedding similarita del coseno e indice HNSW? | S2:Come funziona la ricerca vettoriale (in breve); S3:3. Lo schema Postgres; S3:5. Il retrieval — query reale | Cite S2 vector terminology or S3 schema/query details; do not equate HNSW with the note graph. |
| Q04 | `cross-note-synthesis` | Quali componenti sono reali oggi quali sono tecnica generale e quali sono implementati nel rapporto tecnico? | S1:Riepilogo: cosa è reale oggi; S2:Riepilogo: da dove cominciare; S3:Stato finale, in una tabella | Cite all three summary sections and preserve their different evidence scopes. |
| Q05 | `implementation-boundary` | Il servizio legge il vault via rete oppure dal filesystem montato e quale parte resta solo configurata? | S1:Il plugin Local REST API: cosa fa davvero oggi; S3:1. Il vault e come arriva al servizio; S3:2. Il plugin Obsidian Local REST API — configurazione reale | Cite S1 or S3; filesystem batch path is active and Local REST API is configured but not called by code. |
| Q06 | `privacy` | Quali metadati governano classificazione PII e visibilita tenant e dove viene applicato il filtro ACL? | S1:Il frontmatter: metadati obbligatori, non decorativi; S3:3. Lo schema Postgres; S3:5. Il retrieval — query reale | Cite S1 frontmatter and/or S3 schema/query; no claim that this is the current llm-wiki privacy policy. |
| Q07 | `incremental-update` | Quando cambia una nota cosa viene ricalcolato secondo hash e quali vicini propone il grafo? | S1:Dal file alla risposta: cosa succede a una nota; S2:8. Aggiornamento incrementale guidato dal grafo (medio costo); S3:4.4 Scrittura incrementale | Cite hash-based changed-note behavior separately from the proposed changed-note-plus-backlinks technique. |
| Q08 | `graph-terminology` | Come funzionano wikilink e attraversamento guidato dal modello senza un motore di grafo dedicato? | S1:I wikilink: il grafo che gli esperti scrivono; S2:L'alternativa leggera: grafo esplicito + attraversamento guidato dal modello | Cite S1 wikilinks and/or S2 lightweight traversal; distinguish described behavior from current llm-wiki behavior. |
| Q09 | `no-answer` | OHR_PRODUCTION_P95_MS | none (abstain) | Return no context; the source bundle defines no approved production P95 threshold. |
| Q10 | `explicit-link-expansion` | Quali documenti concettuali richiama esplicitamente il rapporto di implementazione e quali prospettive aggiungono? | S3:Come abbiamo implementato Obsidian nel progetto; S1:*; S2:* | Seed on the S3 introduction and trace its two real relative Markdown links to S1 and S2; expanded chunks must retain edge provenance. |

The judgments above were authored and hashed before any retrieval ran. They came from direct reading of the sources, never from rankings under test.

## Explicit-link boundary

The three-file corpus has **no resolvable wikilink target**: nine wikilink-like occurrences are examples or point to absent vault notes. It does have two real, resolvable relative Markdown edges in S3’s introduction:

- `S3 --markdown-link:come-usiamo-obsidian.md--> S1`
- `S3 --markdown-link:obsidian-rag-ibrido-tecnologia.md--> S2`

Those two real edges—not example wikilinks—drive the measured one-hop method. A strictly separate two-file synthetic control used `SYN1 [[Target Note]] -> SYN2`; seed retrieval returned `SYN1:seed-note:01` and one-hop expansion added `SYN2:target-note:01` with `kind=expanded`. The control passed and never entered corpus metrics. Thus real Markdown-edge behavior and synthetic wikilink plumbing are not conflated.

## Index build observations

| Component | Build ns |
|---|---:|
| Direct index wrapper | 1000 |
| BM25 lexical index | 516292 |
| Sparse TF-IDF lexical-vector index | 1123584 |
| Explicit-link graph | 178375 |
| BM25 + sparse TF-IDF used by RRF | 1639876 |
| Complete disposable build | 1819251 |

The corpus is too small for these build times to predict production cost; they are retained to make this run auditable.

## Aggregate results

| Method | Recall@5 | Precision@3 | MRR | Citation correct | Unsupported context | First-call (“cold-per-question”) median ns | Warm median ns |
|---|---:|---:|---:|---:|---:|---:|---:|
| `direct-token-lookup` | 0.733333 | 0.6 | 0.75 | 0.7 | 0.4 | 571354 | 565593 |
| `bm25-lexical` | 0.783333 | 0.633333 | 0.9 | 0.9 | 0.366667 | 45750 | 37271 |
| `sparse-tfidf-cosine-lexical-vector` | 0.783333 | 0.566667 | 0.85 | 0.8 | 0.433333 | 49562 | 40458 |
| `rrf-bm25-plus-sparse-tfidf` | 0.783333 | 0.6 | 0.9 | 0.9 | 0.4 | 109813 | 94905 |
| `rrf-plus-one-hop-explicit-links` | 0.816667 | 0.6 | 0.9 | 0.9 | 0.4 | 127437 | 110604 |

## Per-question raw aggregate rows

`R` means a human-judged relevant chunk, `N` unsupported context, and `E←seed` a one-hop addition. Rows preserve exact ranking order. These values are sufficient to recompute every macro score above.

| Method | Q | Ranked chunk IDs | R@5 | P@3 | MRR | Citation | UCR | First-call ns | Warm median ns |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `direct-token-lookup` | Q01 | `S1:plugin-local-rest-api-fa:01[R]` `S3:plugin-obsidian-local-rest-api-configurazione-reale:01[R]` `S1:plugin-local-rest-api-fa:02[R]` `S1:riepilogo-reale:01[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 718292 | 645583 |
| `direct-token-lookup` | Q02 | `S1:struttura-del-vault:01[R]` `S1:note-correlate:01[N]` `S3:vault-arriva-servizio:01[N]` `S1:plugin-local-rest-api-fa:01[N]` `S1:riepilogo-reale:01[N]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 684708 | 617084 |
| `direct-token-lookup` | Q03 | `S3:cache-del-modello-embedding-persistente:01[N]` `S1:plugin-local-rest-api-fa:01[N]` `S1:plugin-local-rest-api-fa:02[N]` `S1:struttura-del-vault:01[N]` `S2:chunking-consapevole-del-grafo-basso-costo-alto-impatto:01[N]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 561000 | 564979 |
| `direct-token-lookup` | Q04 | `S2:funziona-motore-graph-rag-vero-caso-generale:01[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` `S3:bug-reali-risolti-durante-attivazione:01[N]` `S3:abbiamo-implementato-obsidian-progetto:01[N]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 528167 | 537062 |
| `direct-token-lookup` | Q05 | `S3:vault-arriva-servizio:01[R]` `S1:plugin-local-rest-api-fa:01[R]` `S1:struttura-del-vault:01[N]` `S1:plugin-local-rest-api-fa:02[R]` `S3:stato-finale-tabella:01[N]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 588167 | 591375 |
| `direct-token-lookup` | Q06 | `S1:frontmatter-metadati-obbligatori-decorativi:01[R]` `S3:schema-postgres:01[R]` `S3:tenant-default-disallineato:01[N]` `S1:frontmatter-metadati-obbligatori-decorativi:02[R]` `S3:retrieval-query-reale:01[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 572417 | 566208 |
| `direct-token-lookup` | Q07 | `S2:ranking-centralità-grafo-basso-costo:01[N]` `S1:file-risposta-succede-nota:01[R]` `S1:wikilink-grafo-esperti-scrivono:01[N]` `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[N]` | 0.666667 | 0.333333 | 0.5 | 0 | 0.666667 | 569875 | 545167 |
| `direct-token-lookup` | Q08 | `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[R]` `S1:wikilink-grafo-esperti-scrivono:01[R]` `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:01[N]` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 570292 | 553771 |
| `direct-token-lookup` | Q09 | `ABSTAIN` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 482459 | 470563 |
| `direct-token-lookup` | Q10 | `S2:hypothetical-document-embeddings-hyde-medio-costo:01[R]` `S1:plugin-local-rest-api-fa:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:funziona-motore-graph-rag-vero-caso-generale:01[R]` `S2:leve-concrete-ottimizzare-retrieval:01[R]` | 0.666667 | 1.0 | 1.0 | 1 | 0.0 | 589833 | 575937 |
| `bm25-lexical` | Q01 | `S1:plugin-local-rest-api-fa:01[R]` `S1:riepilogo-reale:01[N]` `S3:plugin-obsidian-local-rest-api-configurazione-reale:01[R]` `S1:plugin-local-rest-api-fa:02[R]` `S3:architettura-dei-componenti-coinvolti:01[N]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 55375 | 32875 |
| `bm25-lexical` | Q02 | `S1:struttura-del-vault:01[R]` `S1:riepilogo-reale:01[N]` `S2:problema-fondo-due-modi-diversi-trovare-informazione-giusta:01[N]` `S1:git-governance-pensata-stato-reale:01[N]` `S1:note-correlate:01[N]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 52208 | 44583 |
| `bm25-lexical` | Q03 | `S3:retrieval-query-reale:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[R]` `S3:schema-postgres:01[R]` `S2:fusione-più-liste-risultati-reciprocal-rank-fusion-medio-costo:01[N]` `S3:embedding:01[N]` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 49625 | 41667 |
| `bm25-lexical` | Q04 | `S3:abbiamo-implementato-obsidian-progetto:01[N]` `S2:obsidian-rag-ibrido-funziona-tecnologia-si-ottimizza:01[N]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` `S3:bug-reali-risolti-durante-attivazione:01[N]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 38584 | 25604 |
| `bm25-lexical` | Q05 | `S3:vault-arriva-servizio:01[R]` `S3:stato-finale-tabella:01[N]` `S1:plugin-local-rest-api-fa:01[R]` `S1:plugin-local-rest-api-fa:02[R]` `S3:embedding:01[N]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 46041 | 41729 |
| `bm25-lexical` | Q06 | `S3:schema-postgres:01[R]` `S1:frontmatter-metadati-obbligatori-decorativi:01[R]` `S3:parsing-validazione-del-frontmatter:01[N]` `S3:tenant-default-disallineato:01[N]` `S1:frontmatter-metadati-obbligatori-decorativi:02[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 35167 | 30542 |
| `bm25-lexical` | Q07 | `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[R]` `S2:riepilogo-cominciare:02[N]` `S2:funziona-ricerca-vettoriale-breve:01[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N]` `S3:scrittura-incrementale:01[R]` | 0.666667 | 0.333333 | 1.0 | 1 | 0.666667 | 45459 | 42729 |
| `bm25-lexical` | Q08 | `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[R]` `S1:perché-comunque-senso-così:01[N]` `S1:note-correlate:01[N]` `S3:cache-del-modello-embedding-persistente:01[N]` | 0.5 | 0.666667 | 1.0 | 1 | 0.333333 | 60458 | 47000 |
| `bm25-lexical` | Q09 | `ABSTAIN` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 12375 | 6250 |
| `bm25-lexical` | Q10 | `S2:leve-concrete-ottimizzare-retrieval:01[R]` `S3:abbiamo-implementato-obsidian-progetto:01[R]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[R]` `S3:tool-arriva-modello:01[N]` `S2:reranking-cross-encoder-medio-alto-costo:01[R]` | 0.666667 | 1.0 | 1.0 | 1 | 0.0 | 29167 | 26292 |
| `sparse-tfidf-cosine-lexical-vector` | Q01 | `S1:plugin-local-rest-api-fa:01[R]` `S1:riepilogo-reale:01[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` `S3:plugin-obsidian-local-rest-api-configurazione-reale:01[R]` `S1:plugin-local-rest-api-fa:02[R]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 74125 | 38958 |
| `sparse-tfidf-cosine-lexical-vector` | Q02 | `S1:struttura-del-vault:01[R]` `S1:riepilogo-reale:01[N]` `S2:problema-fondo-due-modi-diversi-trovare-informazione-giusta:01[N]` `S1:plugin-local-rest-api-fa:01[N]` `S1:git-governance-pensata-stato-reale:01[N]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 54958 | 43791 |
| `sparse-tfidf-cosine-lexical-vector` | Q03 | `S3:retrieval-query-reale:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[R]` `S1:plugin-local-rest-api-fa:02[N]` `S3:embedding:01[N]` `S2:fusione-più-liste-risultati-reciprocal-rank-fusion-medio-costo:01[N]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 50875 | 41958 |
| `sparse-tfidf-cosine-lexical-vector` | Q04 | `S3:abbiamo-implementato-obsidian-progetto:01[N]` `S2:obsidian-rag-ibrido-funziona-tecnologia-si-ottimizza:01[N]` `S3:bug-reali-risolti-durante-attivazione:01[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[N]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 40708 | 36041 |
| `sparse-tfidf-cosine-lexical-vector` | Q05 | `S3:vault-arriva-servizio:01[R]` `S1:plugin-local-rest-api-fa:01[R]` `S3:section:01[N]` `S3:stato-finale-tabella:01[N]` `S1:plugin-local-rest-api-fa:02[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 54875 | 45583 |
| `sparse-tfidf-cosine-lexical-vector` | Q06 | `S3:tenant-default-disallineato:01[N]` `S1:frontmatter-metadati-obbligatori-decorativi:01[R]` `S3:schema-postgres:01[R]` `S3:parsing-validazione-del-frontmatter:01[N]` `S3:retrieval-query-reale:01[R]` | 1.0 | 0.666667 | 0.5 | 0 | 0.333333 | 44333 | 38499 |
| `sparse-tfidf-cosine-lexical-vector` | Q07 | `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[N]` `S2:riepilogo-cominciare:02[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N]` `S1:file-risposta-succede-nota:01[R]` | 0.666667 | 0.333333 | 1.0 | 1 | 0.666667 | 48250 | 42354 |
| `sparse-tfidf-cosine-lexical-vector` | Q08 | `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[R]` `S1:perché-comunque-senso-così:01[N]` `S3:cache-del-modello-embedding-persistente:01[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:01[N]` | 0.5 | 0.666667 | 1.0 | 1 | 0.333333 | 54250 | 46708 |
| `sparse-tfidf-cosine-lexical-vector` | Q09 | `ABSTAIN` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 2500 | 1125 |
| `sparse-tfidf-cosine-lexical-vector` | Q10 | `S2:leve-concrete-ottimizzare-retrieval:01[R]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[R]` `S3:abbiamo-implementato-obsidian-progetto:01[R]` `S3:tool-arriva-modello:01[N]` `S2:reranking-cross-encoder-medio-alto-costo:01[R]` | 0.666667 | 1.0 | 1.0 | 1 | 0.0 | 32500 | 29479 |
| `rrf-bm25-plus-sparse-tfidf` | Q01 | `S1:plugin-local-rest-api-fa:01[R]` `S1:riepilogo-reale:01[N]` `S3:plugin-obsidian-local-rest-api-configurazione-reale:01[R]` `S3:architettura-dei-componenti-coinvolti:01[N]` `S1:plugin-local-rest-api-fa:02[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 95334 | 78541 |
| `rrf-bm25-plus-sparse-tfidf` | Q02 | `S1:struttura-del-vault:01[R]` `S1:riepilogo-reale:01[N]` `S2:problema-fondo-due-modi-diversi-trovare-informazione-giusta:01[N]` `S1:git-governance-pensata-stato-reale:01[N]` `S1:plugin-local-rest-api-fa:01[N]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 124292 | 109874 |
| `rrf-bm25-plus-sparse-tfidf` | Q03 | `S3:retrieval-query-reale:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[R]` `S1:plugin-local-rest-api-fa:02[N]` `S2:fusione-più-liste-risultati-reciprocal-rank-fusion-medio-costo:01[N]` `S3:embedding:01[N]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 128125 | 114625 |
| `rrf-bm25-plus-sparse-tfidf` | Q04 | `S3:abbiamo-implementato-obsidian-progetto:01[N]` `S2:obsidian-rag-ibrido-funziona-tecnologia-si-ottimizza:01[N]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[N]` `S3:bug-reali-risolti-durante-attivazione:01[N]` `S3:architettura-dei-componenti-coinvolti:01[N]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 77625 | 72396 |
| `rrf-bm25-plus-sparse-tfidf` | Q05 | `S3:vault-arriva-servizio:01[R]` `S1:plugin-local-rest-api-fa:01[R]` `S3:stato-finale-tabella:01[N]` `S3:section:01[N]` `S1:plugin-local-rest-api-fa:02[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 126416 | 110542 |
| `rrf-bm25-plus-sparse-tfidf` | Q06 | `S3:schema-postgres:01[R]` `S1:frontmatter-metadati-obbligatori-decorativi:01[R]` `S3:tenant-default-disallineato:01[N]` `S3:parsing-validazione-del-frontmatter:01[N]` `S1:frontmatter-metadati-obbligatori-decorativi:02[R]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 86834 | 79937 |
| `rrf-bm25-plus-sparse-tfidf` | Q07 | `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[N]` `S2:riepilogo-cominciare:02[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N]` `S1:file-risposta-succede-nota:01[R]` | 0.666667 | 0.333333 | 1.0 | 1 | 0.666667 | 139583 | 115604 |
| `rrf-bm25-plus-sparse-tfidf` | Q08 | `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[R]` `S1:perché-comunque-senso-così:01[N]` `S3:cache-del-modello-embedding-persistente:01[N]` `S2:instradamento-della-query-query-routing-medio-costo:01[N]` | 0.5 | 0.666667 | 1.0 | 1 | 0.333333 | 127708 | 122895 |
| `rrf-bm25-plus-sparse-tfidf` | Q09 | `ABSTAIN` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 12584 | 8500 |
| `rrf-bm25-plus-sparse-tfidf` | Q10 | `S2:leve-concrete-ottimizzare-retrieval:01[R]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[R]` `S3:abbiamo-implementato-obsidian-progetto:01[R]` `S3:tool-arriva-modello:01[N]` `S2:reranking-cross-encoder-medio-alto-costo:01[R]` | 0.666667 | 1.0 | 1.0 | 1 | 0.0 | 75125 | 64104 |
| `rrf-plus-one-hop-explicit-links` | Q01 | `S1:plugin-local-rest-api-fa:01[R]` `S1:riepilogo-reale:01[N]` `S3:plugin-obsidian-local-rest-api-configurazione-reale:01[R]` `S1:plugin-local-rest-api-fa:02[R;E←S3:plugin-obsidian-local-rest-api-configurazione-reale:01]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[N;E←S3:plugin-obsidian-local-rest-api-configurazione-reale:01]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 116625 | 95042 |
| `rrf-plus-one-hop-explicit-links` | Q02 | `S1:struttura-del-vault:01[R]` `S1:riepilogo-reale:01[N]` `S2:problema-fondo-due-modi-diversi-trovare-informazione-giusta:01[N]` `S1:git-governance-pensata-stato-reale:01[N]` `S1:plugin-local-rest-api-fa:01[N]` | 1.0 | 0.333333 | 1.0 | 1 | 0.666667 | 159500 | 129792 |
| `rrf-plus-one-hop-explicit-links` | Q03 | `S3:retrieval-query-reale:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[R]` `S1:plugin-local-rest-api-fa:02[N]` `S1:struttura-del-vault:01[N;E←S3:retrieval-query-reale:01]` `S2:fusione-più-liste-risultati-reciprocal-rank-fusion-medio-costo:01[N;E←S3:retrieval-query-reale:01]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 142459 | 131250 |
| `rrf-plus-one-hop-explicit-links` | Q04 | `S3:abbiamo-implementato-obsidian-progetto:01[N]` `S2:obsidian-rag-ibrido-funziona-tecnologia-si-ottimizza:01[N]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[N]` `S1:usiamo-obsidian-knowledge-base-del-chatbot:01[N;E←S3:abbiamo-implementato-obsidian-progetto:01]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N;E←S3:abbiamo-implementato-obsidian-progetto:01]` | 0.0 | 0.0 | 0.0 | 0 | 1.0 | 97875 | 86854 |
| `rrf-plus-one-hop-explicit-links` | Q05 | `S3:vault-arriva-servizio:01[R]` `S1:plugin-local-rest-api-fa:01[R]` `S3:stato-finale-tabella:01[N]` `S1:plugin-local-rest-api-fa:02[R;E←S3:vault-arriva-servizio:01]` `S2:problema-fondo-due-modi-diversi-trovare-informazione-giusta:02[N;E←S3:vault-arriva-servizio:01]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 138250 | 126167 |
| `rrf-plus-one-hop-explicit-links` | Q06 | `S3:schema-postgres:01[R]` `S1:frontmatter-metadati-obbligatori-decorativi:01[R]` `S3:tenant-default-disallineato:01[N]` `S1:frontmatter-metadati-obbligatori-decorativi:02[R;E←S3:schema-postgres:01]` `S2:reranking-cross-encoder-medio-alto-costo:01[N;E←S3:schema-postgres:01]` | 1.0 | 0.666667 | 1.0 | 1 | 0.333333 | 103583 | 94770 |
| `rrf-plus-one-hop-explicit-links` | Q07 | `S2:aggiornamento-incrementale-guidato-grafo-medio-costo:01[R]` `S2:funziona-ricerca-vettoriale-breve:01[N]` `S2:riepilogo-cominciare:02[N]` `S2:funziona-motore-graph-rag-vero-caso-generale:02[N]` `S1:file-risposta-succede-nota:01[R]` | 0.666667 | 0.333333 | 1.0 | 1 | 0.666667 | 139542 | 129895 |
| `rrf-plus-one-hop-explicit-links` | Q08 | `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:01[R]` `S2:alternativa-leggera-grafo-esplicito-attraversamento-guidato-modello:02[R]` `S1:perché-comunque-senso-così:01[N]` `S3:cache-del-modello-embedding-persistente:01[N]` `S2:instradamento-della-query-query-routing-medio-costo:01[N]` | 0.5 | 0.666667 | 1.0 | 1 | 0.333333 | 149750 | 137396 |
| `rrf-plus-one-hop-explicit-links` | Q09 | `ABSTAIN` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 25833 | 23937 |
| `rrf-plus-one-hop-explicit-links` | Q10 | `S2:leve-concrete-ottimizzare-retrieval:01[R]` `S2:hypothetical-document-embeddings-hyde-medio-costo:01[R]` `S3:abbiamo-implementato-obsidian-progetto:01[R]` `S1:plugin-local-rest-api-fa:01[R;E←S3:abbiamo-implementato-obsidian-progetto:01]` `S2:reranking-cross-encoder-medio-alto-costo:01[R;E←S3:abbiamo-implementato-obsidian-progetto:01]` | 1.0 | 1.0 | 1.0 | 1 | 0.0 | 91792 | 80041 |

## Update and removal control

The harness made only the S2 **copy** writable, appended a new `## Disposable sentinel update` section containing `ohrincrementalsentinel`, and rebuilt all derived state. The fusion result was ``S2:disposable-sentinel-update:01``; `update_passed=true`. The updated corpus had 58 chunks and rebuild took 1467208 ns.

It then deleted the S2 copy and rebuilt from S1/S3. The sentinel returned `[]`; no S2 chunk remained; `removal_passed=true`. The remaining corpus had 34 chunks and rebuild took 1031833 ns. This proves the prototype’s full rebuild removes changed/deleted content; it does not establish a production incremental invalidation algorithm or backlink policy.

## Gain and cost comparison

- BM25 improved over direct lookup on terminology and citation metrics while using a prebuilt corpus-statistics index. Direct lookup intentionally retokenized every chunk per call, so its higher local latency is an implementation observation, not an algorithmic guarantee.
- Sparse TF-IDF is a second lexical view. Fusion’s equal Recall@5 (`0.783333`) shows that combining correlated lexical methods did not add coverage here; it did change rankings and unsupported context.
- One-hop expansion added the missing S1 judgment on Q10 and raised macro recall by `0.033334`. It also injected nonrelevant neighbor chunks on questions such as Q01 and Q03. Explicit edges can add traceable coverage and traceable noise.
- Every method correctly abstained on Q09 because its sole token was outside the corpus. This proves only the fixed zero-overlap control, not general hallucination resistance.
- Q04’s zero recall under all methods is the strongest negative result: matching the human-selected summary sections requires better query formulation, a genuinely semantic method, reranking, different judgments, or another bounded experiment. This report does not choose among them.
- Timing, build cost, and quality all come from three notes and ten questions. No result authorizes a production threshold, provider, database, source-copy policy, privacy policy, graph algorithm, or adoption tier.

## Cleanup and non-mutation evidence

- Pre-cleanup fixture inventory: `8` regular files and `171180` bytes under `/private/tmp/ohr-02-benchmark-20260901.9QPyUs`. S2 was intentionally absent at this point because the removal control had deleted its copy.
- Post-cleanup inventory: fixture existence `false`, entries `[]`. The harness, question fixture, remaining source copies, synthetic control, chunks, vectors, indexes, cache-equivalent objects, query results, and transient result JSON were deleted; the S2 copy had already been removed by the deletion control.
- Original unchanged: `/Users/carlogiuseppesergi/Downloads/come-usiamo-obsidian.md` → `eecbb8aa6a187a68e2afaeea381c6a53cc80c3b5e9a0d98b01996de8b7b64b6f`.
- Original unchanged: `/Users/carlogiuseppesergi/Downloads/obsidian-rag-ibrido-tecnologia.md` → `b4faac15f70ac9a0f96b040518fa5abea68810bdbf2d9792bcda2a9111b7c62c`.
- Original unchanged: `/Users/carlogiuseppesergi/Downloads/obsidian-implementazione-tecnica.md` → `6f03b0e2867e60a0ab07aadda264f85ef5c13a3eac947e2b67e971d8ad25b9ff`.
- The benchmark never wrote `knowledge/`, `wiki/queries/`, `raw/`, a database, a model cache, a provider log, or a repository-side retrieval index. No source content was sent to HTTP, MCP, Ollama, qmd, or another provider/runtime.
- Only this report and its reciprocal parent-map edge are intended repository changes. Operational QA/verification artifacts remain runner evidence, not retrieval state or wiki content.

## Limitations and OHR-03 inputs

- Relevance judgments are human-authored but single-reviewer and heading-oriented; Q04 shows sensitivity to that choice.
- Semantic embedding was unavailable inside the declared boundary. Sparse TF-IDF cannot answer semantic-vector questions and must never be cited as embedding evidence.
- Real one-hop evidence uses two relative Markdown edges, while wikilink resolution is only a separate synthetic control because the source bundle omits the example target notes.
- Latency excludes filesystem startup, service serialization, model inference, network, concurrency, and answer generation.
- The source documents report another project’s behavior; this prototype measures only retrieval over their text copies.
- Update/removal uses full rebuilds in disposable memory. It does not decide changed-note-plus-backlink invalidation, persisted answer invalidation, or cache retention.

OHR-03 must consider the measured lexical baseline, the unavailable semantic baseline, Q04 failure, Q10’s bounded recall/noise trade-off, source location, raw-byte versus normalized digest, privacy/retention/deletion, dependency/model/provider policy, expansion depth, and an explicit success threshold. This benchmark grants none of those decisions and does not emit OHR-04/OHR-05 production tickets.

## Conclusion

The corpus supports a reproducible local lexical baseline and traceable one-hop experiment, not a production architecture. The evidence favors keeping retrieval optional and derived while the human decision weighs whether the small Q10 recall gain, unchanged unsupported-context rate, failed Q04 synthesis, and absent semantic baseline justify another prototype or a no-build/content-only tier.
