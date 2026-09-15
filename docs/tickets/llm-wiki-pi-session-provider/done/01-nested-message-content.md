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
