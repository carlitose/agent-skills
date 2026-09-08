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

| Line | Code | Role |
|---|---|---|
| 735 | `receipt_path = str(Path(destination).with_suffix(".completion.json"))` | builds the index path |
| 536 | `receipt["path"] != str(Path(ticket["destination_path"]).with_suffix(".completion.json"))` | validates a received manifest against the same shape |

They must change together. Fixing only 735 makes a Windows-produced manifest fail its own
validation at 536; fixing only 536 leaves the Git call broken.

The module already owns the correct normalisation. `_path()` at line 157 ends with
`candidate.as_posix()` and every path that flows through it is repository-relative POSIX.
These two sites bypass it.

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

The projection produces POSIX index paths on every platform, and a test proves it.

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
