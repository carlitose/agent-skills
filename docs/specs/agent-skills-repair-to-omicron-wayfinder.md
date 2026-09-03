# Agent Skills repair-to-Omicron work queue

## Artifact Graph

- Artifact ID: `artifact:agent-skills-repair-to-omicron-wayfinder`
- Role: `wayfinder`
- Standalone: true

## Purpose

This is the durable ordering map for the work agreed after FTV-05. It preserves the
frontier, dependencies, authority boundaries, and intentionally deferred work so a later
session does not conflate Pi Code Tool, the Pi coding agent, wiki publication, or merge
consent.

## Current Baseline

- FTV-05 is terminally integrated. PR `#221` merged exact head
  `a00b53e8d12e011660b935beda9ff0143e90fe65` as merge commit
  `5158e0a4fe2bc7ffba8e24772d00c6913a961af9`.
- Its post-integration wiki sync failed terminally before candidate production because the
  tracked 48,573-byte `knowledge/wiki/index.md` predates WS-08 ownership markers.
- The FTV-05 merge authorization was scoped to that ticket set and is not reusable.
- Corrective intake is isolated at
  `/Users/carlogiuseppesergi/Projects/.agent-skills-wiki-picode-intake-20260903`, branch
  `intake/agent-skills-wiki-picode-20260903`, based on the FTV merge commit above.
- Local Agent Skills is currently a clean checkout at
  `/Users/carlogiuseppesergi/.pi/agent/local/agent-skills`, commit
  `d78592d7ad5b4fe4a3197159ac3d1f846ff9d287`.
- Installed Pi is `0.84.4`; installed `pi-code-tool` is `0.6.1`.
- `pi-personal-config` is a clean `main` checkout at commit
  `668503d0c7746bf72b04150896d24a708698ffc2` when this map was written.
- The first WCA run reached an independent pre-implementation blocker: schema-1 repository
  merge/reconciliation authority is stored in the shared Git common directory but bound to
  the stale `.agent-skills-runner-latest` worktree root. Sibling worktrees report a
  contradictory binding, and `resume` currently consumes that optional reconciliation
  state even when the manual run has no conflict proposal.
- WCA-01 v2 is frozen at final delivery tree
  `14ac5eb88beb20e366f23e2d940ac4d6361aea6c`, stage `qa-execute`, with no unstaged changes
  or open gate. Review and QA planning are bound to that tree.
- The operator explicitly reprioritized Break Glass before further WCA execution. The
  existing read/confirmed-Bash design does not escape a broken control plane because it
  forbids the local tracked or ledger repair needed to make `status`/`resume` work again.

## Fixed Ordering

### Phase 0 — Intake and scheduling

**Artifacts**

- [Legacy root-catalog adoption](llm-wiki-legacy-root-catalog-adoption.md)
- `WCA-01 — Adopt the Agent Skills legacy root catalog`
- [Worktree-stable repository authority](ticket-autopilot-worktree-stable-repository-authority.md)
- [Natural-language merge-all regression](ticket-autopilot-natural-language-merge-all-intent.md)
- [Natural-language Break Glass local repair](pi-break-glass-natural-language-local-repair.md)
- [Omicron Code frontier](omicron-code-wayfinder.md)

**Actions**

1. Validate reciprocal Artifact Graph links for the wiki spec/ticket.
2. Commit only the intake map, specs, and canonical WCA ticket on the isolated branch.
3. Preserve the first run's exact pre-implementation authority-binding failure; do not
   rewrite its ledger or the shared authority files.
4. Materialize an independent clean clone with GitHub `origin`, import the exact intake
   commit, and start WCA-01 there under manual merge/wiki policy. The clone intentionally
   carries no authority from another Git common directory.

**Exit**

WCA-01 has a canonical tracked ticket, a clean intake commit, and an active isolated run in
the independent clone. The failed first attempt remains truthful diagnostic evidence. The
MRA, MAR, and Omicron tickets remain un-emitted so external sequencing cannot be bypassed
accidentally.

### Urgent Phase BG — Make Break Glass a real escape hatch

This phase is an explicit operator priority override, not an inferred reorder. Replace the
current metadata-heavy, read-only recovery turn with:

