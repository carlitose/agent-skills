---
ticket_schema: 1
ticket_id: "LW-03"
execution_mode: AFK
blocked_by: []
---

# Bind a wiki instance to its host project

## Artifact Graph
- Artifact ID: `artifact:lw-03-bind-wiki-to-project`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
The one piece of state without which no other op can run: a wiki has to know which project
it is the history of, and how to reach that project's artefacts and sessions.

Today nothing records it. `../minnarone/wiki/minnarone-wiki/purpose.md` states the project's
goal in prose and `schema.md` states page conventions, but neither names a filesystem root,
and the ingested source pages carry only repository-relative paths
(`sources: ["docs/adrs/2026-06-29-live-media-backpressure-boundary.md"]`) with no anchor to
resolve them against.

The binding must carry:

- `project_root` — an absolute path to the host project.
- the docs globs to ingest, defaulting to this repository's actual shape:
  `docs/specs/*.md`, `docs/tickets/**/*.md`, `docs/research/*.md`,
  `docs/prototypes/**/*.md`.
- a git mode, with `auto` meaning "use git if the host is a repository and the artefact is
  tracked, otherwise fall through".
- session providers for Claude Code and Codex, resolved by `LW-07`'s rules.

Three constraints the design must satisfy, all of them stated requirements rather than
preferences:

1. **No assumption about what is tracked.** The wiki may be git-ignored, as in minnarone
   (`.gitignore:48: wiki/`), or committed. `docs/` may be tracked, as it is here, or not.
   The host may not be a git repository at all. All four combinations are valid inputs; none
   may raise, and none may silently produce a wrong answer.
2. **Worktree-correct.** This repository currently has 11 worktrees, including
   `Projects/.agent-skills-ticket-autopilot-worktrees/<id>/` outside the project directory.
   Resolution must not assume `project_root` is the same directory as the git common dir.
3. **Relocatable.** An absolute path in a config file breaks when the project moves. The
   design must state what happens then — re-resolve, fail loudly, or record a warning — and
   must not produce silently stale reads.

## Acceptance Criteria
- [ ] A config file at the wiki root holds `project_root`, docs globs, git mode, and session
      providers, in a format the app tolerates (see `LW-02` for front matter; a standalone
      file avoids that question entirely and is the safer default).
- [ ] A resolver returns, for a given wiki root: the project root, whether the host is a git
      repository, and whether a given artefact path is tracked — as three separate facts,
      never conflated.
- [ ] Verified on all four tracked/untracked combinations, including a non-git host.
- [ ] Verified from inside a worktree: resolution returns the same `project_root` and the
      same tracked-ness answers as from the main working tree.
- [ ] A missing or stale `project_root` fails with a message naming the path it tried, and
      never falls back to the current working directory.
- [ ] Nothing in the resolver reads or writes the host project's git state beyond queries.

## Frontier
Ready, no blockers. `LW-04`, `LW-05` and `LW-08` all block on it.

## Step-by-Step Implementation Plan
1. Define the config file: name, location, format, required and optional keys, and the
   default docs globs. Checkpoint: a documented schema and a written example for this
   repository.
2. Implement the resolver, keeping "is a git repo", "artefact is tracked" and "path exists"
   as three independent predicates. Checkpoint: each answerable in isolation.
3. Build fixtures for the four combinations plus a non-git host. Checkpoint: five fixtures
   that a test can construct without network or the real repository.
4. Add worktree coverage using `git worktree add` in a temporary directory. Checkpoint:
   identical answers from both trees.
5. Handle the moved-project case explicitly. Checkpoint: a loud failure with the attempted
   path, never a cwd fallback.

## Testing Plan
Automated: unit tests over the five fixtures, plus a worktree test. Follow the repository's
existing convention — stdlib `unittest`, discovered from the skill's own test root; `pytest`
is not installed here.

Manual: point a config at this repository and confirm the resolver reports git present,
`docs/` tracked, and the 14 specs plus 8 ticket folders discovered by the default globs.

Unavailable boundary: only Windows is available in this session. POSIX path handling —
particularly the absence of a drive letter — must be covered by fixture, and any
cross-platform claim stays unobserved until the suite runs on POSIX.

## Out of Scope
- Reading any artefact content. This ticket resolves locations only.
- Date resolution, which is `LW-04`.
- Session discovery rules, which are `LW-07`; this ticket only holds the fields they fill.
- Deciding where this repository's own wiki instance lives.
