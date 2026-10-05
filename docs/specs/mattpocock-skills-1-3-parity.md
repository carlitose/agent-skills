# Matt Pocock skills 1.3 parity refresh

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity`
- Role: `spec`
- Standalone: true

### Children
- [MP13-01 grilling in rounds](../tickets/mattpocock-skills-1-3-parity/01-grilling-in-rounds.md)
- [MP13-02 session retro for Pi](../tickets/mattpocock-skills-1-3-parity/02-session-retro.md)
- [MP13-03 skills-only PR body](../tickets/mattpocock-skills-1-3-parity/03-skills-only-pr-body.md)

## Type
Decision spec. Decisions confirmed by the human on 2026-10-05 (approved option 1 of the
refresh analysis; keep `resolving-merge-conflicts`).

## Baselines
- **Previous:** [`mattpocock/skills@84fdeffd`](https://github.com/mattpocock/skills/commit/84fdeffd12f2ee307994d1eb6feb48173b6e0502)
  (1.2.3, 2026-08-06), analysed in [mattpocock-skills-parity.md](../research/mattpocock-skills-parity.md).
- **Current:** [`mattpocock/skills@4588b32`](https://github.com/mattpocock/skills/commit/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d)
  (1.3.1 plus four commits, 2026-10-05). 83 commits in between.
- **Local:** `agent-skills@a2c2d79`.

Most of the 83 commits are form only: em-dash removal across the repo, the
`CONTEXT.md` → `GLOSSARY.md` rename, and "Call the Skill tool with X" replacing bare
`/skill` prose. The analysis below ignores hunks that change only those.

## Upstream delta that matters
| Upstream change | Decision | Owner |
| --- | --- | --- |
| [`grilling`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/productivity/grilling/SKILL.md) asks the whole decision frontier per **round**, numbered, each with a recommended answer, separated by `---` | adopt | MP13-01 |
| New [`retro`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/retro/SKILL.md): read a session's logs and propose changes to the agent environment (navigation pointers, missing or unwired checks, no-op steering, expensive tool calls); mechanical violations get a deterministic check, not a written rule | adapt | MP13-02 |
| New [`pr`](https://github.com/mattpocock/skills/blob/4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d/skills/engineering/pr/SKILL.md): PR body = smallest visual summary, before/after evidence, merge danger (one-way/two-way door, blast radius) | adapt into the skills-only PR body | MP13-03 |
| `domain-modeling` description triggers on terminology talk and on editing the glossary or an ADR | optional, not ticketed | — |
| Skill-to-skill calls must never target a user-invoked skill (`.agents/invocation.md`) | optional check, not ticketed | — |
| New `implement-spec` (parallel implementer subagents per ticket, one integration branch) | reject | — |
| New in-progress `chief-of-staff` (long session that does all work through subagents) | reject | — |
| `resolving-merge-conflicts` removed upstream | keep ours | — |
| `CONTEXT.md` → `GLOSSARY.md` rename | reject | — |
| "Call the Skill tool with X" phrasing | reject | — |
| `diagnosing-bugs` drops its post-mortem hand-off to architecture | already aligned | — |

## Decisions
1. **Grilling in rounds.** `grilling` asks every question whose prerequisites are settled in one
   message, numbered, each with a recommended answer; questions that depend on an answer
   still open in the round wait for a later round. Fewer turns for the same decisions.
2. **Retro, adapted.** A user-invoked, read-only skill that reads Pi session logs (current
   session by default), redacts secrets, and returns ranked environment improvements. It
   proposes only: no edits to steering files, settings, or code.
3. **PR body.** The skills-only short PR body gains a smallest-visual summary, before/after
   evidence, and a merge-danger line, and keeps checks and open gates. It stays short.
   `explain-pr` and the Verification Record are unchanged.
4. **Keep `resolving-merge-conflicts`.** Our version has explicit authority limits (no implicit
   abort, commit, continuation, or scheduler-worktree mutation) that upstream never had.
5. **Reject subagent orchestration.** `implement-spec` and `chief-of-staff` depend on parallel
   subagents, against the serial skills-only lane and explicit-delegation-only default.
6. **No rename, no phrasing import.** `GLOSSARY.md` would break repos that already use
   `CONTEXT.md`; Pi has no Skill tool, and our relative skill links already resolve.
7. **Parallelizable tickets.** From `implement-spec` we keep only the idea of a ready
   **frontier** of tickets worked at once, served by human-opened Pi sessions rather than
   subagents: `to-tickets` keeps slices vertical, adds blockers only for real dependencies,
   and prefers disjoint files. Applied directly in `to-tickets/SKILL.md` with this spec
   (human request, 2026-10-05); the tickets below follow it (no blockers, disjoint files).

## Not ticketed (optional follow-ups)
- Widen the `domain-modeling` description triggers.
- A test that no skill instructs the agent to run a user-invoked skill
  (`grill-me`, `grill-with-docs`, `handoff`) by itself.

## Non-goals
- Importing the upstream tree, its installer, or `setup-matt-pocock-skills`.
- Any runner, scheduler, or subagent change.

## Verification strategy
Each ticket keeps its own causal checks: skill text/frontmatter checks,
`ticket-autopilot/tests/test_skill_graph.py` where a skill's graph or wording assertions are
touched, and the artifact audit for new docs.
