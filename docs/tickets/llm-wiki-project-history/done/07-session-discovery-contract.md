---
ticket_schema: 1
ticket_id: "LW-07"
execution_mode: AFK
blocked_by: []
---

# Derive the session discovery contract for Claude Code and Codex

## Artifact Graph
- Artifact ID: `artifact:lw-07-session-discovery-contract`
- Role: `ticket`
- Parent: [llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## Parent Spec
[llm-wiki-project-history-wayfinder.md](../../specs/llm-wiki-project-history-wayfinder.md)

## What to Build
The rules for answering "which agent sessions belong to this project", derived and tested
rather than hardcoded from one lucky observation.

Measured this session, on this machine:

- **Claude Code** stores per-project transcripts in a path-mangled directory:
  `~/.claude/projects/C--Users-CGS03-Projects-agent-skills/` holds 6 `*.jsonl` files,
  ~6.7 MB, 3757 records. Record types, counted: `assistant` 1491, `user` 836,
  `attachment` 377, `mode` 193, `last-prompt` 189, `ai-title` 186, `permission-mode` 130,
  `file-history-delta` 70, `pr-link` 66, `queue-operation` 62, `bridge-session` 57,
  `system` 56, `file-history-snapshot` 36, `atis-latch` 8. The same directory also holds
  `memory/`, which is **not** a transcript and must be excluded.
- **Codex** stores date-partitioned rollouts:
  `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO>-<uuid>.jsonl`, 84 files in total. Project
  identity is a field, not a path: `session_meta.payload.cwd`. Filtering on it yields 5
  files for this project, ~40 MB. Record types across all 84: `event_msg` 23420,
  `response_item` 20585, `turn_context` 317, `world_state` 106, `session_meta` 98,
  `inter_agent_communication_metadata` 35, `compacted` 21.

The problem with the Claude side is that `C--Users-CGS03-Projects-agent-skills` is a single
sample. It is consistent with more than one transform of
`C:\Users\CGS03\Projects\agent-skills` — for instance "replace every non-alphanumeric run
with `-`", or "drop the colon and replace each separator with `-`", which differ the moment
a path contains a dot, a space, or a UNC prefix. Guessing wrong silently yields zero
sessions, which reads as "this project has no history" rather than as an error.

The open question the map assigns here: **do worktree sessions count?** The observed Codex
`cwd` distribution includes `...\minnarone\.claude\worktrees\prompt-externalization` and
`...\translate-lector\.claude\worktrees\ocr-layout-wayfinder`; this repository's autopilot
worktrees live at `Projects/.agent-skills-ticket-autopilot-worktrees/<id>/`, outside the
project directory. The answer changes both the session index and which tickets receive a
`session-observed` date from `LW-04`'s ladder, so it must be recorded, not left implicit.

## Produces
- A recorded contract (a `to-spec` reference or decision spec) covering: the Claude mangling
  rule, the Codex `cwd` filter, the worktree answer, the transcript-versus-non-transcript
  exclusions, and where each timestamp lives per provider.
- Every one of those outputs links back to this ticket.

## Acceptance Criteria
- [ ] The Claude mangling rule is tested against at least three real project directories
      under `~/.claude/projects/`, chosen to differ in shape, and the rule reproduces each
      directory name exactly from its path.
- [ ] A path the rule cannot reproduce is reported as a failure with both strings, never
      silently skipped.
- [ ] The Codex filter reads `session_meta.payload.cwd` and is verified to return exactly
      the 5 known files for this project out of 84.
- [ ] `memory/` and any other non-transcript entry under a Claude project directory is
      excluded by an explicit rule, not by a glob that happens to miss it.
- [ ] The worktree question has a recorded answer with its reason, and the contract states
      how a worktree path maps back to its project.
- [ ] The timestamp field is documented per provider: record-level `timestamp` for Claude;
      record-level `timestamp` plus `session_meta.payload.timestamp` for Codex.
- [ ] The contract states what a session with no resolvable project is — skipped, or
      reported — and never attributes it to the wrong project.

## Frontier
Ready, no blockers. `LW-08` blocks on it, and through `LW-08` so does the `session-observed`
rung of `LW-04`'s ladder.

## Step-by-Step Implementation Plan
1. Enumerate `~/.claude/projects/` and pair each directory name with a plausible source
   path. Checkpoint: a table of samples wide enough to discriminate between candidate rules.
2. Derive the transform and test it against every sample. Checkpoint: exact reproduction, or
   a named counterexample.
3. Implement the Codex filter over `session_meta`. Checkpoint: 5 of 84 for this project,
   and the 12 distinct `cwd` values otherwise accounted for.
4. Decide the worktree question and record it. Checkpoint: written, with the reason.
5. Write the contract. Checkpoint: a reader can implement discovery from it without the
   observations in this ticket.

## Testing Plan
Automated: table-driven tests for the mangling rule over the collected samples; a Codex
filter test over a small fixture of synthetic `session_meta` records including a missing
`cwd`, a worktree `cwd`, and a `cwd` on another drive.

Manual: run discovery against the real stores and confirm 6 Claude files and 5 Codex files
for this project.

Unavailable boundaries: only this machine's stores are observable, so the mangling rule is
derived from one user's paths — a UNC or network path is untested and must be declared as
such. POSIX Claude directories are unobserved here. Codex's `thread_history_1.sqlite` is
explicitly not consulted.

## Out of Scope
- Reading or summarising session content. That is `LW-08`.
- Copying transcripts anywhere.
- Codex sqlite state (`thread_history_1.sqlite`, `logs_2.sqlite`).
- Sessions belonging to other projects.
