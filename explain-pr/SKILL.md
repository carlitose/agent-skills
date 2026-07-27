---
name: "explain-pr"
description: "Render and optionally publish a deterministic PR body from a validated verification bundle without changing its claims."
---

# Explain PR

Owns: PR-body rendering from an already validated bundle. It does not review code,
reinterpret evidence, raise a claim ceiling, authorize merge, or decide integration.

The required sections, visibility rules, and wording ceiling come from the canonical
[Verification Record](../verification-audit/references/verification-record.md) and its
validator.

## Inputs

Require:

- PR identifier or prepared branch/base/head context;
- normalized ticket summary;
- frozen CandidateRef and observed provider PR head SHA;
- validated verification bundle;
- concise code map or diff facts.

Reject missing/stale bundles. Never turn simulated, skipped, or gated evidence into a
stronger narrative.

## Render

Produce the headings required by the contract, including:

- what changed and why;
- before/after behavior;
- code map;
- tests and classified evidence;
- open/failed gates and residual limits;
- reviewer checklist;
- exactly one before/after Mermaid diagram.

Use literal IDs and dispositions from the bundle so machines and reviewers can trace each
statement. Do not add forbidden wording or infer provider capability.

Validate the rendered body with:

`VERIFICATION_AUDIT_ROOT` is the absolute verification-audit skill root resolved from the
skill catalog, never from repository cwd.

```bash
python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py" \
  validate-pr <bundle.json> <body.md> --pr-head-sha <observed-sha>
```

If validation fails, fix rendering only. A semantic bundle problem goes back to
`verification-audit`; a changed head requires fresh upstream evidence.

When the user or scheduler requested publication, update only the PR body through the
selected provider adapter, read it back, and revalidate the observed body/head. Return the
body, validation result, provider observation, and any publication error. Never merge.
