---
ticket_schema: 1
ticket_id: "LW-08"
execution_mode: AFK
blocked_by:
  - "LW-03"
  - "LW-07"
---

# Ingest agent sessions as a pointer plus a digest page

## Artifact Graph
- Artifact ID: `artifact:lw-08-ingest-agent-sessions`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
An `ingest-sessions` op that turns this project's Claude Code and Codex transcripts into
something the wiki can hold, without holding the transcripts themselves.

The size constraint is the whole design. Measured for this project: 6 Claude files at
~6.7 MB and 5 Codex files at ~40 MB — **~47 MB**, growing with every session. The skill's own
raw-file policy already forbids copying sources at that scale, and prescribes the shape:
a pointer file with `external_path` and a size, cited from wiki pages exactly like any other
source. Confirmed with the user as the chosen approach.

So each session yields two artefacts:

1. **A pointer** in `raw/refs/`, carrying `external_path`, size, provider, session id, and
   the time span. No transcript content.
2. **A digest page** of 200–400 words — the length the skill mandates for a summary, and the
   reason this scales — recording what the session did: tickets touched, files touched,
   decisions reached.

The extraction rules per provider, from `LW-07`'s contract:

- Claude: `~/.claude/projects/<mangled>/*.jsonl`, record-level `timestamp`, content in
  `user` (836) and `assistant` (1491) records. `attachment` (377) and the 11 other record
  types are structural. `memory/` in the same directory is not a transcript.
- Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, filtered on
  `session_meta.payload.cwd`, content in `event_msg` and `response_item`, and note the
  `compacted` records (21 observed) — a compacted session has lost detail, and a digest built
  from it must say so rather than imply completeness.

**This op also feeds `LW-04`.** Because every record is timestamped and sessions name tickets
by ID (`WT-05`, `TK-01`), extracting dated ticket mentions supplies the `session-observed`
rung of the provenance ladder — the only witness available when `docs/` is untracked and git
can say nothing. The extraction must therefore emit mentions as structured data, not only as
prose inside the digest page.

Two hazards to handle rather than discover later:

- **Resumed sessions.** `claude --resume` appends to the same JSONL, so a digest written
  today goes stale tomorrow while the filename and session id are unchanged. A staleness
  signal is required — size, record count, or last record timestamp recorded in the pointer.
- **A digest is a summary of an agent's own output**, so it will confidently restate things
  the session got wrong. The digest records what the session *did*, and attributes claims to
  the session rather than asserting them as project facts.

## Acceptance Criteria
- [ ] No transcript content is copied into the wiki. Verified by size: the wiki grows by
      kilobytes, not by ~47 MB.
- [ ] One pointer per session in `raw/refs/` with `external_path`, size, provider, session
      id, and span; the referenced file is not moved or modified.
- [ ] One digest page per session, 200–400 words, listing tickets touched, files touched, and
      decisions, with claims attributed to the session.
- [ ] Dated ticket mentions are emitted as structured data consumable by `LW-04`'s
      `session-observed` rung, with the earliest and latest mention per ticket id.
- [ ] Ticket-id matching does not produce false positives on prose. A bare `01` is not a
      ticket reference; `WT-01` is. The rule is written down and tested against a transcript
      containing both.
- [ ] A compacted Codex session produces a digest that states its detail is incomplete.
- [ ] A resumed session is detected as stale and re-digested; an unchanged session is skipped
      with no write.
- [ ] Runs against the real stores and produces 6 Claude plus 5 Codex artefact pairs for this
      project, with no session from the other 79 Codex files included.

## Frontier
Dependency-blocked on `LW-03` for the project binding and `LW-07` for the discovery rules.
Nothing else blocks it, and `LW-06` waits on it.

## Step-by-Step Implementation Plan
1. Implement the pointer writer. Checkpoint: 11 pointers, no content, and the sources
   untouched.
2. Implement per-provider content extraction. Checkpoint: user and assistant text recoverable
   from both formats without loading a whole 13 MB file into memory at once.
3. Implement ticket-mention extraction with the written matching rule. Checkpoint: the rule
   is tested against a transcript containing both `WT-01` and a bare `01`, and rejects the
   bare form.
4. Generate digests. Checkpoint: every page inside the word band, with claims attributed.
5. Implement the staleness signal. Checkpoint: appending to a fixture transcript triggers a
   re-digest; a byte-identical file does not.

## Testing Plan
Automated: fixtures for both formats including a `compacted` Codex session, a missing
`session_meta`, and an appended-to session; a table test for the ticket-mention rule.

Manual: run against the real stores and confirm the counts (6 and 5), the wiki size delta,
and that a spot-checked digest is accurate against its transcript.

Unavailable boundaries: only this machine's stores exist, so the digests are as good as these
11 sessions and no claim about other shapes is supported. Codex sqlite state is not consulted
by design. Whether worktree sessions are included follows `LW-07`'s recorded answer; if that
answer is "no", this op must be verified to exclude them rather than to merely not find them.

## Out of Scope
- Copying, moving or rewriting any transcript.
- Reading `thread_history_1.sqlite` or `logs_2.sqlite`.
- Sessions from the other 11 `cwd` values observed on this machine.
- Rendering the timeline, which is `LW-06`.
- Implementing the `session-observed` rung itself; this ticket supplies its input.
