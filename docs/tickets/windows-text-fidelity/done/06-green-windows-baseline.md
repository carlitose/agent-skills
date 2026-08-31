---
ticket_schema: 1
ticket_id: "WT-06"
execution_mode: AFK
blocked_by: []
---

# Restore a green Windows baseline for the test suite

## Artifact Graph
- Artifact ID: `artifact:wt-06-green-windows-baseline`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
The suite cannot go green on Windows, so correctness is only ever readable as a *delta*.
Measured on base `d306799`, Windows 11 / Python 3.12.10, LF checkout: **391 tests, 19 red**
(9 failures, 10 errors). That is the number a reviewer must currently hold in their head to
judge any change.

Two distinct causes, both on the test side:

**1. Raw-bytes digest vs normalized digest.** Four tests in `test_ticket_lifecycle.py` do

```python
source.write_text(ticket("01"), encoding="utf-8")        # text mode -> CRLF on Windows
digest = hashlib.sha256(source.read_bytes()).hexdigest() # hashes the CRLF bytes
```

while production computes `ticket_source_digest`, which reads with `newline=None` and
therefore hashes the LF-normalized text. Demonstrated:

```
bytes on disk contain CRLF: True
test digest (raw bytes) : b26740beeafde2de...
code digest (normalized): 2cc05aedc13da313...
```

The production code is correct — this is `WD-01`'s invariant working as designed. The tests
take a shortcut that only happens to agree on POSIX. Note the first test in the same file,
`test_canonical_digest_accepts_crlf_but_rejects_whitespace_edits`, uses
`ticket_source_digest` properly and passes; it is the model to follow.

**2. Path-separator assertions.** For example
`test_writing_for_agents_skill.py:18` compares `'agents/openai.yaml'` against
`'agents\\openai.yaml'`. Same class in `test_codebase_design_skill.py`.

## Acceptance Criteria
- [ ] The four `test_ticket_lifecycle.py` tests compute their expected digest with
      `ticket_source_digest`, not `sha256(read_bytes())`.
- [ ] Path assertions compare normalized paths (`as_posix()` or equivalent) so they hold on
      both separators.
- [ ] The full suite is green on Windows, or every remaining red is individually justified
      in this ticket with the reason it cannot be fixed here.
- [ ] The full suite is executed on Linux or macOS and its result recorded, closing the
      POSIX observation gap.
- [ ] The baseline count is written down where the next reviewer will find it.

## Frontier
Ready, and it is the highest-leverage ticket on the map after `WT-01`: until the baseline
is green, every other result must be reported as a delta against 19, which is exactly how
PR #78's two new regressions stayed invisible.

## Step-by-Step Implementation Plan
1. Fix the four digest computations. Checkpoint: `test_ticket_lifecycle` green on Windows.
2. Normalize the path assertions. Checkpoint: the two skill-package tests green.
3. Re-run the full suite on Windows and triage whatever remains. Checkpoint: a red count
   with a named reason for each.
4. Run the full suite on POSIX and record the result.

## Testing Plan
Automated: `python -m unittest discover -s tests -t tests` from `ticket-autopilot/`, on
Windows and on POSIX, with both counts recorded. Note that `pytest` is not installed and
not required; these are stdlib `unittest` tests.

Unavailable boundary: no POSIX environment has been observed in this investigation. If none
becomes available, step 4 stays an open gate and no cross-platform claim may be made.

## Out of Scope
- Any production code change. Every fix here is test-side; if a production defect is found
  while doing this, it gets its own ticket.
- Introducing CI, which is `WT-07`.
