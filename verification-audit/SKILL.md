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
- [Versioned JSON contract](references/verification-contract-v1.json)
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
7. Run the deterministic reducer. The declared implementation status, maximum claim,
   release status, and final disposition must exactly equal the reduction.

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

Return the validated bundle and a concise audit summary:

- CandidateRef and artifact version;
- implementation status and final disposition;
- claim ceiling and permitted/forbidden wording;
- blocking gaps and open gates;
- provider limitations and merge-authorization state;
- residual uncertainty.

If no material runtime or release claim exists, say the audit is not applicable. If the
contract cannot be established, fail closed rather than emitting a partial PASS.
