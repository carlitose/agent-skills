---
name: ticket-driver
disable-model-invocation: true
argument-hint: "--live-authorization <human-authorized-batch.json>"
description: Run one ticket or task through a process-owned worktree with model leaves, observed tests, receipts and local fast-forward integration; use for explicitly authorized benchmark batches only. Never start live runs on an AFK ticket without a separate batch authorization.
---

# Ticket Driver

The driver, not the model, owns the worktree, test execution, receipts, candidate tree and local integration. A leaf works through `to-spec → to-tickets → execute-ticket` without any reporting schema. This skill is **not** the ticket-autopilot runner or a replacement for the user's suspended execution lane.

## When authorized for a live benchmark batch

Run `python -B ticket-driver/scripts/ticket_driver.py run --candidate c1a --ticket docs/tickets/example/01.md --repo /path/to/seed --live-authorization /path/to/batch-authorization.json`. `--task` accepts a plain-text task instead of a canonical ticket. Without the batch-bound authorization, only `--leaf` substitution is available for tests; do not infer authorization from AFK or from this skill being installed.

`c1b` adds fresh reviewer/QA leaves; `c2a`/`c2b` add typed Jev judgments and an uncertainty cascade. For live `c2`+ batches, the authorization file must also carry `jev_spend_authorized: true`; TypeSafe gets only allow-listed code. On an uncertain semantic gate, `approve --repo <path> <run_id> --actor <human> --reason <decision>` rechecks the frozen tree and suite before local integration, retaining the original summary and appending an approval result. Do not manufacture human approval from AFK.

`status --repo <path> <run_id>` reads the summary or ledger; `report` prints the observed summary. The run stays local: no provider PR/merge, skill sync, or remote push. An integration failure leaves its worktree intact. Keep the run ID to inspect `.git/ticket-driver/runs/<run_id>/`.

## Constraints

- Only one ticket per invocation; no scheduler, no model-generated status JSON.
- Never call the driver or `ticket-autopilot` from inside a leaf. The builder's only products are files in its worktree and ordinary skill prose.
- `--leaf` is for local fakes, not an authorization bypass to invoke a live model. Live runs require an independently authorized batch file, checked against candidate and repository.
- See [the architecture spec](../docs/specs/ticket-driver.md) for candidate meanings, evidence ownership and the human gates; see `policy.json` for versioned model and time settings.
