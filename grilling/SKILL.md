---
name: grilling
description: Grill the user relentlessly about a plan or design. Use when the user wants to stress-test a plan before building, asks for a design interview, or uses trigger phrases such as "grill me", "grill this", "stress test this plan", "poke holes", or "challenge this design".
---

# Grilling

Interview the user until you and the user reach shared understanding of the plan, design, decision, or proposal.

## Core Rules

- Ask one question at a time, then wait for the user's answer before continuing.
- For each question, include your recommended answer or the default you would choose, with a brief reason.
- Walk the decision tree deliberately. Resolve blocking dependencies before asking downstream questions.
- If a fact can be found by exploring the codebase or provided artifacts, look it up instead of asking the user.
- Keep questions relevant to the plan or design. Be direct and concise.
- The user owns the decision. Challenge assumptions, but do not overrule the user's choice.
- Do not enact the plan, edit files, create tickets, or write durable docs until the user confirms the shared understanding.

## Workflow

1. Restate the plan in one or two sentences and identify the riskiest unresolved decision.
2. Ask the single next question that most reduces uncertainty.
3. Include your recommended answer in the same message.
4. Wait for the user's response.
5. Update your mental model, note any resolved dependency, and choose the next question.
6. Repeat until the plan is coherent enough to summarize.
7. Summarize the agreed plan, explicit trade-offs, unresolved assumptions, and next recommended action.
8. Ask for confirmation before switching from grilling into implementation, documentation, ticketing, or another skill.

## Question Selection

Prefer questions that expose:

- The user or stakeholder the plan serves.
- The failure mode the plan must prevent.
- The constraint that would make the obvious solution wrong.
- The boundary between this work and adjacent work.
- The reversible versus hard-to-reverse parts of the decision.
- The data, API, workflow, or ownership contract that other code depends on.
- The simplest concrete scenario that proves the plan works.

Avoid broad surveys and multi-part interrogations. If several questions seem necessary, choose the one that blocks the rest.

## Response Shape

Use this shape for each turn:

```markdown
Question: <one focused question>

My recommended answer: <your answer and why>
```

If you looked something up in the codebase first, add one short evidence line before the question.
