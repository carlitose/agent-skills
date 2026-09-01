---
name: "change-status-ticket"
description: "Change an exact ticket's administrative disposition to open, on-hold, or canceled. Use only for explicit hold, cancel, reopen, or disposition-setting requests; not for implementing, completing, pausing, blocking, stopping, waiting on, or inspecting a ticket."
---

# Change Status Ticket

Owns one explicit administrative-disposition transaction. It does not implement or complete
the target ticket, edit its prose or dependencies, pause a run, approve a gate, or create
review, QA, verification, provider, merge, publication, wiki, Pi, cleanup, or issue
authority.

## Intake

Require these normalized inputs before mutation:

- canonical primary `repository_identity` and Git common-directory identity;
- exact ticket source path, globally unique short ID, Artifact ID, and file digest;
- prior disposition and target disposition, where the target is exactly `open`, `on-hold`,
  or `canceled`;
- explicit non-empty `actor`, `reason`, and durable `authority_ref` bound to this ticket,
  prior/target disposition, actor, and reason;
- tracked or ignored source mode and the terminal branch;
- for `open`, one exact ticket-bound passed human `reopen_gate_id`; reject that field for
  hold or cancel.

Never infer actor or authority from agent identity, provider login, Git configuration, a
prior run, or prose. Ask for a missing authority-bearing input. Treat “open” as a
disposition only when the user explicitly says reopen or set the administrative
disposition; do not route “open this file/issue/PR” here.

**Completion criterion:** every field is exact and non-contradictory, or the request is
reported `rejected` before an effect.

## Resolve without mutation

Resolve `TICKET_AUTOPILOT_ROOT` from the installed skill catalog. Use the repository's
read-only inventory and Git commands to establish the canonical primary worktree, source
mode, exact source location, prior disposition, Artifact ID, ticket digest, uniqueness, and
target branch. Reject aliases, linked worktrees, duplicate identities, symlinks, escapes,
submodules, conflicts, secret-shaped inputs, unsupported dispositions, or source drift.
A unique usable run is only an optional projection target; multiple usable owners gate.

Do not edit or stage the target ticket, dependencies, acceptance criteria, or links. The
repository transaction owns every source, Git, provider, terminal, and projection effect.

**Completion criterion:** all non-authority inputs have exact read-only evidence, and no
repository content or external object changed during resolution.

## Execute one repository transaction

Invoke the public runner command once with the normalized values:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  status-change-transaction "$TICKET_SOURCE" \
  --repo "$REPOSITORY_IDENTITY" \
  --ticket-id "$TICKET_ID" \
  --artifact-id "$ARTIFACT_ID" \
  --ticket-digest "$TICKET_DIGEST" \
  --from-disposition "$FROM_DISPOSITION" \
  --to-disposition "$TO_DISPOSITION" \
  --source-mode "$SOURCE_MODE" \
  --actor "$ACTOR" \
  --reason "$REASON" \
  --authority-ref "$AUTHORITY_REF" \
  --base "$TERMINAL_BRANCH"
```

For reopen only, append `--reopen-gate-id "$REOPEN_GATE_ID"`. Do not invoke
`execute-ticket`, synthesize quality stages, replay an uncertain dispatch, or perform a
second command to bypass a gate. A tracked request may consume only an already-configured
separate exact-head merge grant. An ignored request must terminate without Git or provider
publication.

**Completion criterion:** the command returns one exact terminal result or named gate; an
exact completed-success replay returns `already-applied`, while a gated replay returns the
same named gate, always without a second effect.

## Report separated axes

Render the command response without collapsing fields:

```text
result: changed-integrated | external-unpublished | already-applied | gated | rejected
transaction_id: <exact id or absent before intent>
transaction_phase: <durable phase>
disposition: <prior -> target, actor, reason, authority_ref, reopen gate>
execution_lifecycle: <separate run attempt axis>
readiness: <derived dependency axis>
stop_reason: <separate attempt reason>
source_mode: tracked | ignored
provider_state: <separate observation>
merge_authority: <separate grant state>
terminal_proof: <separate exact-head proof state>
run_projection: <run id and projection state, or not-applicable>
gate: <exact named gate or none>
non_authorities: <literal list>
```

Use `changed-integrated` only when tracked provider/head, separate merge decision, fresh
terminal reachability, terminal source readback, and projection agree.
Use `external-unpublished` only for ignored source readback; it implies neither publication
nor completion. Preserve provider ambiguity, missing merge authority, and terminal-proof
failures as gates. Never describe administrative supersession as approval.

Post-integration local Pi synchronization is a separate actor/evidence-bound operation, and
an active session still requires `/reload` afterward.

**Completion criterion:** every axis above is present, exact gates and limitations are
literal, and no result claims an authority or effect absent from the transaction receipt.
