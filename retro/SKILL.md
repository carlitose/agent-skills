---
name: retro
description: "Review a Pi coding session and suggest changes to the agent's environment, not the code."
argument-hint: "Which session should I review (default: this one), and what went wrong or felt slow?"
disable-model-invocation: true
---

# Session Retro

Owns: session retrospective suggestions. It reads one session and returns ranked changes to
the agent's **environment** (pointers, checks, standards, steering files, tooling) so future
runs go better. Adapted from upstream `retro` in `mattpocock/skills`.

Read-only: it proposes and never edits steering files, settings, or code. Applying a suggestion
is separate work routed through `ask-skills`. Work inline, with no subagents.

## Steps

1. **Pick the session.** Default to the current one, `PI_SESSION_FILE`. Otherwise use the
   session the user names: Pi keeps one JSONL file per session under
   `~/.pi/agent/sessions/<encoded-cwd>/`. Read only this user's local logs.
2. **Digest it.** Run `python -B scripts/session_digest.py [SESSION.jsonl]` from this skill's
   directory. It prints, already redacted, the turn and call counts, cost, tool errors,
   costliest turns, repeated identical calls, and largest tool results. Open the raw log
   only around the lines the digest points to.
3. **Read the guardrails.** Before proposing any check, read the repository's own check
   commands and CI (package scripts, test and lint config, workflows), so a check that
   exists but is unwired or broken is the finding, not a reinvention.
4. **Find candidates** in the categories below, each tied to evidence from the session.
5. **Report** the candidates ranked by severity, in the output shape below, then stop.

Completion criterion: every candidate cites session evidence and names one concrete change;
nothing has been edited.

## Categories

- **Navigation**: the agent searched long for a file or fact. Propose a navigation pointer
  where the agent would have looked first.
- **Automated checks**: the agent made a mistake a linter, type check, test, or file check
  could have caught. A repository with no guardrail (no hook and no CI running its checks)
  is a finding in itself.
- **Coding standards**: classify the violation first. A mechanical one (banned API, import
  shape, file location, fixed pattern) gets a deterministic check, not a written rule; keep
  prose standards for real judgement calls, enforced at review rather than implementation.
- **Steering files**: always-loaded instructions (`AGENTS.md`, `CLAUDE.md`, skill
  descriptions) that are too long, never change behaviour (no-ops), or belong in a check or a
  pointed-to doc instead.
- **Tool economy**: expensive or repeated tool calls, turns carrying a single call that could
  be batched, oversized tool results, errors from the wrong shell or path form.
- **Information access**: a fact the agent needed but could not reach (logs, a service's
  read-only state, docs). Propose the narrowest read-only access.

## Output shape

```markdown
1. <title>: <category>
   - Severity: high | medium | low (cost or risk it causes per session)
   - Evidence: <session line or digest entry, redacted>
   - Proposed change: <one concrete change and where it lives>
```

## Redaction

Quote only the signal-carrying part of a command, output, or log line. Replace every
credential, token, cookie, password, or personal identifier with `<REDACTED>`, even when the
digest missed it. Never print environment values or whole log entries.
