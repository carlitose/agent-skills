---
type: source
title: "Decide the audit surface for the LLM-Wiki app profile"
identity_key: ticket:llm-wiki-project-history/LW-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-project-history/done/01-decide-audit-surface.md
source_digest: sha256:351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-26
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Decide the audit surface for the LLM-Wiki app profile

Compiled from `docs/tickets/llm-wiki-project-history/done/01-decide-audit-surface.md`. Identity is `ticket:llm-wiki-project-history/LW-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-26** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-project-history-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-project-history-lw-01.md","payload_bytes":6098,"payload_sha256":"351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc"}],"payload_bytes":6098,"payload_sha256":"351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc","schema":1,"source_digest":"sha256:351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc","source_identity":"ticket:llm-wiki-project-history/LW-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6098,"payload_sha256":"351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc","schema":1,"source_digest":"sha256:351da1231321edce2af1ca872f9fb42500c84a0ed798dee475bdb30c462a98bc","source_identity":"ticket:llm-wiki-project-history/LW-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "LW-01"
execution_mode: HITL
blocked_by: []
---

# Decide the audit surface for the LLM-Wiki app profile

## Artifact Graph
- Artifact ID: `artifact:lw-01-decide-audit-surface`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
A recorded decision, not code. The map selected the LLM-Wiki app profile as the target
layout, and that profile has nowhere to put human feedback.

The evidence on both sides:

- **The skill assumes `audit/` exists.** `llm-wiki/SKILL.md` makes it one of five core
  operations and one of four core principles ("Audit is the human feedback surface").
  `llm-wiki/references/audit-guide.md` defines the file format and the
  `anchor_before`/`anchor_text`/`anchor_after` triple. `llm-wiki/scripts/lint_wiki.py`
  carries two dedicated passes over it — malformed front matter in `audit/*.md`, and audit
  target resolution — and `llm-wiki/scripts/audit_review.py` exists for nothing else.
- **The profile in live use does not have it.** `../minnarone/wiki/minnarone-wiki` has
  `purpose.md`, `schema.md`, `raw/{sources,assets}/`, `wiki/{comparisons,concepts,entities,
  queries,sources,synthesis}/` and `.llm-wiki/{chats,lancedb,page-history}/`. Verified
  absent: `log/`, `audit/`, `CLAUDE.md`. Its `schema.md` documents a `## Contradiction
  Handling` workflow that routes disagreement into query and synthesis pages instead.
- **The two writers are not in this repository.** The Obsidian plugin and the web viewer
  that produce audit files live in the other copy of the skill,
  `~/Downloads/llm-wiki-skill-main/{plugins/obsidian-audit,web}/`, sharing one anchor
  algorithm. This repository's copy has neither, so nothing here currently writes an audit
  file at all.
- **The app may already own this surface.** `.llm-wiki/` exists in the live wiki, and the
  portable bundle ships an MCP server against a local `/api/v1`. Whether the app has its
  own feedback channel is unknown and is worth one look before deciding.

At least three outcomes are defensible, and which one is chosen changes what `LW-09` has to
do to `lint_wiki.py`:

1. The app profile gains `audit/` and `audit/resolved/`, and the skill's audit op works
   unchanged in both profiles.
2. The audit op becomes profile-conditional: present in the documented profile, replaced in
   the app profile by the `schema.md` contradiction-handling workflow.
3. The audit op is dropped for the app profile, and `audit_review.py` plus the two lint
   passes become documented as profile-scoped.

This ticket is `HITL` because it is a genuine human decision about a human workflow: how
the user wants to file a correction on an AI-written page. It cannot be derived from the code.

**Outcome.** Decided on 2026-08-26 through `grilling` and recorded in
[llm-wiki-app-independence-decision.md](../../../specs/llm-wiki-app-independence-decision.md).
The chosen outcome is none of the three listed above, because the interview surfaced a fourth
constraint: the skill must be **independent of the application** at runtime and in its data.
From that, `audit/` is kept as the human-to-agent channel and the skill targets **one layout**
rather than two profiles. The application's own channels were found to run the opposite way —
74 agent-written review items, none resolved, and an MCP server with no write tool — so it
could not have supplied this surface.

## Acceptance Criteria
- [x] `grilling` is run on the decision before anything is recorded, one question at a time.
- [x] A decision record exists under `docs/specs/` produced through `to-spec`, naming the
      chosen outcome and the rejected alternatives with their reasons.
- [x] The decision states explicitly what happens to `audit_review.py` and to the two
      `audit/` passes in `lint_wiki.py`.
- [x] The decision states whether the skill keeps two named profiles or retargets wholesale
      to one, because `LW-09` cannot be scoped without that answer.
- [x] The map's `## Not Yet Specified` entry for the audit surface is removed and the
      decision is linked from `## Decisions So Far`.

## Frontier
Ready, and blocked on a human. It is the only `HITL` ticket in the folder. `LW-09` cannot
start until it lands.

## Step-by-Step Implementation Plan
1. Check whether the app itself offers a feedback channel: look for a comment or annotation
   surface in `.llm-wiki/` and in the `mcp-server` client against `/api/v1`. Checkpoint: a
   one-line finding, either way, recorded in the decision.
2. Run `grilling` on the three outcomes. Checkpoint: one confirmed choice.
3. Record it through `to-spec`. Checkpoint: a decision spec with an Artifact ID and a
   reciprocal edge from this map.
4. Update the map. Checkpoint: the unknown is deleted rather than left stale.

## Testing Plan
No automated test; the output is a document. Manual verification: the decision answers all
four questions in the acceptance criteria, and a reader who has not seen this session can
tell from it alone where a correction gets filed.

Step 1 was resolved by reading, not by running. The assumption that the application could only
be observed through its GUI was wrong: the v0.5.4 source is cloned at `../llm_wiki`, and the
review channel's direction is established by `src/components/review/review-view.tsx` calling
only `resolveItem` and `dismissItem`, and by the ingest LLM writing items through a
`---REVIEW: <type> | <title>---` marker
(`src/lib/ingest-source-path-collision.test.ts:434,467`).

Remaining unobserved: the application was never launched, so nothing here claims what its GUI
displays. Under the independence decision that no longer matters to any acceptance criterion.

## Out of Scope
- Implementing whatever is decided. That is `LW-09` and, if a new writer is needed, a
  ticket that does not exist yet.
- Porting the Obsidian plugin or the web viewer into this repository.
- Changing the anchor algorithm.

```
