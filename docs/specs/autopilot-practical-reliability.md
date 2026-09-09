# Practical Reliability for Ticket Autopilot

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability`
- Role: `spec`
- Standalone: true

### Children
- [APM-PREP-01 Rebind the wiki to this checkout](../tickets/autopilot-checkout-preparation/done/01-rebind-wiki.md)
- [APM-01 Practical prompt defaults](../tickets/autopilot-practical-reliability/done/01-practical-prompts.md)
- [APM-02 Portable final-tree Git paths](../tickets/autopilot-practical-reliability/done/02-portable-git-paths.md)
- [APM-03 Hermetic Git and line-ending tests](../tickets/autopilot-practical-reliability/done/03-hermetic-git-tests.md)
- [APM-04 Unified local test entry point](../tickets/autopilot-practical-reliability/done/04-unified-local-tests.md)
- [APM-05 Bounded command execution](../tickets/autopilot-practical-reliability/05-bounded-commands.md)
- [APM-06 Final-tree vertical boundary](../tickets/autopilot-practical-reliability/06-final-tree-boundary.md)
- [APM-07 Progressive operational references](../tickets/autopilot-practical-reliability/done/07-progressive-references.md)
- [APM-08 Local operational measurements](../tickets/autopilot-practical-reliability/08-operational-measurements.md)
- [APM-09 Localized Azure CLI JSON decoding](../tickets/autopilot-practical-reliability/done/09-provider-json-encoding.md)
- [APM-10 Portable wiki project binding](../tickets/wiki-portable-checkouts/done/01-portable-project-binding.md)
- [APM-11 Windows long-path wiki candidates](../tickets/wiki-portable-checkouts/done/02-windows-long-path-candidates.md)

## Type
Architecture and reliability improvement specification.

## Status
Planning baseline: APM-PREP-01 is integrated; APM-01 is active at implementation in the existing nine-ticket run, with no implementation changes yet at this update. The user subsequently requested portable wikis across computers and asked to create and queue the S10/S11 follow-up tickets. Runtime state belongs to the runner ledger; this document does not certify implementation or verification.

## Destination
Make Autopilot more predictable on Windows and POSIX, resistant to stuck commands, and easier to understand without adding another framework or a more elaborate authorization process. Prefer a small, directly verifiable change over a general rewrite.

The user requested improvement tickets after a read-only review, plus this prompt preference:

> Non siamo la CIA o la NSA: non usare protocolli di sicurezza super se non espressamente richiesto e non usare subagenti se non espressamente richiesto.

The initial request created the backlog without executing it. The user subsequently requested execution, repository-wide merge, and wiki synchronization, then explicitly requested these checkout prerequisites. The repository merge grant retains that message's provenance. No installed/global prompt change or delegation is implied.

## Observed Baseline
The preceding analysis inspected clean commit `301accd3fb32c07e2a51767c9c68b0c9d6e88227` with Python 3.12.10 on Windows. These are scoped observations, not a full-suite or live-provider certification:

- The `ticket-autopilot/scripts/autopilot` package contains 42 Python modules and 44,693 lines. `cli.py`, `ledger.py`, and `kernel.py` contain 7,218, 5,606, and 4,548 lines respectively. AST measurements found 1,548 lines in `_process_events` and 3,599 in `_validate_event_transition`; size is a maintainability signal, not proof that every branch is defective.
- There are 57 `test_*.py` modules and 782 statically defined test methods.
- Eight selected modules ran 166 tests: 153 succeeded, 11 errored, and two symlink tests were skipped. All eleven errors shared the final-tree fixture's `tracked ticket bytes differ from the index` failure. The inherited system Git configuration had `core.autocrlf=true`.
- Repeating that selection with process-only `core.autocrlf=false` still produced eleven errors, now at `git update-index --cacheinfo` for a receipt path containing backslashes. This did not make the suite green.
- A separate temporary-repository reproduction passed the same blob and receipt location to `git update-index --add --cacheinfo`. The Windows-style path failed with exit 128; the POSIX-style path succeeded with exit 0. This proves the path boundary, not the complete corrected workflow.
- The common command runner calls `subprocess.run` with captured output but without a timeout. `ProviderExecutor` uses that runner by default. Indefinite blocking is an identified risk; no live-provider hang was induced.
- The root `package.json` test command covers the TypeScript extensions, not the Python suite.

Selected test modules: `test_kernel`, `test_history_codec`, `test_platform_locks`, `test_repository_merge_authority`, `test_context_budget`, `test_model_invocation_policy`, `test_skill_graph`, and `test_token_reduction_guide`.

Primary code anchors: `final_tree_projection.plan_tracked_completion`, `_path`, `_blob_oid`, and the temporary-index tree construction; the shared transaction fixture in `test_kernel.py`; `git_ops._run_captured`; `providers.ProviderExecutor`; `AtomicLedger.save/load`; and `package.json`.

Related context, not replacement ownership:
- [Windows text fidelity](windows-text-fidelity-wayfinder.md) covers earlier provider/decoding failures. S2/S3 address final-tree paths and fixtures; S9 extends the text-fidelity family to localized provider JSON while retaining the strict-data decision. Its canceled CI ticket remains closed.
- [Final-tree validation](delivery-revalidation-final-tree-validation-decision.md) owns final-tree semantics.
- [Stale excluded projections](ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md) records a separate candidate-invalidation fix which the refactor must retain.
- [Token economics](autopilot-token-economics-wayfinder.md) owns context units and distinguishes reported leaf usage from total session cost. This spec does not duplicate the existing live-token investigation.

## S0 — Checkout Preparation
The immediate prerequisite request has two observable outcomes:

1. The existing spec and canonical ticket sources belong to a local Git base commit. Validate envelopes, dependency order, and reciprocal links before committing only these planning artifacts; this is source preparation, not implementation completion of APM-01 through APM-08.
2. `knowledge/llm-wiki-project.json` binds `project_root` to the explicitly selected checkout `C:/Users/rdpuser/projects/agent-skills`, preserving every other configuration value. The current resolver interprets relative paths against process cwd, so do not substitute `..` or silently add a fallback. This is an exact checkout repair, not a portable-binding redesign.

APM-PREP-01 lives in its own narrow ticket folder and owns the JSON configuration repair through the runner. Read back the binding using the existing resolver from a different cwd, prove that project discovery finds the APM ticket sources, and test that only `project_root` changed. A later wiki compile may expose independent lint or publication gates; do not hide them or mix generated pages into this configuration candidate. Existing APM implementation remains separate.

## S1 — Practical Prompt Defaults
Put the following table in the repository-owned operating guidance and make the applicable prompt entry points consume it without copying a long policy into every skill:

| Default | Intended prompt wording | Observable behavior |
| --- | --- | --- |
| Proportionate security | Non siamo la CIA o la NSA. Usa misure di sicurezza semplici e proporzionate al rischio; non introdurre protocolli di sicurezza avanzati, nuovi livelli di approvazione o procedure aggiuntive salvo richiesta esplicita. | Routine work gains no speculative security framework, approval ceremony, or threat-modeling phase. Essential protection of secrets, data integrity, and authorization for destructive or external actions remains. |
| Explicit delegation only | Lavora inline con un solo agente. Non creare o usare subagenti salvo richiesta esplicita dell'utente. AFK, complessita del lavoro, disponibilita degli strumenti e silenzio non sono consenso. | Skills may be composed serially in the same context. Generic host capability or delegation permission is not treated as a user request. A requested subagent is restricted to the requested scope. Inline review is never labeled independent. |

APM-01 implements this guidance in repository-owned prompts and reconciles conflicting default delegation suggestions in related skills. It must not edit personal settings, installed skill copies, or global prompt files. Higher-priority mandatory instructions remain controlling; a genuine conflict is reported rather than bypassed. This preference is not permission to remove existing runtime protections or invent additional ones.

## S2 — Portable Final-Tree Git Paths
Use one consistent representation for Git index/tree paths: repository-relative POSIX spelling. Native filesystem paths remain native at filesystem boundaries. Receipt derivation, validation, effect planning, and application must agree. Exercise the complete tracked-completion path, including replay, not only a string helper. Preserve bytes, modes, candidate identity, and the distinction between projected and integrated.

## S3 — Hermetic Git and Line-Ending Tests
Temporary-repository fixtures must not depend on the operator's global/system Git configuration, hooks, signing defaults, or implicit text newline conversion. Give canonical fixture bytes and intentional CRLF cases explicit ownership. Cover both `core.autocrlf` settings without modifying the user's Git configuration.

Do not silently normalize production digests or weaken byte equality to make tests green. If a production source format is incompatible with the exact-byte contract, reject it before projection effects with an actionable diagnostic and a documented supported setup. Preserve worktree/index bytes on rejection. Separate this behavior from the independent receipt-path defect.

## S4 — Unified Local Tests
Provide a documented cross-platform entry point for quick and full local checks. It must include both the TypeScript extension tests and the appropriate Python suites, propagate failures, list omitted scopes, and distinguish unavailable/skipped checks from success. Reuse the existing frameworks. Python/Node/Git requirements must be discovered from the project and verified, not guessed.

Do not activate hosted CI, change provider policies, install tools globally, or silently skip Python when prerequisites are missing. Real Windows/POSIX observations remain distinct from simulated platform branches.

## S5 — Bounded Command Execution
Make the common Git/provider execution path bounded by a finite timeout and a declared output limit. Support cancellation and reap child processes on supported platforms. Preserve strict data decoding and diagnostic decoding semantics, including the provider-specific encoding boundary established by S9.

Surface timeout, cancellation, and output-limit outcomes through the existing error/reporting boundary with an actionable next step. Never parse truncated JSON or a partial SHA as valid data. A timed-out mutating provider command has an uncertain outcome: reconcile through existing readback before another attempt; no blind mutation retry. Do not invent a second transaction ledger or generalized retry framework. Choose documented configurable defaults using local hanging/noisy-child tests, not credentialed provider experiments.

## S6 — One Final-Tree Vertical Boundary
Extract only the final-tree orchestration family from the large CLI dispatcher, together with the corresponding ledger-validation organization where needed. Reuse the existing projection and transaction owners. Keep public CLI inputs, event vocabulary, serialized schema, replay behavior, and authority boundaries stable for this refactor.

The new boundary should let a maintainer trace projection, quality retry, semantic candidate invalidation, and replay without reading unrelated wiki/bootstrap/merge code. Retain negative replay validation and independent assertions; do not make tests prove only that writer and validator share the same assumption. Prove that non-final-tree events continue through the existing path. Larger decomposition is deferred until this slice's leverage is measured.

## S7 — Progressive Operational References
Keep the common Autopilot workflow and safety-critical decision points in `SKILL.md`. Move infrequent operational procedures behind explicit trigger-based references. Resolve documentation from actual ownership rather than restating the same protocol in README, the skill, and multiple prompts.

Preserve discoverability, every supported command path, and required evidence/authorization semantics. Measure normalized UTF-8 bytes with the existing context-budget tooling before and after; do not describe static-byte savings as observed token/currency savings. Do not raise ceilings merely to make a documentation check pass. This is a navigation improvement, not a new security protocol or a wholesale prose compression exercise.

## S8 — Local Operational Measurements
Add a small local report over existing run/leaf/command observations: per-phase recorded duration, recorded retry counts, missing measurements, and the slowest observed phases. Keep source and units explicit. Reuse existing status/budget fields and report unavailable values as unavailable, never as zero.

Use controlled, provider-free examples and document how to compare equivalent runs. Reported leaf time is not total session time, and static bytes are not model tokens. Do not add a daemon, external telemetry, prompt/transcript collection, new database, or a release gate. The existing live-token work remains separate.

## S9 — Localized Azure CLI JSON Decoding

### Observed and Reported Behavior
The user reported an Azure DevOps PR creation response containing human project-description prose encoded in cp1252. A byte `0xF3` in `logica` with an accented o reaches the shared strict UTF-8 stdout decoder and raises `UnicodeDecodeError`. The original provider response is not present in this checkout; retain a sanitized byte fixture instead of copying project/customer descriptions into tests.

Local confirmation on planning base `ddf5dd7`:
- A disposable Python producer emitted the exact byte sequence `b'{"description":"l' + bytes([0xF3]) + b'gica"}'`. `SubprocessCommandRunner.run` rejected it with `UnicodeDecodeError` from UTF-8 decoding. This confirms the shared-decoder mechanism, not live Azure PR creation.
- The installed Azure CLI is 2.87.0, with bundled Python 3.13.13. Both its Bash and CMD launchers invoke Python with `-IBm azure.cli`.
- A captured-stdout probe of that bundled Python under `-I` reported `stdout_encoding=cp1252`, `utf8_mode=0`, and `ignore_environment=1`. Process-local `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` overrides did not change those results.
- The host ANSI code page was 1252 while the console output code page was 850. They are not interchangeable signals. The user's unsuccessful `chcp` workaround was reported, not repeated here.
- CPython's strict cp1252 decoder accepted `0xF3` as the accented o but rejected undefined byte `0x81`. Therefore cp1252 is not a total decoder in Python.

### Diagnosis and Constraints
This is another instance of the family documented in [Windows text fidelity](windows-text-fidelity-wayfinder.md), not evidence that the existing strict-data/lenient-diagnostics decision should be reversed. WT-02 and WT-03 are predecessor context, not tickets to reopen. At the investigation baseline, `git_ops._run_captured` captured bytes with lenient diagnostic decoding and `SubprocessCommandRunner` exposed the same strict UTF-8 stdout path to `ProviderExecutor`.

Keep Git stdout strict under its current UTF-8 contract and keep stderr's diagnostic policy unchanged. Add the missing distinction for Azure provider JSON stdout, including arbitrary Unicode string fields. Do not claim Git output is universally ASCII. No worktree deletion was reproduced; weakening data decoding is a potential integrity risk, not an observed deletion in this incident.

The desired result is exact text under the actual producer encoding, not merely parseable JSON or absence of U+FFFD. A UTF-8-first/system-code-page fallback is a proposed approach, not a globally approved heuristic: valid byte strings can decode differently under two codecs without any error, and encoding round trips alone do not identify the intended text. Use an explicit supported producer profile, reliable version-bound signal/configuration, or a demonstrated producer-side UTF-8 mechanism; if the encoding cannot be established, surface an actionable error rather than guessing.

Prefer the smallest provider-scoped change. Do not add a codec framework, hard-code cp1252 for every Windows/provider invocation, use `errors="replace"` or `ignore` for data, alter global console/Python settings, or assume ignored environment variables solve the MSI launcher case. Decode bytes using the selected codec strictly, then parse JSON; do not prescribe the obsolete `json.load(..., encoding=...)` argument on current Python.

### Acceptance and Failure Behavior
- Existing UTF-8 Azure JSON continues to work under its supported profile; the supported cp1252 case preserves the accented text exactly when that producer encoding is established.
- Git SHAs, branch data, cleanup inputs, and existing stderr handling retain their contracts. Unknown providers do not acquire a fallback automatically.
- Tests cover UTF-8, established cp1252, another configured Windows code page, non-ASCII paths/text, undefined codec bytes, truncated/malformed JSON, nonzero exits, and ambiguous byte sequences. Test fixtures assert intended characters, not only successful parsing or round trips.
- A decoding/JSON failure after `az repos pr create` is an uncertain mutation outcome. Preserve available diagnostics and use existing readback/reconciliation before another creation attempt; do not blindly retry or declare that no PR was created.
- Baseline tests exercise raw bytes through the actual command runner and provider JSON boundary, not a fake returning already-decoded strings. An installed Azure launcher probe and a real authenticated PR operation remain separate evidence classes; the latter is not required merely to create or implement this ticket.

APM-09 owns this provider-decoding slice. APM-05 now depends on it so timeout/output-limit work preserves the chosen provider decoding boundary. The `cmd.exe` Markdown separator problem and Azure expected-head merge capability remain separate destinations.

Documentation lookup: the official Azure CLI source documentation retrieved through Context7 (`/azure/azure-cli`) confirmed the JSON output-format surface but did not establish a stdout codec guarantee. Implementation must verify the relevant producer/version behavior rather than treating `--output json` as an encoding promise. Local source anchors are `git_ops._run_captured`, `_decode_data`, `SubprocessCommandRunner.run`, and `providers.ProviderExecutor`; installed launcher probes did not perform provider mutations or upgrade the CLI.

### APM-09 Selected Boundary
Use one explicit producer profile captured by `SubprocessCommandRunner`, with Azure-specific strict decoding before provider JSON parsing. The [operator contract](../../README.md#azure-cli-json-stdout-encoding) owns configuration, supported assumptions, and limitations. Keep the existing scalar command result rather than migrating every caller to raw results, and do not rewrite or bypass MSI launchers automatically. APM-05 reuses this boundary.

The installed Knack0.14.0 formatter/output method was also probed with sanitized text under the MSI-equivalent flags. It preserved representable cp1252 text, but on unrepresentable Unicode it warned, discarded characters, and emitted valid ASCII JSON with exit0. Explicit `-X utf8` preserved wider Unicode in that local probe. Reject the observed discarded-characters signal as invalid data, not successful JSON. No authenticated Azure command was involved.

[Raw-byte and cleanup regressions](../../ticket-autopilot/tests/test_azure_json_encoding.py) cover exact text, alternate configured code pages, ambiguous inputs, diagnostic retention, real disposable Git cleanup inputs, and accepted-create/failed-response reconciliation. A missing profile stops before the Azure child starts; a failure after execution retains uncertainty and must not manufacture absence or authorize blind recreation. Native POSIX, another real ACP host, and live Azure behavior remain outside the observed evidence.

## S10 — Portable Wiki Project Binding

### Observation and Decision
The checkout-specific S0 repair changed `knowledge/llm-wiki-project.json` to an absolute Windows project root. It repaired this checkout, not portability. The user's new requirement is that the same versioned wiki work in different directories and on different computers without editing a personal path into the repository.

`project_binding.resolve_project_root` constructs `Path(document["project_root"])` without anchoring relative values to the binding directory. `sync_project._assert_compatible` and Ticket Autopilot's `_bound_project_target` separately interpret the raw value. Merely replacing the JSON string with `..` would therefore be cwd-dependent and break exact-source target resolution.

Use the existing project-binding owner for one interpretation of `project_root`. Relative values are anchored to the directory containing `llm-wiki-project.json`, never process cwd. For this internal wiki, the portable configuration is `"project_root": ".."`; an internal root-level wiki uses `"."`. The writer/scaffolder must also produce portable internal bindings, not reintroduce absolute personal paths. Preserve the schema-1 field and other configuration values. Explicit compatibility is required for deliberately absolute, checkout-pinned bindings and external wikis; they remain literal and are not silently rebound if missing.

This decision supersedes S0's local-only configuration target and the absolute-binding-only assumptions of [exact-source sync](llm-wiki-exact-source-checkout-sync.md) and [cross-checkout delivery](ticket-autopilot-cross-checkout-wiki-delivery.md) for portable internal bindings. Preserve their source/target distinction and identity checks; do not reopen completed predecessor tickets.

### Source and Target Semantics
For a normal invocation, the relative binding identifies the local project from the binding's location. Two independent clones can therefore use identical versioned binding bytes while each resolves its own project; equal remotes do not make their runtime state or authority interchangeable.

For an exact-source sync, interpret the internal relative binding in its validated source layout, then project that layout onto the invocation's explicit canonical project root. Keep the source-head and shared-Git-common-directory proof for the alternate source. The logical wiki, frozen candidate store, and publication destination belong to the canonical target, not the temporary source or compile copy. An explicitly absolute cross-checkout destination keeps the existing same-provider/remote checks. Never discover a destination by scanning sibling checkouts or choosing the first repository with the same remote.

Update all consumers of the binding, including discovery, ingestion, lint, scaffold, ordinary sync, exact-source sync, and runner target resolution. Wiki links and project `source_path` values stay relative. Absolute filesystem paths in local runtime receipts are allowed and remain local; copying a wiki never transfers ledgers, grants, or resumability. Missing local session transcripts must be reported as unavailable provenance, not make project-doc synchronization depend on another computer's home directory.

### Acceptance
- The same committed binding and wiki can be cloned or relocated to two distinct paths, including spaces/non-ASCII characters, and discover the correct local docs from an unrelated cwd without rewriting the binding.
- Missing roots, malformed bindings, ambiguous discovery, stale exact heads, and mismatched target identities remain actionable failures; legitimate `..` to the project root is not confused with an unsafe candidate-path escape.
- An exact detached source compiles to the canonical target with protected source/canonical worktrees unchanged; a distinct explicit absolute target retains its existing behavior.
- Focused binding, ingestion/lint, and sync integration tests cover the public behavior. Observe native Windows and POSIX separately; an unavailable platform is not a pass.

APM-10 owns this vertical slice, its repository binding change, tests, and documentation. Long-path publication remains S11; S10 must report that separate gate rather than claim full wiki publication.

## S11 — Windows Long-Path Wiki Candidate Delivery

### Observation
After APM-PREP-01 integrated through PR #242, wiki compilation produced 23 changed candidate files and lint without errors. Publication became terminal with `delivery-invalid: tracked wiki candidate contains a non-regular path`.

The reproducing relative filename was `wiki/sources/artifact-artifact-graph-disposition-drift-diagnostic.md`. Its absolute path under `<git-common-dir>/llm-wiki/candidates/<64-character-sync-digest>/<64-character-tree-digest>/` was 262 characters. Ordinary Windows `Path.stat()` raised `FileNotFoundError`/WinError 3; the same file through the Windows extended-length path form was a regular file with mode `0o666`. A shorter index path succeeded normally. This is an observed native filesystem access defect, not an absolute link embedded in a wiki page, and relative binding alone does not fix it.

Owning anchors are `wiki_sync._frozen_files`, canonical target/candidate validation, `deliver_tracked_candidate`, and the `sync_project` candidate producer. The persisted observation belongs to run `apm-checkout-preparation`, ticket APM-PREP-01, exact integrated source `a73c0985822833af0c33991ba7546d31de9ad1d0`, in `.git/ticket-autopilot/runs/apm-checkout-preparation/artifacts/post-integration-status.json`. That local evidence is not a portable configuration or a new authorization.

### Target Behavior
Make the complete frozen-candidate path work for supported long native Windows paths, including enumeration, regular-file checks, strict reads, digest validation, isolated Git materialization, and delivery readback. Prefer a narrow native-I/O adaptation in the existing owners; do not introduce a generic path framework. Keep Git/manifest paths repository-relative with forward slashes. Native extended-length spelling, if used, must not leak into Markdown links, Git index paths, logical identity, or identity-bearing serialized records.

Preserve the existing content-addressed candidate layout and the recorded frozen candidate. Do not truncate/hash-shortcut filenames or digests, relocate/delete uncertain worktrees, change global Windows/Git settings, or treat a failed stat as a valid file. A genuinely absent, linked, non-regular, executable, escaped, unreadable, malformed UTF-8, or digest-mismatched candidate must still be rejected with a diagnostic that distinguishes filesystem failure from an invalid file type where possible.

Reuse the existing `wiki-delivery-retry-status` / `retry-wiki-delivery` transaction for a narrowly eligible historical false-negative long-path failure. Its current predicate accepts only the older outside-project failure and does not accept this record. Extend that owning predicate and replay validation only after fully validating the unchanged candidate through the repaired I/O boundary. Require the existing exact-record digest and actor/evidence inputs, preserve the complete predecessor, and reject prior provider mutation/ambiguous outcome, drift, or a genuinely invalid file. Existing exact outside-project retry behavior remains supported. Retry stays provider-free; normal resume owns publication. Do not edit a terminal ledger or manufacture a new approval.

### Acceptance and Evidence Limits
- A native Windows fixture reproduces the >=262-character failure before the fix and passes full validation/materialization after it; short paths remain correct. Also test deep/Unicode paths and the platform-appropriate handling of drive/UNC forms at the I/O boundary without claiming a live network-share test.
- The portable binding from S10 works in this complete sync-to-delivery flow, with an injected provider and exact candidate/manifest/receipt checks; protected worktrees and frozen payload bytes remain unchanged.
- Negative filesystem, containment, UTF-8, and digest tests retain rejection. Recovery accepts only a fully revalidated eligible record, preserves history, makes no provider calls, and replays idempotently; uncertain publication never triggers a duplicate operation.
- After implementation integration, the existing candidate may be revalidated and recovered only through the owned transaction with valid existing or explicit recovery inputs. Missing recovery authority remains a visible local gate, not a new implementation dependency. Live publication remains ordinary separately authorized wiki delivery and is not certified by a provider fake.

APM-11 depends on APM-10 because its end-to-end acceptance consumes the portable binding and canonical-source/target behavior. It is separate from APM-02's Git receipt separator fix and APM-09's Azure JSON decoding.

## Semantic Invariants and External Boundaries
- Protect secrets and user-owned data; do not publish, delete, merge, or delegate through inferred permission.
- Keep implementation evidence bound to the exact candidate and retain separate integration state.
- Preserve literal payload bytes where the existing contract makes them identity-bearing.
- Maintain current Git/provider public behavior except for the specified portable paths, explicit bounded-execution failures, S9's provider-scoped encoding support, S10's portable binding semantics, and S11's native-I/O and exact recovery support. Preserve uncertain-mutation handling.
- Preserve atomic ledger persistence, valid replay, and rejection of invalid transitions.
- Keep the refactor wire-compatible with current CLI/event/schema contracts; compatibility is explicitly required for S6, not permission to add new aliases or migration infrastructure.

## Ticket Plan
| ID | Mode | Blocked by | Frontier | Scope | Outcome |
| --- | --- | --- | --- | --- | --- |
| APM-01 | AFK | — | Ready | S1 | Practical prompt defaults and explicit-user-only delegation |
| APM-02 | AFK | — | Ready | S2 | Portable final-tree receipt paths with real Git regression coverage |
| APM-03 | AFK | APM-02 | Dependency-blocked | S3 | Hermetic fixtures and explicit line-ending behavior |
| APM-04 | AFK | APM-03 | Dependency-blocked | S4 | One local quick/full test entry point with honest results |
| APM-09 | AFK | — | Ready | S9 | Provider-scoped strict JSON decoding with explicit encoding evidence |
| APM-05 | AFK | APM-09 | Dependency-blocked | S5 | Bounded Git/provider subprocesses preserving the provider decoding boundary |
| APM-06 | AFK | APM-04, APM-05 | Dependency-blocked | S6 | One smaller, testable final-tree workflow boundary |
| APM-07 | AFK | APM-01 | Dependency-blocked | S7 | Discoverable operational references and a smaller common prompt |
| APM-08 | AFK | APM-04, APM-05 | Dependency-blocked | S8 | Reproducible local phase/retry report using existing observations |
| APM-10 | AFK | — | Ready in follow-up queue | S10 | Portable wiki binding across computers and exact source checkouts |
| APM-11 | AFK | APM-10 | Dependency-blocked | S11 | Windows long-path delivery and exact pre-provider recovery |

APM-10/APM-11 live in `docs/tickets/wiki-portable-checkouts/` as a separate queued folder run. Do not amend the existing nine-ticket run's immutable source snapshot, add unresolved cross-folder dependency IDs, or start a second mutation in its worktree. Validate and locally commit only the new/updated planning sources before creating the follow-up tracked-source run. Queue creation is not ticket activation, implementation, or integration; the current request does not interrupt APM-01.

AFK means executable inline without an unresolved product decision; it is not subagent or merge authorization. Missing execution environments must be reported honestly. All implementation remains pending after this planning request.

## Verification Strategy
Each ticket owns a causal regression or observable document behavior and its focused checks. Establish the current baseline before comparing results. Re-run the recorded eight-module selection after the Windows fixes; use full-suite checks for runtime/refactor changes and the existing skill graph/context/forward checks for prompt changes. Do not claim POSIX or live-provider verification from Windows mocks. For timing/cancellation tests use disposable local processes and temporary repositories only.

## Alternatives and Non-Goals
- Reject a whole-engine rewrite: start with one vertical boundary and existing adapters.
- Reject another security/approval layer: apply the user's proportionality default.
- Reject default subagents: serial inline composition is the default.
- Reject suppressing failures, removing digest checks, or silently disabling projection.
- No new hosted CI, autonomous merge grant, live provider mutation, installed-Pi update, ad hoc historical ledger repair, or production optimization is authorized by this planning change. S11 specifies only an extension to the existing exact recovery transaction; using it later still requires its actual inputs.

## Next Review
After ticket emission, validate the canonical envelopes, dependency graph, and reciprocal artifact links. Invoke the owned post-batch hook once and preserve its result separately from the planning candidate. Register S10/S11 in a new tracked-source queue, report its ready frontier and wiki result, and leave the existing active run and terminal wiki record untouched. Any tracked wiki output is a separate generated candidate, not part of the planning commit.
