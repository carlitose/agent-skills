# Frozen workflow skill snapshot for the modified comparison

Source: installed local agent skills; no runner or scheduler. These are skill instructions for coding quality, not task solutions or authority to access host files. Use only sandbox_exec for task files; all stages stay inline.


### to-spec/SKILL.md

---
name: "to-spec"
description: "Create or update a focused feature, decision, diagnostic, architecture, or bug-analysis spec; backward compatibility is opt-in."
---

# To Spec

Owns: specification framing, decisions, constraints, and implementation intent. It does
not serialize tickets, schedule work, implement code, or decide verification claims.

## Defaults

Unless the user or destination explicitly requires compatibility, specify the clean target
state. Do not add legacy aliases, parallel formats, shims, or migration work by inference.
Still identify destructive data changes, breaking external contracts, and irreversible
operations.

Save under `docs/specs/<slug>.md` unless the user provides a path. Update an existing
matching spec rather than creating a duplicate.

Every saved spec includes one `## Artifact Graph` section with a stable Artifact ID,
`Role: spec`, and exactly `Standalone: true` or one `Parent`. For an owned spec, update
the owner's reciprocal `Children` or `Produces` link in the same change.

## Process

1. Choose the smallest fitting type:
   - feature: desired behavior and product boundaries;
   - decision: options, decision, trade-offs, and consequences;
   - diagnostic: evidence, hypotheses, root cause, and fix direction;
   - architecture: components, contracts, state, and rollout;
   - bug analysis: observed/expected behavior, reproduction, cause, and acceptance.
2. Reconstruct known context from user decisions, code, current docs, prior specs, tickets,
   and evidence. Fetch current primary documentation when an external library/API/CLI/cloud
   contract matters.
3. Separate fact, decision, assumption, and unresolved question. Ask only for a missing
   decision that materially changes the target.
4. Write concise sections appropriate to the type. Include goals, non-goals, current and
   target behavior, semantic invariants, external contracts, failure modes, security/data
   concerns, alternatives, implementation slices, and verification strategy when relevant.
5. Use project domain language consistently and link evidence rather than copying large
   source blocks.

## Quality checks

- Acceptance outcomes are observable.
- Every material external behavior is preserved or explicitly changed.
- Unknowns and human decisions are visible.
- The implementation plan is ordered but not tied to brittle line numbers.
- Tests distinguish unit, integration, system, live, and manual needs without claiming
  they ran.
- Compatibility and migration obligations are explicit rather than assumed.

## Handoff

If executable tickets are requested, pass the spec path and slice defaults to
`to-tickets`. Do not emit YAML/front matter yourself.

Report the spec path, type, key decisions, unresolved questions, and recommended next
step.


### to-tickets/SKILL.md

---
name: "to-tickets"
description: "Break a spec into independently-grabbable tracer-bullet tickets and emit each versioned Ticket Envelope through the canonical ticket contract."
---

# To Tickets

Owns: Ticket Envelope production and executable tracer-bullet slicing. It does not
schedule, implement, audit, or preserve a separate Markdown schema.

Use [Ticket Envelope v1](../ticket-autopilot/references/ticket-envelope-v1.md) and
`"$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" ticket-emit` from the absolute ticket-autopilot
skill root resolved from the catalog, never repository cwd. Never hand-serialize front matter;
legacy input requires the explicit `migrate` command.

For explicit skills-only or runner-suspended work, use the same contract's pure serializer
and parser, not the runner CLI: follow the [skills-only contract](../execute-ticket/references/skills-only.md).
This is no alternate schema or hand-serialization. Preserve atomic writes and exact readback validation.

## Process

1. Locate and read the spec. Inspect the codebase only enough to understand ownership,
   conventions, tests, and vertical behavior boundaries.
2. Split work into thin end-to-end slices. Each ticket must be independently verifiable;
   avoid horizontal schema/API/UI/test-only batches.
3. Classify each slice as `AFK` or `HITL`. Make dependencies explicit and acyclic. Prefer
   AFK, but do not hide real decisions, credentials, or environment gates.
