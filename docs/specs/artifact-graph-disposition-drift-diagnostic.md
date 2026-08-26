# Artifact Graph Drift Across a Ticket Disposition Move

## Artifact Graph

- Artifact ID: `artifact:artifact-graph-disposition-drift-diagnostic`
- Role: `spec`
- Standalone: true

### Children
- [AG-01 record-suite-baseline](../tickets/artifact-graph-disposition-drift/01-record-suite-baseline.md)
- [AG-02 classify-llm-wiki-skill](../tickets/artifact-graph-disposition-drift/02-classify-llm-wiki-skill.md)
- [AG-03 disposition-tolerant-links](../tickets/artifact-graph-disposition-drift/03-disposition-tolerant-links.md)
- [AG-04 normalise-llm-wiki-front-matter](../tickets/artifact-graph-disposition-drift/04-normalise-llm-wiki-front-matter.md)
- [Test suite baseline](../research/test-suite-baseline.md)

## Type

Diagnostic spec

## Status

Active

## Summary

Two independent defects, found while running the `llm-wiki-project-history` ticket folder.
Both were shipped by hand-made pull requests that skipped the ticket pipeline, which is why
neither was caught before merge.

1. **`llm-wiki/SKILL.md` uses a front-matter form the repository's own tooling rejects, and
   three tests fall over it.** One root cause, three symptoms. Corrected attribution: these
   three were first recorded here as pre-existing and unrelated, which was wrong.
2. **`artifact-audit` reports a false owner-edge break after every ticket completion.** The
   runner moves a completed ticket into `done/`, and the audit's literal link resolution then
   fails in both directions. Repository-wide effect: **16 `broken-link` and 5
   `reciprocity-mismatch` errors**, all of them on tickets in a disposition subdirectory. It
   also blocks `docs-only-adopt` for the next ticket in any folder, because that contract runs
   the canonical audit over changed managed artifacts.
3. **The test suite is also red because `llm-wiki` was vendored without a policy entry.**
   `tests/test_model_invocation_policy.py::test_every_skill_is_classified` fails with
   `- ['llm-wiki']`. Introduced by PR #87.

## Observed behavior

### Defect 1

`context-budget . --json` on `main` at `8f99374` reports exactly one diagnostic:

```
malformed-front-matter: repository/llm-wiki/SKILL.md:4: multiline front matter is unsupported
```

`llm-wiki/SKILL.md` declares its description as a YAML folded block scalar,
`description: >-` followed by indented continuation lines. `context_budget._front_matter`
rejects any indented line outright — `if line.startswith((" ", "	")): raise
ContextBudgetError(...)` — so it reads `key: value` lines only.

That single diagnostic sets `always_on_listing["complete"]` to false, and the listing then
reports `normalized_bytes: None` rather than a count, because the aggregate is written as
`visible_bytes if complete else None`. Three tests fall over the `None`:

- `test_context_budget.test_repository_baseline_reproduces_the_autopilot_inventory` asserts
  `4999` against `None`. Its earlier assertions all pass, so the skill counts and the workflow
  closure are unaffected — only the aggregate is lost.
- `test_token_reduction_guide.test_quoted_baseline_matches_the_controlled_tk02_report` raises
  `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.
- `test_context_budget.test_cli_check_distinguishes_breach_from_deliberate_raise` observes exit
  `0` where it expects `2`: an incomplete measurement detects no ceiling breach.

**How the attribution was corrected.** These three were first recorded as pre-existing by
parking the new spec and tickets out of the tree and re-running. That could never have revealed
the cause, because `llm-wiki/` had already merged in PR #87 and was therefore still present.
Re-tested with `llm-wiki/` itself moved aside: **all four tests pass.** So all four reds come
from one pull request, not one.

The repository convention is unambiguous: **31 of 32 skills declare a single-line
description**, and `llm-wiki` is the sole outlier, introduced by copying the vendored skill
verbatim.

### Defect 2

Reproduced on this repository at `507d6a7`:

- `docs/tickets/llm-wiki-project-history/done/02-measure-app-tolerance.md` declares
  a `Parent` whose target is `../../specs/llm-wiki-project-history-wayfinder.md`. Read from
  inside `done/`, that prefix resolves to `docs/tickets/specs/`, which does not exist →
  `broken-link`. (Written without Markdown link syntax on purpose: the docs-only link check
  extracts bracket-and-parenthesis link forms even inside an inline code span, so quoting a
  broken link verbatim makes it report the example as a defect of its own.)
- `docs/specs/llm-wiki-project-history-wayfinder.md` declares a `### Children` entry pointing
  at `../tickets/llm-wiki-project-history/02-measure-app-tolerance.md`, the path the ticket
  occupied before the move → `broken-link`.
