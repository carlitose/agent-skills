# Matt Pocock skills parity

## Answer

Do not merge the upstream tree wholesale. At the inspected revision, all 25 promoted
upstream skills have been accounted for: 12 are already covered by local skills, four
should be adopted as new local skills, five should be adapted behind local ownership and
safety boundaries, and four should be rejected with a specific reason.

The highest-value changes are small and separable: add secret-redaction rules to
`diagnose`; align `tdd` with the current seam and tautological-test guidance; introduce the
shared `codebase-design` vocabulary; and remove the hard-coded AgentTool language from
`improve-codebase-architecture`. The local Ticket Envelope, scheduler, verification, and
delivery stack should remain authoritative.

## Inspected baselines

- **Upstream:** [`mattpocock/skills@84fdeffd12f2ee307994d1eb6feb48173b6e0502`](https://github.com/mattpocock/skills/commit/84fdeffd12f2ee307994d1eb6feb48173b6e0502),
  committed 2026-08-06 20:49:51 +01:00 and observed from `main` on 2026-08-08
  (Europe/Madrid). `package.json` reports `1.2.3`; the topic commit and its merge commit
  are two commits after the dereferenced `v1.2.3` tag. Their net diff modifies only
  `docs/productivity/grill-me.md`, not a promoted `SKILL.md`.
- **Local:** commit `b2ca2964645875f513d812db0024350d689098c6`, tree
  `317ee5ef2fbf1bbb4ed2514fa65130f739b25424`, inspected in the isolated OI-01 worktree.
- **Definition of promoted:** the 18 Engineering and seven Productivity skills listed in
  the pinned upstream [README Reference](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/README.md#reference).
  `in-progress`, `misc`, and `deprecated` are deliberately excluded.
- **Release delta:** upstream [1.2.3 changelog](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/CHANGELOG.md#123)
  records secret redaction in `diagnosing-bugs`, harness-neutral subagent wording in
  `code-review`, `codebase-design`, and `improve-codebase-architecture`, and removal of
  time estimates from `wizard`. These claims were also checked against the pinned files.

`adopt` means add a missing capability with only packaging changes. `adapt` means take a
specific upstream idea while retaining local contracts. `already-covered` means the local
capability meets or exceeds the relevant intent. `reject-with-reason` means importing the
delta would add a competing owner, unsafe default, or out-of-scope workflow.

## Engineering matrix

| Upstream skill | Local counterpart or gap | Classification | Delta, affected surface, validation, and risk |
|---|---|---|---|
| [`ask-matt`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/ask-matt/SKILL.md) | [`ask-skills`](../../ask-skills/SKILL.md) | `already-covered` | Local routing covers the same entry-point role and additionally distinguishes normalized tickets, folder scheduling, QA, verification, and PR explanation. **Files/tests:** none; retain `ticket-autopilot/tests/test_skill_graph.py`. **Risk of import:** two routers could select different owners. |
| [`code-review`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/code-review/SKILL.md) | [`code-review`](../../code-review/SKILL.md), [`pr-antipattern-review`](../../pr-antipattern-review/SKILL.md) | `already-covered` | Upstream separates standards/spec review and carries a Fowler smell list. Local review covers maintainability, acceptance, regression, causal evidence, and claim safety for a frozen CandidateRef; the separate antipattern reviewer owns architecture-pattern checks. Local dispatch is already harness-neutral. **Files/tests:** none. **Risk of import:** losing CandidateRef staleness and evidence boundaries. |
| [`codebase-design`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/codebase-design/SKILL.md) | Explicit gap; vocabulary is duplicated in [`improve-codebase-architecture`](../../improve-codebase-architecture/SKILL.md) and `tdd` references | `adopt` | Add the shared module/interface/depth/seam/adapter reference, including `DEEPENING.md` and `DESIGN-IT-TWICE.md`, then point consumers at it. **Files:** new `codebase-design/{SKILL.md,DEEPENING.md,DESIGN-IT-TWICE.md,agents/openai.yaml}`; later consumer edits. **Tests:** frontmatter/link checks and `test_skill_graph.py` only if it becomes part of the owned orchestration graph. **Risk:** terminology drift unless duplicate local definitions are removed in a separate slice. |
| [`diagnosing-bugs`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/diagnosing-bugs/SKILL.md) | [`diagnose`](../../diagnose/SKILL.md), [`triangulate-diagnosis`](../../triangulate-diagnosis/SKILL.md) | `adapt` | Port the 1.2.3 redaction rule and the requirement that shown commands, outputs, and captured artifacts be redacted; retain local single-pass scope and report contract instead of copying the six-phase workflow. **Files:** `diagnose/SKILL.md`, possibly the shared report wording in `triangulate-diagnosis`. **Tests:** a static invariant or fixture ensuring examples never expose credentials. **Risk:** over-redaction can erase diagnostic signal; the rule must allow a gated request for redacted evidence. |
| [`domain-modeling`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/domain-modeling/SKILL.md) | [`domain-modeling`](../../domain-modeling/SKILL.md) | `already-covered` | Both use `CONTEXT.md`, optional context maps, and sparse ADRs. Local adds bounded-context guidance, explicit lazy creation, and user ownership of contested terms. **Files/tests:** none. **Risk of import:** replacing the local ADR/user-consent policy. |
| [`grill-with-docs`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/grill-with-docs/SKILL.md) | [`grill-with-docs`](../../grill-with-docs/SKILL.md) | `already-covered` | Upstream is a thin composition; local already composes `grilling` and `domain-modeling`, including lazy docs and ADR criteria. **Files/tests:** none. **Risk of import:** none material, but it would discard useful local boundaries. |
| [`implement`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/implement/SKILL.md) | [`execute-ticket`](../../execute-ticket/SKILL.md), [`ticket-autopilot`](../../ticket-autopilot/SKILL.md) | `already-covered` | Upstream is a 15-line orchestrator that runs TDD/review and commits. Local deliberately splits ticket mutation from scheduling, evidence, delivery, and commits. **Files/tests:** none; ownership is enforced by `test_skill_graph.py`. **Risk of import:** an executor could commit, push, or bypass Verification Records inside a scheduler-owned worktree. |
| [`improve-codebase-architecture`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/improve-codebase-architecture/SKILL.md) | [`improve-codebase-architecture`](../../improve-codebase-architecture/SKILL.md), [`codebase-improver`](../../codebase-improver/SKILL.md) | `adapt` | Current upstream scopes scans using change history, uses generic subagent wording, consumes shared `codebase-design`, and emits a temporary visual report before grilling. Local still names `Agent tool`/`subagent_type=Explore` and inlines older vocabulary. **Files:** `improve-codebase-architecture/{SKILL.md,REFERENCE.md,agents/openai.yaml}` after `codebase-design`; keep the self-contained `codebase-improver` separate. **Tests:** static no-AgentTool check, reference/link validation, manual HTML smoke test if the report path is adopted. **Risk:** changing its interactive output contract or accidentally folding the human-gated full-repo improver into this smaller survey. |
| [`prototype`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/prototype/SKILL.md) | [`prototype`](../../prototype/SKILL.md) | `already-covered` | Local already separates logic and UI branches, requires a runnable disposable artifact, compares divergent UI options, and records the learned answer. **Files/tests:** none. **Risk of import:** upstream's single-HTML default is too prescriptive for repo-native logic probes. |
| [`research`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/research/SKILL.md) | [`research`](../../research/SKILL.md) | `already-covered` | Local expands the same primary-source workflow with question pinning, evidence checks, observed/inferred separation, version/date constraints, and a durable report shape. **Files/tests:** none. **Risk of import:** weaker completion evidence. |
| [`resolving-merge-conflicts`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/resolving-merge-conflicts/SKILL.md) | Explicit gap | `adapt` | Preserve the intent-tracing, hunk-by-hunk resolution and checks, but remove the unconditional “never abort”, staging, commit, and rebase-continuation authority. Make it standalone or caller-authorized and exclude scheduler worktrees unless delegated. **Files:** new `resolving-merge-conflicts/{SKILL.md,agents/openai.yaml}`. **Tests:** synthetic conflicted repository covering compatible and incompatible intents, plus a no-commit invariant. **Risk:** destructive or lineage-changing Git operations without explicit authority. |
| [`setup-matt-pocock-skills`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/setup-matt-pocock-skills/SKILL.md) | Explicit gap | `reject-with-reason` | It configures upstream-specific tracker pointers, triage labels, `AGENTS.md`/`CLAUDE.md`, and domain-doc layout. This repository already has provider-neutral local tickets and canonical contracts. **Files/tests:** none. **Risk of import:** a second configuration authority and tracker-dependent assumptions. A future setup skill would need a separate local spec. |
| [`tdd`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/tdd/SKILL.md) | [`tdd`](../../tdd/SKILL.md) | `adapt` | Port pre-agreed seams and the tautological-test anti-pattern; move post-GREEN refactoring to `code-simplification`/review, where the local execution stack already owns it. Replace local `deep-modules.md`/`interface-design.md` duplication with `codebase-design` only after that skill lands. **Files:** `tdd/{SKILL.md,tests.md,mocking.md}` and eventually remove superseded `deep-modules.md`, `interface-design.md`, `refactoring.md`. **Tests:** Markdown-link checks plus a red/green example fixture if added. **Risk:** breaking existing references and requiring human seam confirmation during an AFK ticket; the ticket must predeclare seams or open a gate. |
| [`to-spec`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/to-spec/SKILL.md) | [`to-spec`](../../to-spec/SKILL.md) | `already-covered` | Local supports multiple spec types, explicit compatibility, external contracts, and verification without requiring publication to a configured issue tracker. **Files/tests:** none. **Risk of import:** provider mutation becomes implicit and local spec ownership becomes ambiguous. |
| [`to-tickets`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/to-tickets/SKILL.md) | [`to-tickets`](../../to-tickets/SKILL.md) | `already-covered` | Local already has tracer bullets and blocking edges, but serializes Ticket Envelope v1 through the canonical CLI and reparses it. **Files/tests:** none; retain `test_ticket_contract.py` and `test_skill_graph.py`. **Risk of import:** a second Markdown/tracker schema would bypass the scheduler parser. |
| [`triage`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/triage/SKILL.md) | No direct skill; local lifecycle work is planned separately | `reject-with-reason` | Upstream's category/state labels and external-PR workflow are tracker roles, not the local ticket disposition/execution/readiness model. Reuse the state-machine evidence when resolving OI-03/OI-04, but do not install it as a second lifecycle owner. **Files/tests:** none in this parity tranche. **Risk of import:** `blocked`, ready state, and provider labels could contradict derived local readiness and ledger state. |
| [`wayfinder`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/wayfinder/SKILL.md) | [`wayfinder`](../../wayfinder/SKILL.md) | `already-covered` | Local retains destination, fog/frontier, AFK/HITL, and plan-not-do semantics while making the map and tickets durable local artifacts with canonical envelopes. **Files/tests:** none; `test_skill_graph.py` already checks its ownership. **Risk of import:** upstream tracker-native child issues would compete with local ticket serialization and scheduling. |
| [`wizard`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/engineering/wizard/SKILL.md) | Explicit gap | `adapt` | Adopt the current stage-count template (1.2.3 removed unreliable time estimates), hidden input, idempotent environment updates, and cross-platform URL opening only as an explicitly human-run tool. Keep it outside AFK execution and require authority for secrets/provider writes. **Files:** new `wizard/{SKILL.md,template.sh,agents/openai.yaml}`. **Tests:** `bash -n`, `shellcheck` when available, and a fixture mode that cannot call `gh` or open a browser. **Risk:** credential disclosure, unintended `.env`/provider mutation, and non-portable shell behavior. |

## Productivity matrix

| Upstream skill | Local counterpart or gap | Classification | Delta, affected surface, validation, and risk |
|---|---|---|---|
| [`grill-me`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/grill-me/SKILL.md) | [`grill-me`](../../grill-me/SKILL.md) | `already-covered` | Both are user-invoked aliases over the reusable grilling primitive; local also documents compatibility behavior. **Files/tests:** none. **Risk of import:** none material. |
| [`grilling`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/grilling/SKILL.md) | [`grilling`](../../grilling/SKILL.md) | `already-covered` | Local retains one-question-at-a-time HITL behavior and adds recommended answers, dependency ordering, lookup-before-asking, confirmation, and explicit no-execution boundaries. **Files/tests:** none. **Risk of import:** weaker gates could revive self-grilling or premature execution. |
| [`handoff`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/handoff/SKILL.md) | Explicit gap | `adopt` | A temporary, redacted, pointer-based session handoff does not overlap scheduler state and is useful across non-ticket work. **Files:** new `handoff/{SKILL.md,agents/openai.yaml}`. **Tests:** frontmatter plus an output-shape/redaction fixture. **Risk:** stale or sensitive context in the OS temp directory; include expiry/deletion guidance without storing the handoff in Git. |
| [`teach`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/teach/SKILL.md) | Explicit gap | `reject-with-reason` | This is a multi-session learning product with four state documents and reusable teaching assets, outside the repository's planning/execution/review focus. **Files/tests:** none. **Risk of import:** workspace pollution and a large unowned state lifecycle. Reconsider only after a dedicated product decision. |
| [`to-questionnaire`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/to-questionnaire/SKILL.md) | Explicit gap; complements HITL tickets | `adopt` | “Grill the send, not the subject” provides a narrow way to externalize a decision that the current user cannot answer. **Files:** new `to-questionnaire/{SKILL.md,agents/openai.yaml}`. **Tests:** frontmatter and template-shape check. **Risk:** names or business context may be sensitive; require explicit destination and avoid automatic sending. |
| [`wait-what`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/wait-what/SKILL.md) | Normal clarification plus [`domain-modeling`](../../domain-modeling/SKILL.md) | `reject-with-reason` | The seven-line skill asks for a contextual re-pitch in simplified language. Normal interaction already supplies this, while hard-depending on `CONTEXT.md` would fail in repositories without one. **Files/tests:** none. **Risk of import:** cognitive/skill-list load without a durable workflow. |
| [`writing-for-agents`](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/skills/productivity/writing-for-agents/SKILL.md) | Explicit repository-local gap | `adopt` | Its pointer, information-hierarchy, completion-criterion, leading-word, and pruning vocabulary directly applies to maintaining this skills repository. Include the current 1.2.2+ Codex metadata that permits implicit invocation. **Files:** new `writing-for-agents/{SKILL.md,SKILL-MECHANICS.md,agents/openai.yaml}`. **Tests:** frontmatter/metadata trigger check and link validation. **Risk:** overlap with host-provided skill-creation guidance; position this as writing reference, not a second scaffold owner. |

## Smallest follow-up slices

Each slice below is independently reviewable; later slices name their only material
dependency.

1. **U-01 — Redact diagnostic evidence (`adapt`).** Add secret-redaction rules to
   `diagnose` and verify representative command/log examples. No dependency.
2. **U-02 — Adopt shared codebase-design reference (`adopt`).** Add the four upstream
   artifacts with local metadata and link validation. No consumer rewrites yet.
3. **U-03 — Align TDD (`adapt`).** Add pre-agreed seams and tautological-test guidance,
   route refactoring to the existing post-GREEN quality stage, then remove superseded
   references. Depends on U-02.
4. **U-04 — Make architecture improvement host-portable (`adapt`).** Replace AgentTool
   names, consume `codebase-design`, and decide separately whether the temporary HTML
   report becomes the stable output. Depends on U-02; this is also evidence for issue #34.
5. **U-05 — Adopt writing-for-agents (`adopt`).** Add the skill and mechanics reference,
   explicitly subordinate to the existing scaffold owner. No dependency.
6. **U-06 — Adopt handoff (`adopt`).** Add redacted temp handoffs with a small output
   contract. No dependency.
7. **U-07 — Adopt to-questionnaire (`adopt`).** Add local metadata and a no-send boundary;
   later link it from HITL guidance only if a concrete caller needs it. No dependency.
8. **U-08 — Safe conflict resolution (`adapt`).** Introduce intent-based conflict
   resolution without unconditional abort/commit/rebase authority. No dependency.
9. **U-09 — Safe wizard (`adapt`).** Port the current stage-count template behind an
   explicit human-run boundary and non-mutating fixture tests. No dependency.

Do not create slices for `already-covered` or `reject-with-reason` rows. OI-07 can select
from U-01 through U-09 without reopening the full comparison.

## OI-07 approved adoption selection

The user approved every actionable slice U-01 through U-09. This is selective adoption,
not authority to import the upstream tree or replace local workflow owners. The canonical
implementation tickets are:

| Slice | Decision and local owner | Mode | Blocker | Ticket |
| --- | --- | --- | --- | --- |
| `U-01` | Adapt secret-safe evidence handling in `diagnose`; keep `triangulate-diagnosis` as the multi-pass coordinator. | AFK | none | [Redact diagnostic evidence](../tickets/mattpocock-skills-adoption/done/01-redact-diagnostic-evidence.md) |
| `U-02` | Adopt `codebase-design` as the shared vocabulary owner without rewriting consumers in the same slice. | AFK | none | [Adopt codebase-design](../tickets/mattpocock-skills-adoption/done/02-adopt-codebase-design.md) |
| `U-03` | Adapt `tdd` after U-02, preserving `code-simplification` and review ownership of post-GREEN cleanup. | AFK | `U-02` | [Align TDD guidance](../tickets/mattpocock-skills-adoption/done/03-align-tdd-guidance.md) |
| `U-04` | Narrow architecture work to consuming `codebase-design`, recent-change scoping, and a human decision on visual-report stability. Preserve the separate `improve-codebase-architecture` survey and human-gated `codebase-improver` owners. | HITL | `U-02` | [Scope architecture improvement](../tickets/mattpocock-skills-adoption/done/04-scope-architecture-improvement.md) |
| `U-05` | Adopt `writing-for-agents` as a writing reference subordinate to the existing skill scaffold owner. | AFK | none | [Adopt writing-for-agents](../tickets/mattpocock-skills-adoption/done/05-adopt-writing-for-agents.md) |
| `U-06` | Adopt temporary, redacted session handoffs; do not create scheduler state. | AFK | none | [Adopt session handoff](../tickets/mattpocock-skills-adoption/done/06-adopt-session-handoff.md) |
| `U-07` | Adopt `to-questionnaire` with an explicit destination and no-send boundary. | AFK | none | [Adopt to-questionnaire](../tickets/mattpocock-skills-adoption/done/07-adopt-to-questionnaire.md) |
| `U-08` | Adapt intent-based merge-conflict resolution without implicit abort, commit, continuation, or scheduler-worktree authority. | AFK | none | [Add safe conflict resolution](../tickets/mattpocock-skills-adoption/done/08-add-safe-conflict-resolution.md) |
| `U-09` | Adapt the current wizard template behind an explicitly human-run boundary and non-mutating fixture mode. | AFK | none | [Add safe wizard](../tickets/mattpocock-skills-adoption/done/09-add-safe-wizard.md) |

The delivered OI-08 Wayfinder-to-Grilling routing and OI-09 AgentTool-optional execution
contract remain authoritative. U-04 therefore excludes routing changes, AgentTool removal,
and execution-isolation vocabulary. It cannot absorb `codebase-improver` or change its
human gate. The upstream `grilling`, `grill-me`, `grill-with-docs`, and `prototype` deltas
remain `already-covered`; OI-07 emits no duplicate tickets for them.

## Evidence

- The pinned upstream [README](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/README.md)
  defines the promoted set and its user-invoked/model-invoked split.
- The pinned upstream [changelog](https://github.com/mattpocock/skills/blob/84fdeffd12f2ee307994d1eb6feb48173b6e0502/CHANGELOG.md)
  records the 1.2.3 security, portability, and wizard changes.
- The upstream source links in each matrix row are immutable commit permalinks; the local
  links point to the inspected counterparts.
- Local ownership boundaries are explicitly declared by
  [`ask-skills`](../../ask-skills/SKILL.md),
  [`execute-ticket`](../../execute-ticket/SKILL.md),
  [`ticket-autopilot`](../../ticket-autopilot/SKILL.md), and
  [`verification-audit`](../../verification-audit/SKILL.md), and are exercised by
  `ticket-autopilot/tests/test_skill_graph.py`.

## Unknowns and limitations

- Classifications are design recommendations, not observed runtime proof. No upstream
  skill was installed or executed by OI-01.
- GitHub `main` is mutable. The report remains reproducible because every upstream source
  link and claim is pinned to the inspected commit; a later sync must refresh the baseline.
- Shell, browser-opening, secret-store, provider, and human-interaction behavior for the
  proposed `wizard`, conflict-resolution, handoff, and questionnaire slices remains
  untested until those slices are implemented.
- This report does not decide whether issue #25 should close; OI-07 owns the adoption
  decision and resulting implementation scope.

## Next step

Execute the approved U-01 through U-09 ticket graph. U-03 and U-04 wait for the shared
U-02 vocabulary; the remaining AFK tickets form the initial ready frontier. U-04 must
resolve its visual-report output contract through its HITL gate without reopening OI-08
or OI-09.