4. Present ticket title, mode, blockers, frontier state, and covered spec sections. In an
   explicitly autonomous request, record reasonable assumptions and continue.
5. Create `docs/tickets/<spec-slug>/<NN>-<ticket-slug>.md` in deterministic dependency
   order.

Every body includes one `## Artifact Graph` section with a stable Artifact ID,
`Role: ticket`, and one `Parent` link. Tickets are never standalone. Update the owning
spec or map with the reciprocal `Children` link in the same change. A research ticket
lists each durable output in `Produces`; every output points back to that ticket.

For each ticket, prepare an envelope JSON:

```json
{
  "ticket_schema": 1,
  "ticket_id": "NN",
  "execution_mode": "AFK",
  "blocked_by": []
}
```

Prepare a Markdown body:

```markdown
# <Ticket title>

## Artifact Graph
- Artifact ID: `artifact:<stable-id>`
- Role: `ticket`
- Parent: [<spec-filename>](../../specs/<spec-filename>)

## Parent Spec
[<spec-filename>](../../specs/<spec-filename>)

## What to Build
Narrow end-to-end behavior and the source spec sections.

## Acceptance Criteria
- [ ] Observable criterion.

## Frontier
Ready, dependency-blocked, or exact human decision required.

## Step-by-Step Implementation Plan
1. Change, reason, affected contract/module, and checkpoint.

## Testing Plan
Automated and manual checks, including unavailable boundaries.

## Out of Scope
- Explicit exclusion.
```

In the Autopilot lane, emit atomically through the CLI (skills-only uses the pure
serializer and atomic persistence described above):

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  ticket-emit <envelope.json> <body.md> --output <ticket.md>
```

Read the emitted ticket back with the canonical parser (`ticket-parse` in the Autopilot lane,
`parse_ticket_markdown` in skills-only) and verify exact normalized envelope, body, unique
ID, dependency links, and reciprocal graph edge.

In skills-only, stop at the validated batch handoff; never invoke `finalize_batch.py` or
start wiki/provider work implicitly. Report wiki synchronization as deferred unless separately
requested and authorized through `llm-wiki`; require evidence for success/no-op. Ticket validation is unchanged.

In the Autopilot lane, after every ticket in the batch has been emitted and those checks
pass, invoke the owned post-batch boundary exactly once, never once per ticket:

```bash
python3 -B "$TO_TICKETS_ROOT/scripts/finalize_batch.py" \
  <project-root> <ticket-folder> <ticket-path>...
