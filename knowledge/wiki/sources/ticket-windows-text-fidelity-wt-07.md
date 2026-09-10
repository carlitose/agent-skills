---
type: source
title: "Decide and introduce continuous integration"
identity_key: ticket:windows-text-fidelity/WT-07
identity_strength: stable
source_path: docs/tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md
source_digest: sha256:611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e
source_status: present
artefact_kind: ticket
disposition: canceled
created: 2026-08-12
created_provenance: git-commit
disposition_changed: 2026-08-13
disposition_changed_provenance: git-rename
---

# Decide and introduce continuous integration

Compiled from `docs/tickets/windows-text-fidelity/canceled/07-decide-and-introduce-ci.md`. Identity is `ticket:windows-text-fidelity/WT-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-12** via `git-commit`
- Disposition changed: **2026-08-13** via `git-rename`

## Graph

- Parent source: [[sources/artifact-windows-text-fidelity-wayfinder]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-windows-text-fidelity-wt-07.md","payload_bytes":2864,"payload_sha256":"611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e"}],"payload_bytes":2864,"payload_sha256":"611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e","schema":1,"source_digest":"sha256:611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e","source_identity":"ticket:windows-text-fidelity/WT-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2864,"payload_sha256":"611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e","schema":1,"source_digest":"sha256:611d17097e5388223875177236cca933ee3cf1874cdb2acd943c226d622d685e","source_identity":"ticket:windows-text-fidelity/WT-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WT-07"
execution_mode: HITL
blocked_by: []
---

# Decide and introduce continuous integration

## Artifact Graph
- Artifact ID: `artifact:wt-07-decide-and-introduce-ci`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
There is no continuous integration in this repository. Verified: no `.github/` directory,
no `azure-pipelines*`, no `.gitlab-ci*`, no `Jenkinsfile`, and `gh pr checks 78` reports
"no checks reported on the branch".

This is the gate underneath every other ticket on this map. PR #78 stated, in good faith,
"I am relying on CI rather than claiming a green result I did not see" — a compensating
control that does not exist. The two regressions it shipped would each have been caught by
a single suite run.

The decision content is real and belongs to a human: which provider, which platform matrix,
which Python versions, whether the suite's ~21-minute runtime is acceptable per PR or needs
splitting, and whether checks become required for merge.

## Acceptance Criteria
- [ ] A decision is recorded covering provider, platform matrix, Python versions, and
      whether checks are required for merge.
- [ ] CI executes `python -m unittest discover -s tests -t tests` for `ticket-autopilot`.
- [ ] The matrix includes Windows and at least one POSIX platform, since the entire defect
      family on this map is platform-dependent.
- [ ] The Python floor declared in `WT-04` is the floor tested.
- [ ] `gh pr checks` reports a result on a new PR.
- [ ] The runtime is measured and stated; the observed full-suite duration is ~1285s on
      Windows.

## Frontier
**Human decision required.** Invoke `grilling` before implementing: the matrix and the
required-checks question determine cost and merge friction for everyone working in this
repository, and a wrong default here is expensive to walk back.

Sequencing note: CI turned on before `WT-06` will be red on Windows from the first run.
Decide deliberately whether to land `WT-06` first, or to start with a POSIX-only job and
add Windows once green.

## Step-by-Step Implementation Plan
1. Run `grilling` on provider, matrix, and required-checks.
2. Record the decision through `to-spec`.
3. Implement the pipeline.
4. Open a throwaway PR and confirm checks report.

## Testing Plan
The pipeline verifies itself: a PR that reports checks is the evidence. Confirm both a
passing and a deliberately failing run, so the pipeline is known to be able to fail — a CI
that cannot go red is the same defect as `FakeAzureRunner` in `WT-01`.

## Out of Scope
- Fixing the tests the pipeline will report as red, which is `WT-06`.
- Publishing coverage, linting, or release automation.

```
