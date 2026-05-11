---
name: write-a-adr
description: Create an Architecture Decision Record and follow-up implementation issue from an existing bug, architecture problem, technical decision, or agent-discovered codebase context. Use when the user asks to write an ADR, record an architectural decision, turn a known problem into an ADR, or produce an ADR plus issue from context already gathered by the agent.
---

# Write an ADR

Create an ADR that records a real technical decision, then create the follow-up implementation issue that turns the decision into actionable work.

Prioritize context already available in the conversation and agent workspace. If the user has already described the bug, design conflict, or codebase problem, do not restart the interview. Distill the known context, explore only what is needed to verify it, and ask only blocking questions.

Both the ADR and follow-up issue must be junior-developer-ready: explain the decision, implementation sequence, verification steps, and risks clearly enough that a junior developer can execute the work without relying on hidden conversation context.

## Process

### 1. Reconstruct the problem from current context

Start from the agent's existing context:

- User-provided bug reports, constraints, logs, screenshots, test failures, or design goals
- Codebase findings already gathered in the current session
- Prior implementation attempts, failed approaches, or known regressions
- Existing PRDs, issues, ADRs, docs, comments, or commit messages if relevant

Write a short working summary for yourself before exploring:

- The concrete problem or decision pressure
- The affected users, modules, workflows, or operational constraints
- What decision appears necessary
- What is still uncertain

If the context is sufficient, proceed. If a missing fact would materially change the decision, ask the user one concise question before continuing.

### 2. Verify against the codebase

Explore the repo enough to avoid recording a speculative decision. Look for:

- Existing architectural boundaries, ownership patterns, and similar decisions
- Tests or workflows that demonstrate the current behavior
- Prior ADRs or docs that constrain the new decision
- Callers, data flows, integration points, and failure modes affected by the decision

Do not over-explore. The goal is to support a decision record, not to implement the change.

### 3. Frame the decision

Identify:

- The decision to be made, phrased as a durable architectural choice
- The status: usually `Proposed` unless the user explicitly says it is already accepted
- The considered options, including "do nothing" when realistic
- The chosen option and why it fits the constraints
- Consequences, including trade-offs, migration cost, operational risk, and testing impact

Prefer durable architecture language over brittle file-by-file implementation detail. Mention concrete files only when needed as evidence or anchors.

### 4. Write the ADR

Use the ADR template in [REFERENCE.md](REFERENCE.md). Save the file under:

`docs/adrs/YYYY-MM-DD-<descriptive-slug>.md`

Use the current local date for `YYYY-MM-DD`. Create `docs/adrs` if it does not exist.

### 5. Create the implementation issue

After writing the ADR, create a follow-up issue from the issue template in [REFERENCE.md](REFERENCE.md). Save it under:

`docs/issues/<descriptive-slug>.md`

Create `docs/issues` if it does not exist. The issue should be actionable without rereading the whole conversation:

- Link to the ADR path
- Describe the implementation scope
- Provide a step-by-step implementation plan in execution order
- List acceptance criteria
- Include test expectations
- Call out non-goals and migration risks

If the repository clearly uses GitHub issues, Linear, or another tracker and the user has asked for a real issue, create it there instead of a local Markdown issue. Otherwise, use the local Markdown file.

### 6. Report paths and open questions

Tell the user:

- The ADR path
- The issue path or tracker URL
- Any unresolved assumptions that should be confirmed before implementation

Keep the final response short. Do not paste the full ADR unless the user asks.
