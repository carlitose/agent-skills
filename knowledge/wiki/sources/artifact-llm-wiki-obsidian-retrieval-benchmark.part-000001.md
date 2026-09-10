---
type: source-part
source_identity: artifact:llm-wiki-obsidian-retrieval-benchmark
source_digest: sha256:638d7781d93dd19ec99e884674c0275e3b4755ce70ea983c06b87e4f4169a20d
source_entry: wiki/sources/artifact-llm-wiki-obsidian-retrieval-benchmark.md
---

# Preserved source — Part 2

Entry and provenance: [[sources/artifact-llm-wiki-obsidian-retrieval-benchmark]]

<!-- semantic-payload-v1: {"part_index":1,"payload_bytes":1734,"payload_sha256":"7f85d63f33554cf0fa369af0ba8e825baca7b6a4e0fa607f08b6e332ec1f1f96","schema":1,"source_digest":"sha256:638d7781d93dd19ec99e884674c0275e3b4755ce70ea983c06b87e4f4169a20d","source_identity":"artifact:llm-wiki-obsidian-retrieval-benchmark"} -->
```markdown
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

```
