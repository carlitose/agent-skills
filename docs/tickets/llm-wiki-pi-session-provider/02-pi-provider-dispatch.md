---
ticket_schema: 1
ticket_id: "PSP-02"
execution_mode: AFK
blocked_by:
  - "PSP-01"
---

# PSP-02 — Compile Pi sessions through binding-declared providers

## Artifact Graph
- Artifact ID: `ticket:llm-wiki-pi-session-provider:PSP-02`
- Role: `ticket`
- Parent: [LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md)

## Parent Spec
[LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md), especially "Layer 1 — discovery", "Layer 3 — record-kind vocabulary", "Provider dispatch", "Pi adapter", and "Failure modes".

## What to Build

Two coupled changes that are one behavior: a wiki compiles the providers its binding names, and Pi becomes one of them.

**Dispatch.** `session_discovery.py` and `session_ingest.py` take their provider set from the binding's `session_providers`. `project_binding.py` already validates the field and nobody reads it, so a binding listing `"pi"` today changes nothing. After this ticket the field decides. An unknown provider name is an error naming the value — a typo must not look like an empty store. A binding listing `claude-code` and `codex` produces exactly today's output.

**Pi adapter.** Discover `~/.pi/agent/sessions/<mangled>/*.jsonl` and `~/.pi/agent/sessions/_oversized-backup/*.jsonl`. Attribute a transcript by the `cwd` recorded in its first `type: "session"` record, compared the way Codex `cwd` is compared today; the mangled directory name is a prefilter only. That is what makes `_oversized-backup/` work without a special case: Pi rotates large transcripts there and they lose their project directory while keeping their `cwd`.

Session id is the UUID after `_` in `<iso>_<uuid>.jsonl`, which must equal the `id` field of that first record; a disagreement is unresolved, not a silent preference. Map the record-kind vocabulary per provider: Pi's `session` carries `cwd` where Codex uses `session_meta`, and Pi's `compaction` is the compaction counter where Codex uses `compacted`.

## Acceptance Criteria
- [ ] A wiki whose binding lists `pi` compiles one digest and one pointer per Pi transcript belonging to its project, including transcripts found in `_oversized-backup/`.
- [ ] A wiki whose binding omits `pi` compiles no Pi session and does not report the Pi store as empty; a binding naming an unknown provider fails with the offending value.
- [ ] Claude and Codex digests and pointers are byte-identical to their pre-change output.
- [ ] A transcript with no resolvable `cwd`, or whose filename UUID disagrees with the in-file `id`, is reported as unresolved and ingested nowhere.
- [ ] A Pi transcript whose `cwd` names a different project is not attributed to this one, proven with a fixture that sits in this project's directory.
- [ ] Pi digests carry non-zero extracted text, with `cwd` and compaction counts populated from Pi's own kind spellings.
- [ ] Re-running with no new records writes nothing; `lint_wiki.py` reports no new errors or warnings.
- [ ] An absent Pi store reports zero transcripts rather than failing.

## Frontier

Dependency-blocked by PSP-01: without the nested-content extractor every Pi digest would be empty, and the acceptance criterion on non-zero extracted text could not pass.

Spec Q1 (is `~/.pi/agent/sessions` relocatable by configuration?) must be resolved from Pi's own configuration during implementation rather than assumed: if the store is configurable, honor the configuration; if it is not, hardcode the root and say so in the code. Spec Q2 (is the `--…--` directory wrapper stable?) does not gate this ticket, because the wrapper is only a prefilter and `cwd` decides.

## Step-by-Step Implementation Plan
1. Add fixture stores for all three providers, including a Pi transcript in a project directory, one in `_oversized-backup/` belonging to the project, one belonging to a different project, and one with no `session` record.
2. Thread `session_providers` from the binding through discovery and ingest, with an explicit error for an unknown name; pin Claude/Codex output as a regression first.
3. Add the Pi discovery adapter with `cwd` attribution and unresolved reporting.
4. Add the per-provider kind mapping and the session-id rule, including the filename/`id` disagreement case.
5. Resolve Q1 against Pi's configuration and implement whichever answer holds.
6. Run the focused suite plus a real re-ingest of a bound wiki, and simplify only after GREEN.

## Testing Plan

Automated unit tests for `cwd` matching across Windows and POSIX paths, session-id extraction including the disagreement case, and provider dispatch including the unknown-name error. Automated integration over fixture stores asserting digest and pointer output per provider and byte-identical Claude/Codex results. System check: re-ingest of a real bound wiki followed by `lint_wiki.py`, and a second run asserting no writes. The multi-hundred-megabyte path is deliberately not exercised here; PSP-03 owns it.

## Out of Scope
- Large-transcript wall time, memory, and refusal behavior (PSP-03).
- Copying any transcript into `raw/`; the pointer contract is unchanged.
- Widening `TICKET_REFERENCE`.
- Any change to Pi itself; its store format is read as found.
