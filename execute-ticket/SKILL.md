---
name: "execute-ticket"
description: "Implement one normalized ticket through a bounded quality loop and return a validated handoff without scheduler or Git finalization side effects."
---

# Execute Ticket

Owns: one-ticket quality loop from semantic baseline through implementation, focused
simplification, review isolation gates, QA coordination, and verification handoff.

It does not choose from a folder, parse legacy Markdown, update the run ledger, move ticket
files, commit, push, open or edit PRs, merge, or clean worktrees.

Consume the normalized
[Ticket Envelope](../ticket-autopilot/references/ticket-envelope-v1.md) supplied by the
caller. Verification semantics and the output record are owned by
[verification-audit](../verification-audit/references/verification-record.md).

## Inputs

Require:

- normalized envelope and ticket body;
- repository/worktree path and allowed file scope;
- source and current CandidateRef;
- acceptance criteria and explicit compatibility requirements;
- quality retry limit and any already-open ticket-scoped gates.

Reject stale CandidateRefs and unresolved implementation-start HITL gates. A human-only
verification gate may remain open, but it limits the final disposition.

## Portable composition

Without delegation authority, invoke every stage inline in serial order; this is the
default and requires no AgentTool. Delegate to a distinct host worker only when the user or
an applicable host instruction explicitly authorizes it, and record that authority.
`AFK`, available capability, silence, and convenience are not delegation authority.

## Quality loop

1. Inspect only the code, tests, specs, and current documentation needed to establish the
   semantic baseline. For library, SDK, CLI, API, or cloud behavior, fetch current primary
   documentation as required by the repository.
2. Translate acceptance criteria into observable tests and invariants. When code behavior
   changes, use the requested test-first flow: reproduce RED, implement GREEN, then
   refactor without changing semantics.
3. Implement only ticket scope. Preserve unrelated user changes and do not add
   compatibility shims unless compatibility is explicit.
4. Run targeted checks. Invoke focused cleanup through `code-simplification` only after
   GREEN; rerun affected checks after any edit.
5. Freeze the candidate diff and CandidateRef. Invoke read-only `code-review`; describe it
   as independent only when separate-context isolation was observed. Never edit during it.
6. On blocker findings, mutate the candidate, invalidate prior review/QA/audit evidence,
   and retry from the relevant stage. Stop at the configured retry limit.
7. Invoke QA-plan construction through `qa-test-plan`. Execute only feasible authorized
   checks, and classify observations truthfully; simulated evidence never becomes live.
8. Give the runner-provided normalized ticket ID, Ticket Envelope artifact reference, full
   frozen CandidateRef, review result, QA plan/results, gates, provider records, and
   requested operation to `verification-audit`. It alone emits the canonical Verification
   Record and claim ceiling.

## Handoff

Return a structured result containing:

- ticket ID, Ticket Envelope artifact reference, and CandidateRef;
- changed paths and acceptance-criterion status;
- commands run and their observed outcomes;
- review findings and retry count;
- QA plan plus executed evidence references;
- each leaf's normalized execution mode, isolation, parallel flag, and authority reference;
- validated Verification Record or exact validation errors;
- unresolved human, credential, provider, or live-environment gates.

Do not claim `done`, `PR-open`, `integrated`, or production readiness. Those states belong
to the scheduler and the canonical verification reduction.
