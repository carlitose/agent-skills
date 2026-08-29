# Claude Code Compaction Control Baseline

## Artifact Graph

- Artifact ID: `artifact:cross-host-context-compaction-controls`
- Role: `research`
- Parent: [CR-05 map supported compaction controls](../tickets/cross-host-context-rollover/done/05-map-supported-compaction-controls.md)

## Status

CR-05 complete for the source and local versions recorded below. Runtime effects that would
require a real provider-backed compaction remain explicitly unobserved.

## Research question

Which current Claude Code surfaces can a rollover controller use to observe, prevent, or
respond to compaction without relying on `--autocompact`?

## Current answer

`--autocompact` is not an acceptable controller dependency. The selected local Claude Code
2.1.223 help parses the flag, while the Homebrew 2.1.17 help does not, and the user reports that
it does not provide the required behavior. The current official changelog at 2.1.251 mentions
the interactive `/autocompact` dialog and internal auto-compaction behavior, but the official
hook material and Context7 query expose no stable `--autocompact` controller contract. A local
help entry remains parser evidence only.

Official material supports the existence of `/compact`, `PreCompact`, `PostCompact`, and
`DISABLE_COMPACT`. It says a `PreCompact` hook can block compaction, `PostCompact` fires after
compaction, and `DISABLE_COMPACT` changes maximum-context handling and suppresses `/compact`
hints. None of those facts proves a local controller can prevent every compaction before the
fixed 150,000-token edge without a provider-backed runtime observation.

CR-06 must therefore remove the flag and use a fail-closed capability contract: no prevention
surface is enabled or claimed by the prototype; an observed `PreCompact` below 150,000 with no
pending generation makes the host visibly incompatible (`no-go`); an already pending generation
survives `PreCompact`/`PostCompact`; and `PostCompact` is observation-only. `DISABLE_COMPACT` may
be recorded as an operator-configured host fact in a future live proof, but the prototype may
not set it or depend on it.

## Evidence

- Local `~/.local/bin/claude --version` reports 2.1.223 and its help lists
  `--autocompact`, `--session-id`, `--include-hook-events`, and
  `--forward-subagent-text`. The version output SHA-256 is
  `b3073071fcc455b9eaf2d8f432871ad6919ec2640ab99b05c1ffcf9cf9a73dcc`; the sanitized help
  SHA-256 is `59ff6173f822ec7f9c98d700edec11ec383bc1d52faa83811651ebcbac52895d`.
- Local `/opt/homebrew/bin/claude --version` reports 2.1.17 and its help lists
  `--session-id` but not `--autocompact`. The version output SHA-256 is
  `7103b2db1f9ecd4d0d69436b7ee0e71ac8462f0047634ccf924d119be61cd189`; the sanitized help
  SHA-256 is `efa2d7a66a885f064ce53829b4c664b000f93a5fe5f7485924d891a20e451ea2`.
- The official `anthropics/claude-code` source was read at Git commit
  `f1af9b1f4b1fd4c776135381606edada82ef638e` (changelog 2.1.251). Context7 resolved the
  exact official library ID `/anthropics/claude-code` and returned the same hook/changelog
  sources.
- The official
  [Claude Code changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
  records blocking `PreCompact` in 2.1.105, `DISABLE_COMPACT` maximum-context and hint behavior
  in 2.1.98, `PostCompact` in 2.1.76, and continuing `/compact` and internal auto-compaction
  behavior through 2.1.251.
- The official
  [hook-development skill](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md)
  defines `PreCompact`, exit code 2 as a blocking error, and hook load at session start. The
  changelog additionally records `{"decision":"block"}` for compaction.
- An isolated local process used `CLAUDE_CONFIG_DIR=/tmp/cr05-claude-isolated/config`,
  `--setting-sources local`, inline empty `PreCompact`/`PostCompact` settings, and process-local
  `DISABLE_COMPACT=1`. Version and help exited successfully and the isolated config remained
  empty. This proves argument/configuration isolation only; it does not promote any compaction
  effect to runtime evidence.
- The existing prototype requires `--autocompact`, stores `autocompact_tokens: 160000`, and
  rejects a fixture that lacks that field. Those are the exact assumptions `CR-06` removes.

## Capability classification

| Surface | Official source | Local process | Controller classification |
| --- | --- | --- | --- |
| `--autocompact` | No stable flag contract found; current changelog describes `/autocompact` and internal behavior | Parsed by 2.1.223 help; absent from 2.1.17 help; reported ineffective for the required guarantee | `unsupported` — remove every dependency and success claim |
| `DISABLE_COMPACT` | Documented for maximum-context behavior and hint suppression | Process-local env/config isolation observed; compaction effect not exercised | `unobserved` for prevention — do not set or depend on it |
| blocking `PreCompact` | Documented: exit 2 or `{"decision":"block"}` | Hook event and blocking effect not exercised against real compaction | `unobserved` for prevention — early event means visible `no-go` |
| `PostCompact` | Documented to fire after compaction | Event not exercised against real compaction | `supported` as an official observation surface, never prevention; local effect remains unobserved |
| `/compact` | Documented interactive manual compaction with explicit failure behavior | Not invoked because that would mutate a real provider-backed session | `supported` as an operator command, `unsupported` as automatic prevention or fresh-session rollover |

## CR-06 input contract

1. Delete `--autocompact`, `autocompact_tokens`, and the synthetic 160,000-token flag fixture.
2. Start the stream controller without any compaction-control argument.
3. Preserve the 150,000-token `rollover_pending` edge exactly.
4. If `PreCompact` arrives below 150,000 and no generation is pending, return an explicit
   incompatible-host/no-go result. Do not arm rollover and do not call it success.
5. If a generation is already pending, preserve its identity across `PreCompact` and
   `PostCompact`; neither event creates a new generation or replacement-session receipt.
6. Report `DISABLE_COMPACT`, hook blocking, and live `/compact` behavior as unobserved unless
   CR-04 later supplies provider-backed evidence. No prototype configuration may change them.

## Limits

- No long-running provider-backed session, real compaction, or real 150,000-token boundary was
  exercised. Those live boundaries remain with CR-04.
- Changelog documentation proves supported product concepts, not their runtime effect in either
  installed local version.
- This report authorizes no global hook, environment change, session clear, or production
  controller installation.
- The official source was newer than both local binaries; version-bound differences remain
  explicit and do not upgrade the older installations.

## Next step

`CR-06` consumes the fail-closed contract above. CR-04 later decides, through an explicitly
authorized live run, whether a prevention surface can upgrade the local host from `no-go`.
