# Claude Code Compaction Control Baseline

## Artifact Graph

- Artifact ID: `artifact:cross-host-context-compaction-controls`
- Role: `research`
- Parent: [CR-05 map supported compaction controls](../tickets/cross-host-context-rollover/05-map-supported-compaction-controls.md)

## Status

Baseline recorded; isolated runtime validation remains owned by `CR-05`.

## Research question

Which current Claude Code surfaces can a rollover controller use to observe, prevent, or
respond to compaction without relying on `--autocompact`?

## Current answer

`--autocompact` is not an acceptable controller dependency. The selected local Claude Code
2.1.223 help lists the flag, while the Homebrew 2.1.17 help does not, and the user reports that
the flag does not provide the required behavior. A version-bound parser surface does not prove
runtime control.

Current official material documents automatic compaction as host behavior, `/compact`,
`PreCompact`, `PostCompact`, and `DISABLE_COMPACT`. It also records that a `PreCompact` hook can
block compaction and that `DISABLE_COMPACT` affects compact hints and maximum-context handling.
Context7 did not find an official stable `--autocompact` contract in the current
`/anthropics/claude-code` source.

The supported replacement remains unproven. `CR-05` must observe each candidate in isolation;
until then the only safe policy is to remove the flag and report `no-go` when host compaction
prevents the fixed 150,000-token trigger.

## Evidence

- Local `~/.local/bin/claude --version` reports 2.1.223 and its help lists
  `--autocompact`, `--session-id`, `--include-hook-events`, and
  `--forward-subagent-text`.
- Local `/opt/homebrew/bin/claude --version` reports 2.1.17 and its help lists
  `--session-id` but not `--autocompact`.
- The official
  [Claude Code changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
  records internal auto-compaction behavior, context thresholds, thrash-loop protection,
  `DISABLE_COMPACT`, `/compact`, and `PostCompact` evolution.
- The official
  [hook-development skill](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md)
  defines `PreCompact`; current changelog evidence says the hook can block compaction.
- The existing prototype requires `--autocompact`, stores `autocompact_tokens: 160000`, and
  rejects a fixture that lacks that field. Those are the exact assumptions `CR-06` removes.

## Required experiments

1. Bind exact Claude versions, help output, and official-source revisions.
2. In an isolated temporary configuration, test `DISABLE_COMPACT` without changing global
   shell or Claude settings.
3. Test blocking `PreCompact`, including exit-code and structured-decision forms, and record
   whether the host preserves the active turn safely.
4. Observe `PostCompact` and status-line context fields before and after compaction.
5. Classify each surface as `supported`, `unsupported`, or `unobserved`; never infer support
   from help text.

## Limits

- No long-running production session or real 150,000-token boundary has been exercised here.
- Changelog documentation names supported concepts but does not prove behavior in either local
  installed version.
- This report authorizes no global hook, environment change, session clear, or production
  controller installation.

## Next step

`CR-05` runs the isolated experiments and updates this report. `CR-06` then removes the
autocompact-dependent prototype path and adopts only behavior that `CR-05` classifies as
supported.
