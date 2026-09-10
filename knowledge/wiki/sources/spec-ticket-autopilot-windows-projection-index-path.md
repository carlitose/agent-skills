---
type: source
title: "Windows Index Path Separator in Tracked Completion Projection"
identity_key: spec:ticket-autopilot-windows-projection-index-path
identity_strength: stable
source_path: docs/specs/ticket-autopilot-windows-projection-index-path.md
source_digest: sha256:b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-08
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Windows Index Path Separator in Tracked Completion Projection

Compiled from `docs/specs/ticket-autopilot-windows-projection-index-path.md`. Identity is `spec:ticket-autopilot-windows-projection-index-path`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-08** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-windows-projection-index-path-wps-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[11],"status":"present"},"goals":{"headings":[9],"status":"present"},"invariants":{"headings":[10],"status":"present"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/spec-ticket-autopilot-windows-projection-index-path.md","payload_bytes":5975,"payload_sha256":"b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242"}],"payload_bytes":5975,"payload_sha256":"b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242","schema":1,"source_digest":"sha256:b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242","source_identity":"spec:ticket-autopilot-windows-projection-index-path","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 9: Destination |
| exclusions | 11: Out of Scope |
| decisions | no matching section identified in the source; complete source retained |
| invariants | 10: Invariants |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5975,"payload_sha256":"b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242","schema":1,"source_digest":"sha256:b19e25a25711d7b59a723bf643140a859b539592233acc4c98d847bd26987242","source_identity":"spec:ticket-autopilot-windows-projection-index-path"} -->
````markdown
# Windows Index Path Separator in Tracked Completion Projection

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-windows-projection-index-path`
- Role: `spec`
- Standalone: true

### Children

- [WPS-01](../tickets/ticket-autopilot-windows-projection-index-path/done/01-posix-index-paths.md) — `artifact:wps-01-posix-index-paths`

Lineage (evidence, not owner edges): same defect family as
`docs/specs/windows-text-fidelity-wayfinder.md` and
`docs/tickets/autopilot-windows-digest-drift/done/`. This is a different property: those
maps own **text** crossing the provider boundary, this one owns a **path** crossing the Git
index boundary.

## Type

Bug-analysis specification.

## Status

Ready. Root cause measured on Windows 11, Python 3.12.10, Git for Windows, against
`301accd`.

**Superseded in part while this was being written.** `APM-02` and `APM-03` reached `main`
first and wrapped both expressions in `_path(...)`, which ends in `as_posix()`. Verified on
Windows against `origin/main`: the derived path is `docs/tickets/.../01.completion.json`
and `git update-index` accepts it. The production defect is therefore already fixed on
`main`, and this map keeps only what is still missing there:

- **no test covers the separator.** `main`'s test file contains no occurrence of `posix`,
  `backslash`, or `separator`. The fix landed without a guard, so it can come back;
- **no record of why it happened**, or why nobody saw it for a week.

## Observed Regression

Tracked completion projection builds the completion receipt path with `str(Path(...))`.
On Windows that returns backslashes. Git rejects backslashes in index paths, so
`git update-index --add --cacheinfo` fails and the whole delivery gates.

Measured failure, verbatim:

```
git update-index --add --cacheinfo 100644,45b24ce1,
  docs\tickets\langfuse-modelo-y-coste-por-entorno\done\M03-evidencia-del-patron.completion.json
  failed: error: Invalid path
```

Delivery result: `gated`, gate `finalization-environment`, phase `git`. The gate is
correct: the runner fails closed and publishes nothing. The cause is not the environment.

## The Two Sites

Both live in `ticket-autopilot/scripts/autopilot/final_tree_projection.py`:

| Line | Code at `301accd` | Role |
|---|---|---|
| 735 | `receipt_path = str(Path(destination).with_suffix(".completion.json"))` | builds the index path |
| 536 | `receipt["path"] != str(Path(ticket["destination_path"]).with_suffix(".completion.json"))` | validates a received manifest against the same shape |

They must change together. Fixing only 735 makes a Windows-produced manifest fail its own
validation at 536; fixing only 536 leaves the Git call broken.

The module already owns the correct normalisation. `_path()` at line 157 ends with
`candidate.as_posix()` and every path that flows through it is repository-relative POSIX.
These two sites bypass it.

`main` now wraps each expression in `_path(...)` separately, so the derivation is written
twice in two places. That duplication is what let the defect exist: the same formula lived
in two lines, and only one of them had to be wrong. This map therefore keeps one function,
`_receipt_path()`, that both sites call, and it still routes through `_path()` so the
repository-relative guarantees `APM-02` and `APM-03` added are preserved.

## Why It Stayed Hidden

The defect has existed since `b0a9816` (02/09). It never fired because a second problem
masked it.

With `core.autocrlf=true`, worktree bytes differ from the blob, projection raises
`ProjectionExcluded("source-content-drift")`, and the `update-index` call is never
reached. Fourteen projection artifacts recorded on this machine, six of them naming that
exact reason:

```
07/09 13:39  93811882  excluded  source-content-drift
07/09 17:24  49fc0869  excluded  source-content-drift
07/09 17:37  c2d4212b  excluded  source-content-drift
07/09 18:13  2e2423a9  excluded  source-content-drift
07/09 18:23  de672609  excluded  source-content-drift
08/09 09:41  af0fa261  excluded  source-content-drift
```

Setting `core.autocrlf=false` in a consumer repository removes the drift, projection
starts applying for real, and the latent defect surfaces on the first delivery. So a
correct local fix in one repository exposes a real defect here. That ordering is worth
recording: **the exclusion path was doing the work of a shield, and nobody knew.**

## Root Cause, Proven

Same blob, same repository, same command, only the separator changes:

```
forward slashes  -> ACCEPTED
backslashes      -> REJECTED   error: Invalid path 'docs\tickets\...'
```

`str(Path("a/b/c.md"))` returns `a\b\c.md` under `sys.platform == "win32"` and `a/b/c.md`
everywhere else. That single difference is the whole defect. No POSIX host can observe it,
which is why the suite has never caught it.

## Destination

The projection produces POSIX index paths on every platform, one function owns that
derivation, and a test proves it.

## Invariants

- **No behaviour change on POSIX.** `str()` and `as_posix()` already agree there. The diff
  must be observable only on Windows.
- **The two sites stay in agreement.** Construction and validation derive the receipt path
  the same way.
- **No new normalisation dialect.** Reuse the module's existing rule rather than inventing
  a second one.
- **The exclusion path keeps its meaning.** `source-content-drift` stays a real exclusion
  reason; it must not become a workaround for this defect.

## Out of Scope

- Text fidelity at the provider boundary. That is
  `docs/specs/windows-text-fidelity-wayfinder.md`.
- `str(Path(...).resolve())` at `ledger.py:808`. That value is an absolute local artifact
  path, not a Git index path, and native separators are correct there.
- The Windows green-suite baseline. `WT-06` owns it.

## Open Questions (human)

1. Should a Windows job run in CI? Without one this class of defect is only found by
   whoever works on Windows. `WT-07` was canceled, so the answer today is no.

````
