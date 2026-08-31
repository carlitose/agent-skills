# Windows Text Fidelity at the Provider Boundary

## Artifact Graph

- Artifact ID: `artifact:windows-text-fidelity-wayfinder`
- Role: `wayfinder`
- Standalone: true
- Children:
  - [WT-01](../tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md) — `artifact:wt-01-body-round-trip-fidelity`
  - [WT-02](../tickets/windows-text-fidelity/done/02-decide-decoding-errors-policy.md) — `artifact:wt-02-decide-decoding-errors-policy`
  - [WT-03](../tickets/windows-text-fidelity/done/03-implement-decoding-errors-policy.md) — `artifact:wt-03-implement-decoding-errors-policy`
  - [WT-04](../tickets/windows-text-fidelity/done/04-platform-conditional-tests.md) — `artifact:wt-04-platform-conditional-tests`
  - [WT-05](../tickets/windows-text-fidelity/05-strip-equality-hazard.md) — `artifact:wt-05-strip-equality-hazard`
  - [WT-06](../tickets/windows-text-fidelity/06-green-windows-baseline.md) — `artifact:wt-06-green-windows-baseline`
  - [WT-07](../tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md) — `artifact:wt-07-decide-and-introduce-ci`

Lineage (evidence, not owner edges): this map continues the defect family opened by
`WD-01` and `WD-02` in `docs/tickets/autopilot-windows-digest-drift/done/`. Those tickets
are complete; this map exists because the family is not.

## Type

Wayfinding spec

## Status

Active

## Destination

Text that crosses the provider and Git boundary must survive the round trip
**character-identical on every platform**, and that property must be protected by tests
that actually execute somewhere.

The reachable outcome is:

- a PR body published through `az` or `gh` reads back literally equal to the validated
  body, including its trailing newline, its line endings, and its non-ASCII characters;
- `ticket-hold`, `ticket-cancel` and `ticket-reopen` work on Windows and POSIX with a
  documented, consistent contention semantics;
- the `errors` decoding policy is an explicit recorded decision rather than a value that
  flips whenever someone is debugging a different problem;
- the suite has a **green baseline on Windows**, so a regression is visible as a change of
  colour rather than as a change of count;
- PR #78 merges with its three real fixes intact and its two regressions removed.

## Decisions So Far

- **The three defects PR #78 diagnoses are real.** Verified this session on
  CandidateRef `acd881c` vs base `d306799`.
- **The lifecycle lock fix works in production.** `ticket-hold` fails on base with
  `LifecycleError: ticket lifecycle folder is locked` and succeeds on head with
  `state='applied'`. This is not in question and must not be lost.
- **The PR is net positive but not mergeable as-is.** Full suite, 391 tests, Windows 11 /
  Python 3.12.10: base **19 red** (9F+10E), head **15 red** (8F+7E). Net −4, with 2 new
  reds introduced.
- **The delivery gate has a proven single-character root cause.** `body.splitlines()`
  discards the body's trailing newline; `finalizer.py:1103` compares literally. Measured
  at the failure site: `expected len=419` / `received len=418`.
- **`FakeAzureRunner` replicates the bug under test.** `test_cli.py` reads
  `command[command.index("--description") + 1]`, i.e. only the first line. This is why the
  `--description` defect was never caught.
- **The remedy is verified.** `split("\n")` plus a fake that joins the argument vector
  turns both new reds green *and* fixes `test_azure_external_merge_...`, which was red on
  base with `[WinError 2]`.
- **`errors="strict"` was a deliberate decision, not an accident.** `WD-02`'s plan says
  "Pass `encoding="utf-8"` (and decide on `errors`)", and the choice was encoded as an
  assertion in `test_utf8_io.py:46`. PR #78 reverses it silently.
- **This is one family, not three incidents.** `WD-01` named it: *platform-dependent text
  handling silently breaking an equality or digest check*. `WD-02` hit the exact same
  `delivery-pr-body` / `readback-validation` gate for a different reason (cp1252
  em-dashes, 4830 vs 4836 chars). PR #78 is the third instance (419 vs 418).

## Not Yet Specified

- **The `errors` policy.** Diagnostic legibility on a non-English Windows and silent
  corruption in a data path are in genuine tension. `assert_cleanup_safe` decides whether a
  worktree may be deleted; `errors="replace"` lets undecodable bytes become U+FFFD inside
  the equality checks that authorize that deletion. Owner: `WT-02`.
