# Verification Record Contract

This file is the canonical shared contract used by `verification-audit` and consumed by
implementation, review, QA, and autopilot workflows.

## Versioned machine contract

[verification-contract-v2.json](verification-contract-v2.json) is the canonical
machine-readable shape and policy table. It covers `CandidateRef`, stage results,
evidence, invariants, External Boundary Delta items, scoped gates, normalized provider
records, per-claim causal mappings, verification disposition, SHA-bound merge
authorization, and their deterministic reduction.

The Ticket Envelope is separately owned by
[Ticket Envelope v1](../../ticket-autopilot/references/ticket-envelope-v1.md) and the
shared `ticket_contract`; its schema is not duplicated here. The verification bundle
receives the normalized `ticket_id`, a `ticket_envelope_ref` to the runner-owned artifact,
and the complete frozen `CandidateRef`.

Claim targets use structured environment and boundary scopes. Provider capability facts
must reconcile with returned provider data; unavailable capabilities required by the
requested claim or operation are represented by explicit gates. Unknown fields are rejected
throughout the bundle so schema evolution requires a version change.

Every nested semantic artifact carries the complete `CandidateRef`. The validator rejects
the bundle when any nested reference differs from the bundle candidate or when the current
candidate passed by the runner differs from it. Merge authorization is separate: it must
reference a passed human gate and match the normalized provider record's exact PR head SHA.

The validator owns structural and referential facts only. It does not infer semantic
authorization, causal coverage, impact, evidence class, or gate resolution from prose.
Agents or humans classify those facts; the reducer applies only the versioned policy table.
Required stage outcomes, per-claim ceiling rules, release-critical classifications, and
merge-authorization and provider-capability requirements are data in that same contract,
not prose heuristics.

`VERIFICATION_AUDIT_ROOT` below is the absolute skill root resolved from the skill catalog
or this reference's parent skill, never from repository cwd:

```text
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" validate <bundle.json>
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" reduce <bundle.json>
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" validate-pr \
  <bundle.json> <pr-body.md> --pr-head-sha <sha>
```

Pass `--current-candidate <candidate-ref.json>` to `validate` before reusing stored
artifacts. Diagnostics are JSON on stderr and exit status `2` means contract-invalid.
Malformed legacy records are rejected; conversion, when required, must be explicit.

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

## External Boundary Delta rules

1. Build the delta independently from the raw fixed diff and known-good baseline.
2. Inspect the complete relevant call or contract before and after. A diff hunk alone may
   hide defaults, sibling fields, or deleted semantics.
3. Enumerate each meaningful argument, nested option, header, scope, literal, event,
   callback, ordering rule, and side effect separately.
4. Reconcile every changed item into the Invariant Register and claim matrix.
5. Do not accept broad summaries such as "SDK launch preserved" when nested contract items
   changed.
6. If an external boundary changed but its full delta is missing, classify it `unknown`,
   set the audit verdict to `unsupported`, and keep the ticket incomplete.
7. An unauthorized high-impact `modified` or `removed` item is a semantic regression. Live
   evidence cannot authorize it retroactively.
8. Require item-specific authorization. Cite the exact requirement, decision, or current
   documentation that authorizes the changed field or semantic behavior.
9. Do not infer authorization from broad goals such as "single configuration," "backend
   authoritative," "support another mode," "remove the selector," or "refactor." These do
   not authorize deleting provider-routing, feature-enabling, negotiation, fallback, or
   compatibility fields unless the source says so unambiguously.
10. If the cited source permits incompatible interpretations, classify the item `unknown`.
    A high-impact removed/modified `unknown` item blocks implementation completion.

## Claim ceilings

- `implementation-complete`: the requested code change exists and declared local checks
  passed. No untested runtime behavior is implied.
- `deployable-for-test`: build and pre-deployment checks support putting the change in a
  named environment for further verification.
- `behavior-verified`: the full causal segment named by the behavior claim was observed
  in the named environment with no critical contradictory evidence.
- `production-ready`: all release-critical acceptance criteria are evidenced, production-
  relevant risks are addressed, and no critical HITL or live gate remains open.
- `release-blocked` is not a claim ceiling. It is the orthogonal release disposition used
  when a critical verification, approval, environment, credential, provider-policy, or
  human gate remains open. It preserves the strongest supported environment-scoped claim.

Use the lowest evidence-supported ceiling for `max_claim`, then derive release status
independently from critical gates, provider policy, contradictory critical evidence, and
implementation blockers.

An unresolved External Boundary Delta or unauthorized high-impact regression prevents
`implementation-complete`; use `max_claim: none`, `release_status: blocked`, and identify
the implementation defect.

## Language rules

Prefer exact scoped wording:

- "Targeted unit and simulated checks passed."
- "The implementation is complete and deployable to staging for live verification."
- "The behavior was verified in staging across <named segment>."
- "Release is blocked pending <specific gate>."

Do not collapse these into "verified", "working", or "production-ready" without naming the
supported scope and environment.
