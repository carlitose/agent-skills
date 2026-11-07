---
name: "execute-ticket"
description: "Execute one canonical ticket or a clear requirements-and-plan request through the same bounded quality loop, without scheduler or Git finalization side effects."
---

# Execute Ticket

Owns: one-deliverable quality loop from semantic baseline through implementation, focused
simplification, review isolation gates, QA coordination, and verification handoff.

It does not choose from a folder, parse legacy Markdown, update a run ledger, move ticket
files, commit, push, open or edit PRs, merge, or clean worktrees. Choose one intake below.
Both intakes use the single Quality loop, not separate implementation workflows.

## Ticket intake

For a canonical ticket or runner handoff require:
- normalized [Ticket Envelope](../ticket-autopilot/references/ticket-envelope-v1.md) and body;
- repository/worktree path and allowed file scope;
- source and current CandidateRef;
- acceptance criteria and explicit compatibility requirements;
- quality retry limit and any already-open ticket-scoped gates.

Reject stale CandidateRefs and unresolved implementation-start HITL gates. A human-only
verification gate may remain open, but it limits the final disposition. In skills-only,
load the [canonical input and handoff contract](references/skills-only.md); no runner is
needed. Canonical Ticket Envelope, CandidateRef and Verification Record schemas are unchanged.

## Requirements-and-plan intake

For a clear request with one cohesive deliverable and no required canonical ticket/audit,
load [plan execution](references/plan-execution.md). It owns source sufficiency, one plan,
standalone scope identity, escalation and the short handoff. Do not create canonical artifacts
just to satisfy the ticket intake above. In the loop, use source acceptance criteria and
standalone intake for review/QA; CandidateRef applies only to ticket intake.

## Portable composition

Without delegation authority, invoke every stage inline in serial order; this is the
default and requires no AgentTool. Before selecting distinct workers, apply the
[operating defaults](../ask-skills/OPERATING-DEFAULTS.md); record the user-requested scope
and observed isolation.

## Quality loop

1. Inspect only the code, tests, source requirements, and current documentation needed to
   establish the semantic baseline. For library, SDK, CLI, API, or cloud behavior, fetch
   current primary documentation as required by the repository.
2. Translate acceptance criteria into observable tests and invariants. When code behavior
   changes, use the requested test-first flow: reproduce RED, implement GREEN, then
   refactor without changing semantics.
3. Implement only the supplied scope. Preserve unrelated user changes and do not add
   compatibility shims unless compatibility is explicit.
4. Before executing checks, apply [verification admission and cost per attempt](references/verification-cost.md): validate the delivered packaging/artifact graph, select causal and mandatory checks, and retain all prior attempts and the current attempt's remaining budget. Do not automatically repeat a complete suite because the candidate changed. Run the admitted targeted checks. Pass leaves manifests and content-addressed references instead of
   pasted artifacts, enforce each leaf's declared normalized-byte intake and output caps,
   and continue a `budget-exhausted` partial result without dropping remaining scope.
   Invoke focused cleanup through `code-simplification` only after GREEN; rerun affected
   checks after any edit.
5. Freeze the candidate diff and its intake-specific identity. Invoke read-only `code-review`;
   describe it as independent only when separate-context isolation was observed. Never edit during it.
6. On blocker findings, mutate the candidate, invalidate prior review/QA/audit evidence,
   and retry from the relevant stage. Stop at the configured retry limit.
7. Invoke QA-plan construction through `qa-test-plan`. Recheck verification admission after
   drift; preserve old evidence under its original identity rather than relabel it. Execute
   only feasible authorized checks, and classify observations truthfully; simulated evidence
   never becomes live.
8. Return the selected intake's handoff. If a full Verification Record is required, obtain
   canonical inputs through their owners (promoting plan intake first), then supply ticket ID,
   envelope reference, frozen CandidateRef, review, QA, gates, provider records and requested
   operation to `verification-audit`. It alone emits the canonical record and claim ceiling.

## Handoff

In skills-only, return the selected intake's short note unless a full record is required.
For a runner-owned ticket/full-record handoff return:
- ticket ID, Ticket Envelope artifact reference, and CandidateRef;
- changed paths and acceptance-criterion status;
- commands run, observed outcomes, all retained attempts/shards, consumption per attempt,
  unknown costs, remaining budget, and the reason for any full-suite repeat;
- review findings, retry count, QA plan and executed evidence references;
- each leaf's normalized execution mode, isolation, parallel flag, and authority reference;
- validated Verification Record or exact validation errors, and unresolved gates.

Do not claim `done`, `PR-open`, `integrated`, or production readiness from implementation
handoff. Delivery needs the scheduler's receipts in Autopilot, or separately authorized
caller delivery and provider readback in skills-only. Neither intake confers that authority.
