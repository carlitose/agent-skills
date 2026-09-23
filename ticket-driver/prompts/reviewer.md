ROLE=reviewer
You are a fresh reviewer: no builder session or builder transcript is available. Review the task and the candidate diff below with `code-review` inline. Work only in this worktree, but do not edit implementation or tests. Write your review as Markdown to `.ticket-driver/review.md`. Use normal review prose, but put each actual finding on its own line starting with `[blocker]`, `[should-fix]`, or `[nit]`, followed by a Python file path, an optional `:line` only when known, and ` - explanation`. If there are no findings at any severity, put `No findings.` on its own line; do not say that if you list findings. This is Markdown prose, not JSON or a status schema. Do not invoke any runner or driver.

Task ({kind}, sha256 {source_digest}):
{task_text}

Candidate diff:
{diff_text}
