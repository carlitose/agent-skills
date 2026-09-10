---
type: source
title: "Normalise the vendored llm-wiki front matter to a single-line description"
identity_key: ticket:artifact-graph-disposition-drift/AG-04
identity_strength: stable
source_path: docs/tickets/artifact-graph-disposition-drift/done/04-normalise-llm-wiki-front-matter.md
source_digest: sha256:1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-26
created_provenance: git-commit
disposition_changed: 2026-08-26
disposition_changed_provenance: git-rename
run_id: 9ea0f2970dad49ac
---

# Normalise the vendored llm-wiki front matter to a single-line description

Compiled from `docs/tickets/artifact-graph-disposition-drift/done/04-normalise-llm-wiki-front-matter.md`. Identity is `ticket:artifact-graph-disposition-drift/AG-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-26** via `git-commit`
- Disposition changed: **2026-08-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-artifact-graph-disposition-drift-diagnostic]]

## Run

Completed under autopilot run `9ea0f2970dad49ac`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-artifact-graph-disposition-drift-ag-04.md","payload_bytes":5984,"payload_sha256":"1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b"}],"payload_bytes":5984,"payload_sha256":"1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b","schema":1,"source_digest":"sha256:1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b","source_identity":"ticket:artifact-graph-disposition-drift/AG-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5984,"payload_sha256":"1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b","schema":1,"source_digest":"sha256:1b831c584805009d1513147f79ff0e24a7d357601858f1535d45a5f014d0fc2b","source_identity":"ticket:artifact-graph-disposition-drift/AG-04"} -->
````markdown
---
ticket_schema: 1
ticket_id: "AG-04"
execution_mode: AFK
blocked_by: []
---

# Normalise the vendored llm-wiki front matter to a single-line description

## Artifact Graph
- Artifact ID: `artifact:ag-04-normalise-llm-wiki-front-matter`
- Role: `ticket`
- Parent: [artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## Parent Spec
[artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## What to Build
One front-matter edit that turns three red tests green.

`llm-wiki/SKILL.md` declares its description as a YAML folded block scalar:

```yaml
description: >-
  Build and maintain a Karpathy-style LLM knowledge base — a self-compiling
  Obsidian markdown wiki where an Agent ingests raw sources, ...
```

`context_budget._front_matter` rejects any indented continuation line outright —
`if line.startswith((" ", "\t")): raise ContextBudgetError(...)` — so it reads `key: value`
lines only. `context-budget . --json` on `main` at `8f99374` reports exactly one diagnostic:

```
malformed-front-matter: repository/llm-wiki/SKILL.md:4: multiline front matter is unsupported
```

That single diagnostic sets `always_on_listing["complete"]` false, and the aggregate is written
as `visible_bytes if complete else None`, so `normalized_bytes` becomes `None`. Three tests fall
over the `None`:

- `test_context_budget.test_repository_baseline_reproduces_the_autopilot_inventory` asserts
  `4999` against `None`;
- `test_token_reduction_guide.test_quoted_baseline_matches_the_controlled_tk02_report` raises
  `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`;
- `test_context_budget.test_cli_check_distinguishes_breach_from_deliberate_raise` observes exit
  `0` where it expects `2`, because an incomplete measurement finds no ceiling breach.

**The parser is not the defect.** Its strictness is deliberate and correct: a silently
mis-parsed description would corrupt a budget that feeds a ceiling check, instead of failing
it. The defect is that the vendored skill was copied in without normalising it to the form the
rest of the repository already uses — **31 of 32 skills declare a single-line description**, and
`llm-wiki` is the sole outlier.

Collapsed to one line the description is **854 characters**, inside the existing range;
`project-blueprint/SKILL.md` is 875. So this is the repository's ordinary shape, not a
concession to the parser.

The description is the model's trigger surface for the skill, so the text must be preserved
word for word. Only the YAML form changes.

## Acceptance Criteria
- [ ] `llm-wiki/SKILL.md` front matter has a single-line `description:` value.
- [ ] The description text is **byte-identical** to the folded original once folding is applied
      — every line joined with one space, leading and trailing whitespace per line removed, and
      nothing added, dropped, reworded or truncated. Verify by comparing the collapsed original
      against the new value programmatically, not by eye.
- [ ] `name` is unchanged and still matches the directory.
- [ ] No other field is added, and in particular `disable-model-invocation` is not introduced
      here — that classification belongs to `AG-02`.
- [ ] `context-budget . --json` reports **zero** diagnostics, and
      `always_on_listing["complete"]` is true with an integer `normalized_bytes`.
- [ ] The three named tests pass. Each must be observed red before the edit and green after, so
      the transition is measured rather than assumed.
- [ ] The body of `llm-wiki/SKILL.md` below the front matter is untouched.
- [ ] `test_every_skill_is_classified` is still red afterwards, because `AG-02` owns it. This
      ticket must not quietly fix a second thing.

## Frontier
Ready, no blockers. It is the cheapest of the four tickets and clears three of the four red
tests on its own.

## Step-by-Step Implementation Plan
1. Observe the three tests red, and capture the `context-budget` diagnostic. Checkpoint: the
   starting state is recorded, not assumed.
2. Collapse the folded scalar programmatically — join the continuation lines with single
   spaces — and assert the result equals the original folding before writing. Checkpoint: text
   preservation is proven, not inspected.
3. Write the single-line front matter. Checkpoint: `context-budget . --json` reports zero
   diagnostics.
4. Re-run the three tests. Checkpoint: green.
5. Re-run `test_model_invocation_policy`. Checkpoint: still red, confirming scope was not
   widened.

## Testing Plan
Automated: `python -m unittest tests.test_context_budget tests.test_token_reduction_guide` from
`ticket-autopilot/`, red before and green after. Then the twelve repository-scanning modules,
which cover this whole failure class and run in about 8 seconds — the full suite takes roughly
17 minutes and is not required to observe this change, since the cause and effect are both
inside those modules.

Manual: read the resulting front matter and confirm the description still reads as a usable
trigger surface on one line.

Unavailable boundary: only Windows and CPython 3.12.10 are observed. `normalized_text` handles
line-ending normalisation, so the edit is not expected to be platform-sensitive, but POSIX stays
unobserved.

## Out of Scope
- Teaching `context_budget._front_matter` to parse folded block scalars. Explicitly rejected in
  the parent spec: it relaxes a deliberate fail-closed contract for one file.
- The missing `docs/model-invocation-policy.md` row, owned by `AG-02`.
- The artifact-audit disposition defect, owned by `AG-03`.
- Rewording, shortening, or improving the description's content.
- Installing the skill into `~/.agents/skills/`.
- Updating the baselines asserted in `test_context_budget`; the assertion of `4999` is expected
  to hold once the measurement completes. If it does not, that is a finding for a new ticket
  rather than a number to adjust here.

````
