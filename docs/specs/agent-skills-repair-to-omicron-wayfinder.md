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

## Fixed Ordering

### Phase 0 — Intake and scheduling

**Artifacts**

- [Legacy root-catalog adoption](llm-wiki-legacy-root-catalog-adoption.md)
- `WCA-01 — Adopt the Agent Skills legacy root catalog`
- [Natural-language merge-all regression](ticket-autopilot-natural-language-merge-all-intent.md)
- [Omicron Code frontier](omicron-code-wayfinder.md)

**Actions**

1. Validate reciprocal Artifact Graph links for the wiki spec/ticket.
2. Commit only the intake map, specs, and canonical WCA ticket on the isolated branch.
3. Start one Ticket Autopilot run for WCA-01 from the committed clean base.

**Exit**

WCA-01 has a canonical tracked ticket, a clean intake commit, and an active isolated run.
The merge-all and Omicron tickets remain un-emitted so external sequencing cannot be
bypassed accidentally.

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

### Phase 3 — Restore “merge all” natural-language semantics

Use the focused bug spec above. After Phase 2, emit and run MAR-01.

Required behavior:

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

The MAR code PR is integrated under valid authority and the behavior is pinned by routing,
mandatory-policy, context, and repository merge-authority tests.

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
- No authority is inferred for merge, wiki publication, Pi sync, conflict resolution,
  cleanup, force push, visibility, source publication, or history rewriting.
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
| 1 | WCA intake/ticket | active | canonical emit and clean commit |
| 2 | WCA implementation/PR | pending | phase 1 run and new merge authority |
| 3 | WCA tracked wiki update | pending | exact integrated WCA head and separate wiki authority |
| 4 | MAR-01 merge-all semantics | deferred | terminal WCA wiki receipt |
| 5 | MAR tracked wiki + local Pi sync | deferred | exact integrated MAR head and separate authorities |
| 6 | Omicron OMC-01/02 | deferred | phase 4 terminal state |
| 7 | Omicron prototype/decision | deferred | OMC-01 and OMC-02 evidence |
| 8 | Omicron implementation tickets | deferred | accepted OMC-04 decision |

Update this table and the individual frontier after every terminal receipt or newly observed
blocker. Do not silently reorder phases.