1. `/break-glass` arms the next natural-language turn without a wizard or magic phrase;
2. that prompt is the complete one-turn repair scope;
3. canonical `read`, `bash`, `edit`, and `write` run without per-call confirmation;
4. local tracked files and Ticket Autopilot control-plane state may be repaired directly;
5. the same turn reads back `status`/`resume`, closes, and restores normal routing;
6. remote/provider/merge/completion/wiki/Pi authority remains separate.

Use a v2 state and policy marker so an old v1 arm cannot inherit wider mutation scope.
Integrate and locally synchronize this correction before resuming WCA-01. The user controls
the required `/reload`.

**Exit**

The exact Break Glass correction is integrated, local Agent Skills points to that integrated
head, and the operator has been told to run `/reload`. WCA-01 remains frozen unless its exact
CandidateRef is still valid; any drift is handled by normal runner revalidation.

### Phase 1 — Repair legacy wiki adoption

Implement WCA-01 exactly:

- caller-supplied complete ownership map for `project-sources`, `session-sources`, and
  `timeline`;
- exact SHA-256 binding to the legacy bytes;
- validate-first, write-once insertion of the six canonical marker lines;
- byte-perfect marker-removal round trip and byte-idempotent replay;
- no heading inference and no permissive fallback in normal compilation;
- full LLM Wiki, Ticket Autopilot wiki-sync, context/token, static, forward, and Artifact
  Graph checks on the exact final candidate.

**Authority boundary**

A new exact-candidate Verification Record and PR are required. The old FTV-05 merge grant
cannot authorize this PR. Unless a distinct active repository-wide grant is proven, request
new authorization for the exact live PR head immediately before merge.

**Exit**

The WCA code PR is integrated and provider readback proves the exact integrated commit.

### Phase 2 — Publish the repaired tracked wiki

1. Run the post-integration wiki hook only from the exact WCA integrated head.
2. Stage compilation outside the protected checkout and validate ingest, timeline rebuild,
   generated scopes, links, lint, determinism, and protected-tree non-mutation.
3. Freeze the tracked-wiki candidate SHA and report.
4. Request separate authorization for that exact wiki candidate SHA.
5. Publish/merge only the authorized candidate, then rerun readback and unchanged replay.

Code merge authority never transfers to this candidate. A stale or regenerated wiki SHA
requires new authorization.

**Exit**

The legacy catalog repair and its generated wiki update both have terminal receipts; the
tracked wiki matches the exact integrated WCA source.

### Phase 3 — Repair repository-wide authority and “merge all” semantics

After Phase 2, emit and run the two focused slices in order:

1. **MRA-01:** make repository merge/reconciliation authority stable across linked
   worktrees, add explicit digest-bound migration for legacy checkout-bound state, and keep
   unrelated manual runs independent of optional authority.
2. Publish MRA-01's separately protected wiki refresh.
3. **MAR-01:** restore the natural-language repository-wide merge-all route.

Required final behavior:

- an unambiguous affirmative “merge all” / “merge everything” / “mergia tutto” routes to
  repository-wide `current-and-future-runs` authority plus `merge-all`;
- the agent does not ask the user to provide a PR SHA and does not narrow the instruction to
  the currently shown PR;
- Ticket Autopilot still discovers and revalidates each live exact head before mutation;
- quoted text, examples, questions, negations, and regression reports create no merge
  authority;
- conflicts and all non-merge authorities remain separate.

The current report is a bug request, not a live instruction to merge all open PRs.

**Exit**

MRA and MAR code PRs are integrated under valid authority; their separately protected wiki
refreshes are terminal; worktree identity/migration, routing, mandatory-policy, context,
and repository merge-authority tests pin the complete behavior. A live legacy-authority
migration or `merge-all` call still requires an affirmative operator transaction.

### Phase 4 — Refresh generated and local projections

1. Generate and publish the separate tracked-wiki candidate for the integrated MAR head,
   under its own exact-SHA authorization.
2. Run `sync-local-pi` only for the exact latest integrated Agent Skills head and only with
   explicit actor/evidence-bound local-sync configuration.
3. Validate package-source identity, owned manifests, `pi install` readback, and `pi list`.
4. Preserve unrelated settings and packages.
5. Report that the user must run `/reload`; do not reload or mutate the active session.

