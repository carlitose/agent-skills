# Plan review checkpoint

Run this after any of three events, each observable rather than a matter of judgement:

- **context compaction**, which keeps the wording of a plan and loses its reasons;
- **phase end**, when a ticket reaches a terminal state or an artifact integrates;
- a **blocker**, when work waits on a human decision, an authorization, or an absent environment.

A refresh is not a review: rewriting the same wrong plan leaves it wrong. The reasoning behind this
rule lives in the [checkpoint decision](../docs/specs/plan-review-checkpoint.md).

Reconcile the **complete list**, not only the active item, checking each entry for:

- **goal** — the result it serves; an entry that serves none is retired or reworded, not carried;
- **evidence** — for anything called completed, cite the observation that supports it;
- **omissions** — work already known to be necessary and written nowhere;
- **duplicates** — two entries for one result, merged into the more precise wording;
- **priority and dependencies** — what unblocks what, so order does not rely on memory;
- **tree state** — inventory every checkout of the repository (`git worktree list`, then
  `worktree-gc-plan`) and give each unclean path exactly one disposition: `commit` with its
  ticket, `discard` with the reason, or `handoff` with the recipient and a saved patch.
  "Later" is not a disposition. A worktree holding an applied completion projection whose
  ticket is not integrated is never discarded without a patch: it may be the only copy.

Finish by naming **exactly one next action**, specific enough to start without deciding again.
While more than one candidate remains, the checkpoint is not finished.

Reflect the reconciliation in `update_plan` when it exists, keeping one step `in_progress`; without
it, declare the substitute used instead of implying a plan exists. Where `wayfinder` is in play its
frontier wins: a plan may reorder work, never declare an open investigation edge resolved.

The plan is **never evidence** and **never authority**. It closes no gate, grants no permission, and
rewrites neither runner state nor an investigation frontier; it reflects them.
