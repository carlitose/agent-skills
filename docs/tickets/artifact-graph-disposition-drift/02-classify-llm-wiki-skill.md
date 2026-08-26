---
ticket_schema: 1
ticket_id: "AG-02"
execution_mode: AFK
blocked_by: []
---

# Classify the vendored llm-wiki skill in the model invocation policy

## Artifact Graph
- Artifact ID: `artifact:ag-02-classify-llm-wiki-skill`
- Role: `ticket`
- Parent: [artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## Parent Spec
[artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## What to Build
One row in `docs/model-invocation-policy.md`, and the decision behind it.

PR #87 vendored `llm-wiki/SKILL.md` and added no policy row, so
`tests/test_model_invocation_policy.py::test_every_skill_is_classified` fails with
`- ['llm-wiki']`. That test compares the skills present in the repository against the
`## Classification` table, whose rows have the form:

```
| `<skill>` | <classification> | <reason> |
```

The vocabulary in use is exactly two values, `model-invocable` and `user-invoked`, across 31
existing rows.

**The classification is a real decision, not a formality.** The test can be made quiet by
either value, so the row must state what is true rather than what is convenient:

- `llm-wiki/SKILL.md` front matter carries `name` and `description` only. It does **not** carry
  `disable-model-invocation: true`, which is how `grill-me`, `grill-with-docs` and `handoff`
  are hidden from model invocation and then recorded as `user-invoked` with a "Ground A/B"
  reason.
- Its description is written as a trigger surface — *"Use when (1) scaffolding a new knowledge
  base ... (2) ingesting articles/papers/PDFs/web pages ..."* — which is the shape of a skill
  meant to be reached by the model while deciding how to proceed.

So the honest row is `model-invocable`, and the reason must say why an agent needs to reach it.
If the intended answer were `user-invoked`, the front matter would need
`disable-model-invocation: true` as well, and this ticket must not classify it that way while
leaving the front matter model-invocable — the two would contradict.

## Acceptance Criteria
- [ ] One row for `llm-wiki` exists in the `## Classification` table, in the same form and the
      same alphabetical position as its neighbours.
- [ ] The classification matches the skill's front matter. If the row says `user-invoked`, then
      `disable-model-invocation: true` is added to `llm-wiki/SKILL.md` in the same change;
      otherwise the row says `model-invocable`.
- [ ] The reason column states why, in the register the other 31 rows use — not "so the test
      passes".
- [ ] `tests/test_model_invocation_policy.py` passes in full, both
      `test_every_skill_is_classified` and
      `test_policy_classifies_no_skill_that_does_not_exist`.
- [ ] No other skill's row is edited.

## Frontier
Ready, no blockers. Independent of `AG-01`: its verification is two named tests passing, which
does not require the full-suite baseline.

## Step-by-Step Implementation Plan
1. Confirm `llm-wiki/SKILL.md` front matter has no `disable-model-invocation` key.
   Checkpoint: the classification follows from an observed fact, not a preference.
2. Insert the row in alphabetical position with a substantive reason. Checkpoint: the table's
   ordering and column shape are unchanged around it.
3. Run the policy test module. Checkpoint: both tests green.

## Testing Plan
Automated: `python -m unittest tests.test_model_invocation_policy` from `ticket-autopilot/`.
Verify the failure first — the test is currently red, so this is a red-to-green transition that
can be observed rather than assumed.

Manual: read the inserted row beside its neighbours and confirm it does not read as filler.

Unavailable boundary: none. This is a documentation edit verified by an existing local test.

## Out of Scope
- Any other red test in the suite. `AG-01` names them; each gets its own ticket.
- Changing the policy document's structure, vocabulary, or the test that enforces it.
- Installing the `llm-wiki` skill into `~/.agents/skills/`.
- Any change to `llm-wiki/` beyond the front-matter key, and only if the classification
  requires it.
