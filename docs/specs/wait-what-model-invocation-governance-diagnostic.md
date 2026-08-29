# Wait-What Model-Invocation Governance Drift

## Artifact Graph

- Artifact ID: `artifact:wait-what-model-invocation-governance-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [WI-01 register wait-what as an explicit user-invoked compatibility surface](../tickets/wait-what-model-invocation-governance/01-register-wait-what-user-invocation.md)

## Type

Diagnostic spec

## Status

Diagnosed; ready for ticket execution.

## Diagnosis Report - lens: recent-change

### Root cause

Commit `747ffc3485e2cb93bc1b5ab5c977d89498467e1b` added `wait-what/SKILL.md`
with `disable-model-invocation: true`, but did not register the new skill in
`docs/model-invocation-policy.md` or refresh the controlled inventory's hidden-skill count.
The repository therefore contains a hidden skill that its governance table does not know
about. One missing integration step produces all three observed failures.

The existing flag is deliberate evidence about the intended behavior: `wait-what` is a
manual compatibility surface for a clarification capability that ordinary conversation
already provides. Its extra value is the explicitly requested controlled-language profile,
not a model-selected workflow. The policy's current Ground B wording is narrower than that
intent because it names only aliases of another listed skill. The coherent repair is to make
Ground B cover compatibility surfaces for an already available capability, register
`wait-what` under that ground, and refresh the hidden inventory count without making the skill
model-visible.

### Evidence

- On commit `747ffc3^`, all three targeted tests pass.
- On commit `747ffc3`, with no other change, the same three tests fail: hidden count `7`
  instead of `6`, missing classification `['wait-what']`, and a flag/classification mismatch.
- `git blame` attributes all five front-matter lines, including
  `disable-model-invocation: true`, to the same add-skill commit.
- `ticket-autopilot/tests/test_model_invocation_policy.py` derives its skill set directly
  from repository `*/SKILL.md` files and requires one policy row per skill.
- The controlled context-budget fixture installs `wait-what`, so the hidden count rises by
  exactly one while visible listing bytes remain `4,999`.
- `docs/research/mattpocock-skills-parity.md` records ordinary clarification as the existing
  capability and rejects a second always-visible listing entry for it.

### Feedback loop built

Run the following three tests on the parent and addition commits:

```bash
python3 -B -m unittest \
  ticket-autopilot.tests.test_context_budget.ContextBudgetTests.test_repository_baseline_reproduces_the_autopilot_inventory \
  ticket-autopilot.tests.test_model_invocation_policy.ModelInvocationPolicyTests.test_every_skill_is_classified \
  ticket-autopilot.tests.test_model_invocation_policy.ModelInvocationPolicyTests.test_flag_matches_classification -v
```

The parent passes three of three. The addition commit fails three of three with the exact
signals above.

### Fix location and approach

Update the Ground B definition and classification table in
`docs/model-invocation-policy.md`, add the `wait-what` row as `user-invoked`, and update the
controlled hidden-skill count and policy prose to seven. Preserve the front-matter flag and
the visible-listing byte baseline. Add or tighten a regression that proves the policy row,
flag, and controlled inventory remain aligned.

The context-budget test currently contains a second, independent static-closure and ceiling
drift that becomes visible after the hidden-count assertion advances. That defect is not
caused by `wait-what`; it requires its own diagnosis and ticket rather than being hidden in
this fix.

### Alternatives ruled out

- **A parser or discovery error.** Rejected: discovery returns `wait-what` by name and reads
  its hidden flag correctly; the missing data is only in the governed policy and fixture.
- **An environment-specific installed-skill difference.** Rejected: the failing fixture
  constructs a controlled temporary installation from repository skills.
- **Classifying the skill as model-invocable and removing the flag.** Rejected for this fix:
  it reverses the explicit author choice, adds permanent listing bytes, and conflicts with
  the recorded parity decision that normal clarification is already available.
- **Calling the optional argument Ground A.** Rejected: the skill can run without an answer,
  so claiming that it cannot start without human-supplied values would contradict both its
  `argument-hint` and its instructions.

### Confidence: high

The parent/addition commit pair isolates the regression to one commit, and the failing values
map directly to the omitted policy row and inventory count.
