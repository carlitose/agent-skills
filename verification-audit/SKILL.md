---
name: "verification-audit"
description: "Produce, validate, and reduce the canonical Verification Record for a frozen candidate without fabricating evidence or authorization."
---

# Verification Audit

Owns: Verification Record production, validation, and deterministic claim reduction. It is
the only skill that interprets evidence, invariants, boundary deltas, gates, provider
capabilities, and merge authorization into a final disposition.

The complete normative contract is:

- [Verification Record reference](references/verification-record.md)
- [Versioned JSON contract](references/verification-contract-v2.json)
- `scripts/verification_contract.py`

Other skills may collect facts or flag gaps. They must not independently implement this
policy.

## Inputs

Require the runner-provided normalized ticket ID, Ticket Envelope artifact reference, and
frozen CandidateRef plus:

- acceptance criteria from the already-normalized ticket handoff;
- stage results for implementation, simplification, review, and QA;
- evidence records with actual class/result and causal references;
- invariant register and External Boundary Delta;
- gates and normalized provider records;
- requested operation and requested claims;
- exact-SHA merge authorization when merge is requested.

Treat absent, stale, contradictory, or unvalidated material input as unknown or blocking.
Never infer live access, provider support, approval, merge success, or production behavior.

## Volatile intake bound

- `max_volatile_bytes`: `12017` normalized UTF-8 bytes per invocation, the largest observed
  serialized `verification_inputs` payload in compact TK-01 and TK-02 checkpoint events.
- `max_single_output_bytes`: `12017`, from that same observed payload.

Count pasted stage results, evidence bodies, provider output, and tool results after CRLF or
lone-CR normalization to LF. Consume the normalized input manifest first; truncate command
output before it enters context. Prefer path plus SHA-256 references over pasted artifacts
and load an artifact body only when a specific causal or contract question requires it,
charging those bytes to the same total. If the next required read would exceed a cap, emit
a schema-3 partial checkpoint with exact remaining references and `budget-exhausted`; leave the fact
unknown or gated. Never weaken evidence classification, causal scope, boundary accounting,
verification duties, or the deterministic claim ceiling to fit the bound.

## Audit flow

1. Bind every stage result and nested artifact to the same current CandidateRef.
2. Validate IDs, references, required mappings, boundary completeness, and gate
   consistency against contract version 1.
3. Confirm evidence crosses the changed causal mechanism and carries no stronger class
   than its observation permits.
4. Confirm every externally meaningful change has an explicit disposition, invariant,
   evidence/QA mapping, claim mapping, and gate where unresolved.
5. Normalize provider capability and mutation observations. A required unavailable
   capability needs exactly one explicit provider-capability gate.
6. Validate exact-head merge authorization when applicable.
7. For each schema-3 leaf, copy its isolation into existing stage limitations without
   changing the Verification Record schema. An independence claim with shared-context or
   unknown isolation requires a limitation and an explicit `unsupported-independence` gate.
8. Run the deterministic reducer. The declared implementation status, maximum claim,
   release status, and final disposition must exactly equal the reduction.

When `ticket-autopilot` supplies its verification checkpoint adapter, produce
the semantic bundle inputs once and let the runner serialize, hash, validate,
reduce, and resume them. This skill still owns every evidence classification,
boundary authorization, contradiction, uncertainty, gate, and final wording.
The runner must inject this skill's `validate_bundle` and `reduce_claims`
functions; a checkpoint cache hit may reuse their exact prior outputs only
when CandidateRef and normalized input hash are unchanged. Skipped, simulated,
blocked, or unavailable live boundaries remain explicit inputs and cannot be
upgraded by checkpointing.

## Commands

`VERIFICATION_AUDIT_ROOT` means the absolute skill root resolved from the available skill
catalog or from this `SKILL.md` location, never from repository cwd.

```bash
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" validate <bundle.json>
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" reduce <bundle.json>
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" \
  validate-pr <bundle.json> <body.md> --pr-head-sha <observed-sha>
```

Ticket Markdown parsing belongs to `ticket-autopilot`. This skill consumes only the
runner-provided identity, Ticket Envelope artifact reference, and CandidateRef; it never
rediscovers ticket identity from Markdown or prose.

## Output

For a runner handoff, return a schema-3 `verify` leaf result plus the validated
bundle. Bind its schema-1 `quality` evidence to the exact `handoff-ready`
checkpoint hash and CandidateRef; interruptions remain non-passing partial
handoffs. For standalone use, return the validated bundle and a concise audit
summary:

- CandidateRef and artifact version;
- implementation status and final disposition;
- claim ceiling and permitted/forbidden wording;
- blocking gaps and open gates;
- provider limitations and merge-authorization state;
- residual uncertainty.

If no material runtime or release claim exists, say the audit is not applicable. If the
contract cannot be established, fail closed rather than emitting a partial PASS.
