# LLM Wiki Docs-Only Auto-Sync Forward Test

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-docs-only-autosync-forward-test`
- Role: `research`
- Parent: [LLM Wiki Docs-Only Auto-Sync](../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Result

The deterministic forward matrix passes for both public trigger boundaries. The
[machine-readable report](llm-wiki-docs-only-autosync-forward-test.json) owns the raw
given/when/then scenarios, executable commands, expected test counts, invariants, and
limitations.

| Trigger | States exercised | Result |
| --- | --- | --- |
| After complete ticket batch | absent, untracked, tracked, ambiguous, partial, invalid graph | pass |
| After durable ticket integration | absent, external, untracked, tracked, retry, replay, policy pending | pass |
| Shared sync boundary | broken binding, multiple roots, partial tracking, mixed paths, lint failure, stale and concurrent change | pass |

The suite proves one sync per complete batch and one stable effect per durable integrated
ticket. Missing wikis are never scaffolded. External and internal-untracked output applies
directly only after validation. Internal tracked output remains a separate docs-only
candidate with exact-head authority and an `implementation-complete` claim ceiling.

## Reproduce

```bash
python3 -B -m unittest ticket-autopilot.tests.test_wiki_sync_forward_matrix
```

The test loads the report, rejects coverage or policy drift, and executes the listed public
boundary suites. The report intentionally does not treat wiki pages as primary evidence.

## Limitations

All cases use local temporary filesystems, disposable Git repositories, and deterministic
provider fakes. No production wiki, live provider mutation, or host-specific cross-process
queue is observed, so the result supports `implementation-complete`, not a live or
production-ready claim.
