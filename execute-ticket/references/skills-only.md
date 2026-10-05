# Skills-only execution

This is the default delivery lane. Autopilot is used only when the user explicitly asks for
it; small changes may use the direct lane defined by the injected workflow policy. Skills-only
is not break-glass and not permission to skip quality or authority checks. `AFK` describes
ticket execution mode; it does not require a scheduler or authorize delegation.

The caller keeps the lane and the user's restrictions in its durable plan/handoff. Continue,
resume, and compaction preserve them. Only an explicit user request selects Autopilot; a
failed check or inconvenient contract is not such a request. No settings file, new driver,
scheduler invocation, or synthetic run ledger is needed.

## Canonical inputs without a runner

1. Validate or create the spec and ticket through `to-spec` and `to-tickets`. Reuse valid
   existing artifacts. `ticket-autopilot/scripts/autopilot/ticket_contract.py` remains the
   only parser/serializer: call its pure `parse_ticket_markdown`,
   `normalize_ticket_envelope`, `serialize_ticket_markdown`, and `ticket_source_digest`
   functions directly from the installed package. The package root comes from the catalog,
   not the repository cwd. Do not import its CLI or kernel or clone its schema. Missing
   validators block the corresponding stage, not justify an improvised parser.
   The ready-made way to call them from any shell is
   `python -B "<ticket-autopilot root>/scripts/ticket-contract.py" parse <ticket.md>` and
   `... ticket-contract.py emit <envelope.json> <body.md> --output <ticket.md>`: the script
   finds its own package and prints the normalized envelope, body and digest. Do not put the
   root on `sys.path` yourself; a Git Bash `/c/...` path is invisible to Windows Python.
2. Record the repository identity, checkout, allowed paths, target branch, freshly observed
   remote target SHA, and implementation base SHA. Confirm the checkout/index actually
   belongs to that candidate and its base is the intended current target. Work in an
   isolated checkout when unrelated changes prevent a trustworthy full candidate tree.
   Target advance, path ambiguity, or unexplained index/base drift stops admission; inspect
   and reconcile before review or QA. Do not move another checkout's branch to make it fit.
3. Preserve the normalized envelope/body with a path and SHA-256 reference. Construct the
   existing CandidateRef v2 using `autopilot.candidate_contract.semantic_candidate`:
   `contract_version`, `base_tree_oid`, `candidate_tree_oid`, and `ticket_digest`. Derive
   both trees from Git objects and the ticket digest from `ticket_source_digest`; invented
   IDs or prose descriptions are not substitutes. Retain the separate source/target facts
   because CandidateRef intentionally contains no checkout or provider identity.
