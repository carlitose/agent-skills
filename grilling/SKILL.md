---
name: grilling
description: Grill the user relentlessly about a plan or design. Use when the user wants to stress-test a plan before building, asks for a design interview, or uses trigger phrases such as "grill me", "grill this", "stress test this plan", "poke holes", or "challenge this design".
---

# Grilling

Owns: live decision interview and confirmation gate. It does not plan destination work or
create durable artifacts.

Interview the user until you and the user reach shared understanding of the plan, design, decision, or proposal.

## Core Rules

- Work the decision tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled. Ask every frontier question in one round, then wait for the user's answers before the next round.
- A question whose answer depends on another question still open in this round belongs to a later round, not this one.
- For each question, include your recommended answer or the default you would choose, with a brief reason.
- If a fact can be found by exploring the codebase or provided artifacts, look it up instead of asking the user.
- Keep questions relevant to the plan or design. Be direct and concise.
- The user owns the decision. Challenge assumptions, but do not overrule the user's choice.
- Do not enact the plan, edit files, create tickets, or write durable docs until the user confirms the shared understanding.

## Workflow

1. Restate the plan in one or two sentences and map the open decisions and their dependencies.
2. Ask the current frontier as one round, each question with its recommended answer.
3. Wait for the user's answers.
4. Update your mental model: settled decisions push the frontier outward. Recompute it.
5. Repeat until the frontier is empty and the plan is coherent enough to summarize.
6. Summarize the agreed plan, explicit trade-offs, unresolved assumptions, and next recommended action.
7. Ask for confirmation before switching from grilling into implementation, documentation, ticketing, or another skill.
8. Return control to the calling skill with the confirmed decisions and unresolved risks;
   do not continue into planning or artifact creation.

## Question Selection

Prefer questions that expose:

- The user or stakeholder the plan serves.
- The failure mode the plan must prevent.
- The constraint that would make the obvious solution wrong.
- The boundary between this work and adjacent work.
- The reversible versus hard-to-reverse parts of the decision.
- The data, API, workflow, or ownership contract that other code depends on.
- The simplest concrete scenario that proves the plan works.

Keep each question focused on one decision; a round of one question is fine.

## Response Shape

Format a round like this:

```markdown
**Q1** - **<question title>**: <question body, with the choices when there are any>

Recommended: <your answer and why>

---

**Q2** - **<question title>**: <question body>

Recommended: <your answer and why>
```

If you looked something up in the codebase first, add one short evidence line to the question it informs.
