---
name: "code-simplification"
description: "Simplify recently changed code for clarity while preserving behavior, scope, tests, errors, side effects, and project conventions."
---

# Code Simplification

Make recently changed code easier to understand, modify, test, and debug while preserving its behavior exactly. The target is comprehension, not fewer lines.

Adapted from Addy Osmani's `code-simplification` skill:
https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md

That skill is inspired by Anthropic's Code Simplifier agent. Preserve this attribution when redistributing this adaptation.

## Inputs

Accept one focused change target:

- an uncommitted or staged diff;
- a branch or pull-request diff;
- a ticket plus its implementation diff;
- explicitly named files or functions.

When invoked by `ticket-autopilot`, use only the implementation diff for the current ticket and the evidence returned by `execute-ticket`.

## Non-negotiable contract

- Preserve outputs, errors, side effects, ordering, concurrency behavior, public APIs, data formats, and edge cases.
- Do not weaken validation, authorization, logging, observability, or error handling.
- Do not change tests merely to make a refactor pass. Existing tests are behavior evidence.
- Follow the repository's conventions and neighboring patterns; do not impose personal style.
- Prefer clear names and explicit control flow over dense or clever code.
- Do not optimize for line count.
- Stay inside changed code and its smallest necessary supporting boundary unless the user explicitly broadens scope.
- Do not mix unrelated cleanup into a feature or bug-fix diff.
- If the code is already clear, return a no-op result. Churn is not simplification.

## Process

### 1. Understand before editing

Inspect the diff and enough surrounding code to answer:

- What responsibility does this code have?
- Who calls it and what does it call?
- What behavior do tests, types, contracts, and acceptance criteria define?
- Which error paths, side effects, ordering constraints, performance constraints, or historical decisions matter?

Read project instructions and conventions. Use history or blame only when the reason for a suspicious construct is unclear. Do not remove a fence before understanding why it exists.

### 2. Find concrete opportunities

Look for evidence-backed improvements such as:

- deeply nested control flow that can become guard clauses;
- long functions with more than one responsibility;
- unclear, generic, abbreviated, or misleading names;
- duplicated logic within the change scope;
- nested ternaries or dense expressions that slow comprehension;
- redundant wrappers, assertions, branches, comments, or temporary variables;
- dead code proven unreachable or unused;
- speculative abstractions with no current consumer;
- repeated conditions that deserve a well-named predicate;
- needless indirection that hides the main flow.

Do not automatically remove abstractions that provide test seams, stable boundaries, compatibility, extension points, or performance value.

### 3. Simplify incrementally

For each candidate:

1. State why the new form is easier to understand.
2. Make one coherent behavior-preserving change.
3. Run the narrowest relevant tests or checks.
4. Keep the change only when evidence shows behavior is preserved and readability improves.

If a cleanup would touch more than roughly 500 lines, stop and recommend a separate automated refactor or ticket instead of performing a risky manual sweep.

### 4. Verify the complete diff

Run the repository's relevant test, lint, typecheck, build, and format commands when available. Compare before and after:

- Is the new code genuinely faster to understand?
- Are project conventions still followed?
- Did the diff remain focused and reviewable?
- Were errors, side effects, public contracts, and performance characteristics preserved?
- Did the simplification introduce a new abstraction or pattern that costs more than it saves?

Revert any candidate that fails these checks.

## Result contract

Return a structured summary:

- `status`: `simplified`, `no-op`, or `blocked`;
- `files_changed`: paths and concise changes;
- `simplifications`: before/after intent for each accepted cleanup;
- `behavior_evidence`: tests, contracts, or code paths used to establish equivalence;
- `commands`: commands run with pass/fail/skipped results;
- `risks`: remaining uncertainty, performance concerns, or skipped checks;
- `review_focus`: areas the next reviewer should inspect.

Never claim equivalence or a passing check without evidence.

## Red flags

Stop or reject a proposed simplification when it:

- requires changing expected test behavior;
- alters exceptions, return values, serialization, side effects, or call order;
- removes handling merely because it looks verbose;
- spreads outside the ticket's scope;
- replaces ordinary code with a clever one-liner;
- changes a performance-critical path without measurement;
- combines feature work and broad refactoring;
- creates a new shared abstraction for only one speculative use.
