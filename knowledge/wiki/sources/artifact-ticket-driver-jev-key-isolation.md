---
type: source
title: "Ticket Driver: isolate the Jev credential from model leaves"
identity_key: artifact:ticket-driver-jev-key-isolation
identity_strength: stable
source_path: docs/specs/ticket-driver-jev-key-isolation.md
source_digest: sha256:1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-23
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Driver: isolate the Jev credential from model leaves

Compiled from `docs/specs/ticket-driver-jev-key-isolation.md`. Identity is `artifact:ticket-driver-jev-key-isolation`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-23** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-jev-key-isolation-tdk-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-driver-jev-key-isolation.md","payload_bytes":3649,"payload_sha256":"1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2"}],"payload_bytes":3649,"payload_sha256":"1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2","schema":1,"source_digest":"sha256:1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2","source_identity":"artifact:ticket-driver-jev-key-isolation","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 8: Non-goals |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3649,"payload_sha256":"1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2","schema":1,"source_digest":"sha256:1282455067a092319c57402293d1ab822f3674a6e7d76399c642db7f32b866d2","source_identity":"artifact:ticket-driver-jev-key-isolation"} -->
```markdown
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

```
