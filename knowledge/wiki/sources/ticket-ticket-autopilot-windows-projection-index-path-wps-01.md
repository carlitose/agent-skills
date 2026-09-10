---
type: source
title: "Build the completion receipt path as a POSIX index path"
identity_key: ticket:ticket-autopilot-windows-projection-index-path/WPS-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-windows-projection-index-path/done/01-posix-index-paths.md
source_digest: sha256:f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-08
created_provenance: git-commit
disposition_changed: 2026-09-08
disposition_changed_provenance: git-rename
run_id: 623109fdaca74406
---

# Build the completion receipt path as a POSIX index path

Compiled from `docs/tickets/ticket-autopilot-windows-projection-index-path/done/01-posix-index-paths.md`. Identity is `ticket:ticket-autopilot-windows-projection-index-path/WPS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **2026-09-08** via `git-rename`

## Graph

- Parent source: [[sources/spec-ticket-autopilot-windows-projection-index-path]]

## Run

Completed under autopilot run `623109fdaca74406`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-windows-projection-index-path-wps-01.md","payload_bytes":4150,"payload_sha256":"f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a"}],"payload_bytes":4150,"payload_sha256":"f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a","schema":1,"source_digest":"sha256:f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a","source_identity":"ticket:ticket-autopilot-windows-projection-index-path/WPS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4150,"payload_sha256":"f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a","schema":1,"source_digest":"sha256:f88d64880aa9cd6d7b0200f6be31d2f45f7cd996a610c1acbab917c7e847b72a","source_identity":"ticket:ticket-autopilot-windows-projection-index-path/WPS-01"} -->
````markdown
---
ticket_schema: 1
ticket_id: "WPS-01"
execution_mode: AFK
blocked_by: []
---

# Build the completion receipt path as a POSIX index path

## Artifact Graph
- Artifact ID: `artifact:wps-01-posix-index-paths`
- Role: `ticket`
- Parent: [ticket-autopilot-windows-projection-index-path.md](../../specs/ticket-autopilot-windows-projection-index-path.md)

## Parent Spec
[ticket-autopilot-windows-projection-index-path.md](../../specs/ticket-autopilot-windows-projection-index-path.md)

## What to Build

`final_tree_projection.py` derives the completion receipt path with `str(Path(...))`. On
Windows that returns `docs\tickets\...\x.completion.json`, and Git refuses it:

```
error: Invalid path 'docs\tickets\...\M03-evidencia-del-patron.completion.json'
fatal: git update-index: --cacheinfo cannot add ...
```

Delivery gates at `finalization-environment`, phase `git`. Nothing is published, which is
the correct failure, but no Windows delivery can complete its projection.

Two sites derive that path and must agree:

- line 735 builds it for `update-index`;
- line 536 validates a received manifest against the same expression.

The module already owns the right rule: `_path()` at line 157 returns `candidate.as_posix()`.
These two lines bypass it. Route them through the same normalisation instead of adding a
second dialect.

Measured proof that the separator is the whole defect, same blob and same repository:

| Separator | Result |
|---|---|
| `docs/tickets/.../x.completion.json` | accepted |
| `docs\tickets\...\x.completion.json` | `error: Invalid path` |

## Acceptance Criteria
- [ ] The receipt path is POSIX on every platform. On Windows the projection reaches
      `update-index` and Git accepts the path.
- [ ] Construction (735) and validation (536) derive the receipt path through the same
      normalisation, so a manifest produced on Windows validates on Windows.
- [ ] A regression test covers the receipt path and asserts no backslash appears in it. The
      test must be honest about what it proves: on POSIX it passes before and after the fix,
      because `str()` and `as_posix()` already agree there.
- [ ] `python3 -m unittest ticket-autopilot.tests.test_final_tree_projection` passes, or the
      repository's documented way of running that module's tests passes.
- [ ] No behaviour change on POSIX: the diff touches separator normalisation only.
- [ ] `source-content-drift` keeps its meaning as a real exclusion reason.

## Frontier
Ready. The root cause is measured, both sites are identified, and the module already
contains the normalisation to reuse.

## Step-by-Step Implementation Plan
1. Extract the receipt-path derivation into one helper that ends in `as_posix()`, or route
   both sites through `_path()`. Checkpoint: one expression, two call sites.
2. Replace line 735 and line 536 with that helper. Checkpoint: `grep -n "str(Path(" ` in the
   module returns nothing for receipt paths.
3. Add the regression test next to the existing projection tests. Checkpoint: the test names
   the platform limitation in a comment or docstring.
4. Run the module's test file. Checkpoint: green, and no unrelated test changes status.

## Testing Plan
- `python3 -m unittest` on `ticket-autopilot/tests/test_final_tree_projection.py`, before and
  after, to show no test regresses.
- The new test asserts the derived receipt path equals its POSIX form and contains no
  backslash.
- **Stated limitation**: on POSIX this test cannot fail before the fix. It is a
  platform-conditional guard, in the same spirit as `WT-04`. Claiming it proves the fix on
  Linux would be false.
- Real end-to-end proof is a Windows delivery whose projection applies. That is available on
  the machine where this was found, and it is what the fix must be checked against there.

## Out of Scope
- `ledger.py:808`, `str(Path(bundle["artifact"]).resolve())`. That is an absolute local path,
  not a Git index path. Native separators are correct there.
- Provider text fidelity, owned by `windows-text-fidelity-wayfinder.md`.
- Adding a Windows CI job. `WT-07` was canceled, and reopening that decision is not this
  ticket's business.

````
