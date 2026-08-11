# Autopilot Token Economics

## Type

Wayfinding spec

## Status

Active

## Artifact Graph

- Artifact ID: `artifact:autopilot-token-economics-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [TK-01 Freeze the context budget unit](../tickets/autopilot-token-economics/done/01-freeze-context-budget-unit.md)
- [Context budget unit decision](autopilot-context-budget-unit-decision.md)
- [TK-02 Measure the static prompt prefix](../tickets/autopilot-token-economics/done/02-measure-static-prompt-prefix.md)
- [TK-03 Bound leaf context intake](../tickets/autopilot-token-economics/done/03-bound-leaf-context-intake.md)
- [TK-04 Compose the worst-case per-turn ceiling](../tickets/autopilot-token-economics/done/04-compose-worst-case-ceiling.md)
- [TK-05 Document autopilot dependencies](../tickets/autopilot-token-economics/done/05-document-autopilot-dependencies.md)
- [TK-06 Write the token-reduction guide](../tickets/autopilot-token-economics/done/06-write-token-reduction-guide.md)
- [Autopilot context-cost guide v1](../autopilot-context-cost-guide.md)
- [TK-07 Audit model-invocation exposure](../tickets/autopilot-token-economics/done/07-audit-model-invocation-exposure.md)
- [TK-08 Record the context-passing boundary](../tickets/autopilot-token-economics/done/08-record-context-passing-boundary.md)
- [TK-09 Observe live run token consumption](../tickets/autopilot-token-economics/09-observe-live-token-consumption.md)
- [WD-01 Fix Windows ticket digest drift](../tickets/autopilot-windows-digest-drift/done/01-fix-windows-digest-drift.md)
- [WD-02 Fix Windows provider decoding](../tickets/autopilot-windows-digest-drift/done/02-fix-windows-provider-decoding.md)
- [Cross-host context rollover](cross-host-context-rollover-wayfinder.md)

## Destination

Close GitHub issue [#53](https://github.com/carlitose/agent-skills/issues/53) with a
deterministic, locally verifiable account of what `ticket-autopilot` puts into a model
context, declared upper bounds on the variable content its leaf skills may read, published
guidance for operating it cheaply, and an honest separation between measured bounds and
unobserved live consumption.

The destination is reached when the repository can state a worst-case per-turn context
budget from local evidence, enforce it against regression, and document both the skill
dependencies and the operator practices that reduce cost — without claiming a live token
total that no local test observed.

## Decisions So Far

- Use normalized UTF-8 bytes as the canonical deterministic budget unit: normalize CRLF
  and lone CR newlines to LF, encode strictly as UTF-8, and count octets. Report the
  always-on listing, workflow static closure, and bounded variable leaf inputs as separate
  components plus a composed total. The accepted rationale and stability contract are in
  [Context budget unit decision](autopilot-context-budget-unit-decision.md).
- Keep deterministic budget enforcement separate from live context observation. Local byte
  measurement is explicit or CI-only; it never runs synchronously on every model call.
  Host-reported tokens, including chat history, are sampled at ticket boundaries and retain
  the host's own unit and available category breakdown. A missing breakdown is reported as
  unavailable, never estimated.
- PR checks report every component delta but gate only a deliberately configured ceiling.
  Measurement records contain aggregate counts and minimal technical metadata only: no
  prompts, messages, file contents, chat IDs, or implicit external upload.
- Accept three distinct legs instead of one "token reduction" effort. Bounding what enters
  context per turn is the substantive lever; static prompt measurement is the instrument
  and the regression guardrail; live per-run consumption is a separate observation gate.
  Collapsing them produces either an unclosable issue or a cosmetic prose edit.
- Reject prose compression of `SKILL.md` files as a primary goal. The measured static
  closure of a full autopilot run is ~6,289 words across eleven files, so editorial cuts
  return a few thousand tokens at most, while every clause is a load-bearing contract
  covered by `test_skill_graph.py` and `forward_test.py`. Any reduction must be bounded by
  a measured ceiling and guarded by those tests, never done by eye.
- A stable static prefix is an asset, not a liability. It is the portion a KV cache reuses
  across turns, so rewriting it churns the cached prefix for a marginal return. The
  expensive term is volatile content re-sent every turn.
- Treat live token totals like the OI-10 host boundary. The runner is a Python CLI that
  never observes model usage, and `ticket-autopilot/SKILL.md:34` already reports optional
  host metrics as `unavailable` unless configured. Only a user-controlled live session can
  observe consumption, so it must not sit on the critical path.
- The ledger already carries a token slot, so the gap is a source and not a schema. An
  observed run reports `verbosity.token_count` as
  `{"enforcement": "unavailable", "value": null}` for every ticket, alongside populated
  `leaf_interactions`, `leaf_tool_calls`, and `leaf_wall_time`. `token_count` is the only
  metric whose enforcement is `unavailable`, so `TK-09` should populate an existing slot
  rather than add an axis.
- Ledger budget accounting observes only what leaves report, not what the session spent.
  In an observed run that activated `TK-05` and completed its implementation inline, the
  ledger recorded `leaf_interactions`, `leaf_tool_calls`, and `leaf_wall_time` all at `0`,
  because those counters advance only through `leaf-result` events. Discovery, debugging,
  editing, and two full suite executions were therefore invisible to the runner. Budget
  totals are a leaf-reporting artifact and must never be presented as session cost.
- The durable leaf handoff is already pointer-based and must stay that way.
  `leaf_protocol.py:460-478` validates quality evidence as 64-character `sha256` digests
  rather than inlined payloads, so the gap is not the runner's serialized contract.
- `handoff` is not the subagent context-passing mechanism. `handoff/SKILL.md:12` states it
  is neither scheduler state nor a ticket-autopilot checkpoint, it writes only to the
  operating-system temporary directory, and it already carries
  `disable-model-invocation: true`. Context reaches leaves through the `leaf-result`
  schema-3 contract of `resume --events` (`ticket-autopilot/SKILL.md:48-53`). This answers
  the issue's handoff question as a boundary decision, not an open unknown.
- `disable-model-invocation: true` measurably removes a skill from the model-visible
  listing. Six skills already carry it — `grill-me`, `grill-with-docs`, `handoff`,
  `resolving-merge-conflicts`, `to-questionnaire`, and `wizard` — and none appear in an
  observed Claude Code skill listing. The flag is therefore a real always-on lever, but a
  small one.
- Bounding intake must constrain volume, never verification. Read budgets, output
  truncation, and reference-over-paste rules may change how much a leaf reads; they may not
  change what it must verify, its evidence classification, or its claim ceiling.
- The versioned `ticket-autopilot` per-turn upper bound is 166,002 normalized UTF-8 bytes:
  4,999 bytes of visible listing, 53,347 bytes of workflow static closure, and the largest
  applicable single-leaf intake bound, 107,656 bytes for `code-review`. Applicable leaf
  invocations are alternative turns, so their bounds are maximized rather than summed.
  The figure is not observed model consumption and excludes chat history, host prompts,
  tool schemas, output, and cache behavior. `context-budget --check-ceiling` fails only an
  explicit breach; a legitimate increase requires a separate reviewed edit to the
  versioned ceiling, rationale, and ticket/decision reference.
- Automatic context rollover is a separate child investigation rather than an extension of
  the active ticket-source folder. Codex and Claude Code expose different lifecycle and
  conversation APIs, while the current `handoff` contract deliberately forbids implicit
  invocation. The cross-host design and its decisions live in
  [Cross-host context rollover](cross-host-context-rollover-wayfinder.md).

## Issue Analysis

### #53 — Token usage of Autopilot

**Observed baseline.** Two costs are separable and both were measured locally.

| Surface | Measure | Note |
| --- | --- | --- |
| Full autopilot static closure | 6,289 words across 11 files | `ticket-autopilot` → `execute-ticket` → `code-simplification`, `code-review`, `qa-test-plan`, `verification-audit`, plus `explain-pr` and 4 references |
| `ticket-autopilot/SKILL.md` | 1,229 words | Largest single skill body in the closure |
| `verification-record.md` | 1,030 words | Largest reference in the closure |
| Always-on skill listing | ~714 words over 22 installed, model-visible skills | Smaller than the issue assumes |
| Already hidden by the flag | 267 words over 6 skills | Existing saving, not a pending one |

`peer-programming`, `pr-antipattern-review`, and `project-blueprint` hold the three largest
descriptions in the repository at 123, 123, and 120 words, but they are absent from
`~/.agents/skills/` and therefore cost nothing in an installed session today. Their size
becomes a live concern only if they are installed.

**Observed gap.** No command reports any of the numbers above, so "how many tokens does
Autopilot use" currently has no reproducible answer and no regression guard. Separately,
nothing in the leaf contracts bounds how much diff, log, or file content a leaf may read
into context, even though the serialized handoff between leaves is already digest-based.

**Fix direction.** Add a provider-free, read-only measurement command in the shape the
repository already accepts for `ticket-list` and `artifact-audit`, declare explicit intake
bounds in the leaf contracts, compose the two into a worst-case per-turn ceiling enforced
against regression, and publish dependency and operating guidance. Keep live consumption
as a separate human-run observation.

**Acceptance evidence.** Deterministic unit fixtures for the measurement command, one
repository-level run whose JSON reproduces the closure and listing figures, prompt-level
tests proving each leaf declares an intake bound without altering its verification duties,
a ceiling test that fails on unbounded growth, and published documentation. The live gate
contributes an explicitly limited observation, never a passing claim.

## Blocking Defect Found and Resolved

During this investigation, a live run on Windows could not `resume` at all, for a reason
unrelated to token work. Two digest functions disagreed:

- `ticket_source.py:56` hashes the canonical parsed envelope and body, which normalizes line
  endings. The snapshot manifest therefore stores an LF digest, and its stored body contains
  no `CR`.
- `ticket_lifecycle.py:34` hashes raw file bytes, which on a CRLF checkout differ.

For observed ticket `TK-01`, the ledger recorded `cf71d924…`, the LF-normalized digest, while
the raw-bytes digest of the same untouched file was `55fdaa41…`. `assert_ticket_source_state`
compares those two values, so every `resume` fails with
`ticket 'TK-01' content differs from managed snapshot` even though nothing changed. All nine
files were CRLF because `ticket-emit` wrote them in text mode on Windows.

Rewriting the nine files with LF endings made all nine digests match and unblocked the run.
That was a local workaround, not the fix later delivered by `WD-01`.

[WD-01](../tickets/autopilot-windows-digest-drift/done/01-fix-windows-digest-drift.md) owns
the fix. It lived in a separate folder because adding a file to the snapshotted
`autopilot-token-economics` folder would itself trigger real source drift on the active run.

[WD-02](../tickets/autopilot-windows-digest-drift/done/02-fix-windows-provider-decoding.md)
owns the related Windows UTF-8 defect: provider and Git subprocess output inherited the
locale code page, so non-ASCII PR bodies could fail an otherwise correct delivery readback.
Both Windows fixes are now integrated in `main` through PRs #57 and #58.

## Ignored-source Completion Reconciliation

Run `7974966ec8d84a35` produced verified implementation candidates for `TK-01`, `TK-02`,
and `TK-03`, but its frozen folder mode remained `ignored` after `TK-01` published the
folder as tracked. PRs #59, #60, and #61 were subsequently merged while the three tracked
ticket envelopes remained at their open paths. Their dispositions are reconciled here from
the existing CandidateRefs and provider readbacks; no execution or verification evidence
is reconstructed.

| Ticket | Candidate tree | PR head | Merge commit |
| --- | --- | --- | --- |
| `TK-01` | `e9045c0eebb26f8303c6421f930c859efda203a4` | `80daa63982ce11f4da3d4d7e08b50aa427f7929b` (#59) | `ddcac94bfc4ddebc1e213b465728ee3d42e1d19b` |
| `TK-02` | `26aa448c76ced040c9e3196c2dc04c782ddf09d5` | `e55443a8b27f38f18403954f2eea7e20a2940e18` (#60) | `c7c1d9613c486457c57a53dbecb42c59805ebc7a` |
| `TK-03` | `7ea37d54e637bd8edc21045d70e8da9d67cdda49` | `a8c21251103368831075693d991226d6a88bd690` (#61) | `0ca6e4e62d4501869e2b28586708f4013bcf3166` |

## Not Yet Specified

- The exact inventory and versioned JSON schema for measuring each fixed component.
  `TK-02` must implement the accepted normalized-byte unit without changing it or guessing
  a token conversion.
- Which intake bounds are correct per leaf. The bound must be tight enough to matter and
  loose enough that `code-review`, `qa-test-plan`, and `verification-audit` still satisfy
  their existing causal-scope duties. `TK-03` must derive them from observed leaf behavior
  rather than assert round numbers.

## Out of Scope

- Implementing any fix during this Wayfinder pass.
- Compressing `SKILL.md` prose as an end in itself, or any reduction not bounded by a
  measured ceiling and guarded by the existing prompt tests.
- Adding a token axis to ledger budgets, gates, or merge authorization. Measurement must
  not become a new failure mode for scheduling or delivery.
- Weakening evidence classification, causal scope, claim ceilings, or verification duties
  in order to read less.
- Claiming a live token total, a cache hit rate, or a percentage saving from local unit
  tests.
- Repurposing `handoff` as scheduler state or as the leaf context-passing channel.
- Installing or resizing `peer-programming`, `pr-antipattern-review`, or
  `project-blueprint`, which are not installed and cost nothing today.

## Frontier / Blocking Edges

- **Budget unit (#53)** — integrated through PR #59. The
  provider-free regression unit is normalized UTF-8 bytes, while host-reported live tokens
  remain a separate observation layer. Owning ticket: `TK-01`; durable decision:
  [Context budget unit decision](autopilot-context-budget-unit-decision.md).
- **Static prefix measurement (#53)** — integrated through PR #60. It is the instrument
  that makes every later claim reproducible and the guardrail against silent prompt growth;
  its versioned JSON reproduces the closure and listing figures under fixtures. Owning
  ticket: `TK-02`.
- **Leaf intake bounds (#53)** — integrated through PR #61. Each leaf declares a tested
  volume bound without changing its verification clauses. This is the substantive lever
  and the riskiest edit because it touches the contracts that own verification duties.
  Owning ticket: `TK-03`.
- **Worst-case ceiling (#53)** — implemented by `TK-04` as a 166,002-byte upper bound over
  the measured static prefix and the largest applicable declared leaf input. The versioned
  ceiling makes accidental growth fail an explicit CI/operator check while keeping a
  deliberate raise reviewable and separate. It remains local bound evidence, not observed
  model consumption.
- **Dependency documentation (#53)** — integrated. `TK-05` reached
  `implementation-complete` and PR #54 is merged in `main`.
- **Operating guidance (#53)** — implemented by `TK-06`. The
  [operator guide](../autopilot-context-cost-guide.md) covers
  context reset, small-context delegation, cache-friendly practice, and the invariant that
  verification is never weakened to reduce context. It quotes only the reproducible
  `TK-02` baseline and marks live savings as unmeasured pending `TK-09`.
- **Model-invocation exposure (#53)** — integrated. `TK-07` is merged through PR #55; it
  records policy without claiming a token saving.
- **Context-passing boundary (#53)** — integrated. `TK-08` is merged through PR #56; it
  records and guards the boundary without claiming runtime enforcement.
- **Live consumption (#53)** — blocked by `TK-04`, HITL. Only a user-controlled session can
  observe real totals, and the ceiling must exist first to give the observation something to
  compare against. This edge never blocks closing the issue. Owning ticket: `TK-09`.
- **Cross-host context rollover** — ready at its policy gate. Counting chat messages,
  checkpointing a private handoff, opening a fresh Codex or Claude Code session, and
  restoring the current Wayfinder/ticket frontier require a separate host-capability and
  authority decision. Owning map: [Cross-host context rollover](cross-host-context-rollover-wayfinder.md).

## Claim Ceiling

`TK-03` reduces expected context volume, but no local test can quantify that reduction. Its
local evidence proves only that a bound is declared and enforced, and `TK-04` proves only a
worst case. Any statement about actual tokens saved, cost saved, or cache behaviour requires
the `TK-09` observation and must carry its limitations.

## Ticket Plan

| ID | Type | Mode | Blockers | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| `TK-01` | grilling | HITL | none | Freeze the context budget unit | Decision spec fixing the unit, the counted surfaces, and the provider-free constraint |
| `TK-02` | task | AFK | `TK-01` | Measure the static prompt prefix | Provider-free read-only command, versioned JSON, fixtures, repository-level check |
| `TK-03` | task | AFK | `TK-01` | Bound leaf context intake | Declared per-leaf volume bounds plus prompt tests that leave verification duties intact |
| `TK-04` | task | AFK | `TK-02`, `TK-03` | Compose the worst-case per-turn ceiling | Composed ceiling, deliberate-raise procedure, regression test |
| `TK-05` | task | AFK | none | Document autopilot dependencies | README section listing the composed skills and loaded references |
| `TK-06` | task | AFK | `TK-02` | Write the token-reduction guide | Guide covering context reset, small-context delegation, and cache-friendly practice |
| `TK-07` | task | AFK | none | Audit model-invocation exposure | Stated hiding criterion, applied flags, and a listing-drift check |
| `TK-08` | task | AFK | none | Record the context-passing boundary | Observable boundary statement and test that `handoff` is not the leaf channel |
| `TK-09` | task | HITL | `TK-04` | Observe live run token consumption | Human-run observation with explicit limitations and a closure recommendation |

## Next Review

Execute `TK-04` and `TK-06` serially. Their prerequisites are integrated through PRs #59,
#60, and #61, and their completed ticket records are retained here with the earlier PRs
#54 through #58. `TK-09` remains a human-only live-observation gate after `TK-04`. The
cross-host rollover investigation remains separate from the active token-economics ticket
folder.
