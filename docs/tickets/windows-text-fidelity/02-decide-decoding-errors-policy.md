---
ticket_schema: 1
ticket_id: "WT-02"
execution_mode: HITL
blocked_by: []
---

# Decide the decoding `errors` policy for command output

## Artifact Graph
- Artifact ID: `artifact:wt-02-decide-decoding-errors-policy`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
A recorded decision — not an implementation — about how `SubprocessCommandRunner.run` and
the four other `subprocess.run` call sites in `git_ops.py` handle undecodable bytes.

This is a genuine, already-contested trade-off:

- **`strict` (current on `main`)** was chosen deliberately. `WD-02`'s plan reads "Pass
  `encoding="utf-8"` (and decide on `errors`)", and the choice was made durable as
  `assertEqual("strict", invoked.call_args.kwargs["errors"])` at `test_utf8_io.py:46`.
  Its cost: on a non-English Windows, a single `0xf3` byte in a provider error message
  raises `UnicodeDecodeError` inside the subprocess reader thread and destroys the very
  diagnostic being reported. PR #78 observed exactly this.
- **`replace` (PR #78)** keeps diagnostics alive, but applies to every call site, including
  data paths. `assert_cleanup_safe` in `git_ops.py` is the guard that authorizes deleting a
  worktree; it compares a branch name and `remote_head != head`. With `replace`, an
  undecodable byte becomes `U+FFFD` and flows silently into those equality checks instead
  of failing loudly.

The decision must therefore be per-path, not global, or must be argued as global with the
data-path risk explicitly accepted.

## Acceptance Criteria
- [ ] A decision spec exists recording the chosen policy, the alternatives, and the
      evidence for each.
- [ ] The decision states explicitly whether it supersedes or reaffirms `WD-02`, and what
      happens to the assertion at `test_utf8_io.py:46`.
- [ ] The decision distinguishes diagnostic capture from data capture, or argues why it
      should not.
- [ ] `assert_cleanup_safe` is named and its failure mode under the chosen policy is
      stated.
- [ ] No production code changes in this ticket.

## Frontier
**Human decision required.** Invoke `grilling` on this trade-off before any implementation
and confirm the outcome. Do not resolve it inline: it reverses a completed ticket's
invariant and touches a data-loss guard, which is precisely the class of change that should
not be decided as a side effect of debugging something else.

## Step-by-Step Implementation Plan
1. Run `grilling` on the trade-off, with the two positions above as the starting material.
2. Record the confirmed outcome through `to-spec` as a decision spec.
3. Link the decision from the wayfinder map and from `WT-03`.

## Testing Plan
None — this ticket produces a decision, not behavior. Verification is that `WT-03` can be
executed without further questions.

## Out of Scope
- Implementing the policy, which is `WT-03`.
- The `.strip()` hazard in the same method, which is `WT-05`.
