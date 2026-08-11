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

## Volatile intake bound

- `max_volatile_bytes`: `103232` normalized UTF-8 bytes per invocation. This is the
  observed 96,393-byte candidate-diff high-water mark plus the 2,380-byte ticket-body and
  4,459-byte implementation-handoff maxima. The corpus is the run's TK-01/TK-02/TK-05/
  TK-07/TK-08 normalized `git diff --no-ext-diff --no-color` observations, its nine ticket
  bodies, and compact leaf results.
- `max_single_output_bytes`: `32596`, the observed TK-02 executable-code candidate diff.

Count every diff, file slice, pasted handoff, evidence body, and tool result after CRLF or
lone-CR normalization to LF. Read the manifest first; truncate command output before it
enters context and slice larger diffs by file or hunk. Prefer path plus SHA-256 references over
pasted artifacts, and count an artifact only when its content is required. If the next
required read would exceed either cap, stop before reading or editing and return the exact
remaining references with `budget-exhausted`; a later invocation may continue. The bound
never permits omitting preservation duties or claiming equivalence without evidence.

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