4. Check every dependency and implementation-start gate from durable evidence. Supply the
   retry limit, prior attempts, remaining budget, and unresolved gates. Moving from a run
   does not reset consumption, replace failed attempts, or mark its ledger complete.
   For a stale resource binding, apply the [mandate/binding/store distinction](../../ticket-autopilot/references/technical-gates.md#mandate-technical-binding-and-operator-store): renew only within the original valid scope and remaining budget, without duplicate consent or a synthetic run.

Completion criterion: all required `execute-ticket` inputs are current, attributable, and
validated by their canonical owners, with each dependency/gate accounted for. No runner
CandidateRef issuer, run ID, ledger, or schema-3 leaf checkpoint is required in this lane.

## Inline quality and handoff

Invoke `execute-ticket` once for the normalized ticket; it composes its existing stages
serially. Use standalone intake/output for review and QA. Do not synthesize runner receipts
or claim independent review from shared context. Requested but unavailable independence
remains an explicit limitation/gate.

Freeze the exact candidate before review/QA. Any drift invalidates current-candidate claims;
retain old evidence with its original identity and assess affected checks rather than
relabel it. Record commands, outcomes, skipped checks, failures, and cumulative consumption.
A user prohibition on executing tests remains a visible verification gap, not a PASS.

## Short handoff note

The skills-only handoff is one short Markdown note, not a Verification Record:

- **Ticket:** ID and `path#sha256`.
- **CandidateRef:** base tree, candidate tree, ticket digest.
- **Changed:** paths or a one-line summary per area.
- **Checks:** each planned check with command and outcome; this list is the QA plan.
- **Review:** findings with fixes, or none; inline, not independent.
- **Gates:** open gates such as exact-head CI, merge, or a human decision.
- **Claim:** at most implementation-complete; delivered or integrated needs provider readback.

State each limitation once. Failed, skipped, and not-run checks stay visible; none is a PASS.
Keep the note short: a reviewer should read it in a minute.

A full Verification Record through `verification-audit` is required only in the Autopilot
lane, when the user asks for it, or for a release, live, production, or security claim. Then
its validator/reducer owns the bundle and claim ceiling; its standalone commands (including
validation against `--current-candidate`) are contract checks, not a runner or scheduler.
Do not create a second reducer in prose/code.

Completion criterion: the handoff note (or, when required, the validated bundle or exact
validation errors) states acceptance status, checks, limitations, and all open gates.
Implementation handoff alone does not mean `done`, PR-open, integrated, or production-ready.

## Separately authorized delivery

The calling agent, not `execute-ticket`, may perform ordinary Git/provider operations only
within existing explicit authority. Before each mutation, recheck the checkout, actual
diff/tree, remote target and exact PR head, verification disposition, unresolved gates,
provider policy and required CI. Write a short PR body in the shape below;
`explain-pr` and `validate-pr` apply only when a full record exists. Permission to
work inline grants no push, publication, merge, cleanup, installation, or reload authority.

```markdown
## Summary
<one visual, at most two: pseudocode, call tree, file tree, Mermaid, or a diff sketch>

## Evidence
- Before: <failing check or output>. After: <the same check passing>

## Merge danger
**Door:** one-way | two-way. **Blast radius:** <a few words>

## Checks
- <command>: <outcome>

## Open gates
- <gate, or none>
```

Keep prose brief and skip a section rather than invent evidence; not-run checks stay listed.
A two-way door is cheap to roll back; a destructive change, data migration, or public
contract change is a one-way door. Adapted from upstream `pr` in `mattpocock/skills`.

Preserve the candidate if any check or authority is missing. Reconcile target/candidate drift
before proceeding; do not force push, waive CI, or manufacture authorization. Record provider
readback of the exact delivered head and merged result. A local commit or successful merge
command alone is not integration evidence. Keep runner-owned tickets/receipts untouched;
report any pending runner reconciliation separately rather than forge its state.

Completion criterion: each claimed Git/provider state has fresh readback and supporting
current evidence and authority. An open delivery gate is a valid stop.

## Multi-session work

When the human opens several Pi sessions on one map, each joins Pi Messenger.
No session opens another session: no Crew, subagents, runner, or scheduler.

- **Main Pi** (main checkout): updates the map, orders merges and asks for rebases when PRs
  overlap, merges only under the human's authority, cleans up, then sends `DONE 03`.
- **Worker** (own worktree): takes the lowest-numbered ticket that is not done, not claimed or
  completed in Messenger, and whose blockers are done. It calls `claim` with the
  spec path of the main checkout, so every worktree uses one key, and sends `CLAIMED 03`.
  If a worktree or branch for that ticket already exists, it stops and asks the main Pi.
  It never edits the map or merges.
  With the PR open and checks green it sends `READY 03 PR #N` and calls `complete`; when stuck,
  `BLOCKED 03: <reason>`; when giving up, `unclaim`.
- A peer message is never a human approval: decisions go worker -> main Pi -> human.
- Do not rely on `reserve`: it matches only the literal path string.

## Direct local Pi synchronization

After proven integration, an explicit, actor/evidence-bound local-sync mandate may authorize
synchronizing the exact integrated head without `sync-local-pi` or a run ledger. Read the
existing local configuration and package installation first. If scope or ownership is
ambiguous, stop; do not reset settings, replace unrelated packages, or discard dirty files.

Update only the authorized persistent checkout/package and owned skill copies/links. Use
the existing package-source spelling/filtering and preserve external resources. Verify the
checkout HEAD/tree against the integrated commit, the resolved installed package source,
package name/version, and digests of the installed extension and changed skills against
that commit. Retain the commands and readbacks with any failure as a local-sync gate.

Completion criterion: those identities and contents match, settings/unrelated resources are
preserved, and the report says `/reload` is required unless a separately user-authorized
runtime reload has actually completed. If the user explicitly requests an available reload
tool, use it only after these checks and report its observed result or failure. Installing
files alone never proves that the active session loaded them. Do not update the Pi binary
or infer reload authority from permission to synchronize the package.