- The two are **coupled**. Repairing only the map's link makes it resolve, and then the
  reciprocity rule fails instead — `children target must point back to its owner` — because
  the child's own parent link still resolves nowhere. Observed both ways.
- Consequence for the pipeline: `docs-only-adopt` rejected `LW-10` twice, first with
  `documentation link target is missing: ... 02-measure-app-tolerance.md`, then with
  `canonical artifact audit failed for changed managed artifacts: reciprocity-mismatch`.

The same shape accounts for the repository's long-standing findings: every ticket in a `done/`
or `canceled/` directory across the `windows-text-fidelity`, `mattpocock-skills-adoption`,
`ticket-autopilot-delivery-merge`, `cross-host-context-rollover`, `autopilot-token-economics`
and `bounded-ticket-autopilot-leaves` families carries the same broken parent link.

### Defect 3

`docs/model-invocation-policy.md` holds a `## Classification` table with one row per
repository skill, `| \`<skill>\` | <classification> | <reason> |`, and the classification
vocabulary in use is exactly `model-invocable` and `user-invoked`.
`test_every_skill_is_classified` compares the table against the skills present in the
repository. PR #87 added `llm-wiki/SKILL.md` and no row, so the set difference is
`['llm-wiki']`.

`llm-wiki/SKILL.md` front matter carries `name` and `description` only, with no
`disable-model-invocation: true`, so the skill is model-invocable and the row must say so with
a reason, rather than being classified `user-invoked` to silence the test.

## Root cause

### Defect 1 — a deliberate fail-closed parser meets a vendored outlier

`context_budget._front_matter` is intentionally strict, raising rather than guessing on any
indented continuation. That is the correct posture for a measurement that feeds a ceiling
check: a silently mis-parsed description would corrupt the budget instead of failing it. The
defect is not the parser. It is that a vendored skill was copied in without normalising it to
the form 31 other skills already use, and that nothing ran the suite before the merge.

### Defect 2 — literal link resolution against a lifecycle-owned location

`artifact_audit._link_target` resolves a link as `(source.parent / value).resolve()`, with no
notion of the disposition directory. A ticket's location is **owned by the lifecycle, not by
the document**: `ticket_lifecycle._DIRECTORIES` maps `completed` → `done`,
`canceled` → `canceled`, `on-hold` → `hold`, and `transition_ticket_source` moves the file
between them.

**The obvious fix — have the mover rewrite the links — is unavailable, and this is the
non-obvious part.** `transition_ticket_source` verifies `_digest(source) != expected_digest`
before moving and, on replay of an applied receipt, verifies
`_digest(target) != expected_digest` afterwards. The ticket's bytes are frozen by contract
across the move, because the snapshot manifest and the CandidateRef depend on that digest.
Rewriting the file during the move would break the integrity invariant the transition exists
to hold.

So the ticket's own outbound links **cannot** be corrected at all, by anyone, once the file is
under management. The only place the mismatch can be resolved is in the reader.

### Defect 3 — a coupled artifact with no enforcement at authoring time

Adding a skill directory and adding its policy row are two edits that must happen together.
Nothing enforces the pair at authoring time; only the suite does, and the suite was not run
before PR #87 merged.

## Fix direction

### Defect 1

Normalise `llm-wiki/SKILL.md` to a single-line description, preserving the text verbatim.
Collapsed it is 854 characters, inside the existing range — `project-blueprint` is 875 — so
this is the repository's ordinary shape rather than a concession.

