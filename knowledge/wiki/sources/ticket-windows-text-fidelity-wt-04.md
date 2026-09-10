---
type: source
title: "Add the platform-conditional tests that do not exist"
identity_key: ticket:windows-text-fidelity/WT-04
identity_strength: stable
source_path: docs/tickets/windows-text-fidelity/done/04-platform-conditional-tests.md
source_digest: sha256:fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-12
created_provenance: git-commit
disposition_changed: 2026-08-31
disposition_changed_provenance: git-rename
run_id: windows-text-fidelity-afk-20260831
---

# Add the platform-conditional tests that do not exist

Compiled from `docs/tickets/windows-text-fidelity/done/04-platform-conditional-tests.md`. Identity is `ticket:windows-text-fidelity/WT-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-12** via `git-commit`
- Disposition changed: **2026-08-31** via `git-rename`

## Graph

- Parent source: [[sources/artifact-windows-text-fidelity-wayfinder]]

## Run

Completed under autopilot run `windows-text-fidelity-afk-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-windows-text-fidelity-wt-04.md","payload_bytes":3630,"payload_sha256":"fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c"}],"payload_bytes":3630,"payload_sha256":"fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c","schema":1,"source_digest":"sha256:fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c","source_identity":"ticket:windows-text-fidelity/WT-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3630,"payload_sha256":"fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c","schema":1,"source_digest":"sha256:fb2bd05827ab8680d69438093b58194402ed7ff00026e31ce80899e86fcfb52c","source_identity":"ticket:windows-text-fidelity/WT-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WT-04"
execution_mode: AFK
blocked_by: []
---

# Add the platform-conditional tests that do not exist

## Artifact Graph
- Artifact ID: `artifact:wt-04-platform-conditional-tests`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
Two of the three mechanisms PR #78 changed have **no test at all**, on any platform:

- `_folder_lock` in `ticket_lifecycle.py`, whose Windows branch now uses `msvcrt` and whose
  POSIX branch uses `fcntl`. Nothing exercises either. A grep for `_folder_lock` across
  `ticket-autopilot/` matches only the two source files.
- the `shutil.which` resolution in `SubprocessCommandRunner.run`. Nothing asserts that
  `command[0]` is resolved, or that an unresolvable command is passed through unchanged so
  the original error survives.

Both branches must be testable from either platform, because the repository is developed on
Windows and — once `WT-07` lands — will be verified on Linux too. `mock.patch` on `os.name`
is the mechanism already used elsewhere in the suite.

This ticket also declares the minimum supported Python. There is no `pyproject.toml` and no
`requires-python`, which leaves one behaviour undecided: `shutil.which` prepended the
current directory on Windows up to Python 3.11 and stopped in 3.12. Verified on the
observed interpreter (3.12.10) that it does **not** resolve from CWD, so the concern is
inert there — but nothing pins the floor.

## Acceptance Criteria
- [ ] A test drives `_folder_lock`'s Windows branch with `mock.patch("os.name", "nt")` and
      its POSIX branch, independently of the host platform.
- [ ] A test asserts contention produces `LifecycleError` naming the folder, and that the
      lock is released on both normal exit and exception.
- [ ] A test asserts `SubprocessCommandRunner.run` resolves `command[0]` through
      `shutil.which`, and that an unresolvable command is passed through unchanged.
- [ ] The minimum Python version is declared and the `shutil.which` CWD behaviour is either
      excluded by that floor or defended against.
- [ ] The divergence between blocking `LK_LOCK` (Windows, ~10 retries at 1s then `OSError`)
      and indefinitely blocking `fcntl.flock(LOCK_EX)` (POSIX) is either aligned or
      documented at the call site.

## Frontier
Ready. Note that `ledger.py:301-318` already exposes `_acquire_file_lock` and
`_release_file_lock` implementing the same Windows byte-write dance; PR #78 duplicated that
logic inline rather than importing it, and changed it from non-blocking (`LK_NBLCK`,
`LOCK_NB`) to blocking. Consider whether reuse is the right shape before writing tests
against a duplicate.

## Step-by-Step Implementation Plan
1. Decide reuse vs duplication for the lock helpers. Checkpoint: one implementation, or a
   stated reason for two.
2. Add the `_folder_lock` tests for both branches. Checkpoint: they fail against base
   `d306799` on Windows for the right reason.
3. Add the `shutil.which` resolution tests.
4. Declare `requires-python`.

## Testing Plan
Automated unit tests only; both branches are reachable through `mock.patch` without needing
the other platform. Manual: none required. Unavailable boundary: a real POSIX run still
belongs to `WT-06`, since mocking `os.name` proves the branch is selected, not that `fcntl`
behaves as assumed.

## Out of Scope
- The pre-existing Windows test failures, which are `WT-06`.
- The `errors` policy, which is `WT-02` and `WT-03`.

```
