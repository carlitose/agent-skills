# Agent Skills

Local collection of agent skills for planning, executing, reviewing, and improving code
workflows.

## Attribution

A substantial portion of this repository is copied from, adapted from, or inspired by
Matt Pocock's `skills` repository: https://github.com/mattpocock/skills.

The derived skills are not limited to a fixed list here. Some retain their upstream
names, while others have been renamed, reorganized, or substantially adapted for this
repository's top-level skill layout, local Markdown specs/tickets, and agent-agnostic
execution style. They should not be treated as exact copies of the upstream versions.

Credit for the original ideas and upstream versions belongs to Matt Pocock and
contributors to `mattpocock/skills`.

The `code-simplification` skill is adapted from Addy Osmani's
[`code-simplification`](https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md),
which in turn credits Anthropic's Code Simplifier agent. The adaptation keeps the
behavior-preservation principles while scoping the workflow to the current ticket diff
so it can compose cleanly with `ticket-autopilot`.
