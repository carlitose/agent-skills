# Ticket Driver: isolate the Jev credential from model leaves

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-jev-key-isolation`
- Role: `spec`
- Standalone: true

### Children
- [TDK-01](../tickets/ticket-driver-jev-key-isolation/01-isolate-the-jev-key-from-leaves.md)

## Type
Bug analysis / security boundary

## Status
Ready for one skills-only ticket. Live c2a/c2b batches are authorized but paused before any attempt.

## Evidence and cause
`ticket-driver/scripts/arbiter.py` currently reads `TYPESAFE_API_KEY` from the driver environment. A live c2 run must therefore launch its driver with the key. `ticket-driver/scripts/leaf.py` calls the frozen library `autopilot.command_capture.capture_command` to spawn Pi, and the capture library invokes `subprocess.Popen` without an explicit environment. Windows and POSIX children inherit the driver's environment, so Pi and its model tools can read the Jev key. The same inheritance applies to project test subprocesses. This is a potential exposure, not evidence of a real leak: the only Jev smoke was a direct process with no leaf; zero c2 attempts have started. See operator evidence `C:/Users/CGS03/prof/tk1/profile-contract-decision/queued-bugs.md#QB-tdr05-2`.

## Target and invariants
- A live c2/c3/c4 driver retains the Jev key in its own process long enough for typed arbitration, but **removes it from the process environment throughout all child launches**: Pi leaves, project tests (including human-approved rechecks) and Git commands. No key in argv, prompt, receipts, session files, candidate diff or provider artifacts. A child can inspect its environment and must see no `TYPESAFE_API_KEY`.
- The allowed Jev endpoint, repository allowlist, question/usage validation and existing retry policy stay unchanged. No extra request or cost is authorized by this fix.
- When a live Jev candidate has no key, reject before worktree and ledger creation. Fake-leaf tests can still exercise the unavailable/cascade path without a live key.
- Scope secret handling to the driver invocation; do not mutate a caller's environment permanently in tests or in other CLI commands. Never print, hash, or persist the key. Preserve Windows process-tree containment; do not use a shell wrapper.
- `ticket-autopilot` stays frozen. Do not change its command-capture library or start its runner. The ticket-driver's in-process secret isolation is the seam.

## Implementation slice and checks
One end-to-end slice in `ticket-driver/scripts/arbiter.py` and `ticket-driver/scripts/ticket_driver.py`, with focused tests in `ticket-driver/tests/`: move the key from the driver process environment to a private in-process scope before `execute` and restore only after its children have terminated; `ask()` accesses the private key while that scope is active and retains its direct-call environment behavior for the one-off smoke. Verify via a real fake leaf subprocess that the key is absent but a typed local-transport call still receives an Authorization header; verify missing-key live refusal before worktree/ledger and environment restoration on failure. Run causal Python tests plus required local repository profile, freeze/review/QA/audit, and separately authorize any provider delivery and local skill sync. Only after installed-code verification may the existing c2a/c2b batch bindings be renewed and runs started.

## Non-goals
No Jev request during this fix; no customer code, change to `ticket-autopilot`, new runner, provider publication by implication, c2 batch attempt, or modification of benchmark outcome. A later decision on where to store the credential persistently is separate.
