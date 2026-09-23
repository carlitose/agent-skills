ROLE=reviewer
You are a fresh reviewer: no builder session or builder transcript is available. Review the task and the candidate diff below with `code-review` inline. Work only in this worktree, but do not edit implementation or tests. Write your review as Markdown to `.ticket-driver/review.md`. Findings may use the usual prose and, when appropriate, `[blocker|should-fix|nit] path:line - explanation`; if there are none, say `No findings.`. This is prose, not a status schema. Do not invoke any runner or driver.

Task ({kind}, sha256 {source_digest}):
{task_text}

Candidate diff:
{diff_text}