```

`$TO_TICKETS_ROOT` is the absolute skill root from the catalog. Pass configured wikis as
`--wiki-root <path>`; otherwise use `wiki-sync-v1` bounded discovery. Preserve the complete
`ticket-batch-finalize-v1` report: absent wiki is a successful no-op; failures never hide emitted tickets.
Keep a returned tracked-wiki candidate separate and docs-only; never add wiki files to the
ticket-source candidate. `wayfinder` does not own or call this hook.

## Report

Return the ticket folder, paths, ready frontier, blocked tickets, any HITL decisions, and the
normalized `wiki_sync` result from the post-batch report, or the explicit deferred wiki
synchronization state for skills-only.


### execute-ticket/SKILL.md

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

For explicit skills-only or runner-suspended work, load the
[skills-only contract](references/skills-only.md). The caller may supply canonical inputs
without a runner; this skill's quality loop and no-delivery boundary remain unchanged.

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
default and requires no AgentTool. Before selecting distinct workers, apply the
[operating defaults](../ask-skills/OPERATING-DEFAULTS.md); record the user-requested scope
and observed isolation.

## Quality loop

1. Inspect only the code, tests, specs, and current documentation needed to establish the
   semantic baseline. For library, SDK, CLI, API, or cloud behavior, fetch current primary
   documentation as required by the repository.
2. Translate acceptance criteria into observable tests and invariants. When code behavior
   changes, use the requested test-first flow: reproduce RED, implement GREEN, then
   refactor without changing semantics.
3. Implement only ticket scope. Preserve unrelated user changes and do not add
   compatibility shims unless compatibility is explicit.
4. Before executing checks, apply [verification admission and cumulative cost](references/verification-cost.md): validate the delivered packaging/artifact graph, select causal and mandatory checks, and retain all prior attempts and remaining budget. Do not automatically repeat a complete suite because the candidate changed. Run the admitted targeted checks. Pass leaves manifests and content-addressed references instead of
   pasted artifacts, enforce each leaf's declared normalized-byte intake and output caps,
   and continue a `budget-exhausted` partial result without dropping remaining scope.
   Invoke focused cleanup through `code-simplification` only after GREEN; rerun affected
   checks after any edit.
5. Freeze the candidate diff and CandidateRef. Invoke read-only `code-review`; describe it
   as independent only when separate-context isolation was observed. Never edit during it.
6. On blocker findings, mutate the candidate, invalidate prior review/QA/audit evidence,
   and retry from the relevant stage. Stop at the configured retry limit.
7. Invoke QA-plan construction through `qa-test-plan`. Recheck verification admission after
   drift; preserve old evidence under its original identity rather than relabel it. Execute
   only feasible authorized checks, and classify observations truthfully; simulated evidence
   never becomes live.
8. Give the caller-provided normalized ticket ID, Ticket Envelope artifact reference, full
   frozen CandidateRef, review result, QA plan/results, gates, provider records, and
   requested operation to `verification-audit`. It alone emits the canonical Verification
   Record and claim ceiling.

## Handoff

Return a structured result containing:

- ticket ID, Ticket Envelope artifact reference, and CandidateRef;
- changed paths and acceptance-criterion status;
- commands run, observed outcomes, all retained attempts/shards, cumulative consumption,
  unknown costs, remaining budget, and the reason for any full-suite repeat;
- review findings and retry count;
- QA plan plus executed evidence references;
- each leaf's normalized execution mode, isolation, parallel flag, and authority reference;
- validated Verification Record or exact validation errors;
- unresolved human, credential, provider, or live-environment gates.

Do not claim `done`, `PR-open`, `integrated`, or production readiness from this handoff.
The canonical verification reduction limits claims. Delivery states require the scheduler's
receipts in the Autopilot lane, or separately authorized caller delivery and provider readback
in skills-only; neither can be inferred from implementation completion.


### execute-ticket/references/skills-only.md


Use this lane when the user explicitly requests skills-only, inline execution without the
runner, or suspension of Autopilot. It is a supported delivery lane, not break-glass and not
permission to skip quality or authority checks. `AFK` describes ticket execution mode; it
does not require a scheduler or authorize delegation.

The caller keeps the lane and the user's restrictions in its durable plan/handoff. Continue,
resume, and compaction preserve them. Switching back to Autopilot requires the user to lift
the suspension; a failed check or inconvenient contract is not such permission. No settings
file, new driver, scheduler invocation, or synthetic run ledger is needed.

## Canonical inputs without a runner

1. Validate or create the spec and ticket through `to-spec` and `to-tickets`. Reuse valid
   existing artifacts. `ticket-autopilot/scripts/autopilot/ticket_contract.py` remains the
   only parser/serializer: call its pure `parse_ticket_markdown`,
   `normalize_ticket_envelope`, `serialize_ticket_markdown`, and `ticket_source_digest`
   functions directly from the installed package. The package root comes from the catalog,
   not the repository cwd. Do not import its CLI or kernel or clone its schema. Missing
   validators block the corresponding stage, not justify an improvised parser.
2. Record the repository identity, checkout, allowed paths, target branch, freshly observed
   remote target SHA, and implementation base SHA. Confirm the checkout/index actually
   belongs to that candidate and its base is the intended current target. Work in an
   isolated checkout when unrelated changes prevent a trustworthy full candidate tree.
   Target advance, path ambiguity, or unexplained index/base drift stops admission; inspect
   and reconcile before review or QA. Do not move another checkout's branch to make it fit.
3. Preserve the normalized envelope/body with a path and SHA-256 reference. Construct the
   existing CandidateRef v2 using `autopilot.candidate_contract.semantic_candidate`:
   `contract_version`, `base_tree_oid`, `candidate_tree_oid`, and `ticket_digest`. Derive
   both trees from Git objects and the ticket digest from `ticket_source_digest`; invented
   IDs or prose descriptions are not substitutes. Retain the separate source/target facts
   because CandidateRef intentionally contains no checkout or provider identity.
4. Check every dependency and implementation-start gate from durable evidence. Supply the
   retry limit, prior attempts, remaining budget, and unresolved gates. Moving from a run
   does not reset consumption, replace failed attempts, or mark its ledger complete.
   For a stale resource binding, apply the [mandate/binding/store distinction](../../ticket-autopilot/references/technical-gates.md#mandate-technical-binding-and-operator-store): renew only within the original valid scope and remaining budget, without duplicate consent or a synthetic run.

Completion criterion: all required `execute-ticket` inputs are current, attributable, and
validated by their canonical owners, with each dependency/gate accounted for. No runner
CandidateRef issuer, run ID, ledger, or schema-3 leaf checkpoint is required in this lane.

## Inline quality and handoff

Invoke `execute-ticket` once for the normalized ticket; it composes its existing stages
serially. Use standalone intake/output for review and QA, and the standalone
`verification-audit` bundle. Keep the full CandidateRef on stage evidence. Do not synthesize
runner receipts or claim independent review from shared context. Requested but unavailable
independence remains an explicit limitation/gate.

Freeze the exact candidate before review/QA. Any drift invalidates current-candidate claims;
retain old evidence with its original identity and assess affected checks rather than
relabel it. Record commands, outcomes, skipped checks, failures, and cumulative consumption.
A user prohibition on executing tests remains a visible verification gap, not a PASS.

The existing verification validator/reducer owns the bundle and claim ceiling in either
lane. Its standalone commands (including validation against `--current-candidate`) are
contract checks, not a runner or scheduler. Do not create a second reducer in prose/code.

Completion criterion: the handoff contains the validated bundle or exact validation errors,
acceptance status, evidence references, limitations, and all open gates. Implementation
handoff alone does not mean `done`, PR-open, integrated, or production-ready.

## Separately authorized delivery

The calling agent, not `execute-ticket`, may perform ordinary Git/provider operations only
within existing explicit authority. Before each mutation, recheck the checkout, actual
diff/tree, remote target and exact PR head, verification disposition, unresolved gates,
provider policy and required CI. Render/validate the PR through `explain-pr`. Permission to
work inline grants no push, publication, merge, cleanup, installation, or reload authority.

Preserve the candidate if any check or authority is missing. Reconcile target/candidate drift
before proceeding; do not force push, waive CI, or manufacture authorization. Record provider
readback of the exact delivered head and merged result. A local commit or successful merge
command alone is not integration evidence. Keep runner-owned tickets/receipts untouched;
report any pending runner reconciliation separately rather than forge its state.

Completion criterion: each claimed Git/provider state has fresh readback and supporting
current evidence and authority. An open delivery gate is a valid stop.

## Direct local Pi synchronization

After proven integration, an explicit, actor/evidence-bound local-sync mandate may authorize
synchronizing the exact integrated head without `sync-local-pi` or a run ledger. Read the
existing local configuration and package installation first. If scope or ownership is
ambiguous, stop; do not reset settings, replace unrelated packages, or discard dirty files.

Update only the authorized persistent checkout/package and owned skill copies/links. Use
the existing package-source spelling/filtering and preserve external resources. Verify the
checkout HEAD/tree against the integrated commit, the resolved installed package source,
package name/version, and digests of the installed extension and changed skills against
that commit. Retain the commands and readbacks with any failure as a local-sync gate.

Completion criterion: those identities and contents match, settings/unrelated resources are
preserved, and the report says `/reload` is required unless a separately user-authorized
runtime reload has actually completed. If the user explicitly requests an available reload
tool, use it only after these checks and report its observed result or failure. Installing
files alone never proves that the active session loaded them. Do not update the Pi binary
or infer reload authority from permission to synchronize the package.


### code-review/SKILL.md

---
name: "code-review"
description: "Review a runner candidate or standalone PR, commit, local diff, or requested scope read-only for regressions, evidence gaps, and overclaims."
---

# Code Review

Owns: read-only review findings for one frozen scope. It never edits files, runs a quality
loop, produces a Verification Record, decides the final claim ceiling, or mutates
Git/provider state.

Use the semantic vocabulary and required fields from the canonical
[Verification Record](../verification-audit/references/verification-record.md). Flag
missing or contradictory inputs; do not reconstruct a second evidence/gate policy.

## Inputs

Accept one acquisition route:

- **Runner handoff:** frozen diff, CandidateRef, normalized Ticket Envelope, acceptance
  criteria, decisions, baseline, observed evidence, and draft record when one exists.
- **Standalone acquisition:** acquire a PR, commit, local diff, or user-requested scope
  read-only; record its observed head/commit/worktree identity, request constraints,
  relevant repository rules, and available baseline/evidence.

Do not parse Markdown to infer a Ticket Envelope. If standalone context has no normalized
ticket, review against the explicit request and repository contract. If the diff changes,
return `stale-candidate` and stop.

## Volatile intake bound

- `max_volatile_bytes`: `107656` normalized UTF-8 bytes per invocation. This is the
  observed 96,393-byte candidate-diff high-water mark plus maxima of 2,380 bytes for the
  ticket body, 4,459 for the implementation handoff, and 4,424 for simplification. The
  corpus is the run's TK-01/TK-02/TK-05/TK-07/TK-08 normalized
  `git diff --no-ext-diff --no-color` observations, its nine ticket bodies, and compact
  leaf results.
- `max_single_output_bytes`: `32596`, the observed TK-02 executable-code candidate diff.

Count every diff, raw file slice, pasted handoff, evidence body, and tool result after CRLF
or lone-CR normalization to LF. Acquire the expected manifest first; truncate command
output before it enters context and continue larger diffs by file or hunk. Prefer path plus
SHA-256 references over pasted artifacts, loading referenced content only when a review
axis requires it. If the next required read would exceed a cap, return a schema-3 partial
result with exact inspected/remaining scope and `budget-exhausted`; do not skip scope or
downgrade a finding to fit the bound.

## Bounded runner handoff

When the runner supplies a schema-3 bounded `LeafContext`, treat its
CandidateRef, canonical phase contract, expected file manifest, prior
inspection, remaining scope, and resource limits as the authoritative
continuation boundary. Do not rediscover already-inspected immutable scope for
the same CandidateRef.

End every runner-owned review turn with one schema-3 result, including timeout,
interruption, or resource exhaustion. Persist the exact CandidateRef and review
phase contract, ordered expected/inspected/remaining files, commands, findings,
current phase, canonical remaining-phase suffix, and a non-empty stop reason
for partial results.

Include normalized schema-3 `execution` from the observed route. A shared-context or
unknown isolation is not independent; report that limitation instead of upgrading it.

A complete review must reach `handoff-ready`, inspect the declared scope, and
return a validated structured finding list. A partial result is usable
continuation state but never a pass. A real finding may return the pipeline to
implementation and consume a quality failure; timeout, interruption, and
resource exhaustion do not. CandidateRef drift invalidates the handoff.

## Review axes

Review each axis separately and report only evidence-backed findings:

1. **Standards and maintainability** — project conventions, clarity, accidental
   complexity, unsafe error handling, security, data integrity, and unrelated scope.
2. **Ticket acceptance** — every criterion has a concrete implementation path and
   observable check; non-goals remain untouched.
3. **Semantic regression** — externally meaningful behavior is preserved or explicitly
   authorized. Compare changed boundaries and invariants to the supplied baseline.
4. **Causal coverage** — tests/evidence exercise the changed mechanism, not merely an
   adjacent success path. Identify mocked or simulated boundaries explicitly.
5. **Claim safety** — wording does not exceed the evidence and open gates represented in
   the canonical record.

Inspect raw files and diffs rather than trusting summaries. Do not call
`verification-audit`; the caller supplies findings to its single audit pass.

## Finding format

Sort by severity:

```text
[blocker|should-fix|nit] path:line - problem and impact. Suggested fix.
```

- `blocker`: correctness, security, data loss, ticket failure, missing causal coverage, or
  a material unsupported claim.
- `should-fix`: meaningful maintainability or non-critical coverage problem.
- `nit`: optional polish only.

For every finding, name the violated acceptance criterion, invariant, boundary item, or
repository rule when available. If no finding exists, say so and list residual evidence
limits. A standalone output is a read-only draft; it cannot claim ticket completion or release.
Never report PASS for a CandidateRef or standalone scope you did not inspect.


### qa-test-plan/SKILL.md

---
name: "qa-test-plan"
description: "Plan causal QA for a runner candidate or standalone PR, commit, local diff, or requested scope without executing or deciding release."
---

# QA Test Plan

Owns: QA plan construction. It does not execute tests, change code, resolve gates, decide
completion/release status, or produce a Verification Record.

Use the taxonomy and identifiers from the canonical
[Verification Record](../verification-audit/references/verification-record.md). The
caller records observations and `verification-audit` performs the sole semantic
reduction.

## Inputs

Accept one acquisition route:

- **Runner handoff:** normalized Ticket Envelope, acceptance criteria, frozen diff,
  CandidateRef, supplied invariants/boundaries, environments, gates, and observed checks.
- **Standalone acquisition:** acquire a PR, commit, local diff, or user-requested scope
  read-only; record the observed identity, requested behavior, repository rules, available
  environments, limitations, and checks.

Do not parse Markdown to manufacture a Ticket Envelope. Mark unknown inputs as draft
limits or gates; never assume access or successful execution.

## Volatile intake bound

- `max_volatile_bytes`: `103998` normalized UTF-8 bytes per invocation. This is the
  observed 96,393-byte candidate-diff high-water mark plus the 2,380-byte ticket-body and
  5,225-byte review-handoff maxima. The corpus is the run's TK-01/TK-02/TK-05/TK-07/TK-08
  normalized `git diff --no-ext-diff --no-color` observations, its nine ticket bodies, and
  compact leaf results.
- `max_single_output_bytes`: `32596`, the observed TK-02 executable-code candidate diff.

Count every diff, raw file slice, pasted handoff, evidence body, and tool result after CRLF
or lone-CR normalization to LF. Start from the changed-file manifest; truncate command
output before it enters context and slice larger material by file or hunk. Prefer path plus
SHA-256 references over pasted artifacts and load content only for a causal gap the plan
must cover. If the next required read would exceed a cap, return a schema-3 partial plan
with exact inspected/remaining scope and `budget-exhausted`. Never remove a causal case,
evidence classification, invariant, boundary, or gate merely to stay within the bound.

## Build the plan

First apply [verification admission and cumulative cost](../execute-ticket/references/verification-cost.md).
Require current identity and delivered packaging/artifact-graph results before admitting
expensive execution. Inventory all prior attempts, including failed or superseded shards;
keep original evidence identities and unknown costs. Select causal checks without waiving
mandatory profiles or exact-head CI. A repeated full suite needs a specific reason and
remaining budget, not just a new CandidateRef.

For each changed behavior:

1. State the causal chain from injection point to user/external observation.
2. Select the smallest test that crosses the changed mechanism.
3. Classify the intended observation as static, unit, integration, simulated, or live
   using the canonical reference.
4. Name exact setup, action, expected result, cleanup, and evidence to capture.
5. Map the case to ticket criteria, invariants, boundary items, and gate IDs.
6. Add negative/error paths, retries, ordering/idempotency checks, and regression coverage
   where relevant.

Do not label a mocked provider or fake browser as live. If a required environment,
credential, approval, or device is unavailable, write a specific open gate and an
authorized simulation plan; do not silently lower the requirement.

## Output

For a runner handoff, return the caller's schema-3 `qa-plan` leaf result. Bind
it to the exact CandidateRef and canonical phase contract. Its schema-1
`quality` payload names causal scope, content-addressed planned-evidence
references, and limitations; a timeout or interruption returns `complete:
false`, the last durable phase, and exact remaining phases. Do not discard a
partial plan or mark it passing.
Include normalized schema-3 `execution` with observed isolation; never infer delegation,
separate context, parallelism, or authority from the requested plan.

For standalone acquisition, return:

```markdown
# QA Plan

