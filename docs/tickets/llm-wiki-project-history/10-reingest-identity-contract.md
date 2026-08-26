---
ticket_schema: 1
ticket_id: "LW-10"
execution_mode: AFK
blocked_by: []
---

# Decide the re-ingest identity and change contract

## Artifact Graph
- Artifact ID: `artifact:lw-10-reingest-identity-contract`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
The contract that makes the **second** ingest safe. The first ingest of a clean `docs/` tree
cannot fail this way; every ingest after it can, and the failure is silent.

The concrete defect this prevents. The page naming observed in the live wiki is
`wiki/sources/4-docs--4-adrs--43-2026-06-29-live-media-backpressure-boundary--1n8nezu.md`,
which encodes the **source path**. `docs/` is not static: in this repository every ticket
eventually moves, and three of the seven `windows-text-fidelity` tickets already have
(`docs/tickets/windows-text-fidelity/01-body-round-trip-fidelity.md` →
`.../done/01-body-round-trip-fidelity.md`, commit `437b287`). A path-derived page name means
that move mints a *second* page for the same artefact, so the wiki ends up with two pages,
two index entries, and two contradictory lifecycle records — and `lint_wiki.py` as it stands
has no pass that would notice.

Two ingredients are already available in the repository and should be used rather than
invented:

- **A stable identity key exists for the two artefact kinds that matter.** Tickets carry
  `ticket_id` in Envelope v1 front matter (`"WT-04"`, `"TK-01"`); specs carry `Artifact ID`
  in their `## Artifact Graph` section (`artifact:windows-text-fidelity-wayfinder`). Both
  survive renames and disposition moves. `docs/research/*.md` and `docs/prototypes/<slug>/`
  carry neither and need a decided fallback.
- **Content digests are the repository's existing idiom for change detection.** All 36
  `*.completion.json` sidecars carry a `ticket_digest`. A `source_digest` per page makes
  re-ingest a comparison instead of a re-read, and — unlike git — it works when `docs/` is
  untracked, when the host is not a repository, and when a file is touched without being
  changed.

The five transitions to decide, each with a defined behaviour:

| Transition | Question to settle |
|---|---|
| `unchanged` | Skip without touching `updated`, so a no-op ingest produces a zero-byte diff |
| `new` | Create the page, index it, and record which event on the timeline |
| `changed` | Rewrite in place — and whether an amended spec **appends** a timeline event or silently absorbs the edit |
| `moved` | Same page identity, updated `sources:` provenance, a lifecycle event, and provably no duplicate |
| `missing` | Tombstone the page or delete it, and what the timeline says about an artefact that no longer exists |

The `changed`-versus-`amended` question is the sharp one. A timeline that silently absorbs
edits cannot be trusted about the past, which defeats the reason the axis exists.

## Acceptance Criteria
- [ ] `identity_key` is defined per artefact kind: `ticket_id` for tickets, `Artifact ID` for
      specs, and a decided rule for research and prototypes — or an explicit statement that
      they are outside the incremental contract.
- [ ] The digest is fully specified: algorithm, what is hashed, and whether line endings are
      normalized first. On this repository the answer matters — `WT-06` records that hashing
      raw bytes versus normalized text produces different digests on Windows for the same
      logical content.
- [ ] All five transitions have a written behaviour, including which timeline event each one
      emits, or explicitly none.
- [ ] The contract states how a `moved` artefact is distinguished from a `missing` plus `new`
      pair when both happen in one ingest.
- [ ] The contract states where `identity_key` and `source_digest` are stored, consistent
      with `LW-02`'s finding on whether the app preserves unknown front-matter keys. If that
      finding is hostile, a sidecar location is chosen instead.
- [ ] The contract is written so `LW-05` can implement it and `LW-11` can lint it without
      further decisions.

## Frontier
Ready, no blockers, and the cheapest ticket on the frontier. `LW-05` must not start before
it lands: the cost of getting this wrong is not a failed run but a quietly corrupted wiki.

## Step-by-Step Implementation Plan
1. Inventory identity keys across the real corpus: every file matched by the default globs,
   and whether it yields a `ticket_id`, an `Artifact ID`, or neither. Checkpoint: a count
   per kind, so the fallback is sized against reality rather than guessed.
2. Settle the digest definition, reusing `ticket_source_digest`'s normalization decision if
   it applies. Checkpoint: one written rule, with the CRLF case named.
3. Write the five transition behaviours. Checkpoint: each names its timeline event or states
   none.
4. Settle the storage location against `LW-02`'s front-matter finding, with a sidecar
   fallback. Checkpoint: one location, and the reason.
5. Record the contract. Checkpoint: `LW-05` and `LW-11` are implementable from it alone.

## Testing Plan
The output is a contract, so verification is by construction: for each of the five
transitions, write down the concrete fixture that `LW-05` will have to pass — starting with
the real one, moving a fixture ticket into `done/` and re-ingesting, which must update one
page and create zero.

No automated test in this ticket. If a rule cannot be expressed as a fixture here, it is not
specific enough to implement.

## Out of Scope
- Implementing the ops. `LW-05` implements ingest; `LW-11` implements the lint passes.
- Changing Ticket Envelope v1 or writing anything back into `docs/`.
- Deciding date provenance, which is `LW-04`. This ticket decides *whether* an event is
  emitted; `LW-04` decides what date it carries.
