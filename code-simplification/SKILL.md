---
name: "code-simplification"
description: "Simplify the current candidate diff for clarity while preserving behavior, scope, tests, errors, side effects, and project conventions."
---

# Code Simplification

Owns: focused simplification of recently changed code. It does not select tickets, expand
scope, review acceptance, produce QA/audit artifacts, commit, push, open PRs, or finalize
workflow state.

## Inputs

Require the changed diff, allowed paths, semantic invariants, project conventions, and
checks that currently pass. If the candidate is not GREEN, return without editing.

## Contract

Preserve:

- externally observable behavior and public contracts;
- errors, validation order, side effects, retries, and persistence semantics;
- security and data-integrity boundaries;
- ticket scope and unrelated user changes;
- tests and project conventions.

## Process

1. Read the changed code in context and identify concrete duplication, unnecessary
   indirection, confusing names, or locally avoidable branching.
2. Prefer the smallest edit that makes intent obvious. Do not introduce speculative
   abstractions, broad formatting churn, compatibility shims, or architectural rewrites.
3. After each coherent edit, run the narrowest relevant checks. Revert the simplification
   if behavior cannot be shown equivalent.
4. Return changed paths, simplifications made, checks observed, and residual limits.

Never claim equivalence or passing checks without observed evidence. Any edit creates a
new CandidateRef and invalidates prior review/QA/audit evidence owned by the caller.
