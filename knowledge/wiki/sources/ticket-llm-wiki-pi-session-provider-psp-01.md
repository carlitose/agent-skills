---
type: source
title: "PSP-01 — Read session text from nested message content"
identity_key: ticket:llm-wiki-pi-session-provider/PSP-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-pi-session-provider/done/01-nested-message-content.md
source_digest: sha256:6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-15
created_provenance: git-commit
disposition_changed: 2026-09-15
disposition_changed_provenance: git-rename
run_id: c6b2211177154684
---

# PSP-01 — Read session text from nested message content

Compiled from `docs/tickets/llm-wiki-pi-session-provider/done/01-nested-message-content.md`. Identity is `ticket:llm-wiki-pi-session-provider/PSP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-15** via `git-commit`
- Disposition changed: **2026-09-15** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-pi-session-provider]]

## Run

Completed under autopilot run `c6b2211177154684`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-pi-session-provider-psp-01.md","payload_bytes":3785,"payload_sha256":"6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499"}],"payload_bytes":3785,"payload_sha256":"6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499","schema":1,"source_digest":"sha256:6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3785,"payload_sha256":"6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499","schema":1,"source_digest":"sha256:6f7c80462f8944da75f1a600b364528034ba5cb153749290d485e2d115bf1499","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-01"} -->
````markdown
---
ticket_schema: 1
ticket_id: "PSP-01"
execution_mode: AFK
blocked_by: []
---

# PSP-01 — Read session text from nested message content

## Artifact Graph
- Artifact ID: `ticket:llm-wiki-pi-session-provider:PSP-01`
- Role: `ticket`
- Parent: [LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md)

## Parent Spec
[LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md), especially "Layer 2 — a Pi digest would be empty", "Text extraction", and "Semantic invariants".

## What to Build

`session_ingest._text_of()` probes `text`, `content`, `message`, and `summary`, and accepts a string, a list of strings or `{"text": …}` blocks, or a dict whose `text`/`content` is a **string**. It does not descend into a dict whose `content` is a **list**, which is exactly the shape Pi writes:

```json
{"type":"message","message":{"role":"user","content":[{"type":"text","text":"…"}]}}
```

Measured consequence on a real 174-record Pi transcript: zero records yield any text. A digest built from it would report no files, no decisions, and no ticket mentions — indistinguishable from a session that did nothing.

Make the extractor descend one further level, reusing the list walk it already has, so a dict-valued key whose `content` is a list contributes its string items and `{"text": …}` blocks. Non-text blocks stay undecoded, exactly as attachments do today. The change is provider-neutral: it names no provider and adds no provider branch.

This ticket does not add Pi discovery. It makes the extractor capable of reading a Pi-shaped record, which every later slice depends on and which no later slice should have to re-litigate.

## Acceptance Criteria
- [ ] A record of the nested shape above yields its text through `_text_of`, including the multi-block case and the mixed string/block case.
- [ ] Claude Code and Codex digests are byte-identical to their pre-change output for the same fixtures; the comparison is asserted, not described.
- [ ] A non-text block (no `text` key) contributes nothing and raises nothing.
- [ ] A dict whose `content` is a string keeps its current behavior.
- [ ] Depth stays bounded: the walk does not recurse arbitrarily deep, and a deeply nested fixture proves where it stops.
- [ ] Extracted-text length for a committed Pi-shaped fixture is asserted as non-zero with an exact expected value.

## Frontier

Ready; AFK. No dependency and no human decision. Whether Pi's `custom_message` and `custom` records should also contribute text is spec question Q3 and is explicitly out of scope here: only the `message` shape is addressed.

## Step-by-Step Implementation Plan
1. Add a RED unit test with a Pi-shaped record asserting non-empty extracted text, plus a regression test pinning current Claude and Codex extraction output.
2. Extract the existing list walk into a single reusable step and apply it to a dict-valued key whose `content` is a list, keeping the current string cases untouched.
3. Add fixtures for the non-text block, the mixed block list, and the bounded-depth case.
4. Run the focused suite, confirm the pinned Claude/Codex output is unchanged, and simplify only after GREEN.

## Testing Plan

Automated unit tests over `_text_of` for every record shape named above. Automated regression asserting byte-identical digests for existing Claude and Codex fixtures. No live transcript is read: the fixtures are committed and small. Wall-time and large-file behavior are not claimed here; they belong to PSP-03.

## Out of Scope
- Pi discovery, identity, or record-kind mapping (PSP-02).
- Large-transcript behavior and measurement (PSP-03).
- Widening `TICKET_REFERENCE`; the ticket-id pattern is unchanged for every provider.
- Any change to the pointer contract or to digest wording.

````
