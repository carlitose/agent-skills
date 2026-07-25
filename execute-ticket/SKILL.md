---
name: "execute-ticket"
description: "Implement one ticket end-to-end with semantic invariants, classified evidence, review, and truthful claim ceilings."
---

# Execute Ticket

Implement one specific ticket from start to finish. This skill does not choose from a
queue. It executes the ticket the user gives you, or the ticket already present in
context.

## Backward compatibility default

Unless the ticket, spec, or user explicitly requires backward compatibility, implement the
clean target state. Do not preserve legacy APIs, aliases, configuration keys, formats, or
code paths through shims or parallel implementations by default. Treat compatibility as
an explicit acceptance criterion, not an inferred obligation. Still protect data integrity
and report breaking external contracts or irreversible migrations clearly.

## Inputs

Accept a local ticket path or folder, pasted ticket text, tracker context, or a task
described in the conversation. If the target is ambiguous, ask one concise question. If it
is clear, proceed.

## Process

### 1. Understand the ticket

Extract:

- problem, acceptance criteria, and non-goals;
- dependencies, blockers, and HITL requirements;
- expected tests, environments, and verification steps;
- runtime, public, data, and external contracts the change may affect.

If a missing human decision blocks implementation, stop unless the user already provided
it. A human-only verification gate does not prevent implementation, but it must remain open
and constrain the final claim.

### 2. Inspect current state and establish the semantic baseline

Explore only enough of the repository to understand:

- current behavior and failing tests;
- nearby patterns and public interfaces;
- user-visible and externally controlled boundaries;
- known-good prior behavior, configuration, or implementation;
- project commands from README, scripts, CI, Makefile, task files, or solution files.

Create an **Invariant Register** for externally meaningful behavior affected by the diff.
Include request parameters, headers, schemas, scopes, callbacks, event ordering, retries,
timeouts, idempotency, security constraints, persistence effects, and user-visible state
when relevant.

For each invariant record:

- source: ticket, spec, baseline, documentation, or explicit decision;
- before and intended after semantics;
- status: `preserved`, `modified`, `removed`, or `unknown`;
- authorization for every modification or removal;
- evidence or unresolved gap.

Do not treat the baseline implementation as sacred. Do prevent accidental semantic changes.

### 3. Check current external documentation

For third-party frameworks, libraries, SDKs, APIs, cloud services, endpoints, configuration,
or syntax, use the repository's required documentation flow. In repositories that require
`ctx7`, use:

1. `npx ctx7@latest library <name> "<specific question>"`
2. `npx ctx7@latest docs <libraryId> "<specific question>"`

Compare changed external contracts with both current documentation and the Invariant
Register. Do not look up general programming concepts or project-local business logic.

### 4. Implement with focused tests

Use red-green-refactor where feasible:

- RED: reproduce the problem with a failing test or identify an existing failure.
- GREEN: implement the smallest coherent ticket-scoped change.
- REFACTOR: clean up only after targeted behavior is green.
- Test at the public boundary, contract, module interface, or workflow expected by the
  ticket and repository.
- Avoid implementation-detail assertions unless conventional for that layer.

For every mock, stub, fixture, emulator, replay, synthetic event, or fabricated state,
record its injection point and the upstream behavior it does not exercise. A test that
injects an output downstream of the changed point does not verify the skipped causal
segment.

If no new test is justified, record why.

### 5. Verify and classify the evidence

Run targeted feedback loops during implementation, then proportionate broader checks:

- targeted tests;
- broader suite for shared behavior;
- build, typecheck, lint, and format;
- available integration, simulated, staging, or live checks.

For each meaningful result record:

- evidence class: `static`, `unit`, `integration`, `simulated`, or `live`;
- environment;
- injection point;
- causal segment actually observed;
- result and limitations.

If services, credentials, environments, or permissions are missing, record an explicit
gate instead of guessing a pass.

### 6. Review before declaring done

Invoke `code-review` against the diff. Require standards, spec/ticket compliance, and
semantic-regression findings. Address blocking findings or record why they remain.

The review must compare the diff with the Invariant Register and flag tests that begin
downstream of the changed causal boundary.

### 7. Run the verification audit

Invoke `verification-audit` with:

- ticket or acceptance criteria;
- diff and Invariant Register;
- test and command evidence with classifications and injection points;
- review results;
- open blockers and HITL gates;
- proposed completion wording.

Keep its Verification Record, Claim Ceiling, forbidden claims, and blocking gaps. If the
audit finds an unsupported material claim or unauthorized invariant change, fix it or
leave the ticket incomplete.

### 8. Update the ticket record

For a local Markdown ticket:

- move it to `done/` only when its acceptance criteria are met and its required
  verification gates are passed or explicitly waived by an authorized human;
- if implementation is complete but verification remains open, leave it pending and append
  completed work, evidence, Claim Ceiling, and exact gate details;
- never use a green local suite alone to close a live or human-controlled criterion.

Update an external tracker only when the user asked.

### 9. Commit when appropriate

Commit only when requested or clearly allowed by repository workflow. Include what changed,
key decisions, classified verification, Claim Ceiling, and remaining gates. Exclude
unrelated files.

## Final Response

Lead with the strongest statement allowed by the Verification Record. Report:

- what was implemented and files changed;
- Invariant Register changes;
- checks run, evidence classes, and observed scope;
- Claim Ceiling and exact environment;
- ticket status and specific remaining gates.

Do not use `verified`, `working in production`, or `production-ready` above the
Claim Ceiling. Keep the response concise and do not paste large diffs.
