# Ticket-driver builder prompt: a missing ticket is not a reason to stop

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-builder-prompt`
- Role: `spec`
- Standalone: true

### Children
- [TBP-01 — let the builder implement a prose task](../tickets/ticket-driver-builder-prompt/done/01-let-the-builder-implement-a-prose-task.md)

## Problem and evidence
In lot `dbh` of delivery-bench-hard (DBH-09, `openai-codex/gpt-6-luna` with medium thinking), the
two driver arms had 120 runs, and 72 ended with an empty candidate. The builder sessions show
three groups:
- **28 stopped for protocol** (c1a 15, c3a 13). The builder read that the skills-only loop
  runs `to-spec -> to-tickets -> execute-ticket`, saw that the task was prose and not a
  canonical ticket, and stopped without editing a file.
- **36 gave up without editing**, calling the task too large for the session.
- **8 edited files** but left nothing in the candidate.

The skills-only arm used the same model and the same installed skills on the same requests. In
its 84 requests it never stopped for protocol. The difference is the builder prompt
(`ticket-driver/prompts/builder.md`, sha256 `c655b1c6...`):
- it names the full loop, and "a supplied canonical ticket" as the only alternative, so a prose
  task reads as one that needs artifacts first;
- it offers "If you cannot finish, explain the limitation in prose" as an exit.

With sol the same prompt did not trip: 55 of 57 c3a runs of the first measurement integrated.

## Decision
The builder prompt says:
- the task below is the whole assignment, supplied by the driver in place of a ticket;
- a missing spec, ticket or canonical envelope is never a reason to stop;
- skills are used inline as in skills-only execution, and a spec or ticket is written only if it
  helps;
- work goes to the end. What remains unfinished is left as the best implementation in the
  worktree and explained in prose.

The prompt keeps the leaf boundaries: no runner, driver or scheduler, no self-certification, the
worktree only, changes uncommitted. The driver's tests, gates and integration do not change.

## Verification
- **Replay on copies**. Four c1a requests of lot `dbh` whose builder had stopped for protocol
  (lua-vm and sql-engine) were rerun on clones of their cell at the run's base commit. Each ran
  once with the old prompt and once with the new one, with the same driver copy, model and
  thinking. Total spend was 0.05 $.
  - Old prompt: 2 stops for protocol, 1 give-up, 1 integrated.
  - New prompt: no stop for protocol, 2 give-ups, 2 integrated.
  - The sample is small and the model is stochastic: this shows the mechanism, not a rate.
- All ticket-driver tests pass with the new prompt.
- A later measurement binds the new prompt hash; past lots keep the old one.

Out of scope: the 36 give-ups, which are the model's own limit; the driver's output capture
limit, which is a separate defect; and fresh-session-per-run, which is the design.
