---
type: source
title: "Windows Text Fidelity at the Provider Boundary"
identity_key: artifact:windows-text-fidelity-wayfinder
identity_strength: stable
source_path: docs/specs/windows-text-fidelity-wayfinder.md
source_digest: sha256:2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-12
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Windows Text Fidelity at the Provider Boundary

Compiled from `docs/specs/windows-text-fidelity-wayfinder.md`. Identity is `artifact:windows-text-fidelity-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-12** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-windows-text-fidelity-wt-01]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-02]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-03]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-04]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-05]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-06]]
- Child source: [[sources/ticket-windows-text-fidelity-wt-07]]
- Child source: [[sources/artifact-full-suite-timeout-diagnosis]]
- Child source: [[sources/artifact-autopilot-practical-reliability]]
- Child source: [[sources/artifact-ticket-autopilot-orphan-worktree-garbage-collection]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[8],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"goals":{"headings":[7],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-windows-text-fidelity-wayfinder.md","payload_bytes":13589,"payload_sha256":"2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f"}],"payload_bytes":13589,"payload_sha256":"2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f","schema":1,"source_digest":"sha256:2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f","source_identity":"artifact:windows-text-fidelity-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 7: Destination |
| exclusions | 10: Out of Scope |
| decisions | 8: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":13589,"payload_sha256":"2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f","schema":1,"source_digest":"sha256:2480a913d2634b3ddc47933b22d54344f502f18a4638f1719d54db513c71f40f","source_identity":"artifact:windows-text-fidelity-wayfinder"} -->
```markdown
# Windows Text Fidelity at the Provider Boundary

## Artifact Graph

- Artifact ID: `artifact:windows-text-fidelity-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [WT-01](../tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md)
- [WT-02](../tickets/windows-text-fidelity/done/02-decide-decoding-errors-policy.md)
- [WT-03](../tickets/windows-text-fidelity/done/03-implement-decoding-errors-policy.md)
- [WT-04](../tickets/windows-text-fidelity/done/04-platform-conditional-tests.md)
- [WT-05](../tickets/windows-text-fidelity/done/05-strip-equality-hazard.md)
- [WT-06](../tickets/windows-text-fidelity/done/06-green-windows-baseline.md)
- [WT-07](../tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md)
- [Full-profile timeout diagnosis](../research/full-suite-timeout-diagnosis.md)

### Related

- [Practical Autopilot reliability](autopilot-practical-reliability.md)
- [Worktree garbage collection](ticket-autopilot-orphan-worktree-garbage-collection.md)

Lineage (evidence, not owner edges): this map continues the defect family opened by
`WD-01` and `WD-02` in `docs/tickets/autopilot-windows-digest-drift/done/`. Those tickets
are complete; this map exists because the family is not.

## Notas conservadas de las relaciones

- WT-01: `artifact:wt-01-body-round-trip-fidelity`
- WT-02: `artifact:wt-02-decide-decoding-errors-policy`
- WT-03: `artifact:wt-03-implement-decoding-errors-policy`
- WT-04: `artifact:wt-04-platform-conditional-tests`
- WT-05: `artifact:wt-05-strip-equality-hazard`
- WT-06: `artifact:wt-06-green-windows-baseline`
- WT-07: `artifact:wt-07-decide-and-introduce-ci`
- Full-profile timeout diagnosis: `artifact:full-suite-timeout-diagnosis`

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

## Subsequent Windows incidents

The earlier frontier above is historical context, not an instruction to reopen completed WT tickets or the canceled CI decision. The new incidents have distinct owning boundaries:

| Instance | Evidence and current owner | Required distinction |
|---|---|---|
| Localized Azure CLI JSON stdout | [APM-09](../tickets/autopilot-practical-reliability/done/09-provider-json-encoding.md) already specifies raw-byte reproduction and producer-scoped decoding | Establish the producer codec; keep Git data strict and preserve uncertain-mutation reconciliation |
| GC rejects Git's Windows forward slashes | [WGC-03](../tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/03-windows-git-paths.md); native read-only reproduction on `0243c9c` confirmed an absolute Git path rejected before planning | Adapt separators only at the Git inventory boundary; retain canonical persisted identities and cleanup checks |
| Verification-checkpoint input drift after a bundle correction | User-reported in this follow-up; corruption and a platform cause have not been independently reproduced here | Preserve immutable inputs and byte digests; obtain the exact checkpoint/input sequence before defining another fix |

These belong to the same portability family, but do not justify one blanket string normalizer or three identical patches. Markdown/body bytes, provider JSON text, native filesystem paths, and checkpoint records have different equivalence contracts. This update adds the confirmed GC correction to its existing spec, links the already queued Azure work, and records the checkpoint report without claiming its diagnosis.

## The timeouts were hiding this family

[Full-profile timeout diagnosis](../research/full-suite-timeout-diagnosis.md) measured the
local profile: it was never hung. Ninety-five serial `spawnSync` checks shared one flat
300 s allowance, and the three checks above it were killed and reported as `ETIMEDOUT`.
With the profile chunked, sharded and streamed, the concealed observations became readable.
Most of them are this map's family — a platform-dependent observation breaking an equality:

| Observed break | Cause | Correction |
|---|---|---|
| `inventory file changed during scan` on every scanned file | Windows `os.DirEntry.stat()` reports `st_dev=0, st_ino=0`, so the descriptor never matched the entry | Re-observe the path when the entry carries no identity, keeping the comparison instead of dropping it |
| `repoint source contains unexpected content`, `applied tree differs` in status and reconciliation fixtures | Fixture repositories inherited the operator's `core.autocrlf=true`, and fixture writes used the platform line ending | Those fixtures use the disposable Git configuration and write literal bytes |
| `applied reconciliation tree differs from the exact proposal` | `subprocess.run(text=True, input=...)` rewrites `\n` as `\r\n`, so `mktree` received `file.txt\r` | Exact Git object input travels as bytes |
| `'100755' != '100644'`, mode drift never detected | Windows has no executable bit, so `os.chmod` cannot express the fixture's intent | Declare the mode in the index, or assert the honest platform observation |
| Sub-second command-bound deadlines failing under load | Parallel checks starve a fixture that must start within 0.5 s | Wall-clock-bounded suites stay unchunked and run without neighbours |

The stale quoted baselines (`context-budget` word count, the context-cost guide table, the
wiki-sync boundary suite size, the `ask-skills` line budget) were ordinary drift, not
portability: they were simply unreadable while the suite could not finish.

### Still open

- `test_cli` reports two byte-drift observations —
  `test_observe_mode_records_exact_tracked_completion_parity_without_authority` and
  `test_semantic_stack_reconciliation_refreshes_advancing_target_and_rebinds_bundle`.
  Giving `CliTests` the disposable configuration repairs those two and breaks six
  docs-only and projection cases, so it was reverted rather than traded. Both directions
  are now observable; neither is understood.
- Whether the repository should declare `.gitattributes` so an operator checkout satisfies
  the runtime's own working-tree-equals-index requirement, instead of each operator
  configuring `core.autocrlf=false`. This is a repository-wide decision, not a test fix.
- The 250 `_command_supervisor.py` launches per CLI case are the suite's real cost. Making
  them cheaper without weakening process-tree containment is unowned.

## Next Review

Inspect after `WT-01`: does the full suite on Windows show **13 red and no new reds**
against base's 19? That number is the falsifiable claim. If `test_utf8_io` is still red,
`WT-02` has not been decided and `WT-03` has not run — which is correct, not a failure.

```
