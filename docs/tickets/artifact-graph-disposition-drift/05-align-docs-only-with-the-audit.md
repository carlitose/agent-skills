---
ticket_schema: 1
ticket_id: "AG-05"
execution_mode: AFK
blocked_by: []
---

# Align the docs-only gate with the audit it calls

## Artifact Graph
- Artifact ID: `artifact:ag-05-align-docs-only-with-the-audit`
- Role: `ticket`
- Parent: [artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## Parent Spec
[artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## What to Build
One answer where two readers currently give two. `docs_only.py` calls the canonical artifact
audit and then disagrees with it twice — about which links resolve, and about which severities
matter. Neither disagreement is a stricter reading; both are a different reading.

**Disagreement one, links.** `AG-03` resolved Defect 2 in `artifact_audit._link_target`: a
ticket's identity is its folder plus its filename, independent of the disposition directory
holding it, so a link is retried across `done/`, `canceled/` and `hold/` when the literal target
is absent. `docs_only._check_links` was never given that. It builds `repo_target` literally and
raises on the first miss:

```python
if probe.returncode != 0:
    raise DocsOnlyError(f"documentation link target is missing: {path} -> {target}")
```

The consequence is observed, not hypothesised. `LW-12` had to repair seven stale `### Children`
paths in `docs/specs/llm-wiki-project-history-wayfinder.md` and left its own behind for `LW-13`
to repair. The audit reported none of them, and nothing counts them: **130 Markdown links in
this repository do not resolve literally.**

**Disagreement two, severity.** `artifact_audit` emits `legacy-artifact` as a **warning**, with
the message `managed Markdown has no Artifact Graph section`. That severity is the audit's way of
tolerating a file that predates the convention. `docs_only._audit_changed_managed_artifacts` then
reads it as a refusal:

```python
relevant = [
    diagnostic
    for category in ("errors", "warnings")
    for diagnostic in audit[category]
    if managed_paths.intersection(_diagnostic_paths(diagnostic))
]
if relevant:
    raise DocsOnlyError(f"canonical artifact audit failed ...")
```

Measured on this repository: **28 files carry that warning**, and 22 of them are tickets. A
docs-only change can never touch a ticket, because `APPROVED_SCOPE` in
`docs_only_contract.py` sets `excluded_roots: ["docs/tickets"]`. So the set the gate can
actually refuse is the other **six** —

```
docs/research/mattpocock-skills-parity.md
docs/specs/bounded-ticket-autopilot-leaf-protocol.md
docs/specs/candidate-invalidation-decision.md
docs/specs/ticket-autopilot-autonomous-stacked-delivery.md
docs/specs/ticket-autopilot-delivery-merge-wayfinder.md
docs/specs/ticket-lifecycle-disposition-decision.md
```

The 22 tickets are worth naming anyway: they are three families that predate the convention, and
they are not weak-identity artefacts. A ticket carries `ticket_id` in its envelope, so the wiki
keys it on `ticket:<family>/<id>` regardless of whether it has an `## Artifact Graph`. Only the
six above lose identity if they move.

A docs-only ticket that edits any of those six is refused and forced onto the standard path.

`LW-13` decided those six stay as they are, on the user's instruction and with the reason
recorded: `docs/` is the source of truth, and the six carry 38 inbound references between them.
So the reader is what changes, not the files.

Nothing here is a crash. The standard path still runs the ticket. What is lost is the cheap
deterministic adoption, on exactly the documents least likely to need a full leaf cycle.

## Acceptance Criteria
- [ ] `docs_only.py` resolves a documentation link across the disposition directories on the
      same principle as `artifact_audit`, taking the directory names from `ticket_lifecycle` and
      falling back **only** when the literal target is absent.
- [ ] A genuinely dead link — one that resolves in no disposition directory — still raises
      `DocsOnlyError`. The fallback must not turn the link check into a pass-through.
- [ ] The two resolvers share one implementation. A third copy of the rule is how the first
      divergence happened, so a test asserts they agree on the same input.
- [ ] The docs-only gate blocks on `errors` only. A `legacy-artifact` warning on a changed path
      no longer refuses the adoption.
- [ ] An `error` on a changed path still refuses it, with the diagnostic code in the message.
- [ ] Editing any one of the six reachable files through `docs-only-adopt` succeeds, verified
      end to end rather than argued from the code.
- [ ] The count is stated correctly wherever it appears: 28 files carry the warning, 6 are
      reachable by a docs-only change, and the 22 tickets are excluded by scope rather than
      by severity.
- [ ] The existing suite stays green — 410 tests before this ticket — and `test_docs_only.py`
      gains a case per behaviour above.
- [ ] No change to `artifact_audit`'s own severities. `legacy-artifact` stays a warning.

## Frontier
Ready. `AG-03` is merged, and this ticket depends on nothing else.

## Step-by-Step Implementation Plan
1. Record the baseline: the suite count, the repository-wide literal-link failure count, and the
   `artifact-audit` totals. Checkpoint: numbers to compare against, not recollections.
2. Extract `artifact_audit`'s disposition-tolerant resolution into one function both modules
   call. Checkpoint: a test drives the same input through both callers and asserts one answer.
3. Give `docs_only._check_links` that function. Checkpoint: a fixture link that resolves only
   under `done/` passes, and a fixture link that resolves nowhere still raises.
4. Narrow the gate to `errors`. Checkpoint: a seeded `legacy-artifact` warning on a changed path
   is adopted; a seeded error on a changed path is refused.
5. Drive a real `docs-only-adopt` over one of the six files. Checkpoint: it reaches `verified`.
6. Re-run the full suite. Checkpoint: matches the step 1 baseline.

## Testing Plan
Automated: `ticket-autopilot/tests/test_docs_only.py` gains four cases — a link resolving only
under a disposition directory, a link resolving nowhere, a `legacy-artifact` warning on a changed
path, and an error on a changed path. `test_artifact_audit.py` asserts the shared resolver did not
change the audit's own behaviour. Full suite via
`python -m unittest discover -s ticket-autopilot/tests -t ticket-autopilot/tests`.

Manual: run `docs-only-adopt` against a one-line edit to
`docs/specs/ticket-lifecycle-disposition-decision.md` and confirm it is adopted. That file is the
hardest case: it carries the `legacy-artifact` warning and it is the spec that defines the
disposition directories the fix depends on.

Unavailable boundary: POSIX. Only Windows and CPython 3.12.10 are available here, and the link
check goes through `git cat-file`, so path separator handling is verified on one platform only.

## Out of Scope
- Adding `## Artifact Graph` to any of the six files. `LW-13` decided against it.
- Changing `artifact_audit`'s severities or its managed-root set.
- Repairing the 130 literal-link failures. This ticket makes the reader agree with the audit; it
  does not clean the backlog, and it should not, because the backlog is mostly links that resolve
  correctly under the fixed reader.
- Reporting the literal-link count anywhere. A counter is a separate, arguable feature.
- Any change under `llm-wiki/`.