Do not run `pi update`. Do not update unrelated models/packages. Do not remove the
standalone `npm:pi-code-tool` row as part of this Agent Skills repair.

**Exit**

Tracked wiki and local Agent Skills both project the same latest integrated repository
state, with terminal receipts or explicit visible gates.

### Phase 5 — Activate Omicron Code wayfinding

Only after Phase 4, activate `omicron-code-wayfinder.md`:

1. **OMC-01 research:** map official Pi source/version, license, package graph, build,
   release, update, extension, settings, and session seams.
2. **OMC-02 research:** build a secret-safe inventory/ownership matrix for current Pi
   packages/extensions and `pi-personal-config`.
3. **OMC-03 prototype:** compare vendor, dependency-composition, and install-profile models
   in disposable code; prove a distinct `omicron` identity and representative integrations.
4. **OMC-04 decision:** settle repository visibility, package/command names, release and
   upstream-sync policy, telemetry, compatibility, extension ownership, and migration.
   Ask the user only where evidence leaves material product choices.
5. **OMC-05 decomposition:** write the accepted implementation spec and canonical
   tracer-bullet tickets for the fork, CI, packaging, migration, docs, and rollout.
6. Execute the resulting Omicron ticket folder through Ticket Autopilot with its own
   candidate, verification, publication, merge, and projection authorities.

No fork implementation starts during OMC-01/02. The upstream revision must be refreshed at
activation time rather than assuming installed Pi `0.84.4` is still current.

## Explicitly Retired Interpretation

The earlier idea to change the `agent-skills` package into a composite extension that owns
`pi-code-tool` was based on reading “Pi Code” as Pi Code Tool. That interpretation is
superseded and is not queued.

`pi-code-tool` remains relevant only as one installed capability to classify during the
Omicron inventory. Any later decision to vendor or compose it belongs to OMC-03/04 and must
not be preselected here.

## Global Invariants

- Use clean isolated worktrees; stale or dirty checkouts are not authoritative.
- Evidence from implementation tree `I` never satisfies delivery tree `D` verification.
- Preserve historical projection configuration literally; new runs use the current
  configured default without rewriting old ledgers.
- Ordinary wiki compilation remains fail-closed for unmarked catalogs.
- A deliberately armed v2 Break Glass turn may directly repair local tracked or
  `.git/ticket-autopilot` state described by its natural-language prompt; that repair is
  read back through the normal runner and may invalidate stale quality evidence.
- Break Glass does not imply merge, push, provider, wiki publication, completion, Pi sync,
  cleanup, force push, visibility, source publication, or remote history authority.
- Each provider mutation rechecks exact live identity immediately before mutation and reads
  it back afterward.
- Tracked wiki candidates remain separate from implementation candidates.
- Local settings migration must preserve unrelated rows and require exact identity checks
  before removal or replacement.
- Never copy secrets, tokens, trust state, sessions, caches, private audits, or
  machine-specific paths into Omicron.

## Frontier Snapshot

| Order | Work | State | Blocking edge |
|---:|---|---|---|
| 1 | Break Glass natural-language local repair | active | explicit operator priority override |
| 2 | Break Glass local Pi sync + user reload | pending | exact integrated Break Glass head and sync authority |
| 3 | WCA-01 final QA/verification/PR | frozen | Break Glass terminal receipt; revalidate tree `14ac5eb8…` |
| 4 | WCA tracked wiki update | pending | exact integrated WCA head and separate wiki authority |
| 5 | MRA-01 worktree-stable authority | deferred | terminal WCA wiki receipt |
| 6 | MRA wiki refresh, then MAR-01 semantics | deferred | exact integrated MRA head and separate authorities |
| 7 | MAR tracked wiki + local Pi sync | deferred | exact integrated MAR head and separate authorities |
| 8 | Omicron OMC-01/02 | deferred | phase 4 terminal state |
| 9 | Omicron prototype/decision | deferred | OMC-01 and OMC-02 evidence |
| 10 | Omicron implementation tickets | deferred | accepted OMC-04 decision |

Update this table and the individual frontier after every terminal receipt or newly observed
blocker. Do not silently reorder phases.
