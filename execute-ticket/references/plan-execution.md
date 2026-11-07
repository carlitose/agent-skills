# Requirements-and-plan intake

Owns: the lightweight skills-only input and handoff for the existing `execute-ticket`
quality loop. This is not a fourth delivery lane, a ticket format or a scheduler.

## Choose the input

Use this intake when the requirements are sufficient, acceptance is observable and there
is one cohesive deliverable. Size alone is not a reason to manufacture documents: use
clarity and delivery boundaries, not a file or line threshold. Direct-lane rules stay as
published; this intake still runs the full quality loop.

Reuse the user's request, `TASK.md`, or a sufficient existing spec. Keep one plan in the
session context or an existing document; do not rewrite the requirements into another spec
or ticket merely to enter execution. Ask only for genuinely missing behavior/authority.

Use the canonical intake instead for an explicit or existing ticket, independently
handed-off deliveries, Autopilot, or a required full Verification Record. A malformed or blocked ticket
cannot be downgraded into a plan to bypass its validator, dependency or gate. For material
design questions use `grilling -> to-spec`; after decisions are settled a single cohesive
deliverable may return here without creating a ticket. User-requested specs/tickets remain requests.

Completion criterion: the chosen intake matches the requested deliverable and has no
unresolved implementation-start decision. No new spec, ticket, CandidateRef or Verification Record
is required for an eligible plan.

## Carry only what execution needs

The caller supplies, by reference rather than duplicated prose:
- source requirements and observable acceptance criteria, including explicit compatibility;
- repository/checkout, baseline, allowed paths and unrelated changes to preserve;
- one plan of implementation steps and causal checks, plus applicable repository checks;
- authority, open gates, budget, time and maximum attempts from the user/project; unspecified
  limits are none set, not permission for external actions or spending.

Record the observed base/head and the changed-file manifest with SHA-256 content hashes,
including untracked new files, deleted paths and relevant modes. Bind the source requirements
and plan to this standalone scope identity; never manufacture a ticket digest or CandidateRef.
For a non-Git source use the actual before/after file snapshots, not invented commit IDs.
Freeze this identity before review/QA. On changes to requirements, scope or candidate,
invalidate affected review/QA conclusions and return to the relevant quality-loop stage.
Retain failed/superseded checks under their original identities; do not relabel them as fresh.
For the same source, scope and candidate, reuse the plan and evidence; do not regenerate
paperwork or repeat a full suite merely to move between stages.

Completion criterion: execution can identify the requested behavior, authorized scope,
current content and every outstanding gate without a parallel ticket/verification schema.

## Execute and hand off

Run the single [Quality loop](../SKILL.md#quality-loop). Use standalone intake/output for
review and QA, with the source criteria and frozen scope identity. A check must be observed
before it is reported as passed; failed, skipped and not-run checks remain visible.

Return one short note: request/plan references, standalone scope identity, changed paths,
acceptance status, checks and outcomes, review findings/isolation, consumption and unknowns,
and open gates. The ceiling is implementation-complete, never a release, live, production or security claim.
This intake grants no delegation, runner, Git/provider delivery, installation or reload authority.
Separately authorized delivery follows the [same caller-owned boundary](skills-only.md#separately-authorized-delivery).

When a full Verification Record becomes required, promote through `to-spec` and `to-tickets`
and their existing canonical owners before audit. Reuse sufficient source material; preserve
original evidence identities and have the audit classify coverage instead of relabeling old
checks. Promotion is not permission to start Autopilot. Missing authorization gates only its
operation; it does not erase completed local work.

Completion criterion: every planned outcome is accounted for in the note, claims fit the
observed evidence, and any required canonical promotion is completed or explicitly gated.
