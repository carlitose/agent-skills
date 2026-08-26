# Test suite baseline

## Artifact Graph

- Artifact ID: `artifact:test-suite-baseline`
- Role: `research`
- Parent: [Artifact Graph Drift Across a Ticket Disposition Move](../specs/artifact-graph-disposition-drift-diagnostic.md)

Produced by `AG-01`. The owner edge sits on the parent spec rather than on the ticket because
the scheduler binds ticket source by digest, and editing a ticket file mid-run is source drift.

## Purpose

"No regressions" is only a claim if someone can say what was already red. This is that list.
Compare against it; do not judge a run on its own counts.

## Observed run

| | |
| --- | --- |
| Command | `python -m unittest discover -s tests -t tests -v`, from `ticket-autopilot/` |
| Commit | `main` at `8bfc4e5` |
| Tests | **408** |
| Red | **3 failures, 1 error**, 1 skipped |
| Wall clock | **1049 s**, about 17.5 minutes |
| Interpreter | CPython 3.12.10 |
| Platform | Windows-11-10.0.26200-SP0 |

`pytest` is not installed and is not required; these are stdlib `unittest` tests.

## The four red tests

Every one is **attributable**, and all four to the same pull request — PR #87, which vendored
the `llm-wiki` skill outside the ticket pipeline. None is pre-existing.

| Test | Kind | Cause | Owner |
| --- | --- | --- | --- |
| `tests.test_context_budget.ContextBudgetTests.test_repository_baseline_reproduces_the_autopilot_inventory` | FAIL | `assertEqual(4999, None)` — the listing aggregate is `None` | `AG-04` |
| `tests.test_token_reduction_guide.TokenReductionGuideTests.test_quoted_baseline_matches_the_controlled_tk02_report` | ERROR | `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` | `AG-04` |
| `tests.test_context_budget.ContextBudgetTests.test_cli_check_distinguishes_breach_from_deliberate_raise` | FAIL | exit `0` where `2` is expected; an incomplete measurement finds no ceiling breach | `AG-04` |
| `tests.test_model_invocation_policy.ModelInvocationPolicyTests.test_every_skill_is_classified` | FAIL | `- ['llm-wiki']` — no row in `docs/model-invocation-policy.md` | `AG-02` |

The first three share one root cause, recorded in the parent spec:
`llm-wiki/SKILL.md` declares its description as a YAML folded block scalar, and
`context_budget._front_matter` rejects any indented continuation line, so `context-budget`
emits one `malformed-front-matter` diagnostic. That sets `always_on_listing["complete"]` false,
and the aggregate is written as `visible_bytes if complete else None`.

### How the attribution was reached

The first attempt got it wrong, and the method is worth recording so it is not repeated. Three
of the four were initially called pre-existing after parking newly added spec and ticket files
out of the tree and re-running. That could not have revealed the cause, because `llm-wiki/` had
already merged and was therefore still present.

The decisive test was to move **`llm-wiki/` itself** aside and re-run: all four pass. Absence
of the suspect, not absence of the newest files, is what isolates a cause.

## The cheap check

All four red tests live in the twelve modules that inspect the real repository rather than a
fixture — the ones that resolve `REPO_ROOT`:

```
test_codebase_design_skill      test_context_passing_boundary   test_diagnose_redaction
test_improve_codebase_architecture_scope                        test_model_invocation_policy
test_readme_dependencies        test_skill_graph                test_tdd_shared_design
test_token_reduction_guide      test_writing_for_agents_skill   test_ticket_inventory
test_context_budget
```

Run together they are **91 tests in about 8 seconds**, and they reproduce the same
`failures=3, errors=1` tally as the full suite. For any change that touches repository layout,
skills, or `docs/`, this is the check that earns its cost. The 17-minute full run is for changes
to the scheduler, the finalizer, the providers, or the contracts.

This is an observation about where the current reds live, not a rule. A change to
`artifact_audit`, `docs_only`, `kernel` or `cli` still needs its own modules, and a claim of
"no regressions" across the whole suite still needs the whole suite.

## What this record does not claim

- It does not claim the suite reaches green once `AG-02` and `AG-04` land. No run has been
  observed with those fixes applied.
- It is scoped to one commit, one interpreter, and one platform. The repository already carries
  platform-conditional tests — `WT-04` and `WT-06` exist for that reason — so POSIX behaviour is
  unobserved here.
- It fixes nothing. `AG-02` and `AG-04` own the repairs.