## Candidate
- CandidateRef:

## Admission and Cost
- Current identity, delivered packaging/artifact-graph results and evidence references.
- Prior attempts/shards with original identities, outcomes, durations and artifact hashes.
- Summed invocation time versus measured end-to-end elapsed time; unknowns and lower bounds.
- Selected/omitted checks with causal or mandatory-policy reason, full-repeat justification,
  estimated next cost, remaining authorized budget and unresolved execution state.

## Automated Checks
- ID, command, layer, causal path, expected evidence.

## Manual / Environment Checks
- ID, setup, action, expected observation, evidence class, cleanup.

## Negative and Regression Paths
- ID, failure or preserved behavior, expected observation.

## Mapping
- QA ID -> acceptance criterion / invariant / boundary item / gate.

## Open Gates and Limits
- Gate ID, owner, unblock condition, and claim impact.
```

Planning a check is not evidence that it ran. Keep planned, executed, passed, failed,
skipped, and blocked states distinct. A standalone draft cannot claim ticket completion or release.


### code-simplification/SKILL.md

---
name: "code-simplification"
description: "Simplify the current candidate diff for clarity while preserving behavior, scope, tests, errors, side effects, and project conventions."
---

# Code Simplification

Owns: focused simplification of recently changed code. It does not select tickets, expand
scope, review acceptance, produce QA/audit artifacts, commit, push, open PRs, or finalize
workflow state.

## Inputs

Require the changed diff, allowed paths, semantic invariants, project conventions, and
checks that currently pass. If the candidate is not GREEN, return without editing.

## Volatile intake bound

- `max_volatile_bytes`: `103232` normalized UTF-8 bytes per invocation. This is the
  observed 96,393-byte candidate-diff high-water mark plus the 2,380-byte ticket-body and
  4,459-byte implementation-handoff maxima. The corpus is the run's TK-01/TK-02/TK-05/
  TK-07/TK-08 normalized `git diff --no-ext-diff --no-color` observations, its nine ticket
  bodies, and compact leaf results.
- `max_single_output_bytes`: `32596`, the observed TK-02 executable-code candidate diff.

Count every diff, file slice, pasted handoff, evidence body, and tool result after CRLF or
lone-CR normalization to LF. Read the manifest first; truncate command output before it
enters context and slice larger diffs by file or hunk. Prefer path plus SHA-256 references over
pasted artifacts, and count an artifact only when its content is required. If the next
required read would exceed either cap, stop before reading or editing and return the exact
remaining references with `budget-exhausted`; a later invocation may continue. The bound
never permits omitting preservation duties or claiming equivalence without evidence.

## Contract

Preserve:

- externally observable behavior and public contracts;
- errors, validation order, side effects, retries, and persistence semantics;
- security and data-integrity boundaries;
- ticket scope and unrelated user changes;
- tests and project conventions.

## Process

1. Read the changed code in context and identify concrete duplication, unnecessary
   indirection, confusing names, or locally avoidable branching.
2. Prefer the smallest edit that makes intent obvious. Do not introduce speculative
   abstractions, broad formatting churn, compatibility shims, or architectural rewrites.
3. After each coherent edit, run the narrowest relevant checks. Revert the simplification
   if behavior cannot be shown equivalent.
4. Return changed paths, simplifications made, checks observed, and residual limits.

Never claim equivalence or passing checks without observed evidence. Any edit creates a
new CandidateRef and invalidates prior review/QA/audit evidence owned by the caller.
