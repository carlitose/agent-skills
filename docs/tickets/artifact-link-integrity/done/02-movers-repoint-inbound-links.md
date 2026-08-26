---
ticket_schema: 1
ticket_id: "LI-02"
execution_mode: AFK
blocked_by: []
---

# Movers repoint inbound links in the same commit

## Artifact Graph
- Artifact ID: `artifact:li-02-movers-repoint-inbound-links`
- Role: `ticket`
- Parent: [artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## Parent Spec
[artifact-link-integrity-wayfinder.md](../../specs/artifact-link-integrity-wayfinder.md)

## What to Build
The flow fix: when the runner moves a ticket between disposition directories, every Markdown
link in a **writable** `docs/` document that names the old path is repointed to the new one,
staged into **the same tree** as the move. The drift then never accumulates, instead of being
repaired after the fact by whoever edits the map next — observed twice, `LW-12` repairing seven
links and leaving its own, `LW-13` repairing that one and leaving its own.

The feasibility fact this ticket stands on, established by reading `finalizer.py` and recorded
in the parent map: the delivery path already mutates the tree **after** verification —
`finalize_done` moves and stages, `_ensure_summary` writes and stages — and only **then** is
the delivery `candidate_ref` computed and checked by `_ensure_commit`. A staged map repoint
rides the same recomputation. What is digest-frozen is the ticket body, never the documents
that link to it. Commit `787d796` already carries a move, a sidecar, and 162 changed map lines
in one tree.

Two movers, one rule:

- **`finalize_done`** (completion): after `os.replace`, rewrite links to the moved path in
  writable `docs/**/*.md` and extend the existing `git add` to cover them.
- **`_change_ticket_disposition`** (hold / cancel / reopen, in `cli.py`): same rewrite around
  `transition_ticket_source`, including the **reverse** direction — a reopen moves the file
  out of `done/`, and links previously repointed there must follow it back.

The rewrite is textual and exact: a link is repointed only when its normalized repository
target equals the moved file's old repository path. Fenced code blocks are skipped. Sources
that are themselves tickets are never rewritten — their bytes are frozen by the digest that
`transition_ticket_source` verifies on both sides of every move.

## Acceptance Criteria
- [ ] Completing a ticket whose parent map links it produces **one commit** containing the
      move, the `completion.json`, and the repointed map link; verified end to end on a fixture
      run, not argued from the code.
- [ ] `_ensure_commit` is not weakened. The tree recomputation already accommodates the repoint;
      if the guard had to change, the approach is wrong and the ticket stops.
- [ ] Hold and cancel repoint in the forward direction; reopen repoints in reverse. Each has a
      fixture.
- [ ] A link inside a ticket body is never rewritten, and the digest checks in
      `transition_ticket_source` still pass on both sides of every fixture move.
- [ ] A link inside a fenced code block is never rewritten.
- [ ] Documents outside the repository worktree, and documents not matching the moved path, are
      byte-identical after a move.
- [ ] The docs-only receipt revalidation ordering is verified, not assumed: a docs-only ticket
      completed under the new mover reaches `integrated` on a fixture.
- [ ] The commit-timing question on the hold/cancel path is answered in the ticket's own record:
      where the staged repoint lands, and what happens if nothing commits it.
- [ ] The full repository suite stays green, and `test_ticket_lifecycle.py`, `test_kernel.py`
      and `test_cli.py` gain the fixtures above where each behaviour lives.

## Frontier
Ready. Independent of `LI-01` — the stock repair and the flow fix touch different code — and
of `LI-03`.

## Step-by-Step Implementation Plan
1. Establish the hold/cancel/reopen commit timing by reading `_change_ticket_disposition`'s
   callers and one real receipt. Checkpoint: written down, with the file and line.
2. Implement the repoint as one function taking (old repo path, new repo path, worktree),
   returning the changed files; unit-test it in isolation, fences and ticket-exclusion
   included. Checkpoint: fixtures green.
3. Wire it into `finalize_done` before the existing `git add`, extending the staged paths.
   Checkpoint: the end-to-end completion fixture produces one tree with all three changes and
   `_ensure_commit` passes unmodified.
4. Wire it into `_change_ticket_disposition`, both directions. Checkpoint: hold, cancel and
   reopen fixtures.
5. Full suite. Checkpoint: matches the pre-ticket baseline.

## Testing Plan
Automated: stdlib `unittest`. Unit fixtures for the repoint function; kernel/CLI fixtures for
the three transitions; one delivery-path fixture completing a ticket whose parent map links it
and asserting the single-tree property plus an unmodified `_ensure_commit`.

Manual: complete one real ticket after merge and read its commit with `git show --stat`.

Unavailable boundary: POSIX unobserved. The repoint is byte-level on files Git already tracks,
so the CRLF question is confined to reading and writing with the repository's own conventions —
follow `WT-06`: normalize on read, preserve the file's existing line endings on write.

## Out of Scope
- The one-time stock repair (`LI-01`).
- Rewriting ticket bodies, ever.
- Any reader-side change: `artifact_audit`'s tolerance stays exactly as `AG-03` built it, and
  `docs_only`'s literal check stays exactly as it is — after this ticket the literal check is
  *correct* on writable documents because the mover keeps them true.
- A standing checker for prose links.
