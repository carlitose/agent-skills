---
name: "verification-audit"
description: "Audit runtime claims against causal coverage, semantic invariants, evidence classes, and HITL gates before completion or release."
---

# Verification Audit

Audit what the available evidence actually proves before a ticket, review, QA plan, PR,
or release report claims that behavior works.

Use this skill after implementation and before any final completion or release statement
when the change affects runtime behavior, an external integration, a public contract, a
multi-step workflow, or a human-only verification gate. Other skills may invoke this skill
and consume its Verification Record and Claim Ceiling.

Read [references/verification-record.md](references/verification-record.md) completely
before performing the audit. It is the canonical contract for evidence classes, causal
coverage, invariant status, HITL gates, and claim ceilings.

## Non-negotiable rule

Green tests prove only the behavior and boundaries they actually exercise. Never infer
that an upstream, external, browser-controlled, provider-controlled, infrastructure-
controlled, or human-controlled step works when the evidence begins downstream of that
step.

A mock, stub, fixture, synthetic event, recorded response, emulator, or manually fabricated
state must be declared with its injection point.

## Inputs

Gather the smallest complete evidence bundle available:

- originating ticket, spec, acceptance criteria, or user request;
- implementation diff and changed public or external boundaries;
- known-good baseline behavior when one exists;
- automated test results and the tests themselves;
- manual, simulated, integration, staging, or live observations;
- open blockers, skipped checks, credentials, environment limits, and HITL gates;
- proposed completion, PR, deployment, or release claims.

Do not invent missing evidence. Mark it missing.

## Process

### 1. Inventory the claims

Rewrite each material statement as a precise observable claim. Split compound claims.
Distinguish implementation claims from behavior, environment, deployment, and release
claims.

### 2. Build the External Boundary Delta

Before accepting an Invariant Register supplied by another skill, independently inspect the
fixed diff and known-good baseline for every changed boundary controlled outside the current
module or repository. Include SDK/API calls, browser/provider options, headers, scopes, event
names, callback shapes, CLI flags, infrastructure configuration, serialized schemas, and
request/response payloads.

For every affected boundary:

1. identify the complete call or contract before and after, not only the edited lines;
2. enumerate every added, modified, and removed argument, property, literal, header, scope,
   callback, default, ordering rule, and side effect;
3. record the source and authorization for each semantic change;
4. classify each item as `preserved`, `authorized-change`, `regression`, or `unknown`.

Authorization must be item-specific and unambiguous. Cite the exact requirement, decision,
or current documentation that authorizes that field or semantic behavior. A broad product
goal, refactor intent, "single configuration," "backend authoritative," removal of a
user-visible selector, or support for an additional mode does not by itself authorize
removing an upstream provider-routing, capability-enabling, negotiation, or compatibility
field. When one source supports multiple incompatible interpretations, use `unknown`.

Do not summarize several option fields as "the launch is preserved." Record the meaningful
fields individually. If the diff changes an external boundary but the complete before/after
contract cannot be established, fail closed with `unknown`.

An absent or incomplete External Boundary Delta for a changed external boundary makes the
audit `unsupported`. An unauthorized high-impact removal or modification is an implementation
defect, not merely a missing live test.

### 3. Map the causal chain

For each behavior claim, list the required sequence from trigger to observable result.
Mark:

- internal and external boundaries;
- provider-, browser-, infrastructure-, device-, or human-controlled transitions;
- the point where each test or observation enters the chain;
- the first and last step actually observed.

If evidence injects an output downstream of the changed point, it cannot prove the omitted
upstream segment.

### 4. Audit semantic invariants

Compare affected contracts and externally meaningful behavior with the ticket and any
known-good baseline. Reconcile the register with every item in the External Boundary Delta;
no changed boundary item may disappear into a broader summary. Record each invariant as:

- `preserved`;
- `modified`;
- `removed`;
- `unknown`.

Every modified or removed invariant needs an authorizing requirement or decision plus
supporting documentation or equivalent evidence. The baseline is evidence of prior
semantics, not an untouchable implementation.

### 5. Classify every proof

Classify evidence as `static`, `unit`, `integration`, `simulated`, or `live`.
Also record environment, injection point, observed segment, result, and limitations.

The labels are not a universal ranking. Relevance comes from whether the evidence crosses
the boundary and covers the causal segment named by the claim.

### 6. Build the claim-to-evidence matrix

For each claim, identify supporting evidence, uncovered causal segments, contradicted
evidence, and residual uncertainty. A passing downstream test cannot close an upstream
gap.

### 7. Record HITL gates

For every human-only or environment-only gate, record:

- blocked claim;
- required environment;
- exact action;
- responsible actor or role;
- required evidence;
- current status.

"Manual test required" is not a complete gate.

### 8. Compute the claim ceiling

Use the canonical ceilings from the reference. Select the strongest statement supported
by all required evidence and gates. Open critical HITL or live-environment gates impose
`release-blocked`.

Do not use `verified`, `works in production`, `production-ready`, or equivalent
language above the ceiling.

An unauthorized high-impact semantic regression prevents `implementation-complete` even when
all tests pass. Set the verdict to `unsupported`, keep the ticket incomplete, and name the
exact boundary item.

### 9. Audit the proposed language

Compare the proposed final response, ticket status, PR body, or release note with the
claim ceiling. Replace or flag every overclaim. Preserve precise positive statements that
are supported.

## Output

Return one Verification Record using the canonical schema, followed by:

- **External Boundary Delta:** the complete changed-boundary inventory;
- **Verdict:** `supported`, `partially-supported`, or `unsupported`;
- **Claim Ceiling:** the strongest allowed status and exact recommended wording;
- **Forbidden Claims:** statements the current evidence does not permit;
- **Blocking Gaps:** uncovered causal segments and open critical gates;
- **Next Evidence:** the smallest concrete checks needed to raise the ceiling.

If no material runtime or release claim exists, say that the audit is not applicable and
why. Do not manufacture ceremony for documentation-only or formatting-only changes.
