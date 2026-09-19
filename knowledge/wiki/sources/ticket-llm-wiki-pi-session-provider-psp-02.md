---
type: source
title: "PSP-02 — Compile Pi sessions through binding-declared providers"
identity_key: ticket:llm-wiki-pi-session-provider/PSP-02
identity_strength: stable
source_path: docs/tickets/llm-wiki-pi-session-provider/done/02-pi-provider-dispatch.md
source_digest: sha256:0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-15
created_provenance: git-commit
disposition_changed: 2026-09-16
disposition_changed_provenance: git-rename
run_id: c6b2211177154684
---

# PSP-02 — Compile Pi sessions through binding-declared providers

Compiled from `docs/tickets/llm-wiki-pi-session-provider/done/02-pi-provider-dispatch.md`. Identity is `ticket:llm-wiki-pi-session-provider/PSP-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-15** via `git-commit`
- Disposition changed: **2026-09-16** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-pi-session-provider]]
- Blocked by: [[sources/ticket-llm-wiki-pi-session-provider-psp-01]] — `ticket:llm-wiki-pi-session-provider/PSP-01`

## Run

Completed under autopilot run `c6b2211177154684`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-pi-session-provider-psp-02.md","payload_bytes":5204,"payload_sha256":"0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f"}],"payload_bytes":5204,"payload_sha256":"0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f","schema":1,"source_digest":"sha256:0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5204,"payload_sha256":"0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f","schema":1,"source_digest":"sha256:0bb1ccf73775ed8e262c971060272bc86607a7356ecdfea8cd891d96c624bd7f","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-02"} -->
```markdown
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

```