- **Whether CI exists at all, and where.** There is no `.github/`, no Azure Pipelines, no
  GitLab CI; `gh pr checks 78` reports no checks. Until this is answered, "the CI will
  catch it" is not an available argument. Owner: `WT-07`.
- **The minimum supported Python.** No `pyproject.toml`, no `requires-python`. This decides
  whether `shutil.which`'s pre-3.12 Windows CWD lookup is a live concern. Owner: `WT-04`.
- **The `.strip()` hazard.** `WD-02` explicitly deferred it: *"a separate latent equality
  hazard [that] needs its own decision"*. It is still in the method PR #78 edits, and it
  destroys trailing whitespace and newlines — the same failure shape as `splitlines()`.
  Owner: `WT-05`.

## Out of Scope

- The two limitations PR #78 itself declares out of scope: the `azure-devops` provider
  lacking `merge-with-expected-head`, and cmd.exe re-parsing markdown table separators.
  Both are real; both are separate destinations.
- Redesigning the delivery body render or relaxing the literal comparison at
  `finalizer.py:1103`. The comparison is correct; the round trip is what leaks.
- Migrating the repository to a packaging layout beyond declaring `requires-python`.

## Frontier / Blocking Edges

| Edge | Why it blocks | Unblock condition | Ticket |
|---|---|---|---|
| Body round trip is lossy | PR #78 cannot merge; delivery gates on a correct body | `split("\n")`, fake updated, round-trip test green | `WT-01` |
| `errors` policy undecided | Reversing a completed ticket's invariant without a record | Decision recorded via `to-spec` | `WT-02` |
| No green Windows baseline | 13 pre-existing reds hide new ones; only a *delta* is readable | Suite green on Windows | `WT-06` |
| No CI anywhere | Every claim of correctness depends on someone remembering to run tests | CI runs the suite on at least Windows + Linux | `WT-07` |
| No POSIX environment observed | The `fcntl` branch and net-−4 claim are unverified off Windows | Suite executed on Linux/macOS | `WT-06` |
| No live Azure DevOps | Real `az --description` behaviour remains modelled, never observed | Authenticated org for one delivery | `WT-01` |

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
|---|---|---|---|---|---|
| `WT-01` | Defect | AFK | — | Make the PR body round trip character-identical | `split("\n")`, empty-body and `---` handling, `FakeAzureRunner` on the `nargs='+'` contract, round-trip property test |
| `WT-02` | Decision | **HITL** | — | Decide the decoding `errors` policy | Recorded decision spec covering diagnostics vs data paths, superseding or reaffirming `WD-02` |
| `WT-03` | Task | AFK | `WT-02` | Implement the decided `errors` policy | Call sites reconciled, `test_utf8_io` aligned to the decision |
| `WT-04` | Task | AFK | — | Add the platform-conditional tests that do not exist | `_folder_lock` both branches via `mock.patch("os.name")`, `shutil.which` resolution test, `requires-python` declared |
| `WT-05` | Defect | AFK | — | Resolve the deferred `.strip()` equality hazard | Decision applied to `CommandResult`, with a test that trailing whitespace survives or is provably irrelevant |
| `WT-06` | Task | AFK | — | Restore a green Windows baseline | Test-side `sha256(read_bytes())` replaced by `ticket_source_digest`, path-separator assertions normalized, POSIX run observed |
| `WT-07` | Decision | **HITL** | — | Decide and introduce CI | CI executing the suite on Windows + Linux, wired to PR checks |

`WT-02` and `WT-07` carry `execution_mode: HITL` and their bodies require `grilling` before
any implementation, per the deferred-decision rule. They stay on the frontier until
confirmed.

Ready now: `WT-01`, `WT-02`, `WT-04`, `WT-05`, `WT-06`, `WT-07`. Blocked: `WT-03`.

Recommended order: `WT-01` first — it is the only edge standing between PR #78 and merge.
`WT-06` next, because until the baseline is green every later result is read as a delta.

## Next Review

Inspect after `WT-01`: does the full suite on Windows show **13 red and no new reds**
against base's 19? That number is the falsifiable claim. If `test_utf8_io` is still red,
`WT-02` has not been decided and `WT-03` has not run — which is correct, not a failure.
