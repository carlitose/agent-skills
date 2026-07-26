---
name: "code-review"
description: "Review a diff for repo standards, ticket compliance, semantic regressions, causal evidence gaps, and overclaims."
---

# Code Review

Review a diff without editing files, saving reports, committing, or posting elsewhere
unless the user explicitly asks.

Use three independent axes:

1. **Standards**: repository conventions and high-signal maintainability or correctness
   risks.
2. **Spec/ticket compliance**: fidelity to the originating requirement.
3. **Verification semantics**: semantic baseline changes, causal coverage, evidence gaps,
   and overclaims.

If the host permits reviewer agents, assign one independent reviewer per axis and merge
results. Otherwise run the passes serially and keep findings separated.

## Inputs

Accept local changes, staged changes, a branch or range, a commit, pasted diff, spec or
ticket paths, or conversation context. Ask one concise question only when both the diff and
the intended fixed point are ambiguous.

## Process

### 1. Establish the fixed point

Resolve the comparison once and do not change it mid-review:

- worktree: `git diff HEAD`, including staged changes;
- commit: compare with its first parent;
- branch or "since": use `git diff <fixed-point>...HEAD` after resolving the merge-base;
- pasted diff: use the pasted content as fixed input.

If empty, stop and report no reviewable changes.

### 2. Perform an independent raw-context pass

Before reading the implementer's PR body, completion summary, generated explanation, or
prior review conclusions, gather only:

- fixed diff and changed files;
- originating raw ticket, spec, acceptance criteria, or user request;
- relevant known-good baseline behavior;
- nearby tests, public interfaces, and repository conventions.

Freeze initial findings from all three axes. Only then read the implementer's narrative, if
available, and reconcile it against the raw findings. Flag contradictions or unsupported
explanations.

If independent raw context is unavailable, state that limitation. Do not silently inherit
the implementer's framing.

### 3. Build the External Boundary Delta

Before the standards and compliance verdicts, inspect every changed SDK/API call, browser or
provider launch, header, scope, event, callback, CLI flag, infrastructure option, schema, and
public protocol. Compare the complete relevant call or contract at the fixed baseline and
candidate.

Return a row for every meaningful added, modified, or removed item:

```text
{boundary, item_path, before, after, authorization,
 status: preserved|authorized-change|regression|unknown}
```

Do not summarize a nested option object as preserved when one of its fields changed. If a
changed external boundary lacks a complete before/after delta, emit a `blocker` with status
`unknown`. An unauthorized high-impact removal or modification is a `blocker`, even when
tests and live checks pass.

Authorization must cite an exact, unambiguous requirement, decision, or current contract
for the specific item. Do not treat broad intent such as "single configuration," "backend
authoritative," "support another mode," "remove the selector," or "refactor" as permission
to delete provider-routing, capability-enabling, negotiation, fallback, or compatibility
fields. If the source permits incompatible interpretations, classify the item `unknown`;
high-impact `unknown` changes are blockers.

### 4. Standards axis

Documented repository standards override generic smell prompts. Check correctness, data
loss, security, unsafe error handling, dependency direction, missing relevant coverage,
and maintainability regressions.

Use this compact smell baseline only when relevant:

- mysterious names, duplication, feature envy, data clumps, primitive obsession;
- repeated switches, shotgun surgery, divergent change;
- speculative generality, message chains, middle men, refused bequests.

Skip formatter, lint, or type findings already reported by tools unless their output is
part of the requested review.

### 5. Spec/ticket compliance axis

Check:

- acceptance criteria and non-goals;
- required behavior at the correct public boundary;
- unrelated behavior changes;
- user-visible behavior, APIs, migrations, and documentation;
- edge cases and expected verification;
- unresolved dependencies or HITL gates.

If no authoritative requirement exists, limit this axis to the user request and visible
intent and say so.

### 6. Verification-semantics axis

#### Semantic regression review

Compare externally meaningful behavior with the raw ticket and known-good baseline. Inspect
parameters, schemas, headers, scopes, callbacks, event ordering, retries, timeouts,
idempotency, security constraints, persistence effects, and user-visible state.

Classify affected invariants as `preserved`, `modified`, `removed`, or `unknown`.
Reconcile every External Boundary Delta row into this classification.
Treat an unauthorized modification or removal as a blocker or should-fix according to
impact. The baseline is evidence of prior semantics, not an obligation to preserve obsolete
implementation details.

#### Causal-chain review

For each material behavior claim, map trigger to observable result. Mark external,
browser-, provider-, infrastructure-, device-, and human-controlled transitions.

Inspect where each test begins. If a test fabricates an event, response, callback, state, or
output downstream of the changed point, it verifies only the downstream segment. It does
not prove upstream causality.

Also flag:

- final-state assertions compatible with more than one causal path;
- tests that encode the same unverified assumption as the implementation;
- integration labels that hide replaced boundaries;
- simulated evidence presented as live behavior;
- skipped or human-only checks described as passes.

#### Evidence and claim audit

Invoke `verification-audit` when the change has a material runtime, external-boundary,
deployment, or release claim. Give it the raw requirement, diff, baseline, invariant
findings, tests, evidence, open gates, and any proposed PR or completion wording.

Use its Claim Ceiling to identify overclaims. An open critical HITL or live gate must block
`production-ready` and equivalent language.

### 7. Output

Lead with findings:

```markdown
## External Boundary Delta

- [blocker|should-fix|nit] <boundary> <item-path> — before: <value>; after:
  <value>; authorization: <source or missing>. Suggested fix.
- No changed external boundaries.

## Standards

- [blocker|should-fix|nit] path:line - Problem. Suggested fix.
- No findings.

## Spec/Ticket Compliance

- [blocker|should-fix|nit] path:line - Problem. Suggested fix.
- No findings.

## Verification Semantics

- [blocker|should-fix|nit] path:line - Invariant, causal gap, or claim problem. Suggested fix.
- No findings.

## Verification Summary

- Evidence observed: <class, environment, causal segment>.
- Residual gaps: <unobserved segments or none>.
- Claim Ceiling: <level and exact allowed wording>.
- Open gates: <gate or none>.

## Verdict

Pass | Needs changes | Blocked by missing context

## Notes

- Fixed point reviewed: <base/range/input>.
- Independent context: <raw sources used before implementer narrative>.
- Checks run or skipped: <commands and results>.
- Open questions: <only if needed>.
```

Use `blocker` for correctness, data loss, security, broken acceptance criteria,
unauthorized high-impact semantic regressions, or materially false release claims. Use
`should-fix` for meaningful maintainability, evidence, or coverage gaps. Use `nit`
sparingly.

If no problems are found, say so and still name residual evidence limits and checks not
run. A passing review does not raise the Claim Ceiling by itself.

Never return `Pass` when a changed external boundary has no complete delta.
