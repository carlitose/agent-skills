---
ticket_schema: 1
ticket_id: "LW-02"
execution_mode: AFK
blocked_by: []
---

# Check that the LLM Wiki application still opens the tree

## Artifact Graph
- Artifact ID: `artifact:lw-02-measure-app-tolerance`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
A compatibility finding. Not a gate.

`LW-01` decided that the skill is independent of the LLM Wiki application at runtime and in
its data — recorded in
[llm-wiki-app-independence-decision.md](../../specs/llm-wiki-app-independence-decision.md).
That decision changed this ticket twice.

**It is no longer blocking.** Whatever the application does with an unknown directory cannot
dictate the shape of `wiki/timeline/`, because the wiki has to be correct without the
application. This ticket therefore left `LW-06`'s blocker set. Its output is advisory: where
compatibility is free, `LW-06` may as well take it; where it would cost correctness,
correctness wins.

**Its method changed.** The original plan was to launch the GUI and observe, on the mistaken
belief that the application could not be read. It can: **`LLM Wiki` by `nashsu`, v0.5.4**
(`github.com/nashsu/llm_wiki`, Tauri plus React/TypeScript) is cloned at `../llm_wiki` at
exactly the version built into
`~/Downloads/LLM-Wiki-0.5.4-windows-x64-portable/`. Reading the source is cheaper than
driving a GUI and gives an answer that cites a line instead of a screenshot.

The three questions, and where the answer lives:

1. **An unknown directory under `wiki/`.** Does the ingest and file walk include, skip, or
   reject `wiki/timeline/`? Start at `src/lib/ingest.ts` and `src/lib/persist.ts`. Note that
   `.llm-wiki/file-snapshot.json` in the live wiki tracks 275 files under exactly four
   prefixes — `raw/` (194), `wiki/` (79), `purpose.md`, `schema.md` — so the walk is already
   known to be selective; this establishes *how* selective within `wiki/`.
2. **An unknown `type:` value.** Is the page-type set in `schema.md`
   (`entity`, `concept`, `source`, `query`, `comparison`, `synthesis`, `overview`) enforced in
   code, and does `type: lifecycle` render, warn, or fail? Does the lancedb indexer skip it?
3. **Extra front-matter keys.** Are unknown keys preserved on a round trip, or stripped?
   `LW-10` needs `identity_key` and `source_digest` somewhere, and `LW-04` needs
   `date_provenance`. If the application strips them, that is not a blocker under `LW-01` —
   but it is a good reason for `LW-10` to choose a sidecar, so the finding is worth having
   before `LW-10` picks a location.

## Acceptance Criteria
- [ ] Each of the three questions has a recorded answer citing a file and line in
      `../llm_wiki`, at version 0.5.4.
- [ ] The answer names the version it applies to, since a later release may differ.
- [ ] The front-matter round-trip answer is explicit about which keys survive, and is
      delivered as advice to `LW-10` rather than as a constraint on it.
- [ ] The finding states plainly that none of it can block `LW-06`, so a later reader does not
      mistake it for a gate.
- [ ] Nothing in this ticket adds a dependency on the application. Reading its source to learn
      its behaviour is allowed; importing its code, its state, or its API is not.
- [ ] `../llm_wiki` and `../minnarone/wiki/minnarone-wiki` are both left unmodified.

## Frontier
Ready, no blockers, and no longer on the critical path. Cheap enough to do early because its
output can save `LW-06` and `LW-10` a choice, and harmless to defer because nothing waits on
it.

## Step-by-Step Implementation Plan
1. Confirm the clone is at the version in use: `../llm_wiki` `package.json` reads `0.5.4` and
   the last commit is `release: v0.5.4`. Checkpoint: version pinned in the finding.
2. Read the file walk and ingest path for directory selection. Checkpoint: question 1 answered
   with a citation.
3. Read the page-type handling and the indexer entry point. Checkpoint: question 2 answered.
4. Read the front-matter parse and write path. Checkpoint: question 3 answered, with the list
   of surviving keys.
5. Record the finding and hand the front-matter answer to `LW-10` as advice.

## Testing Plan
Reading, not testing. Each claim cites a path and line at a named version.

Optional confirmation: open a throwaway wiki copy in the application and check that the source
reading predicted the behaviour. This is a nice-to-have and its absence does not weaken the
finding, because the source is the authority for what the code does.

Unavailable boundary: the application is third-party and may change. Every answer is scoped to
v0.5.4 and must say so. A claim about "the application" in general is not supported by this
ticket.

## Out of Scope
- Modifying, forking, or patching the application.
- Using the application's API, MCP server, or `.llm-wiki/` state for anything at runtime —
  forbidden by `LW-01`.
- Deciding the timeline's shape, which is `LW-06`'s and is no longer constrained by this.
- Deciding where `identity_key` and `source_digest` live, which is `LW-10`'s.
- Writing to the live minnarone wiki for any reason.
