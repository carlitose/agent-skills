---
name: "qa-test-plan"
description: "Plan causal QA for a runner candidate or standalone PR, commit, local diff, or requested scope without executing or deciding release."
---

# QA Test Plan

Owns: QA plan construction. It does not execute tests, change code, resolve gates, decide
completion/release status, or produce a Verification Record.

Use the taxonomy and identifiers from the canonical
[Verification Record](../verification-audit/references/verification-record.md). The
caller records observations and `verification-audit` performs the sole semantic
reduction.

## Inputs

Accept one acquisition route:

- **Runner handoff:** normalized Ticket Envelope, acceptance criteria, frozen diff,
  CandidateRef, supplied invariants/boundaries, environments, gates, and observed checks.
- **Standalone acquisition:** acquire a PR, commit, local diff, or user-requested scope
  read-only; record the observed identity, requested behavior, repository rules, available
  environments, limitations, and checks.

Do not parse Markdown to manufacture a Ticket Envelope. Mark unknown inputs as draft
limits or gates; never assume access or successful execution.

## Build the plan

For each changed behavior:

1. State the causal chain from injection point to user/external observation.
2. Select the smallest test that crosses the changed mechanism.
3. Classify the intended observation as static, unit, integration, simulated, or live
   using the canonical reference.
4. Name exact setup, action, expected result, cleanup, and evidence to capture.
5. Map the case to ticket criteria, invariants, boundary items, and gate IDs.
6. Add negative/error paths, retries, ordering/idempotency checks, and regression coverage
   where relevant.

Do not label a mocked provider or fake browser as live. If a required environment,
credential, approval, or device is unavailable, write a specific open gate and an
authorized simulation plan; do not silently lower the requirement.

## Output

Return:

```markdown
# QA Plan

## Candidate
- CandidateRef:

## Automated Checks
- ID, command, layer, causal path, expected evidence.

## Manual / Environment Checks
- ID, setup, action, expected observation, evidence class, cleanup.

## Negative and Regression Paths
- ID, failure or preserved behavior, expected observation.

## Mapping
- QA ID -> acceptance criterion / invariant / boundary item / gate.

## Open Gates and Limits
- Gate ID, owner, unblock condition, and claim impact.
```

Planning a check is not evidence that it ran. Keep planned, executed, passed, failed,
skipped, and blocked states distinct. A standalone draft cannot claim ticket completion or release.
