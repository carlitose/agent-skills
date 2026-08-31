# Resolve Pi-normalized local package source identities

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-pi-local-package-source-identity`
- Role: spec
- Parent: [Synchronize the local agent-skills Pi package after integrated tasks](agent-skills-post-task-pi-sync.md)

### Children

- [PLS-01 — Accept Pi-normalized local package source identities](../tickets/ticket-autopilot-pi-local-package-source-identity/01-accept-pi-normalized-local-package-source-identities.md)

## Type

Bug-analysis specification.

## Related contract

This specification repairs the package-install/readback portion of
[the post-task Pi synchronization contract](agent-skills-post-task-pi-sync.md). It does not
change its exact integrated-head, ownership, authority, rollback, Pi self-update, or reload
boundaries.

## Observed behavior

The first authorized live PIS-01 synchronization bound integrated head
`377516f6244b5e1b973e0a4f08684ffed9823c4d` and tree
`6ff39be75ffd8a8776a0eb9bcdd2b34562fde5d3`, materialized its dedicated checkout, replaced
owned skills transactionally, and invoked Pi 0.84.4. It then failed closed with:

```text
pi install readback must create exactly one local package entry
```

The transaction persisted no completion receipt, completed its rollback path, restored
`settings.json` to its exact pre-sync digest, and removed the temporary ownership manifest. The
clean dedicated checkout remains at the authorized head as intended. No pre-mutation live
skill-tree digest was recorded, so byte-for-byte restoration of those roots is not claimed.

A disposable live Pi invocation reproduced the mismatch without touching the real settings:
`pi install <absolute-checkout>` persisted a source relative to `PI_CODING_AGENT_DIR`, and
`pi list` printed that relative configured source as the package row followed by the resolved
absolute installed path. Pi's package documentation explicitly permits absolute and relative
local package inputs and resolves relative settings entries against their settings file.

## Root cause

The synchronization code models the approved checkout only as an absolute path literal:

- pre-install migration recognizes an existing local entry only when its source string equals
  the absolute checkout;
- settings reconciliation requires exactly one post-install entry with that literal; and
- initial and replay `pi list` verification count only a package row equal to that literal.

Pi intentionally normalizes an installed local source relative to the settings root before
persisting it. The live entry therefore has the same resolved package identity but a different
string representation. Fake-Pi tests append the absolute input verbatim, so they did not cross
this external normalization boundary.

## Target behavior

Treat a local Pi package source as an identity resolved against the parent of the approved
`settings.json`, not as an unscoped string literal.

For every settings or `pi list` source considered as the PIS local package:

1. interpret an absolute source directly and a relative source against the exact Pi settings
   root;
2. canonicalize the result using the same filesystem identity boundary as the normalized
   request;
3. accept it only when it equals the actor-approved dedicated checkout; and
4. count exactly one such package row while continuing to reject duplicate Git or local
   identities.

Preserve the Pi-produced source spelling when converting the package entry to object form with
`skills: []`. This keeps Pi's normalized relative representation while the receipt continues
to bind the absolute checkout. Existing absolute local entries remain valid by resolved
identity.

`pi list` verification must inspect package rows only. It must not treat the separately
indented installed-path display as a second package or as substitute evidence for a wrong
configured source.

## Semantic invariants

- The approved absolute checkout, exact integrated head/tree, actor, evidence, settings path,
  and agents root remain immutable intent fields.
- A relative source is never accepted merely because its basename or suffix resembles
  `agent-skills`; its canonical resolution must equal the approved checkout.
- Git package matching remains restricted to the exact normalized
  `carlitose/agent-skills` remote family and preserves the explicit source-replacement flag.
- Exactly one effective local checkout identity and at most one replaceable Git identity are
  permitted during migration; unrelated local, Git, npm, filtered, and top-level settings
  entries remain unchanged.
- First install, second-head refresh, failed-state replay, and completed replay use the same
  source-identity rule.
- Rollback and integrity behavior remain unchanged. A failed or contradictory readback never
  creates a receipt.
- The operation invokes only `pi install` and `pi list`; it never invokes `pi update` or
  claims an active session reloaded.
- The existing PIS-01 sync authority remains bound to its exact intent. This repair grants no
  new local-sync, implementation, merge, provider, wiki, bootstrap, cleanup, or reload
  authority.

## Failure modes

Fail closed when a source is malformed, resolves somewhere other than the approved checkout,
resolves through a changed path identity, appears more than once, coexists with contradictory
Git identities, or cannot be proven from a package row. Preserve the existing transaction
backup and error-reporting behavior.

A previously failed exact PIS-01 state may be retried only with the same immutable intent. The
retry first executes the existing recovery path and then re-observes Pi; it must not edit the
failed state into success or infer a receipt from the earlier install attempt.

## Implementation slice

One tracer-bullet ticket should:

- introduce one settings-root-aware local source identity helper;
- use it in pre-install template selection, settings reconciliation, initial `pi list`
  verification, and completed replay;
- preserve the Pi-produced relative source when adding `skills: []`;
- replace the absolute-only Fake-Pi assumption with coverage for Pi-style relative
  persistence and list output while retaining absolute compatibility and duplicate rejection;
- exercise an exact failed-state retry without changing its actor/evidence-bound intent;
- update the parent spec and operator documentation where they imply literal absolute
  persistence; and
- run focused, repository, extension, forward, static, context, and disposable live-Pi
  verification without mutating the real Pi settings during QA.

## Acceptance outcomes

1. A Pi-style install that receives an absolute checkout but persists a relative settings
   source completes with one filtered local package and a valid receipt.
2. The same code accepts an existing absolute local source and produces no duplicate package.
3. Relative and absolute sources resolving to the approved checkout are treated as one
   identity; two matching rows fail as duplicates.
4. A relative source resolving anywhere else, a misleading basename, or an installed-path-only
   list line cannot satisfy readback.
5. First migration preserves `skills: []`, removes only the exact authorized Git source, and
   preserves unrelated settings semantically.
6. Failed-state retry and completed replay re-observe the same exact intent and do not issue a
   second install after completion.
7. The original rollback, ownership, exact-head/tree, no-self-update, and no-reload invariants
   continue to pass.
8. A disposable Pi 0.84.4 boundary test proves the real relative persistence/list shape; it is
   reported as local environment evidence, not as proof of session reload or portability to
   unexecuted platforms.

## Verification strategy

- **Unit:** source resolution against settings root, relative/absolute equivalence, duplicate
  and mismatch rejection, package-row parsing, and source-spelling preservation.
- **Integration:** a disposable Git/settings/skills fixture whose Pi runner persists relative
  paths exactly as Pi does; cover first migration, failed-state retry, second head, replay,
  rollback, and unrelated entries.
- **Regression:** all Ticket Autopilot tests, mandatory extension tests, forward scenarios,
  static tree/diff checks, artifact audit, and controlled context budget.
- **Live disposable boundary:** invoke the installed Pi 0.84.4 with a temporary
  `PI_CODING_AGENT_DIR`, install the exact candidate checkout, and prove relative settings plus
  `pi list` readback. Do not point this test at the real settings or skill roots.
- **Post-integration:** replay the already authorized exact PIS-01 synchronization and require
  a receipt before instructing the user to run `/reload`.

## Alternatives rejected

- **Force Pi settings to an absolute source after install:** technically accepted by Pi, but
  rewrites Pi's normalized representation and leaves the real normalization boundary
  untested.
- **Trust the indented installed path from `pi list`:** can mask a wrong configured package
  source and confuses a display path with the package row.
- **Manually edit the live settings before retry:** bypasses the receipt-backed transaction,
  rollback, and immutable intent.
- **Treat the failed sync as complete because checkout materialization succeeded:** violates
  the requirement for exact package readback and a completion receipt.
