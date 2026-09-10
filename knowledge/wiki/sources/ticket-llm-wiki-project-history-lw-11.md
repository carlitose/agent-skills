---
type: source
title: "Add the drift and coverage lint passes"
identity_key: ticket:llm-wiki-project-history/LW-11
identity_strength: stable
source_path: docs/tickets/llm-wiki-project-history/done/11-drift-and-coverage-lint.md
source_digest: sha256:6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-26
created_provenance: git-commit
disposition_changed: 2026-08-26
disposition_changed_provenance: git-rename
run_id: b9a2e62ae1cf4868
---

# Add the drift and coverage lint passes

Compiled from `docs/tickets/llm-wiki-project-history/done/11-drift-and-coverage-lint.md`. Identity is `ticket:llm-wiki-project-history/LW-11`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-26** via `git-commit`
- Disposition changed: **2026-08-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-project-history-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-project-history-lw-05]] — `ticket:llm-wiki-project-history/LW-05`
- Blocked by: [[sources/ticket-llm-wiki-project-history-lw-06]] — `ticket:llm-wiki-project-history/LW-06`
- Blocked by: [[sources/ticket-llm-wiki-project-history-lw-08]] — `ticket:llm-wiki-project-history/LW-08`
- Blocked by: [[sources/ticket-llm-wiki-project-history-lw-09]] — `ticket:llm-wiki-project-history/LW-09`
- Blocked by: [[sources/ticket-llm-wiki-project-history-lw-10]] — `ticket:llm-wiki-project-history/LW-10`

## Run

Completed under autopilot run `b9a2e62ae1cf4868`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-project-history-lw-11.md","payload_bytes":5894,"payload_sha256":"6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0"}],"payload_bytes":5894,"payload_sha256":"6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0","schema":1,"source_digest":"sha256:6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0","source_identity":"ticket:llm-wiki-project-history/LW-11","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5894,"payload_sha256":"6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0","schema":1,"source_digest":"sha256:6a7c1c43393df06e31195f6432fe9ed95c03ff48bf5f85e2bb7f1c183c9e58c0","source_identity":"ticket:llm-wiki-project-history/LW-11"} -->
```markdown
---
ticket_schema: 1
ticket_id: "LW-11"
execution_mode: AFK
blocked_by:
  - "LW-05"
  - "LW-06"
  - "LW-08"
  - "LW-09"
  - "LW-10"
---

# Add the drift and coverage lint passes

## Artifact Graph
- Artifact ID: `artifact:lw-11-drift-and-coverage-lint`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
The passes that catch what ingest cannot repair on its own. `lint_wiki.py` today has seven
passes — dead wikilinks, orphan pages, missing index entries, frequently-linked missing pages,
`log/` shape, `audit/` shape, and audit target resolution — and **not one of them looks at the
relationship between a wiki page and the repository artefact it came from**. That relationship
is exactly what rots.

The new passes:

| Pass | Detects |
|---|---|
| dangling source | a page's `sources:` path no longer exists, or has moved outside the configured globs |
| stale page | the artefact's current `source_digest` differs from the page's recorded one |
| un-ingested artefact | a file matches the globs and has no page |
| duplicate identity | two pages share one `identity_key` — the exact corruption `LW-10` exists to prevent |
| index drift | a page missing from `wiki/index.md`, or an index entry with no page |
| timeline coverage | a non-`unchanged` transition with no timeline event, or a ticket with no lifecycle record |
| provenance validity | a date whose rung is absent, unrecognised, or inconsistent with its value |
| stale session pointer | a transcript grew, moved, or vanished since its digest was written |

Two constraints on how these are written.

**Every pass must be able to fail.** The repository already recorded this lesson in
`docs/tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md`, whose plan required
verifying that reverting the fix turns the test red, on the grounds that "a fake that cannot
fail is worse than no fake". Several of the existing passes are currently in that state
because they inspect directories the chosen profile does not have. Each new pass gets a seeded
defect proving it fires.

**No pass may assume git.** `docs/` may be untracked and the host may not be a repository. A
missing git history is not drift; the provenance pass validates that a date's rung is coherent,
not that it came from git. Marking every `mtime` date as an issue would make the lint useless
on an untracked project, which is a supported configuration.

One judgement call to record rather than guess: `un-ingested artefact` will fire on everything
newly added to `docs/` between ingests, which is the normal steady state rather than a defect.
It should report as informational — "3 artefacts awaiting ingest" — while `duplicate identity`
and `stale page` are real errors. Conflating the two trains the reader to ignore the output.

## Acceptance Criteria
- [ ] All eight passes implemented, each with a seeded-defect test proving it fires and a
      clean-fixture test proving it does not fire spuriously.
- [ ] `duplicate identity` catches the concrete case: two pages generated for one ticket
      before and after its move into `done/`.
- [ ] `stale page` catches an artefact edited after ingest, and does **not** fire on a file
      whose mtime changed with identical content.
- [ ] Severity is distinguished: `un-ingested artefact` is informational; `duplicate identity`
      and `stale page` are errors.
- [ ] Every pass runs and reports correctly on a non-git host and on untracked `docs/`, with
      no pass treating absent git history as drift.
- [ ] Running the full lint over a freshly ingested wiki reports zero errors, so a clean state
      is actually reachable.
- [ ] For each reported issue the lint proposes a fix, per the skill's existing convention of
      propose, confirm, then apply.
- [ ] The pass count and their names are documented in `SKILL.md`, which currently advertises
      seven.

## Frontier
Dependency-blocked on `LW-05`, `LW-06`, `LW-08`, `LW-09` and `LW-10` — it is the last ticket in
the folder, and deliberately so: it lints artefacts that do not exist until those land.

## Step-by-Step Implementation Plan
1. Split out from `LW-09`'s retargeted `lint_wiki.py` so the new passes sit alongside the
   existing seven rather than replacing them. Checkpoint: the original seven still pass their
   tests.
2. Implement the four source-relationship passes. Checkpoint: each fires on its seeded defect.
3. Implement the three timeline and provenance passes. Checkpoint: each fires, and none fires
   on a legitimately unknown date.
4. Implement the session pointer pass. Checkpoint: appending to a fixture transcript makes it
   fire; a byte-identical file does not.
5. Add the severity distinction and update `SKILL.md`. Checkpoint: a clean wiki reports zero
   errors and an accurate informational count.

## Testing Plan
Automated: one seeded-defect fixture per pass plus one clean fixture, and a non-git and an
untracked variant of the clean fixture asserting zero errors in both. Stdlib `unittest`, per
repository convention.

Manual: run the full lint over this repository's real ingested wiki and read the output as a
user would — if it is noisy on a healthy wiki, the severity split is wrong.

Unavailable boundary: POSIX behaviour is unobserved here. The digest comparison is the
sensitive one — `WT-06` recorded that hashing raw bytes versus normalized text yields
different digests on a CRLF checkout, so the pass must use `LW-10`'s normalization decision
and not recompute it independently.

## Out of Scope
- Retargeting the existing seven passes, which is `LW-09`.
- Repairing drift automatically without confirmation.
- Any write to `docs/`.
- Semantic or content-quality checks on wiki prose.

```
