# Verification Record Contract

This file is the canonical shared contract used by `verification-audit` and consumed by
implementation, review, QA, and autopilot workflows.

## Record schema

```yaml
verification_record:
  subject: "<ticket, diff, PR, or release>"
  claims:
    - id: C1
      text: "<precise observable claim>"
      kind: implementation | behavior | deployment | release
      criticality: low | medium | high | critical
      causal_chain:
        - step: "<trigger or transition>"
          controller: codebase | external-provider | browser | infrastructure | device | human
          observed: true | false
      evidence_ids: [E1]
      uncovered_segments: []
      status: supported | partially-supported | unsupported

  invariants:
    - contract: "<externally meaningful behavior, parameter, ordering, schema, or side effect>"
      source: ticket | spec | baseline | documentation | decision
      before: "<known prior semantics>"
      after: "<proposed semantics>"
      status: preserved | modified | removed | unknown
      authorization: "<requirement or decision, or missing>"
      evidence_ids: [E1]

  evidence:
    - id: E1
      class: static | unit | integration | simulated | live
      environment: local | ci | dev | staging | production | other
      command_or_action: "<what was run or observed>"
      injection_point: "<none, or where fabricated state enters>"
      observed_segment: "<first observed step -> last observed step>"
      result: pass | fail | inconclusive | skipped
      limitations: "<what this evidence does not prove>"

  hitl_gates:
    - id: H1
      blocked_claim_ids: [C1]
      environment: "<required environment>"
      action: "<exact human action>"
      owner: "<person or role>"
      required_evidence: "<observable artifact or result>"
      status: open | passed | failed | waived
      waiver_authority: "<who explicitly accepted the risk, if waived>"

  claim_ceiling:
    level: implementation-complete | deployable-for-test | behavior-verified | production-ready | release-blocked
    environment: "<where the claim holds>"
    allowed_wording: "<strongest truthful statement>"
    forbidden_wording: []
    reason: "<limiting evidence or gate>"
```

## Evidence classes

- `static`: inspection, type analysis, lint, configuration validation, or reasoning that
  does not execute the behavior.
- `unit`: execution within one isolated unit. Dependencies may be replaced.
- `integration`: execution across real in-scope components or boundaries. Name every
  boundary still replaced.
- `simulated`: execution that fabricates, emulates, replays, or stubs a material runtime
  participant or event.
- `live`: observation against the real participant in the named environment. Live
  evidence must still identify the exact causal segment observed.

These classes are descriptive, not a total ordering. A relevant integration proof may
support a claim better than an unrelated live observation.

## Causal coverage rules

1. Evidence supports only the segment between its injection point and its last observed
   effect.
2. Fabricating step N does not prove steps 1 through N-1.
3. Observing only the final state does not establish the intended path when another path
   can produce the same state.
4. A changed external contract requires evidence at that boundary or an explicit open gap.
5. A known-good baseline establishes prior semantics only when its environment and inputs
   are comparable.
6. A passing test that encodes the same assumption as the implementation is not independent
   confirmation of that assumption.

## Semantic invariant register

Record externally meaningful behavior, not every line-level detail. Common invariants
include request parameters, headers, scopes, event order, callbacks, schemas, retries,
timeouts, idempotency, security constraints, persistence effects, and user-visible state.

A `modified` or `removed` invariant is acceptable only when authorized by the ticket,
spec, explicit decision, or current external contract documentation. Otherwise it is a
semantic regression or an unresolved unknown.

## Claim ceilings

- `implementation-complete`: the requested code change exists and declared local checks
  passed. No untested runtime behavior is implied.
- `deployable-for-test`: build and pre-deployment checks support putting the change in a
  named environment for further verification.
- `behavior-verified`: the full causal segment named by the behavior claim was observed
  in the named environment with no critical contradictory evidence.
- `production-ready`: all release-critical acceptance criteria are evidenced, production-
  relevant risks are addressed, and no critical HITL or live gate remains open.
- `release-blocked`: implementation may be complete, but a critical verification,
  approval, environment, credential, or human gate remains open.

Use the lowest ceiling imposed by any release-critical claim or gate.

## Language rules

Prefer exact scoped wording:

- "Targeted unit and simulated checks passed."
- "The implementation is complete and deployable to staging for live verification."
- "The behavior was verified in staging across <named segment>."
- "Release is blocked pending <specific gate>."

Do not collapse these into "verified", "working", or "production-ready" without naming the
supported scope and environment.
