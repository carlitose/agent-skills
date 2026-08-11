---
name: handoff
description: "Create a small, redacted, pointer-based handoff in the operating-system temporary directory so a fresh session can continue non-ticket work. Use when the user explicitly asks for a handoff or session transfer."
argument-hint: "What should the next session focus on?"
disable-model-invocation: true
---

# Session Handoff

Owns: temporary session continuity artifacts.

This skill creates a short-lived pointer document. It is not scheduler state. It is not a ticket-autopilot checkpoint.
It is not the channel that passes context to a leaf, a worker, or a subagent: that channel is the
schema-3 `leaf-result` contract of `ticket-autopilot resume --events`.
It never replaces a spec, ticket, commit, issue, PR, or other durable source of truth.

## Boundaries

Use this skill when the user wants a temporary context bridge for a fresh session.
Do not use this skill to resume an existing run, serialize ticket state, or create durable
project documentation; use [ticket-autopilot](../ticket-autopilot/SKILL.md) or the owning
workflow instead.
Do not use it to hand context to a leaf, worker, or subagent, and never route leaf context
through a handoff document. Leaf context is carried by the `leaf-result` contract described in
[ticket-autopilot](../ticket-autopilot/SKILL.md), which binds it to an exact CandidateRef; a
handoff carries no such binding and expires.

For every invocation, never write the handoff into the project workspace, repository, or another synced folder;
do not stage, commit, or upload it. Store it only in the operating-system temporary
directory.

## Process

1. Identify the next session's purpose from the user's request. If no focus was supplied,
   state the narrow continuation goal supported by the conversation.
2. Collect only durable pointers: path, URL, issue or PR number, commit, or digest. Do not
   copy durable content already held by those artifacts.
3. Redact before writing. Replace credentials, tokens, cookies, personal data, and other
   sensitive values with the exact marker `<REDACTED>`. Do not copy the conversation transcript.
   Do not retain unnecessary command output.
4. Create a private directory with `mktemp -d` under the operating-system temporary
   directory. Require directory mode `0700`; create `HANDOFF.md` with file mode `0600`.
5. Write the artifact using the exact section order below. Keep every section concise and
   make Remaining work begin with one concrete next action.
6. Set an explicit UTC expiry that expires within 24 hours. Include the exact deletion
   command for the private handoff directory.
7. Verify that the resolved path is outside the workspace, the file is untracked, every
   section is present, and no sensitive or duplicated durable content remains.
8. Return control to the user. In chat, confirm only the path and expiry; do not echo the
   handoff contents.

## Output contract

Write the artifact with this shape:

```markdown
# Session handoff

## Purpose
<one sentence describing the next session>

## Durable pointers
- <path, URL, issue or PR number, commit, or digest plus why it matters>

## Remaining work
1. <one concrete next action>

## Limitations
- <unknown, unresolved decision, or evidence boundary>

## Redacted context
- <only the minimum non-sensitive fact needed to interpret a pointer>

## Suggested skills
- <skill name and the reason to invoke it>

## Expiry and deletion
- Created UTC: <ISO-8601 timestamp>
- Expires UTC: <ISO-8601 timestamp within 24 hours>
- Delete: <exact deletion command for this private temp directory>
```

Do not copy durable content into the handoff. Omit empty pointer entries, but never omit a
section; write `None` when a section has no safe content.

## Examples

- Use this skill: "Create a temporary handoff so a fresh session can continue the design
  investigation from the linked spec and commit."
- Do not use this skill: "Resume an existing run and continue U-06." That belongs to
  `ticket-autopilot`, whose ledger and checkpoints remain authoritative.
- Do not use this skill: "Write an ADR for this decision." Create the durable artifact
  through its owning workflow and link to it from a later temporary handoff if needed.
