---
name: to-questionnaire
description: "Draft a focused questionnaire for an explicit external decision owner when the current user cannot answer alone. Use only when the user asks to externalize questions; never send the draft."
argument-hint: "Who is the intended recipient, where will the draft go, and what decision is needed?"
disable-model-invocation: true
---

# To Questionnaire

Owns: asynchronous decision questionnaire drafting.

Use this skill to turn a knowledge gap into a local Markdown draft for one explicit
decision owner. **Grill the send, not the subject**: clarify who the user intends to ask,
where the draft is intended to go, and what must come back. Do not run a live subject
interview or try to answer the recipient's questions on their behalf.

This skill does not replace `grilling`. Use [grilling](../grilling/SKILL.md) when the
current user owns the decision and wants a live decision interview.

## Preconditions

Require both:

- an explicit intended recipient: the named person or role that owns the missing knowledge;
- an explicit intended destination: the user-selected document path or later delivery
  channel where they plan to use the draft.

Never infer or select a recipient, destination, address, handle, or channel. If either is
absent, do not write the questionnaire; ask one bounded clarification about the missing
send detail and wait. Do not expand that clarification into a subject interview.

Also require a concrete decision or fact the user needs back and observable response
criteria describing what a useful answer must cover.

## Process

1. Confirm the decision owner, intended recipient, intended destination, decision needed,
   and response criteria. Preserve the user's wording for names and destinations.
2. Identify the gap between what the recipient knows and what the user needs. Draft only
   questions that close that gap; do not manufacture answers.
3. Minimize and redact context before rendering. Include only the minimum context the
   recipient needs. Replace credentials, tokens, cookies, personal data, and other
   sensitive values with `<REDACTED>`. Do not include conversation transcripts, unrelated
   command output, or private reasoning.
4. Order questions most important first. Use one decision or fact per question, an answer
   stub below each question, and a short reason only when the question could be misread.
5. Render the draft to `to-questionnaire-<slug>.md` at the user-approved local path, using
   the exact structure below. Mark it as unsent.
6. Verify that every response criterion maps to at least one question, all identity and
   destination fields match the user's input, and no sensitive value remains.
7. Return only the draft path, the intended destination label, and the unsent status. Do
   not paste the whole questionnaire back unless the user asks to review it.

## Document structure

```markdown
# <Questionnaire title>

Status: Draft — not sent

**Decision owner:** <person or role accountable for the resulting decision>
**Intended recipient:** <explicit person or role supplied by the user>
**Intended destination:** <explicit local path or later delivery channel supplied by the user>

## Purpose and decision needed
<what the user must be able to decide or do after the response>

## Context
<the minimum redacted context needed to answer well>

## Response criteria
- <observable fact, choice, constraint, or approval the response must provide>

## Questions

### <one decision or fact per question>
_Why this matters: <include only when clarification is useful>_

> <answer stub>

## Anything else?
What should we know that this questionnaire did not ask?
```

## No-send boundary

Never send, post, email, upload, or publish the questionnaire. Do not call a connector,
provider, messaging tool, or mail client. Do not open a compose window, choose a contact,
or place the draft on a clipboard. Sending requires a separate explicit user action outside
this skill, with the user controlling the final recipient, destination, and content.

## Examples

- Valid: recipient `Example Recipient`, destination `decision-drafts@example.invalid`, and
  decision "which migration window is acceptable." The file is rendered, but the draft remains local.
- Missing destination: ask one bounded destination question and produce no file.
- The current user owns the answer and wants pressure-testing: use `grilling`, not this skill.
