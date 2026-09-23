Work on exactly one task in the current isolated worktree. Run the skills-only loop inline: to-spec → to-tickets → execute-ticket when the task needs specification and tickets, or execute-ticket directly for a supplied canonical ticket. Implement and test carefully; review and QA in this same session. This is the c1a candidate: review is not independent.

Do not invoke ticket-autopilot, ticket-driver, a scheduler, or any replacement runner. Do not produce a leaf-result, JSON status, gate approval, or evidence receipt. The driver owns the Git tree, test command, receipts and integration after this session exits. Modify only this worktree. Leave the changes uncommitted. If you cannot finish, explain the limitation in prose; never certify your own work for the driver.

Task source ({kind}; sha256 {source_digest}):

{task_text}
