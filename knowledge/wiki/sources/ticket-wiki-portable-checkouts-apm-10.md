---
type: source
title: "Make wiki project bindings portable across checkouts and computers"
identity_key: ticket:wiki-portable-checkouts/APM-10
identity_strength: stable
source_path: docs/tickets/wiki-portable-checkouts/done/01-portable-project-binding.md
source_digest: sha256:0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-07
disposition_changed_provenance: git-rename
run_id: apm-wiki-portability
---

# Make wiki project bindings portable across checkouts and computers

Compiled from `docs/tickets/wiki-portable-checkouts/done/01-portable-project-binding.md`. Identity is `ticket:wiki-portable-checkouts/APM-10`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]

## Run

Completed under autopilot run `apm-wiki-portability`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-wiki-portable-checkouts-apm-10.md","payload_bytes":6079,"payload_sha256":"0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf"}],"payload_bytes":6079,"payload_sha256":"0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf","schema":1,"source_digest":"sha256:0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf","source_identity":"ticket:wiki-portable-checkouts/APM-10","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6079,"payload_sha256":"0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf","schema":1,"source_digest":"sha256:0b19fc4d955c9fcf5e3074a8c9694c2bc57e29d8008e71824efd7ebda48cebbf","source_identity":"ticket:wiki-portable-checkouts/APM-10"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-10"
execution_mode: AFK
blocked_by: []
---

# Make wiki project bindings portable across checkouts and computers

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-10`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S10 — Portable Wiki Project Binding.

## What to Build
Make the same versioned internal wiki usable in different checkout directories and on different computers without editing a personal absolute path. Use `project_binding` as the single owner of relative-versus-absolute interpretation, update all consuming paths, and change this repository's `knowledge/llm-wiki-project.json` to the portable internal binding only as part of the verified implementation.

The previous APM-PREP-01 change repaired one checkout; do not reopen that completed ticket. S10 explicitly replaces its local-only target and the older absolute-binding-only assumption for internal wikis, while retaining exact-source/canonical-target separation.

## Acceptance Criteria
- [ ] A relative `project_root` resolves against the directory containing the binding file, not process cwd. This internal wiki uses `..`, a root-level internal wiki uses `.`, and malformed/missing targets fail actionably without a fallback.
- [ ] Writer/scaffold, discovery, ingestion, lint, ordinary sync, exact-source sync, and runner target selection share the binding interpretation. Other configuration values and schema-1 fields are preserved.
- [ ] Two independent clones or relocated copies of the same committed wiki/binding discover their own correct project docs from an unrelated cwd without rewriting tracked configuration. Include spaces and non-ASCII paths.
- [ ] Exact-source synchronization proves the expected head and Git-common relationship, reads the validated source layout, and keeps logical wiki identity, candidate ownership, and publication target at the explicit canonical project root. Temporary source and compile roots never become the target accidentally.
- [ ] Deliberately absolute checkout-pinned/external bindings remain supported and literal, including the existing explicit cross-checkout target case. Different clones do not acquire each other's local ledgers or grants merely because their remotes match.
- [ ] Wikilinks and project source paths stay relative. Unavailable machine-local session transcripts are reported as unavailable provenance without preventing project-doc synchronization.
- [ ] Tests retain rejection of ambiguous roots, invalid source/target identities, stale heads, symlink/containment violations, and partial tracking. Protected source/canonical worktrees stay unchanged during tracked synchronization.
- [ ] Repository documentation explains portable internal versus explicit pinned/external behavior and the superseded assumption without rewriting historical completion evidence. Native-platform and injected-provider observations remain clearly distinguished.

## Frontier
Ready in the separate `wiki-portable-checkouts` queue. No unresolved product decision. APM-11 consumes this binding/target behavior; no dependency on the unrelated APM receipt-path or Azure decoding tickets is required.

Execute inline. AFK does not authorize subagents. Missing native environments are reported, not fabricated. Queueing does not activate this ticket or grant publication, merge, recovery, or local Pi synchronization.

## Step-by-Step Implementation Plan
1. Reproduce the cwd-dependent relative value and absolute-path relocation failure using disposable project/wiki fixtures. Completion: assertions identify the incorrect root and confirm the expected local root in two layouts.
2. Implement the binding-owned interpretation and internal serialization; update every direct consumer of raw `project_root`, including exact-source projection and canonical runner target selection. Completion: consumer inspection and focused tests show no competing cwd-based interpretation remains.
3. Change only this repository binding's project-root value to the portable form and update the applicable docs. Completion: the binding bytes are identical between relocated checkouts and every other setting is unchanged.
4. Exercise discovery through tracked candidate creation using ordinary and exact detached source roots, plus the explicit absolute external/other-checkout cases. Completion: correct docs, candidate owner, source identity, and unchanged protected trees are independently asserted.
5. Run focused binding, ingestion/lint, sync, and runner wiki regression suites. Completion: record actual results and platform limitations; keep any long-path publication failure assigned to APM-11.

## Testing Plan
- Unit: binding location versus cwd, root-level/nested internal layouts, writer/scaffold, explicit absolute values, absent/malformed targets.
- Local Git integration: two clone/relocation paths, unrelated cwd, exact detached source, canonical target without a materialized wiki, explicit absolute cross-checkout target, and strict negative identity/tracking cases.
- Relevant owners: `llm-wiki/tests/test_project_binding.py`, `test_ingest_docs.py`, `test_lint_drift.py`, `test_sync_project.py`, and `ticket-autopilot/tests/test_wiki_sync.py` / `test_wiki_sync_forward_matrix.py`.
- Use hermetic local Git fixtures without global configuration changes. Observe native Windows and POSIX separately; mocks are not native-platform evidence.

These are planned checks, not implementation or verification results.

## Out of Scope
- Windows long-path candidate publication/recovery, owned by APM-11.
- Generic path/configuration frameworks, automatic repository searches, silent absolute-binding rebinding, or copying runtime authority between computers.
- Modifying installed/global skills, regenerating wiki pages inside the implementation candidate, editing old ledgers, or reopening predecessor tickets.

```