Explicitly not chosen: teaching `_front_matter` to fold block scalars. That relaxes a
deliberate fail-closed contract to accommodate one file, and it widens the surface of a parser
whose output feeds a ceiling check.

### Defect 2

Resolve artifact links on one principle: **a ticket's identity is its folder plus its
filename, independent of the disposition directory that currently holds it.** This is the same
principle `llm-wiki-reingest-identity-decision.md` fixes for wiki pages, applied to the
artifact graph.

Both directions need it, with distinct justifications:

- **Links out of a ticket** resolve additionally from the ticket folder root, because the file
  is digest-frozen and its location is lifecycle state.
- **Links into a ticket** accept the disposition subdirectories, because such a link names an
  artifact whose identity does not depend on where it currently sits.

Both fallbacks must apply **only when the literal target is absent**, so a genuinely dead link
still reports. The disposition directory names must come from `ticket_lifecycle`, not be
duplicated as literals.

Explicitly not chosen: making the mover rewrite links (breaks the digest contract); dropping
ticket links from `### Children` (every ticket would then fail reciprocity, since the rule
requires exactly one matching owner edge from the declared parent); rewriting the historical
ticket files (same digest contract, and it would not prevent recurrence).

### Defect 3

Add the missing row, and state the classification with a real reason rather than the one that
makes the test quiet.

## Semantic invariants

- A dead link that resolves nowhere — under the literal path or any disposition directory —
  still reports as `broken-link`. The tolerance must not become blanket permissiveness.
- No managed ticket file is rewritten. The digest contract is preserved untouched.
- `artifact-audit` stays read-only and provider-free; it never repairs what it reports.
- The audit's existing error classes keep their meaning; only resolution changes.

## Unresolved questions

- **Whether any red remains once the fixes land.** The baseline is recorded in
  [test-suite-baseline.md](../research/test-suite-baseline.md): 408 tests, 4 red on `main` at `8bfc4e5`,
  every one attributable to PR #87. Whether the repository then reaches green is unverified,
  since no run has been observed with the fixes applied. That claim belongs to whichever ticket
  lands last.
- **Whether the eight weak-key artefacts should gain `## Artifact Graph` sections.** Out of
  scope here; recorded in `llm-wiki-reingest-identity-decision.md`.
- **Whether the pre-existing `- Children:` bullet form should be migrated.** Five specs use it
  and the parser reads only `### Children`, which accounts for the seven residual
  `reciprocity-mismatch` findings that this fix does not touch. Separate concern.

## Verification strategy

Observable outcomes, none claimed as executed here:

- **Defect 1**: a fixture repository with one map and one ticket, the ticket placed in each of
  `done/`, `canceled/` and `hold/` while the map's `### Children` still names the folder-root
  path, produces zero audit errors. A second fixture, whose parent link names a spec that
  exists nowhere, still reports exactly one `broken-link`. Each test must be shown to fail
  without the change.
- **Defect 1, repository level**: audit errors on this repository drop from 24 to 8, and the
  eight that remain are the unrelated `path-escape` and the seven `- Children:` reciprocity
  findings named above.
- **Defect 2**: `test_every_skill_is_classified` passes, and
  `test_policy_classifies_no_skill_that_does_not_exist` still passes.
- **Both**: the affected modules — `artifact_audit`, `docs_only`, `ticket_lifecycle`,
  `ticket_inventory`, `platform_locks`, `skill_graph` — run green, and the full suite is
  compared against the baseline rather than judged on its own.

## Implementation slices

1. Establish and record the suite baseline on `main`, naming every red test. Nothing else can
   claim a regression status until this exists.
2. Add the `llm-wiki` policy row. Documentation only.
3. Make artifact link resolution disposition-tolerant, with tests proven able to fail.

A hand-written candidate for slice 3 already exists on the branch
`fix/artifact-audit-disposition-links` at commit `b436ca9`, marked not for merge. It was
produced outside the pipeline and is available as an implementation reference for the ticket
that owns the slice, not as a shortcut around it.
