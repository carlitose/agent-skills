# Tracked wiki Git-byte fidelity

## Artifact Graph
- Artifact ID: `spec:wiki-git-byte-fidelity`
- Role: `spec`
- Standalone: true

### Children
- [WBF-01 — Freeze and deliver exact Git-representation wiki bytes](../tickets/wiki-git-byte-fidelity/done/01-freeze-deliver-git-bytes.md)

## Type and status

Bug analysis; implementation pending. This is a new correction, not an amendment of an old validation receipt or a retry grant.

## Observed and expected behavior

APM-08 application PR #267 integrated successfully. Its separate tracked-wiki delivery failed before push with `delivery-invalid`: `materialized wiki branch differs from the frozen docs-only candidate`. The failed local branch and frozen candidate remain preserved.

Expected: a newly validated tracked wiki candidate can be materialized as a separate docs-only commit whose complete generated-file inventory, exact blob bytes, changed-path set, and parent match the validated candidate. Repository EOL settings must not silently transform bytes after validation.

## Evidence and root cause

Read-only probe and full path/hash readback:

- `.git/ticket-autopilot/diagnostics/wiki-materialization/probe.py`
- `.git/ticket-autopilot/diagnostics/wiki-materialization/readback.json`
- Original result: `.git/ticket-autopilot/runs/apm-local-recovery-23257eb8/artifacts/APM-08/publish-D-response.json`.

Preserved delivery head `861eebbbf189f8f2e6a1c8cb21ac5a739503c77e` has exactly parent `c9979c845f10bd99487b86fce17d69d0945f83e7`. The manifest validates, the 66 expected changed paths equal the 66 observed paths, and all 658 generated Markdown files are present. Exactly 657 frozen byte streams differ from their committed blobs; every difference disappears under CRLF-to-LF conversion. `core.autocrlf=true` is effective in this repository.

`llm-wiki/scripts/sync_project.py` currently hashes and freezes physical staged bytes, including Windows line endings. `ticket-autopilot/scripts/autopilot/wiki_sync.py::deliver_tracked_candidate` uses ordinary filtering `git add`, while `_head_matches_frozen` correctly compares committed blobs with literal `--no-filters` hashes. Thus the producer and delivery disagree about the byte representation. Confidence: high for this mechanism; the actual preserved artifacts reproduce it without a provider call. Wrong parent, missing files, extra changed paths, and corrupt manifest were ruled out for this failure.

Git's owning contract: [git-hash-object](https://git-scm.com/docs/git-hash-object) documents that `--no-filters` ignores attribute-selected input filters, including EOL conversion; normal staging applies those filters. Context7 documentation source: `/git/htmldocs`.

## Target behavior and semantic invariants

1. For **new internal-tracked candidates**, the producer determines the exact Git blob representation in the source repository's tracked path/attribute context, in disposable staging, **before** final candidate hashing, scope validation, lint, and receipt creation. A transformed candidate must be validated as transformed; validation of pre-filter content is insufficient.
2. Compare complete Git-representation before/after generated inventories to determine the exact declared changed paths. Preserve an independent literal protected-tree/source compare-and-swap and the complete managed-scope guard: normalization must not hide a forbidden file mutation. Baseline and candidate digests must have an explicit, consistent representation; no receipt may claim a physical tree while describing different filtered bytes.
3. Freeze exact, regular, non-executable UTF-8 Markdown blob bytes with the existing manifest/receipt integrity checks. Tracked baseline/candidate hashes use Git mode semantics (`0644` for non-executable regular blobs), not Windows' physical `0666` permission reporting. Keep literal filesystem mode/nonregular/executable checks and protected-state CAS separate. This representation applies consistently to freeze readback and delivery validation; old physical-mode manifests receive no compatibility fallback or rewrite. Preserve path, kind, mode, deletion, and full-tree checks. Do not implement ad hoc CRLF equivalence in the verifier.
4. Delivery inserts frozen bytes into a disposable index without applying clean/EOL filters again, using raw blob creation and exact index entries. Keep the single-parent, complete changed-path, complete generated-inventory, and raw blob identity assertions. No content changes after freezing, and no blind `git add` over already-filtered output.
5. Respect Git's configured representation: `text`/`eol` conversion yields the intended blobs; explicit `-text` can preserve CRLF. Test a deterministic non-idempotent clean filter to prove it is applied before validation and not again during delivery. Invalid UTF-8, unsafe scope, failed required filters, or byte/tree contradictions fail closed before provider publication.
6. No protected worktree, HEAD, index, repository configuration, global Git settings, or tracked attributes are rewritten to make the check pass. New content-addressed Git objects and owned candidate artifacts are permitted; publication remains caller-owned. Attribute/config inputs used for projection must not be silently mixed across one attempt.
7. External and internal-untracked direct-update behavior is unchanged. Existing failure classes, bounded source checkout, protected-source CAS, and exact remote-base revalidation remain operative.
8. Historical candidates, receipts, ledger events, gates, and failed branches are not edited, normalized, deleted, or relabeled. An old CRLF candidate is not made valid by weakening comparison. The existing historical outside-project-only retry command must not be widened as an incidental fix.

