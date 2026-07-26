---
name: "qa-test-plan"
description: "Generate a manual QA plan from code changes with evidence classes, causal coverage, simulation boundaries, and HITL gates."
---

# QA Test Plan Generator

Convert a commit, PR, diff, file change, or verbal change description into a concrete
manual end-to-end checklist for a human to execute against a named environment.

This skill plans tests; an unexecuted plan is not verification evidence. Do not generate
automated test code unless the user separately asks for it.

## Inputs

Accept:

- commit, tag, branch, range, PR, staged or unstaged changes;
- a specific file or pasted patch;
- a verbal description of a change.

When the input is ambiguous, default to `git diff HEAD` if a repository is available and
state the assumption. Ask once only when manual QA versus automated test code is genuinely
unclear.

## Process

### 1. Acquire the change

Use the appropriate fixed input:

- commit: `git show <hash>`;
- two refs: `git diff <base>..<head>`;
- branch: `git diff main...<branch>`, adjusted to the repository default branch;
- PR: `gh pr diff <number>` or the available GitHub connector;
- unstaged: `git diff`;
- staged: `git diff --staged`;
- full worktree: `git status` then `git diff HEAD`;
- pasted patch or verbal description: use it directly.

Record the fixed point. If the change is empty, stop.

### 2. Understand behavior and invariants

For each relevant changed file determine:

- changed function, endpoint, component, migration, job, or integration;
- user-visible trigger and observable result;
- public, data, runtime, or external contracts affected;
- prior known-good semantics and intended semantics;
- regression surfaces and new behavior.

Trace callers to a user-facing or externally observable entry point. Keep the scope
proportional.

Record affected semantic invariants as `preserved`, `modified`, `removed`, or
`unknown`. Flag unmotivated modifications or removals in plan risks.

Build an **External Boundary Delta** for every changed SDK/API call, browser/provider
option, header, scope, event, callback, CLI flag, infrastructure option, schema, or public
protocol. Compare the complete relevant contract before and after and enumerate every
meaningful item. Reconcile every item into the Invariant Register.

Require item-specific, unambiguous authorization for every semantic change. A broad goal
such as one configuration, backend authority, another mode, selector removal, or refactoring
does not authorize deleting provider-routing, capability-enabling, negotiation, fallback,
or compatibility fields. If no exact source authorizes the item, classify it `unknown` or
`regression` and create a blocking step or gate.

### 3. Map causal chains and boundaries

For each material behavior, write the causal chain from trigger to observable result.
Mark transitions controlled by:

- the codebase;
- an external provider or service;
- browser or device behavior;
- infrastructure or background workers;
- a human decision or action.

Identify the minimum environment and action needed to observe each material segment.

### 4. Design evidence-bearing QA steps

Every QA step must declare:

- concrete action;
- expected observable result;
- target environment;
- planned evidence class: `static`, `unit`, `integration`, `simulated`, or `live`;
- causal segment the step will observe;
- simulation or injection point, if any;
- artifact to retain, such as screenshot, log, trace, response, database row, or provider
  event;
- limitation: what the step will not prove.

Every External Boundary Delta item whose change is `added`, `modified`, or `removed`, or
whose status is `regression` or `unknown`, and every Invariant Register entry with status
`modified`, `removed`, or `unknown`, must map to at least one direct QA step or explicit
HITL/environment gate. Name the exact boundary item in the step. A generic end-to-end happy
path does not satisfy this rule.

The evidence class describes the planned execution, not its quality or result. A simulated
step cannot satisfy an acceptance criterion that requires behavior controlled by the real
external participant.

Do not call a step `live` merely because a human clicks through a local app. Name which
real participant and boundary are exercised.

### 5. Separate executable steps from gates

Put steps that require unavailable credentials, environments, provider accounts, devices,
permissions, approvals, or human judgment into **HITL / Environment Gates**. For each gate
record:

- blocked claim;
- required environment;
- exact action;
- owner or role;
- required evidence;
- status, initially `open`.

"Manually verify" without these fields is not acceptable.

### 6. Generate the plan

Use this structure:

```markdown
# Test Plan — <short change name>

## Scope
- Change:
- Fixed point:
- Verification objective:
- Current status: Plan only; no step is evidence until executed.

## Prerequisites
- Environment:
- Accounts and roles:
- Flags and data:
- Observability and artifacts:

## Causal Chains
- C1: <trigger> → <transition> → <observable result>
- Real or simulated boundaries:

## Invariant Register
- <contract>: preserved|modified|removed|unknown — <reason/evidence>

## External Boundary Delta
- Boundary:
  Item:
  Before:
  After:
  Authorization:
  Status: preserved|authorized-change|regression|unknown
  Covered by: <QA step or gate ID>

## Happy Path
1. Action:
   Expected:
   Environment:
   Planned evidence: live|integration|simulated|unit|static
   Boundary contract:
   Observed segment:
   Injection point:
   Retain:
   Does not prove:

## Edge Cases
<same fields>

## Negative / Error Paths
<same fields>

## Regression Risks
<same fields>

## HITL / Environment Gates
- Blocked claim:
  Environment:
  Action:
  Owner:
  Required evidence:
  Status: open

## Evidence Summary
- Full causal segments covered by planned live or real-boundary checks:
- Segments covered only by simulated or downstream checks:
- Remaining uncovered segments:
- Maximum claim if every executable step passes:
- Claim still blocked by open gates:

## Out of Scope
- <explicit exclusions>
```

Each action must be concrete, ordered, independently observable, and paired with an
expected result.

### 7. Handle executed evidence when supplied

If the user also provides results from executing the plan, do not silently convert planned
steps into passes. Record actual result and artifact for each step.

Invoke `verification-audit` when asked whether the executed evidence verifies the change,
supports release, or closes a ticket. Pass the causal chains, invariant register, evidence
classes, injection points, artifacts, failures, skipped steps, and open gates.

## Output destination

By default save the plan to
`docs/qa/test-plan-<branch-or-hash>.md` when inside a writable repository. Print it in chat
when output is explicitly ephemeral or no repository exists. Ask once only if destination
matters and cannot be inferred.

## Anti-patterns

Avoid:

- vague actions or missing expected results;
- treating plan creation as test execution;
- omitting a changed nested SDK/API option from the External Boundary Delta;
- leaving a modified, removed, regression, or unknown boundary item without a direct step
  or gate;
- calling synthetic or replayed behavior live;
- testing only the final state when multiple causal paths can produce it;
- skipping shared callers and regression surfaces;
- over-scoping unrelated areas;
- hiding unavailable environments as skipped passes;
- claiming `verified` or `production-ready` from the plan itself.

For changes above roughly ten files or five hundred lines, group the plan by feature or
concern and expose the groups at the top.
