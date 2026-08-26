---
ticket_schema: 1
ticket_id: "LW-09"
execution_mode: AFK
blocked_by:
  - "LW-01"
---

# Retarget scaffold and lint to the single wiki layout

## Artifact Graph
- Artifact ID: `artifact:lw-09-retarget-scaffold-and-lint`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
Alignment between what the skill says and what the wiki is. Right now they describe two
different products, and every later ticket pays for the gap.

The divergence, precisely. `llm-wiki/SKILL.md`, `llm-wiki/scripts/scaffold.py` and
`llm-wiki/scripts/lint_wiki.py` describe and enforce:

```
CLAUDE.md · log/YYYYMMDD.md · audit/ + audit/resolved/
raw/{articles,papers,notes,refs}/ · wiki/{concepts,entities,summaries}/ · outputs/queries/
```

The shape the target layout was drawn from, in live use at `../minnarone/wiki/minnarone-wiki`:

```
purpose.md · schema.md · raw/{sources,assets}/
wiki/{concepts,entities,sources,queries,comparisons,synthesis}/ · wiki/index.md · wiki/log.md
```

Verified absent there: `log/`, `audit/`, `CLAUDE.md`. So `scaffold.py` currently creates a tree
the target layout does not use, and `lint_wiki.py`'s seven passes include two that inspect a
directory the target layout did not have until `LW-01` added it back. Its log pass checks for
`log/YYYYMMDD.md` filenames, and its orphan and index passes assume
`wiki/{concepts,entities,summaries}` rather than the six directories in use.

The five reference documents carry the same assumption in prose:
`references/{schema-guide,article-guide,log-guide,audit-guide,tooling-tips}.md`.
`schema-guide.md` documents `CLAUDE.md`, which the target layout replaces with `purpose.md`
plus `schema.md`; `log-guide.md` documents the per-day directory.

`LW-01` has decided both questions this ticket depended on, in
[llm-wiki-app-independence-decision.md](../../specs/llm-wiki-app-independence-decision.md):
**one layout, not two profiles**, and **`audit/` stays** as the human-to-agent correction
channel. So `scripts/audit_review.py` and both `audit/` passes in `scripts/lint_wiki.py` are
kept unconditionally — not made profile-conditional, and not removed. "Aligned" means aligned
to the single target layout:

```
purpose.md · schema.md · audit/ + audit/resolved/
raw/{sources,refs,assets}/ · wiki/index.md
wiki/{concepts,entities,sources,queries,comparisons,synthesis}/ · wiki/timeline/
```

One sub-question `LW-01` deliberately left to this ticket: **where the log lives.** The target
layout's `schema.md` documents a single `wiki/log.md` in reverse chronological order; the
layout being retired uses `log/YYYYMMDD.md`, one file per day, and `lint_wiki.py` has a pass
over that filename shape. Exactly one survives, and this ticket picks it.

A further consequence of `LW-01`: nothing in the retargeted scripts or documents may reference
`.llm-wiki/`, the application's `/api/v1`, or its MCP tools. A static check for those strings
belongs in this ticket's verification.

## Acceptance Criteria
- [ ] `scaffold.py` creates exactly the target layout above, `audit/` and `audit/resolved/`
      included.
- [ ] `lint_wiki.py`'s existing passes operate on the target layout's real directories; no pass
      silently succeeds because the directory it checks does not exist.
- [ ] The two `audit/` passes and `audit_review.py` are **kept and working**, not conditional
      and not dead code that appears to be running. `LW-01` settled this.
- [ ] A static check confirms no file under `llm-wiki/` references `.llm-wiki`, `/api/v1`, or
      the application's MCP tool names.
- [ ] The log question is decided and implemented: either `wiki/log.md` or `log/YYYYMMDD.md`,
      with the losing form removed from the scripts and the references.
- [ ] `SKILL.md` and the five references describe the layout the scripts implement. A reader
      following them produces a wiki that lints clean.
- [ ] `python -m py_compile` passes on all scripts, and the invocation lines in the docs work
      as written on this machine — note that `python3` does not resolve here while `python`
      does, and the docs currently say `python3` in 18 places.
- [ ] Scaffolding a fresh wiki and immediately linting it reports zero issues. A new wiki
      that fails its own lint is the current state and is the thing being fixed.
- [ ] The live `../minnarone/wiki/minnarone-wiki` is not modified.

## Frontier
Dependency-blocked on `LW-01` only, which makes it the earliest of the large tickets. It does
not wait on ingest, the timeline, or sessions.

## Step-by-Step Implementation Plan
1. Enumerate every layout assumption in the three scripts and the five references, as a list
   of concrete paths. Checkpoint: a list, so nothing is retargeted by memory.
2. Apply the target layout to `scaffold.py`, and decide the log form. Checkpoint: a scaffolded
   tree matches the layout above exactly.
3. Retarget `lint_wiki.py`'s passes. Checkpoint: each pass demonstrably fires on a seeded
   defect — a pass that cannot fail is worse than no pass.
4. Keep the audit passes and make them fire on a seeded defect. Checkpoint: no dead pass
   presenting itself as green.
5. Update `SKILL.md` and the references, including the `python3` invocations. Checkpoint:
   every command in the docs runs as written here.
6. Scaffold and lint a fresh wiki. Checkpoint: zero issues.

## Testing Plan
Automated: seed one defect per lint pass in a temporary wiki and assert each pass reports it;
assert a clean scaffold lints clean. Follow the repository convention of stdlib `unittest`.

Manual: open a scaffolded wiki in Obsidian and confirm it loads. Opening it in the LLM Wiki
application is optional under `LW-01` and cannot fail this ticket.

Unavailable boundary: only Windows is available, so the `python` versus `python3` invocation
fix is verified here and stays unobserved on POSIX.

## Out of Scope
- The new drift and coverage lint passes. Those are `LW-11`, which blocks on ingest and the
  timeline existing.
- Any ingest, timeline or session behaviour.
- Migrating the minnarone wiki to any new shape.
- Installing the skill into `~/.agents/skills/`.