## Implementation slices

One AFK vertical slice, WBF-01: producer representation boundary, literal delivery adapter, regression tests, and contract documentation together. These own one invariant and must not be split into independent parallel mutations.

Prefer a small owner-local Git byte-projection helper behind `sync_project` and a raw-index adapter behind `deliver_tracked_candidate`. Reuse existing Git subprocess and native-path handling where appropriate. A temporary index or byte-fed object plumbing must preserve protected state and work under Windows long paths. Do not introduce compatibility schemas, fallback readers, or a parallel delivery format.

## Alternatives rejected

- Relax raw hashes to newline-insensitive equality: would approve bytes different from the frozen receipt.
- Turn off global/repository `core.autocrlf`: changes unrelated user policy and does not cover attributes or custom filters.
- Raw-stage the historical CRLF tree alone: changes hundreds of otherwise-unchanged files and violates the declared 66-path diff.
- Normalize only inside `_freeze_candidate` after receipt creation: publishes unvalidated bytes and stale identities.
- Retry or mark the historical failure successful: changes history without repairing the producer/delivery contract.

## Verification strategy and acceptance

- **Unit/integration:** deterministic LF and CRLF fixtures under `core.autocrlf=true/false`, `text eol=lf`, explicit `-text`, additions/deletions/unchanged pages, and a non-idempotent clean filter. Frozen blobs must equal materialized commit blobs, and declared changes must equal the full actual diff.
- Prove the final filtered bytes receive lint/scope checks; an invalid or forbidden filtered result must not acquire a passing receipt. Preserve dirty/protected files, HEAD/index/config snapshots, stale-tree checks, raw-byte rejection, and external/untracked behavior.
- Exercise public producer-to-delivery behavior using a local bare remote and a clearly simulated provider boundary; no live provider claim from fixtures.
- Run focused `llm-wiki/tests/test_sync_project.py`, `ticket-autopilot/tests/test_wiki_sync.py`, and `ticket-autopilot/tests/test_wiki_long_paths.py` coverage on Windows and, when available, Linux. Run project quick and relevant forward regression checks. A timeout or unavailable full suite remains inconclusive, not a pass.
- **Live:** only after normal fresh code quality and application integration, create a new wiki candidate through the normal sync boundary. Report its actual outcome separately. Wiki merge requires its own exact-head authorization or existing separate wiki grant; application merge authority does not transfer.

## Non-goals and preserved work

No SW semantic policy decision, APM-12/APM-13 execution or disposition change, local runtime-recovery patch delivery, wiki content redesign, arbitrary historical retry API, Pi synchronization, cleanup, or provider policy changes. Keep unrelated dirty files and all recovery/preimage artifacts intact. The old APM-08 wiki result remains terminally failed even if a later fresh synchronization succeeds.

## Open questions

No product decision blocks the correction. The exact helper shape and handling of concurrent attribute/config drift must be established by implementation tests. Live provider publication and any separate wiki merge remain independently gated; no success is claimed here.
