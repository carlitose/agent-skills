---
type: source
title: "Resolve the deferred `.strip()` equality hazard"
identity_key: ticket:windows-text-fidelity/WT-05
identity_strength: stable
source_path: docs/tickets/windows-text-fidelity/done/05-strip-equality-hazard.md
source_digest: sha256:eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-12
created_provenance: git-commit
disposition_changed: 2026-08-31
disposition_changed_provenance: git-rename
run_id: windows-text-fidelity-afk-20260831
---

# Resolve the deferred `.strip()` equality hazard

Compiled from `docs/tickets/windows-text-fidelity/done/05-strip-equality-hazard.md`. Identity is `ticket:windows-text-fidelity/WT-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-12** via `git-commit`
- Disposition changed: **2026-08-31** via `git-rename`

## Graph

- Parent source: [[sources/artifact-windows-text-fidelity-wayfinder]]

## Run

Completed under autopilot run `windows-text-fidelity-afk-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-windows-text-fidelity-wt-05.md","payload_bytes":2941,"payload_sha256":"eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3"}],"payload_bytes":2941,"payload_sha256":"eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3","schema":1,"source_digest":"sha256:eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3","source_identity":"ticket:windows-text-fidelity/WT-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2941,"payload_sha256":"eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3","schema":1,"source_digest":"sha256:eecdc2619a52569a11bfb979039bae3c0cda3018da3bda11139bf42a38895ef3","source_identity":"ticket:windows-text-fidelity/WT-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WT-05"
execution_mode: AFK
blocked_by: []
---

# Resolve the deferred `.strip()` equality hazard

## Artifact Graph
- Artifact ID: `artifact:wt-05-strip-equality-hazard`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
`SubprocessCommandRunner.run` returns `CommandResult(stdout=result.stdout.strip(),
stderr=result.stderr.strip(), ...)`. `WD-02` explicitly declined to touch it and named it
what it is:

> The `.strip()` applied to stdout and stderr in the same method, which is a separate
> latent equality hazard and needs its own decision.

That decision is now overdue, because the family has produced a third instance of the same
failure shape. `WT-01` fixed a lost **trailing newline** that broke a literal comparison at
`finalizer.py:1103`; `.strip()` destroys trailing whitespace and newlines on every command
result that passes through this runner. Any current or future value read through it and
then compared for equality carries the same defect, silently.

The task is to determine which consumers depend on the stripping, which would break if it
were removed, and whether stripping belongs at the call sites that want it rather than in
the shared runner.

## Acceptance Criteria
- [ ] Every consumer of `CommandResult.stdout` / `.stderr` is enumerated, with whether it
      relies on the value being stripped.
- [ ] A decision is recorded: strip at the runner, strip at the call sites, or expose both
      raw and stripped.
- [ ] No consumer that feeds an equality, digest, or readback comparison receives a value
      that was silently trimmed.
- [ ] A test covers a command whose output legitimately ends in whitespace.
- [ ] `WD-02`'s deferral is marked resolved.

## Frontier
Ready. This is investigative before it is corrective: the enumeration in step 1 may show
the hazard is inert, in which case the outcome is a documented invariant rather than a code
change. Do not remove the `.strip()` before knowing who depends on it.

## Step-by-Step Implementation Plan
1. Enumerate consumers of `CommandResult`. Checkpoint: a list, with each one classified as
   whitespace-sensitive or not.
2. Identify any consumer feeding an equality or digest check. Checkpoint: named, or the
   hazard is declared inert with evidence.
3. Apply the chosen shape. Checkpoint: suite no worse than the `WT-06` baseline.
4. Add the trailing-whitespace test.

## Testing Plan
Automated: a unit test driving a child process whose stdout ends with whitespace and a
newline, asserting the contract the decision chose. Regression: the full suite, compared
against the baseline established by `WT-06`.

## Out of Scope
- The `errors` policy in the same method, which is `WT-02` and `WT-03`.
- The body round trip, which is `WT-01`.

```
