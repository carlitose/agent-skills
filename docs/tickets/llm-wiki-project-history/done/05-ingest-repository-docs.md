---
ticket_schema: 1
ticket_id: "LW-05"
execution_mode: AFK
blocked_by:
  - "LW-03"
  - "LW-04"
  - "LW-10"
---

# Ingest repository docs as wiki source pages

## Artifact Graph
- Artifact ID: `artifact:lw-05-ingest-repository-docs`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
An `ingest-docs` op that compiles the project's own `docs/` tree into wiki pages, and stays
correct on the tenth run as well as the first.

The corpus in this repository, as it actually stands: 14 files in `docs/specs/`, 8 ticket
folders in `docs/tickets/` with tickets in the root plus `done/` and `canceled/`
subdirectories, 1 file in `docs/research/`, and 2 folders in `docs/prototypes/`. Plus 36
`*.completion.json` sidecars beside done tickets.

The pattern to formalise already exists in the live wiki rather than being invented here:
`wiki/sources/4-docs--4-adrs--43-2026-06-29-live-media-backpressure-boundary--1n8nezu.md`
carries `type: source`, `sources: ["docs/adrs/..."]`, `related: [...]`, and `created` /
`updated`. What this ticket adds is the graph, the dates, and idempotence.

**The graph comes for free and must not be re-invented.** These artefacts already describe
their own edges:

- specs carry `## Artifact Graph` with an `Artifact ID` and either `Standalone: true` or a
  `Parent`, plus `Children` links;
- tickets carry `Artifact ID`, `Role: ticket`, and a `Parent` link to their spec;
- ticket envelopes carry `blocked_by` as an ordered list of ticket ids.

Materialising those as wikilinks means the wiki graph *is* the project graph. A hand-built
parallel set of `related:` guesses would drift from it immediately.

**Provenance and dates.** Each page records its source path, its `identity_key` and
`source_digest` per `LW-10`, and its dates from `LW-04`'s ladder with the rung that produced
each one. Disposition comes from the artefact's location, using the vocabulary already fixed
by `docs/specs/ticket-lifecycle-disposition-decision.md`: `done/` → `completed`,
`canceled/` → `canceled`, `hold/` → `on-hold`. Where a `*.completion.json` sits beside a done
ticket, its `run_id` is carried onto the page as the ticket-to-run edge — it has no date field
and must not be read as one.

**Idempotence is the acceptance bar, not a nicety.** The naming convention observed in the
live wiki encodes the source path, so without `LW-10`'s identity contract the first ticket to
reach `done/` mints a second page for the same artefact. Three tickets in
`docs/tickets/windows-text-fidelity/` have already made that move.

Parsing note: ticket front matter must be read through the canonical contract, not by
hand-parsing YAML. `ticket-parse` from `ticket-autopilot` is the single owner of envelope
semantics, and `blocked_by` must never be inferred from a `## Blocked By` heading.

## Acceptance Criteria
- [ ] Every artefact matched by `LW-03`'s globs produces exactly one page; run twice over an
      unchanged tree and the second run writes nothing at all.
- [ ] Moving a fixture ticket into `done/` and re-ingesting updates one page and creates
      zero. This is the defect this ticket exists to prevent, so the test must be shown to
      fail without `LW-10`'s identity key.
- [ ] `Artifact ID`, `Parent` and `blocked_by` are materialised as wikilinks, and every
      resulting link resolves to a page that exists.
- [ ] `blocked_by` is obtained via `ticket-parse`, never by reading a heading.
- [ ] Each page records source path, `identity_key`, `source_digest`, disposition, and dates
      with per-date provenance.
- [ ] `run_id` from an adjacent `*.completion.json` appears on the page; no date is derived
      from that file.
- [ ] Research and prototype artefacts are handled per `LW-10`'s fallback, or excluded by an
      explicit written rule rather than by accident.
- [ ] Ingest never writes to `docs/`. Verified by running against a read-only copy.
- [ ] `wiki/index.md` lists every new page exactly once, which is what the existing lint
      already enforces.

## Frontier
Dependency-blocked on `LW-03`, `LW-04` and `LW-10`. Of the three, `LW-10` is the one that must
not be skipped: without it this op is actively harmful on its second run.

## Step-by-Step Implementation Plan
1. Discover and classify artefacts through `LW-03`'s globs and resolver. Checkpoint: the real
   counts above are reproduced — 14 specs, 8 ticket folders, 1 research, 2 prototypes.
2. Parse tickets through `ticket-parse` and specs through their `## Artifact Graph` section.
   Checkpoint: `blocked_by` for `windows-text-fidelity` matches the envelopes on disk.
3. Emit pages with provenance, digest and dates. Checkpoint: a spot-checked page carries the
   three verified dates from `LW-04`.
4. Materialise the graph as wikilinks. Checkpoint: zero dead wikilinks under the existing
   lint pass.
5. Implement the five transitions from `LW-10`. Checkpoint: the no-op run writes nothing; the
   disposition-move run updates one page and creates none.

## Testing Plan
Automated: a fixture repository containing one spec, three tickets across root, `done/` and
`canceled/`, one completion sidecar, one research file; assertions for each of the five
transitions, and a double-run zero-write assertion. Stdlib `unittest`, per repository
convention.

Manual: ingest this repository's real `docs/` into a scratch wiki, then run the existing
`lint_wiki.py` and confirm no dead links and no missing index entries.

Unavailable boundaries: whether the app renders the resulting pages is `LW-02`'s observation,
not this ticket's claim. If `LW-02` found that unknown front-matter keys are stripped, the
digest and identity fields live wherever `LW-10` relocated them, and this ticket must not
quietly put them back in front matter.

## Out of Scope
- The timeline axis, which is `LW-06`.
- Sessions, which are `LW-08`.
- New lint passes, which are `LW-11`.
- Any write to `docs/`, to ticket front matter, or to Envelope v1.
- Summarising artefact content beyond what a source page needs; this is provenance and
  structure, not a rewrite of every spec.
