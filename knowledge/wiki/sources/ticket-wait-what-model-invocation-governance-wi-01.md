---
type: source
title: "Register wait-what as an explicit user-invoked compatibility surface"
identity_key: ticket:wait-what-model-invocation-governance/WI-01
identity_strength: stable
source_path: docs/tickets/wait-what-model-invocation-governance/done/01-register-wait-what-user-invocation.md
source_digest: sha256:8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: bcf736aa887f46f0
---

# Register wait-what as an explicit user-invoked compatibility surface

Compiled from `docs/tickets/wait-what-model-invocation-governance/done/01-register-wait-what-user-invocation.md`. Identity is `ticket:wait-what-model-invocation-governance/WI-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-wait-what-model-invocation-governance-diagnostic]]

## Run

Completed under autopilot run `bcf736aa887f46f0`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-wait-what-model-invocation-governance-wi-01.md","payload_bytes":3150,"payload_sha256":"8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465"}],"payload_bytes":3150,"payload_sha256":"8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465","schema":1,"source_digest":"sha256:8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465","source_identity":"ticket:wait-what-model-invocation-governance/WI-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3150,"payload_sha256":"8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465","schema":1,"source_digest":"sha256:8920acdaa0065583781382a12accb7e36793bd77f0652eb956348986519b7465","source_identity":"ticket:wait-what-model-invocation-governance/WI-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WI-01"
execution_mode: AFK
blocked_by: []
---

# Register wait-what as an explicit user-invoked compatibility surface

## Artifact Graph

- Artifact ID: `artifact:wi-01-register-wait-what-user-invocation`
- Role: `ticket`
- Parent: [wait-what model-invocation governance diagnostic](../../specs/wait-what-model-invocation-governance-diagnostic.md)

## Parent Spec

[Wait-what model-invocation governance diagnostic](../../specs/wait-what-model-invocation-governance-diagnostic.md)

## What to Build

Bring the deliberately hidden `wait-what` skill under the repository's model-invocation
governance. Generalize Ground B narrowly enough to cover a manual compatibility surface for
a capability already available through ordinary conversation, classify `wait-what` as
`user-invoked`, and refresh the controlled hidden-skill inventory without changing the
skill's invocation flag or visible listing bytes.

## Acceptance Criteria

- [ ] `docs/model-invocation-policy.md` classifies `wait-what` as `user-invoked` with a
      truthful Ground B reason that does not claim its optional argument is required.
- [ ] Ground B remains narrow: it covers compatibility surfaces for an already available
      capability and does not hide model-selectable implementation, review, QA, research,
      diagnosis, or planning workflows.
- [ ] The controlled repository inventory expects seven hidden skills, six existing hidden
      skills remain unchanged, and visible listing bytes remain `4,999`.
- [ ] The complete model-invocation policy test module passes.
- [ ] The context-budget baseline advances past the hidden-count assertion; any independent
      static-closure or ceiling drift is reported as an explicit base limitation and is not
      concealed by changing unrelated values in this ticket.
- [ ] No `wait-what` behavior, language profile, output contract, or front-matter invocation
      flag changes.

## Frontier

Ready. The introducing commit, parent/addition reproduction, intended hidden classification,
and independent context-budget limitation are pinned in the diagnostic spec.

## Step-by-Step Implementation Plan

1. Add the policy regression expectation for `wait-what` and observe the current missing-row
   failure.
2. Generalize Ground B and add the `wait-what` classification row while preserving the flag.
3. Refresh only the hidden inventory count and prose owned by this addition.
4. Run policy, inventory, artifact, and full runner checks; isolate the separately diagnosed
   context-budget drift if it remains.

## Testing Plan

Run the full model-invocation policy module, the controlled context-budget baseline, targeted
front-matter discovery, Artifact Graph audit, and the full ticket-autopilot suite. Compare the
visible listing byte count before and after. Report the independent closure/ceiling drift
without attributing it to this candidate.

## Out of Scope

- Changing `wait-what` to model-invocable.
- Rewriting its controlled-language instructions.
- Raising or removing the ticket-autopilot context-budget ceiling.
- Fixing the independent workflow static-closure baseline drift.

```
