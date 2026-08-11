# Model-invocation policy

Every skill in this repository is either offered to the model in its skill listing or
hidden from it with `disable-model-invocation: true` in the skill front matter. Hiding a
skill removes its name and description from the listing the model carries in every
session, so the flag is a small, permanent context saving. It is also a capability
removal: a hidden skill can no longer be chosen by the model, only typed by a person.

This file states when the flag belongs, classifies every skill, and is enforced by
`ticket-autopilot/tests/test_model_invocation_policy.py`.

## The criterion

A skill is `user-invoked` — and therefore hidden — when **either** ground holds.

**Ground A, the skill cannot start without an answer only a person can give.** Its front
matter carries an `argument-hint`, because the skill opens by asking for a decision,
a recipient, a scope of authority, or a set of sensitive values. An agent selecting it
mid-task would have to invent that answer, which is exactly the failure the hint exists to
prevent.

**Ground B, the skill is a compatibility alias for a skill that is already listed.**
Listing both spends the description of every session twice for one capability. The alias
stays typable; only the duplicate listing entry goes away.

A skill is `model-invocable` — and therefore listed — in every other case: the need for it
arises from the state of the work rather than from a person's request, so an agent must be
able to select it while working. Implementation, review, QA, verification, research,
diagnosis, and planning skills are all of this kind.

Two things the criterion deliberately does **not** say:

- It is not about listing size. A skill an agent needs stays listed however long its
  description is. The saving from hiding is bounded by the number of genuinely
  user-gated workflows, which is small.
- It is not about whether a human happens to start the skill. Humans start most work.
  What matters is whether an agent can also reach for it correctly on its own. A skill
  whose description is written to trigger on the user's own phrasing — such as
  `peer-programming`, which lists "pair program", "let's code together", "you navigate I
  type" — depends on the model recognising those phrases, so hiding it would break it.

## Classification

| Skill | Classification | Reason |
| --- | --- | --- |
| `ask-skills` | model-invocable | Routes a request to the right local skill; the agent must reach it while deciding how to proceed. |
| `code-review` | model-invocable | Composed as a quality leaf inside `execute-ticket`. |
| `code-simplification` | model-invocable | Composed as a quality leaf inside `execute-ticket`. |
| `codebase-design` | model-invocable | Shared design vocabulary consulted while shaping a module boundary. |
| `codebase-improver` | model-invocable | A whole-repo audit an agent runs to improve a codebase. |
| `diagnose` | model-invocable | Root-cause analysis selected when a bug needs diagnosis before a fix. |
| `domain-modeling` | model-invocable | Applied while planning or changing software, driven by the work. |
| `execute-ticket` | model-invocable | Composed by the folder scheduler for every ticket. |
| `explain-pr` | model-invocable | Used by delivery finalization to render a PR body. |
| `grill-me` | user-invoked | Ground B: compatibility alias for `grilling`, which is listed. |
| `grill-with-docs` | user-invoked | Ground B: alias of `grilling` seeded with documents; the listed skill covers the capability. |
| `grilling` | model-invocable | Stress-tests a plan or design; acts on an artifact, so an agent can select it from the state of the work. |
| `handoff` | user-invoked | Ground A: `argument-hint` asks what the next session should focus on. |
| `improve-codebase-architecture` | model-invocable | An exploration of architectural improvement run over a codebase. |
| `peer-programming` | model-invocable | Its description triggers on the user's own phrasing, so the model must be able to see and select it. |
| `pr-antipattern-review` | model-invocable | A review pass over a pull request, selectable whenever a PR is in scope. |
| `project-blueprint` | model-invocable | Produces a project specification from a described project. |
| `prototype` | model-invocable | Builds a throwaway prototype to answer a design question raised by the work. |
| `qa-test-plan` | model-invocable | Composed as a quality leaf inside `execute-ticket`. |
| `research` | model-invocable | Answers factual and codebase questions that arise mid-task. |
| `resolving-merge-conflicts` | user-invoked | Ground A: `argument-hint` asks which conflict is in scope and which mutations are authorized. |
| `tdd` | model-invocable | A red-green-refactor loop the agent drives while building. |
| `ticket-autopilot` | model-invocable | The folder scheduler an agent runs to drive a ticket folder. |
| `to-questionnaire` | user-invoked | Ground A: `argument-hint` asks who the external recipient is and what decision is needed. |
| `to-spec` | model-invocable | Creates or updates a spec as part of ordinary planning work. |
| `to-tickets` | model-invocable | Splits a spec into tickets as part of ordinary planning work. |
| `triangulate-diagnosis` | model-invocable | Runs three diagnostic passes on a hard bug; selected from the state of the bug. |
| `verification-audit` | model-invocable | Composed as a quality leaf inside `execute-ticket`. |
| `wayfinder` | model-invocable | Maintains the map and frontier for large or vague work. |
| `wizard` | user-invoked | Ground A: `argument-hint` asks which manual procedure runs, which values are sensitive, and where each may be written. |
| `writing-for-agents` | model-invocable | Improves agent-facing documents the agent is editing. |

Six skills are `user-invoked`. The other twenty-five must stay selectable.

### Flag changes this policy makes

None. Every skill that carries `disable-model-invocation: true` today satisfies the
criterion, and no listed skill meets it. The criterion was derived from the skills as they
are and then checked against them; it did not move any skill.

`peer-programming` was the one candidate examined and rejected. A person always starts it,
which is why it looks user-invoked, but its description exists to make the model recognise
phrases like "I want to be the driver". Hiding it would remove the only mechanism that
starts it.

## Oversized descriptions

Skill descriptions are carried in full in the model-visible listing, so their length is a
recurring per-session cost. These exceed 500 characters:

| Skill | Description characters |
| --- | --- |
| `peer-programming` | 716 |
| `pr-antipattern-review` | 799 |
| `project-blueprint` | 859 |

This is a report, not an instruction. Shortening a description trades trigger precision
for listing size, and that trade belongs to whoever owns the skill. Nothing here rewrites
them. Note that `peer-programming` is the clearest case where the length is doing work:
the trigger phrases are the mechanism.

## Skills not installed

`peer-programming`, `pr-antipattern-review`, and `project-blueprint` exist in this
repository but are absent from the install root, so they occupy no listing space in a
session today. Their classification is recorded anyway, so it is already correct if they
are ever installed. This policy does not ask for them to be installed.

The reverse also holds: an install root may carry skills that do not live in this
repository. Those are outside this policy and outside this repository's control.
