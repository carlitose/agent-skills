---
type: source
title: "Close the weak-key artefacts as a decision, not an open question"
identity_key: ticket:llm-wiki-project-history/LW-13
identity_strength: stable
source_path: docs/tickets/llm-wiki-project-history/done/13-close-weak-key-artefacts.md
source_digest: sha256:d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-26
created_provenance: git-commit
disposition_changed: 2026-08-26
disposition_changed_provenance: git-rename
run_id: 0b94013bf836437c
---

# Close the weak-key artefacts as a decision, not an open question

Compiled from `docs/tickets/llm-wiki-project-history/done/13-close-weak-key-artefacts.md`. Identity is `ticket:llm-wiki-project-history/LW-13`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-26** via `git-commit`
- Disposition changed: **2026-08-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-project-history-wayfinder]]

## Run

Completed under autopilot run `0b94013bf836437c`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-project-history-lw-13.md","payload_bytes":4746,"payload_sha256":"d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b"}],"payload_bytes":4746,"payload_sha256":"d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b","schema":1,"source_digest":"sha256:d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b","source_identity":"ticket:llm-wiki-project-history/LW-13","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4746,"payload_sha256":"d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b","schema":1,"source_digest":"sha256:d9daf2c93453177d8e5aed1abeead7173b2eab2a689791f4a2f3c525cfedff9b","source_identity":"ticket:llm-wiki-project-history/LW-13"} -->
````markdown
---
ticket_schema: 1
ticket_id: "LW-13"
execution_mode: AFK
blocked_by: []
---

# Close the weak-key artefacts as a decision, not an open question

## Artifact Graph
- Artifact ID: `artifact:lw-13-close-weak-key-artefacts`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
A decision where the map currently holds an open question. The user settled it on 2026-08-26:
the eight artefacts that carry no `## Artifact Graph` **stay as they are**. Nothing is added to
them, and nothing is moved.

The eight, verified by grepping every `docs/**/*.md` outside `docs/tickets/` for the heading:

```
docs/prototypes/bounded-ticket-autopilot-leaves/NOTES.md
docs/prototypes/cross-host-context-rollover/NOTES.md
docs/research/mattpocock-skills-parity.md
docs/specs/bounded-ticket-autopilot-leaf-protocol.md
docs/specs/candidate-invalidation-decision.md
docs/specs/ticket-autopilot-autonomous-stacked-delivery.md
docs/specs/ticket-autopilot-delivery-merge-wayfinder.md
docs/specs/ticket-lifecycle-disposition-decision.md
```

Two other options were considered and rejected, and the reasons belong in the record because
both look reasonable until you measure them.

**Adding an `## Artifact Graph` to each** was the repair the map proposed. Rejected by the user.

**Moving them into a `done/` directory** was the second reading of the instruction. Rejected on
evidence: `done/` exists in this repository only under `docs/tickets/<family>/`, so it would
invent a convention for specs that does not exist; the eight carry **38 inbound references**
between them, from `docs/` and from `ticket-autopilot/`, every one of which would break; and
because these eight are precisely the artefacts keyed on a path, moving them is the one
operation that mints a second wiki page instead of updating the first. The move would perform
the failure the map warns about.

So the consequence is accepted rather than repaired: the eight pages key on a path, they lose
their identity if they ever move, and `lint_wiki.py` reports them as eight `orphan-pages`
warnings on every run. Those eight warnings are the **steady state**, not a defect awaiting a
fix, and the map must say so — otherwise the next reader reopens a closed question.

Three places in the map are wrong for as long as this is filed as unknown:

- `## Not Yet Specified` lists it as an open item needing its own ticket;
- `## Next Review` tells the reader to open that ticket;
- `## Decisions So Far` does not record the decision at all.

## Acceptance Criteria
- [ ] The weak-key item is gone from `## Not Yet Specified`, which then holds exactly one open
      item: where this repository's wiki instance lives.
- [ ] `## Decisions So Far` records the decision, both rejected options, and the measured reason
      each was rejected — including the 38 inbound references and the duplicate-page effect.
- [ ] `## Next Review` no longer tells the reader to open a ticket for the eight.
- [ ] The eight warnings are named as the expected steady state wherever the map states the
      lint's output, so a future reader does not read them as a regression.
- [ ] No file other than the map changes. The eight artefacts are not touched.
- [ ] `artifact-audit` totals are unchanged: 8 errors, 0 warnings, 35 unreferenced.
- [ ] Every link in the map still resolves literally.

## Frontier
Ready. The decision is made; this only records it.

## Step-by-Step Implementation Plan
1. Record the `artifact-audit` totals and the map's link count. Checkpoint: a baseline.
2. Move the item from `## Not Yet Specified` into `## Decisions So Far`, carrying the decision
   and both rejected options. Checkpoint: one open item remains.
3. Correct the `## Next Review` line. Checkpoint: no instruction to open a ticket that will
   never be opened.
4. Re-run the baseline checks. Checkpoint: totals match step 1.

## Testing Plan
Automated: `artifact-audit --json` before and after; a literal existence check on every link
target in the map; `ticket-list --json` for diagnostics.

Manual: confirm the eight files are untouched with `git status`, and read `## Not Yet Specified`
to confirm one item remains.

Unavailable boundary: none. This is a documentation change with no runtime behaviour.

## Out of Scope
- Adding an `## Artifact Graph` to any of the eight. That is what the user rejected.
- Moving any of the eight. That is the other rejected option.
- Any change under `llm-wiki/`. The lint already reports these correctly, as warnings.
- The `docs_only.py` link-resolution asymmetry. Still its own ticket, still unopened.

````
