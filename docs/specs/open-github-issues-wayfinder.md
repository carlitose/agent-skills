# Open GitHub Issues Remediation

## Type

Wayfinding spec

## Status

Active

## Artifact Graph

- Artifact ID: `artifact:open-github-issues-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [Canonical artifact graph decision](./artifact-graph-decision.md)

## Destination

Close GitHub issues [#25](https://github.com/carlitose/agent-skills/issues/25),
[#27](https://github.com/carlitose/agent-skills/issues/27),
[#29](https://github.com/carlitose/agent-skills/issues/29), and
[#30](https://github.com/carlitose/agent-skills/issues/30),
[#33](https://github.com/carlitose/agent-skills/issues/33), and
[#34](https://github.com/carlitose/agent-skills/issues/34) with a coherent local ticket
inventory, explicit lifecycle semantics, a conservative artifact-link audit, a verified
Wayfinder-to-Grilling handoff, a host-portable no-AgentTool autopilot path, and a selective
upstream-skills synchronization plan.

The destination is reached when each issue has observable acceptance criteria, a tested
implementation path, and enough evidence to close it without treating a passing local
test suite as proof of untested migration or provider behavior.

## Decisions So Far

- Treat "tickets" in issues #27, #29, and #30 as the canonical Markdown tickets under
  `docs/tickets/`, not GitHub issues. GitHub issues are the request surface; local Ticket
  Envelopes are the executable work surface.
- Build one read-only repository inventory first and reuse it for both open-ticket listing
  and orphan detection. Multiple filesystem scanners would drift on `done/`, ignored
  ticket sources, schema validation, and future lifecycle states.
- The OI-07 selection accepts every actionable parity slice U-01 through U-09 as a
  separately grabbable follow-up. `grilling`, `grill-me`, `grill-with-docs`, and
  `prototype` remain already covered and receive no duplicate implementation ticket.
  The delivered OI-08 routing and OI-09 AgentTool-optional contracts remain authoritative;
  narrowed U-04 only consumes shared codebase-design vocabulary, adds recent-change
  scoping, and gates the visual-report output decision while preserving local owners.
- Lifecycle semantics are accepted in
  [Ticket lifecycle and disposition decision](./ticket-lifecycle-disposition-decision.md).
  Administrative disposition (`open | on-hold | canceled | completed`), execution
  lifecycle, derived readiness, and stop reason are orthogonal. `pause` is temporary
  runtime suspension; `stopped` is an attempt outcome. Held and canceled tickets are not
  schedulable, their dependents are blocked without cancellation cascade, and only an
  audited user action may reopen them to pending work that must be revalidated.
- Prefer source-folder disposition over Ticket Envelope v2 for the first implementation:
  root-level `*.md` remains open, `done/*.md` remains completed, and new `hold/*.md` and
  `canceled/*.md` locations represent administrative disposition. Moving a source while a
  run owns an immutable snapshot must fail closed as source drift.
- Orphan detection is a linter, not a deleter. Broken declared links are errors;
  unreferenced specs or research artifacts are review candidates because accepted
  decisions and standalone research may intentionally have no child ticket.
- Artifact roots and relationships are accepted in the
  [Canonical artifact graph decision](./artifact-graph-decision.md). Every managed
  artifact has an explicit stable Artifact ID and closed Role plus either Standalone or
  one Parent. Parent links are reciprocal with Children or Produces; hierarchy is acyclic;
  legacy gaps warn, unreferenced Markdown is informational, and audit is non-destructive.
- Synchronize selectively with the official
  [`mattpocock/skills`](https://github.com/mattpocock/skills) repository. The inspected
  upstream baseline is commit
  [`84fdeffd12f2ee307994d1eb6feb48173b6e0502`](https://github.com/mattpocock/skills/commit/84fdeffd12f2ee307994d1eb6feb48173b6e0502),
  observed from `main` on 2026-08-08 with package version `1.2.3`. Preserve this
  repository's deterministic Ticket Envelope, runner, verification, and provider
  contracts rather than replacing them with upstream's issue-tracker-native workflow.
- Treat a clear Wayfinder destination and a materially ambiguous one differently. A clear
  destination may be mapped immediately; an ambiguous destination must hand off to the
  canonical `grilling` workflow and wait for the user's confirmation before durable map or
  ticket creation. Later HITL decisions remain independently claimable grilling tickets.
- Skill composition does not imply AgentTool use. `ticket-autopilot` and `execute-ticket`
  must support inline skill execution as the portable default. A host delegation primitive
  may be used only when the user explicitly requested delegation or the host's governing
  policy independently authorizes it; absence of AgentTool must not make the deterministic
  scheduler unusable.

## Issue Analysis

### #29 — Find open tickets

**Observed gap.** `ticket-autopilot plan` accepts one ticket folder and couples inventory
to provider capability negotiation. It cannot inventory the whole repository, and a
folder containing only `done/` tickets returns `no pending ticket files`. The current
CandidateRef's provider-free `ticket-list` reports five open tickets: `02` through `06`
under `bounded-ticket-autopilot-leaves`. Ticket `07` under
`ticket-autopilot-delivery-merge` is completed.

**Fix direction.** Add a provider-free inventory module and a read-only CLI surface such
as:

```text
ticket-autopilot ticket-list [root] [--state <state>] [--json]
```

It should discover ticket folders below `docs/tickets/`, reuse the canonical Ticket
Envelope parser, tolerate all-completed folders, return invalid files as diagnostics
instead of silently skipping them, and expose folder, ticket id, title, source path,
administrative disposition, execution mode, blockers, and derived readiness. Text output
is for humans; stable JSON is the contract used by later audits.

**Acceptance evidence.** Unit fixtures for mixed open/completed folders, all-completed
folders, malformed envelopes, duplicate ids, held/canceled tickets, and ignored sources;
one repository-level integration test whose JSON output identifies the same five current
open tickets.

### #30 — Find orphan tickets, specs, and research

**Observed gap.** Ticket parentage currently lives in Markdown links such as `## Parent
Spec`, while the Ticket Envelope contains only schema, id, execution mode, and blockers.
Specs have heterogeneous `Source`/`Sources` sections, and `docs/research/` does not yet
exist. A filename-only or folder-slug heuristic would therefore produce false positives.

**Accepted decision.** The focused
[Canonical artifact graph decision](./artifact-graph-decision.md) defines the visible
`## Artifact Graph` contract, stable identity, closed roles, explicit roots and single
parents, reciprocal Children/Produces ownership, research outputs, hierarchy cycles, and
diagnostic severities. Related links may cycle; ownership links may not. New and modified
artifacts are strict, while unmigrated legacy files warn and unreferenced Markdown remains
an informational candidate. No relationship is inferred from a slug.

**Implementation direction.** OI-06 may build a provider-free, read-only artifact graph on
the repository inventory and render separate errors, warnings, and unreferenced
information. The audit cannot move, delete, rename, rewrite, or auto-link artifacts.

**Acceptance evidence.** OI-06 fixtures must cover valid reciprocal chains, explicit
standalone roots, research Produces, broken canonical links, duplicate IDs, hierarchy
cycles, reciprocity mismatches, legacy warnings, informational candidates, slug
collisions, path escapes, and mutation guards.

### #27 — Stopped, blocked, on-hold, and canceled tickets

**Observed gap.** The runtime already models `gated`, `failed`, `waiting`, and `aborted`,
and derives dependency blocking. The source contract itself distinguishes only root
pending tickets from `done/` tickets. Adding one free-form `status` field would conflate
operator intent, scheduler state, and terminal outcome.

**Accepted decision.** The focused
[Ticket lifecycle and disposition decision](./ticket-lifecycle-disposition-decision.md)
defines the four-axis model and freezes the implementation constraints. `on-hold` and
`canceled` are durable, unschedulable dispositions; `pause` is temporary runtime
suspension; `stopped` is an attempt outcome. A held dependency blocks descendants. A
canceled dependency blocks descendants with `dependency-canceled`, without cascading
cancellation. Active disposition changes stop at the next atomic safe boundary and retain
checkpoints, worktrees, and evidence. Only an audited user action can reopen held or
canceled work to `open`/`pending`, followed by snapshot and evidence revalidation.

**Delivered implementation.** The preserved `OI-04` candidate was recovered and completed
by retry ticket `OI-12`, merged as commit `e74176d6f89ac0d1719870cf5d867153c1ebb7c1`.
The current source layout supports `hold/` and `canceled/`; the runner exposes audited,
atomic hold/cancel/reopen transitions while preserving source containment, crash recovery,
snapshot drift gates, and explicit schema migration. Follow-up commit `73753adb` hardened
the path-containment and source-mode boundaries without changing the accepted semantics.

**Acceptance evidence.** Contract, source-snapshot, scheduler, crash/resume, dependency,
mixed-era migration, and CLI coverage live in the ticket-autopilot test suite. `OI-04`
therefore records the already-integrated implementation instead of creating a second
competing lifecycle owner.

### #25 — Matt Pocock's new version

**Observed gap.** The pinned parity report accounts for every promoted upstream skill and
identifies nine actionable local slices: diagnostic redaction, shared codebase-design and
TDD alignment, bounded architecture-scoping improvements, writing guidance, temporary
handoffs, external questionnaires, safe conflict resolution, and a human-run wizard.
Tracker setup/triage and competing execution owners are rejected; Grilling aliases and
Prototype are already covered.

**Fix direction.** The user approved U-01 through U-09. Implement them through the
canonical [adoption ticket graph](../tickets/mattpocock-skills-adoption/) without wholesale
import. U-03 and U-04 depend on U-02. U-04 is intentionally narrower than the original
parity row: it must preserve the `improve-codebase-architecture` and `codebase-improver`
owners, consume shared design vocabulary, scope observations using recent changes, and
obtain a human decision before making a temporary visual report a stable output. It must
not duplicate the delivered OI-08 Wayfinder-to-Grilling routing or OI-09 AgentTool-optional
execution work.

**Acceptance evidence.** A durable comparison report names the upstream commit, every
promoted upstream skill, its local counterpart, the decision, and tests/docs affected.
Each adopted change lands as an independently reviewable ticket rather than one sync
commit.

### #33 — Verify Wayfinder's Grilling integration

**Observed gap.** The local Wayfinder names `grilling` as an investigation ticket type,
but its charting process does not explicitly invoke the `grilling` skill. Its only inline
interaction rule is to ask one concise question when the destination is ambiguous.
Consequently, a caller cannot tell whether destination discovery, breadth-first frontier
discovery, or a later HITL ticket owns the interview.

**Fix direction.** Define and test one routing contract:

- clear destination: chart the map without a ceremonial interview;
- ambiguous destination: invoke `grilling`, follow its one-question-at-a-time loop, and do
  not create durable artifacts until the user confirms shared understanding;
- known destination with unresolved product decisions: create canonical HITL grilling
  tickets and leave them on the frontier;
- maintenance of an existing map: never restart destination grilling unless the
  destination itself is being changed.

Update Wayfinder, Grilling aliases, and skill-graph/forward-test prompts together so the
handoff is observable and does not recurse from Grilling back into Wayfinder.

**Acceptance evidence.** Prompt-level tests cover clear, ambiguous, maintenance, and
HITL-ticket scenarios. The ambiguous case pauses for the user; the clear case emits a map;
neither executes destination work.

### #34 — Keep autopilot usable when AgentTool is forbidden

**Observed gap.** The issue reports a Claude Code system instruction forbidding AgentTool
unless the user requested it. The local `ticket-autopilot` says it delegates one attempt to
`execute-ticket`, and `execute-ticket` delegates review/QA/audit leaves, but neither
requires a particular host tool. Other skills explicitly require subagents, which makes
the word "delegate" ambiguous and risks an unauthorized AgentTool call.

**Fix direction.** Freeze a host-portable invocation contract:

- `invoke`/`compose` means load and execute the named skill inline unless explicit
  delegation authority exists;
- ticket-autopilot remains serialized and never requires AgentTool for correctness;
- genuinely independent review records the available isolation level and gates claims
  that require stronger independence;
- skills that truly require parallel subagents must state an inline/sequential fallback or
  an explicit human gate instead of silently violating host policy;
- add a static skill-graph check plus a Claude Code forward test showing the default
  autopilot path completes without AgentTool.

This is primarily a composition-contract change. Do not weaken CandidateRef, review,
verification, or merge-authorization invariants to avoid delegation.

**Acceptance evidence.** Local skill-graph tests prove the autopilot family has no
mandatory AgentTool dependency. A credential-free Claude Code scenario observes no
AgentTool call; any untestable live boundary remains an explicit gate rather than a pass.

## Not Yet Specified

- Whether the open-ticket command should scan only the conventional `docs/tickets/` root
  or accept multiple configured roots. Start with one explicit root and keep discovery
  deterministic.
- Which upstream additions beyond the recommended first tranche are wanted as product
  scope. The parity report should make that a small selection rather than an all-or-none
  upgrade.
- Whether a host can provide review-context isolation without AgentTool. Inline review is
  the portability baseline; stronger independence must be reported as an observed
  capability, not assumed.

## Out of Scope

- Implementing any fix during this Wayfinder pass.
- Automatically deleting, moving, or closing artifacts reported as orphaned.
- Replacing local Markdown tickets with GitHub issues or importing upstream's tracker
  model wholesale.
- Preserving an undocumented output shape for new CLI commands; JSON contracts must be
  versioned before use by other skills.
- Treating GitHub labels as the execution state of local Ticket Envelopes.
- Requiring AgentTool merely because a skill uses the words "delegate" or "independent".
- Changing Claude Code's system prompt or claiming live Claude behavior from local unit
  tests.

## Frontier / Blocking Edges

- **Repository inventory (#29)** — ready. It blocks reliable orphan scanning and provides
  the observable status surface needed by lifecycle work. Unblocked when provider-free
  discovery and versioned JSON output pass repository-level tests. Owning ticket: `OI-02`.
- **Lifecycle terminology (#27)** — accepted. The four-axis model, dependency
  consequences, active safe-boundary behavior, and user-only reopening contract are frozen
  in the linked decision spec. Owning ticket: `OI-03`.
- **Lifecycle implementation (#27)** — delivered by the recovered `OI-04` candidate through
  retry ticket `OI-12`, with later path/source-mode hardening in `WD-01`. The accepted
  four-axis model and the repository-inventory contract remain the owning boundaries.
- **Artifact root policy (#30)** — accepted. Stable IDs, closed roles, explicit roots or
  single parents, reciprocal ownership, migration severity, and non-destructive audit
  behavior are frozen in the linked decision. Owning ticket: `OI-05`.
- **Artifact graph audit (#30)** — no longer blocked by `OI-05`; it remains dependent on
  the inventory contract from `OI-02`. Owning ticket: `OI-06`.
- **Upstream parity research (#25)** — delivered. OI-01 pins commit
  `84fdeffd12f2ee307994d1eb6feb48173b6e0502`, package `1.2.3`, and the complete
  adopt/adapt/already-covered/reject classification in the parity report.
- **Selective upstream adoption (#25)** — selection complete. U-01 through U-09 are
  accepted and emitted as canonical follow-up tickets; U-03 and U-04 wait for U-02, while
  U-04 also retains its explicit visual-report HITL decision. Owning ticket: `OI-07` and
  the [adoption ticket graph](../tickets/mattpocock-skills-adoption/).
- **Wayfinder-to-Grilling routing (#33)** — delivered. OI-08 owns the destination gate,
  canonical Grilling handoff, maintenance behavior, and unresolved-decision envelope,
  with its four causal routing scenarios.
- **No-AgentTool autopilot contract (#34)** — merged through
  [OI-09 commit `de2f175`](https://github.com/carlitose/agent-skills/commit/de2f175bda4ea80b30a150c13559f6be98196b0f)
  in [PR #38](https://github.com/carlitose/agent-skills/pull/38). It establishes inline
  execution as the portable default, explicit delegation authority, and truthful isolation
  records.
- **Claude Code no-AgentTool forward test (#34)** — ready, HITL. OI-09's merged local
  contract unblocks OI-10, but only a user-controlled live host session can observe whether
  Claude Code invokes AgentTool. Local static or simulated evidence cannot satisfy this
  separate host gate.

## Ticket Plan

| ID | Type | Mode | Blockers | Title | Expected output |
| --- | --- | --- | --- | --- | --- |
| `OI-01` | research | AFK | none | Delivered parity research at `84fdeffd` / package `1.2.3` | Delivered: `docs/research/mattpocock-skills-parity.md` with the complete decision matrix |
| `OI-02` | task | AFK | none | Add repository-wide ticket inventory | Provider-free `ticket-list`, versioned JSON, fixtures, integration test |
| `OI-03` | grilling | HITL | none | Freeze ticket lifecycle terminology | Accepted [lifecycle decision](./ticket-lifecycle-disposition-decision.md) for disposition, execution, readiness, stop reasons, and dependency consequences |
| `OI-04` | task | AFK | `OI-02`, `OI-03` | Delivered hold/reopen/cancel lifecycle | Delivered through retry `OI-12`: atomic CLI transitions, source/snapshot/kernel integration, migration, and causal tests |
| `OI-05` | grilling | HITL | none | Define artifact roots and relationships | Accepted [artifact graph decision](./artifact-graph-decision.md) for IDs, roles, roots, relationships, severities, and audit safety |
| `OI-06` | task | AFK | `OI-02`, `OI-05` | Implement orphan and broken-link audit | Read-only artifact graph CLI, versioned JSON, migrations/lint, fixtures |
| `OI-07` | task | HITL | `OI-01` | Select upstream changes to adopt | Approved U-01..U-09 selection and canonical follow-up ticket graph |
| `OI-08` | task | AFK | none | Delivered Wayfinder-to-Grilling routing | Delivered: routing contract plus skill-graph and prompt-level regression tests |
| `OI-09` | task | AFK | none | Merged AgentTool-optional autopilot contract | Merged: inline-default contract, truthful isolation reporting, and static tests |
| `OI-10` | task | HITL | `OI-09` | Forward-test Claude Code without AgentTool | Separate live host observation, limitations, and closure recommendation for #34 |

### Accepted upstream-adoption follow-ups

| ID | Mode | Blockers | Owner and boundary | Ticket |
| --- | --- | --- | --- | --- |
| `U-01` | AFK | none | `diagnose`; redact evidence without replacing diagnostic ownership | [Redact diagnostic evidence](../tickets/mattpocock-skills-adoption/done/01-redact-diagnostic-evidence.md) |
| `U-02` | AFK | none | new shared `codebase-design`; vocabulary only | [Adopt codebase-design](../tickets/mattpocock-skills-adoption/done/02-adopt-codebase-design.md) |
| `U-03` | AFK | `U-02` | `tdd`; post-GREEN cleanup stays with existing quality owners | [Align TDD guidance](../tickets/mattpocock-skills-adoption/done/03-align-tdd-guidance.md) |
| `U-04` | HITL | `U-02` | `improve-codebase-architecture`; no OI-08/OI-09 duplication and no `codebase-improver` takeover | [Scope architecture improvement](../tickets/mattpocock-skills-adoption/done/04-scope-architecture-improvement.md) |
| `U-05` | AFK | none | new `writing-for-agents`, subordinate to scaffold ownership | [Adopt writing-for-agents](../tickets/mattpocock-skills-adoption/done/05-adopt-writing-for-agents.md) |
| `U-06` | AFK | none | new temporary handoff; no scheduler-state ownership | [Adopt session handoff](../tickets/mattpocock-skills-adoption/done/06-adopt-session-handoff.md) |
| `U-07` | AFK | none | new `to-questionnaire`; explicit destination, never auto-send | [Adopt to-questionnaire](../tickets/mattpocock-skills-adoption/done/07-adopt-to-questionnaire.md) |
| `U-08` | AFK | none | new conflict resolver; no implicit Git lineage authority | [Add safe conflict resolution](../tickets/mattpocock-skills-adoption/done/08-add-safe-conflict-resolution.md) |
| `U-09` | AFK | none | new human-run wizard; no unattended secret/provider mutation | [Add safe wizard](../tickets/mattpocock-skills-adoption/done/09-add-safe-wizard.md) |

## Next Review

For #25, start any of U-01, U-02, or U-05 through U-09. U-03 waits for U-02; U-04 waits
for U-02 and its visual-report decision. OI-08 and OI-09 remain separate delivered owners,
not prerequisites to repeat inside U-04. OI-06 is no longer blocked by the accepted OI-05
decision and can proceed on the integrated OI-02 inventory contract. OI-10 remains a
separate live, user-controlled HITL gate.
