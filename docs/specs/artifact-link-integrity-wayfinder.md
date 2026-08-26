# Artifact Link Integrity

## Artifact Graph

- Artifact ID: `artifact:artifact-link-integrity-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [LI-01 repair-existing-drift](../tickets/artifact-link-integrity/done/01-repair-existing-drift.md)
- [LI-02 movers-repoint-inbound-links](../tickets/artifact-link-integrity/done/02-movers-repoint-inbound-links.md)
- [LI-03 decide-ag-05-disposition](../tickets/artifact-link-integrity/03-decide-ag-05-disposition.md)

## Type

Wayfinding spec

## Status

Active

## Destination

Two properties, one for the stock and one for the flow:

- **the stock**: every Markdown link under `docs/` that today points at a ticket's
  pre-disposition path is repointed once to the path the file actually occupies, and the
  genuinely dead remainder is reported rather than guessed at;
- **the flow**: when the runner moves a ticket between disposition directories, the documents
  that link to it are repointed **in the same commit**, so the drift never accumulates again.

Reader-side tolerance — resolving a stale link across `done/`, `canceled/`, `hold/` — remains
only where the source of the link is digest-frozen and cannot be repaired by anyone.

## Decisions So Far

- **The completion commit can carry a map repair; the "reader-only" claim was too broad.**
  Established by reading the delivery path, not by assumption. The order in
  `ticket-autopilot/scripts/autopilot/finalizer.py` is: `finalize_done` moves the ticket into
  `done/` and stages both paths (`os.replace` + `git add -A`); `_ensure_summary` writes and
  stages the `completion.json`; **then** `candidate_ref(...)` recomputes the delivery tree from
  the staging area; and `_ensure_commit` verifies `git write-tree` against **that** recomputed
  tree. The tree the commit is checked against is computed *after* the tree is mutated. What is
  frozen by digest is the **ticket body** (`ticket_digest`); a parent map is not digest-bound.
  So the diagnostic's sentence "the only place the mismatch can be resolved is in the reader"
  holds for a frozen ticket's own outbound links and does **not** hold for inbound links from
  maps: a staged map edit rides the same recomputation that the move and the summary already
  ride. Two commits demonstrate the shape in history: `787d796` ("ticket LW-12: complete")
  carries the disposition move, the completion sidecar, **and** 162 changed lines in
  `docs/specs/llm-wiki-project-history-wayfinder.md` in one tree.
- **The measured drift, with the false positives named.** 131 `.md` links under `docs/` do not
  resolve literally. 41 are Artifact Graph edges: 27 sourced inside tickets — digest-frozen, so
  reader tolerance is the only possible resolution, and `AG-03` was right for them — and 14
  sourced in maps and specs, which are writable. 4 of the 41 sit **inside fenced code blocks**
  in `docs/specs/artifact-graph-decision.md` (verified line by line): they are teaching
  examples, not links, and any scanner that does not skip fences miscounts them as dead. The
  remaining ~90 are prose links no checker reads today; they drift by the same mechanism.
- **`AG-05` as charted is wrong, and the proof is a no-op.** Its Defect 4 said the docs-only
  gate refuses the six graph-less specs because it blocks on the `legacy-artifact` *warning*.
  Measured with the gate already narrowed to errors only: the edit is still refused, by
  `missing-artifact-graph`, an **error** — the audit grandfathers an untouched file and demands
  the section the moment the file is edited, deliberately. Narrowing the gate unblocks nothing.
  Its other half — sharing the disposition-tolerant resolver with `docs_only` — would forgive
  repairable drift in writable files: the refusal is what got the llm-wiki map's seven stale
  links repaired. Tolerance belongs only where the source is frozen.
- **Prevention lives in the mover, not in more readers.** A reader that forgives hides the
  drift; a reader that refuses taxes every completion with a manual repair — observed twice,
  `LW-12` repairing seven links and leaving its own, `LW-13` repairing that one and leaving its
  own. Repointing at move time is the only shape where the ledger of who-links-what is settled
  in the same tree that moved the file.
- **The repair must skip fenced code and must not guess.** A link whose target exists under
  exactly one disposition directory is repointed; a link whose target exists nowhere is
  reported. The four fenced examples must survive any repair byte-identical.

## Not Yet Specified

- **Where the hold/cancel/reopen path commits.** `_change_ticket_disposition` in `cli.py`
  stages the ticket folder (`git add -A -- <tracked_relative>`) and records the receipt, but
  the commit timing on that path is not established the way the delivery path's is. `LI-02`
  must establish it before touching it, and must handle **reopen** — a move out of `done/` —
  in the reverse direction.
- **Whether the docs-only receipt needs a freshness note.** `revalidate_docs_only_receipt`
  runs before `finalize_done`, so the receipt binds a pre-move tree; the move and the summary
  already mutate the tree after it, and a map repoint is the same class of mutation. `LI-02`
  verifies rather than assumes that no revalidation rejects the enlarged commit.
- **Where the repair script lives.** The drift is ticket-lifecycle-owned, which argues for
  `ticket-autopilot/scripts/`; the ticket decides and records why.

## Out of Scope

- Rewriting any ticket body. The digest contract stands; links *inside* tickets stay stale and
  reader-tolerated forever, by design.
- Changing `artifact_audit`'s severities, its grandfathering, or its managed roots.
- A standing lint or counter for prose links under `docs/`. `LI-01` repairs the stock and
  `LI-02` stops the flow; a permanent checker is a separate, arguable feature.
- Any change under `llm-wiki/`. The wiki's own lint already reports its own drift.
- Executing `AG-05` as written. Its disposition is `LI-03`'s question.

## Frontier / Blocking Edges

- `LI-01` and `LI-02` are ready and independent; they share fixtures but no code.
- `LI-03` is HITL: cancelling a ticket requires the user's explicit authority, and run
  `42cf7d6d50a84f97` (AG-05 active at `implement`, never delivered) should be aborted by the
  same decision.

## Ticket Plan

| ID | Type | Mode | Blocked by | Title | Expected output |
|----|------|------|-----------|-------|-----------------|
| LI-01 | task | AFK | — | Repair the existing disposition drift once | A script that repoints every dead `docs/**/*.md` link whose target exists under exactly one disposition directory, skips fenced code, reports the remainder; the corrected documents; before/after counts recorded |
| LI-02 | task | AFK | — | Movers repoint inbound links in the same commit | `finalize_done` and `_change_ticket_disposition` repoint links in writable `docs/` documents when they move a ticket, staged into the same tree; the CandidateRef and digest checks proven intact by test; reopen handled in reverse |
| LI-03 | decision | HITL | — | Decide AG-05's disposition | The user's call on cancelling `AG-05` as superseded, the diagnostic's Defect 4 corrected with the measurement, and run `42cf7d6d50a84f97` aborted |

## Next Review

- After `LI-01`: the literal-resolution count under `docs/` should fall from 131 to the fenced
  examples plus whatever the report names as genuinely dead. If anything else remains, the
  script guessed or skipped.
- After `LI-02`: complete one real ticket and check its commit — the move, the sidecar, and
  the repointed inbound links must be one tree, and `_ensure_commit` must not have been
  weakened to allow it (the tree recomputation already allows it; if the ticket had to touch
  `_ensure_commit`, something is wrong).
- `LI-03` whenever the user is at the keyboard; nothing blocks on it.
