---
type: source
title: "Defer the active Pi session during wiki sync"
identity_key: spec:llm-wiki-active-session-deferral
identity_strength: stable
source_path: docs/specs/llm-wiki-active-session-deferral.md
source_digest: sha256:fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-19
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Defer the active Pi session during wiki sync

Compiled from `docs/specs/llm-wiki-active-session-deferral.md`. Identity is `spec:llm-wiki-active-session-deferral`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-19** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-llm-wiki-active-session-deferral-asd-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[5],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[6],"status":"present"},"verification":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/spec-llm-wiki-active-session-deferral.md","payload_bytes":3424,"payload_sha256":"fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd"}],"payload_bytes":3424,"payload_sha256":"fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd","schema":1,"source_digest":"sha256:fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd","source_identity":"spec:llm-wiki-active-session-deferral","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 8: Out of scope |
| decisions | 5: Decision |
| invariants | 6: Invariants |
| verification | 7: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3424,"payload_sha256":"fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd","schema":1,"source_digest":"sha256:fe974a6ce8438e57520394503601d9aa551c53edb560b6818c594af331bcd4fd","source_identity":"spec:llm-wiki-active-session-deferral"} -->
```markdown
# Defer the active Pi session during wiki sync

## Artifact Graph
- Artifact ID: `spec:llm-wiki-active-session-deferral`
- Role: `spec`
- Standalone: true

### Children

- [ticket:llm-wiki-active-session-deferral:ASD-01](../tickets/llm-wiki-active-session-deferral/done/ASD-01-defer-active-pi-session.md)

## Type
Bug fix.

## Problem
`session_ingest.ingest` treats every changed transcript as a complete source. A Pi transcript is
append-only while its session is active, so every post-integration sync rereads it from byte zero.
The current repository session is over 1 GB and each retry exceeds the bounded command window,
leaving temporary worktrees and preventing the runner from completing post-integration sync.

The provider implementation is present, but the tracked agent-skills binding still lists only
Claude Code and Codex. The earlier adoption therefore never reached the project configuration;
Pi is not actually part of its normal sync. Enabling it without fixing the live-file loop would
make every subsequent sync hit the same unbounded read.

Pi already exposes the exact active transcript through `PI_SESSION_FILE`. An active transcript is
not complete evidence: it can grow while the wiki candidate is being compiled. Compiling it on
every run is both expensive and immediately stale.

## Decision
When the `pi` provider discovers the file named by `PI_SESSION_FILE`, ingestion defers that one
file. It does not open, parse, write, or claim completion for it. The report exposes a `deferred`
entry containing provider, session id, path, size and reason `active-session`.

All other transcripts, including prior Pi sessions, retain the existing full, redacted,
incremental ingestion contract. When a later Pi session starts, the former active transcript no
longer matches `PI_SESSION_FILE` and is ingested normally.

The tracked `knowledge/llm-wiki-project.json` binding explicitly adds `pi` after the deferral is in
place. This is the previously intended explicit adoption, now delivered in the same candidate that
makes it bounded.

The comparison is canonical and platform-aware. A missing or unrelated environment value changes
nothing. Existing pointers for a resumed active session are preserved; drift remains visible via
the existing warning until the session becomes inactive and is rebuilt.

## Invariants
1. The active Pi transcript is not opened by ingestion.
2. Deferral is explicit in the machine-readable report and is never counted as `written`,
   `skipped`, or `refused`.
3. Closed Pi sessions and every non-Pi provider keep their current behavior.
4. The tracked project binding names `pi` explicitly; no implicit binding rewrite is introduced.
5. No transcript content, secret-redaction rule, pointer/digest format, or size bound changes.
6. Absence of `PI_SESSION_FILE` preserves the previous ingestion behavior exactly.

## Verification
A causal unit test sets `PI_SESSION_FILE` to a discovered Pi fixture and uses a fail-on-call
extractor to prove the file is not read. Companion cases prove an unrelated value does not defer
the fixture and that the report shape names the deferred session. Run the llm-wiki session and
sync suites plus the repository's required Linux profile. Windows full is not a QA gate.

## Out of scope
Append-offset checkpointing, partial digests of active sessions, changing provider discovery,
merging wiki candidates, or cleanup of unrelated worktrees.

```
