# Opt-in single-session chain

`chain_session.ChainSession` owns one explicit RPC process, its persistent session and native
entry facts. `chain_controller.ChainController` runs one supplied canonical ticket in a
caller-owned separate copy; it is not a folder scheduler or a delivery command. Import the
existing `autopilot` pure contracts from `ticket-autopilot/scripts` on the caller's Python
path. No package installation or global extension change is required by these modules.

The caller supplies the SessionOwner, exact scope, literal test argv, typed coverage/risk
questions, and `DecisionEngine` ports. No live transport is chosen by default. Permissions
are separate for Jev and judge and must return literal True. The external-call budget is
reserved before each attempt; estimates/missing usage are retained, never called a bill or
zero. Jev thresholds remain 0.2/0.8/0.75/2.5 and only HTTP 429/529 retries, at most 3 attempts.
The judge never overrides a decided negative and runs once per question/candidate. Changed
binding or an interrupted reservation needs reconciliation, not replay. Risk uncertainty
widens findings-only review; global coverage is a separate question after observed tests.

Facts/checkpoints and every test receipt live outside the product tree (or under the owned
Git directory). Native CandidateRef v2 uses actual Git trees and canonical ticket content.
Only the copy is changed; read-only turns and tests are fingerprinted. Completed-local is
not a ticket move, commit, PR or merge. Three final failures are cumulative for each ticket;
failed work is archived before restoring the last valid tree for an independent ticket.
Dependent tickets remain blocked. No `reset --hard`, generic clean, or original-repo write.

Fix and read-only review receive candidate-bound public test observations (argv, exit/failure,
stdout/stderr) from the controller, not the builder's assertion. Their JSON preview is at most
32 KiB; each truncated stream is marked and points to a complete owned receipt with SHA-256.
Only exact public receipt paths may be followed; this is not permission to inspect hidden data.
Coverage receives the same attributed `test_observations` preview, not duplicate full streams;
complete receipts remain in the controller and hashed files. The literal frozen diff, ticket,
review and CandidateRef remain complete in the hashed semantic state. Truncation is explicit,
not proof of a criterion: green tests and a readable review without an explicit blocker still
require a semantic YES, and NO or uncertainty never becomes approval. Parsed should-fix/nit
findings stay in the full review and are adjudicated against the public task/diff/evidence;
they are not automatically blockers or relabeled clean. An explicit blocker or failed public
test remains a veto. Uncertain adjudication gates without consuming a code-failure slot.
The coverage question checks required correctness and grounded material defects, not optional
improvements or requirements invented by the reviewer. This is an explicit internal payload change, not a
migration or replay of prior decisions. Fixing intake does not prove a real Jev/judge cycle.
That adjudicated question lives in `benchmarks/delivery-bench/questions/review.scope_complete.json`
and is passed as `coverage_question`; the distributed `ticket-driver/questions/` registry and its
hashes stay unchanged for `driver.py`. Chain findings call `parse_findings(..., any_extension=True)`
to accept relative filenames with extensions, including C/JS/TS/Python, in the stated
severity/path/line format; the distributed default remains Python-only. This adds no non-Python AST/risk analysis. Unparsed review retains
original prose and gates immediately without becoming clean, calling coverage, or consuming
a code-failure slot. A gate is not a model-quality failure or a completed ticket.

Frozen diffs are stored as raw bytes and bound to the full CandidateRef. Non-UTF-8 diffs are
`infrastructure-gated`, with original bytes/candidate preserved; no lossy decoder can approve
them. Launch/capture/cleanup problems gate with public receipts, not three model failures.
A started test timeout without cleanup issues remains a failed test, not proof of process death.
Unexpected controller exceptions checkpoint a safe exception kind and preserve the original
exception for the caller; interrupted turns keep inflight facts and partial product work.

Unknown process death, inflight checkpoint, changed original/base/product/session, or budget
exhaustion fail closed and preserve work. A valid completed checkpoint may be reentered with
the same owner; this is not proof of universal controller-crash recovery. A native resource
change must separately reconcile observed death, checkpoint, permission and remaining budget.

Tests use synthetic repositories, real Git/test processes, a fabricated Pi peer and stubbed
Jev/judge. They are not model-quality, authentication, native-runtime, cost or performance
proof. The extension/receipt adapter in SPC-03 is opt-in only. Publication still needs its
own authority, required current local profile and exact-head hosted CI.

For an explicit benchmark cell, the caller may supply existing owned directories as scope,
such as `.`. Their classification is frozen before the builder turn; replacing a file with
a directory does not widen a file-only grant. External/symlink-outside, absolute, parent and
Git-metadata paths are rejected. Coverage state includes the literal diff of the exact frozen
Git trees before question/state hashing. The complete request still has a 65,536-byte bound:
a remaining oversized ticket/diff/metadata yields `semantic-input-bound` with observed byte
count and limit before either port is called. No diff/ticket is silently truncated, limit
raised, retry added, or green-test assertion trusted. Raw artifacts and gate stay preserved.

## Owned benchmark preparation and estimates

`benchmarks/delivery-bench/persistent_arm.clone_product(original, target)` requires a committed,
clean owned seed and a new separate destination. It selects LF checkout configuration before
clone, retains normal repository attributes, removes the new clone's origin and verifies its
initial Git tree equals the seed. Existing destinations are never replaced; a failed/partial
clone is preserved and cannot authorize a launch. Neither source nor global Git config is written.

`Budget.observe_operator_cost(usd_estimate, source)` records an attributable **cumulative**
operator estimate from the trusted caller's usage evidence. The source identifies that exact
observation (for example, a usage artifact and digest), not a fresh per-cell counter. Repeating
it is idempotent; changing its amount is an identity error. Known estimates cannot decrease,
including after an unknown observation. `None` means unreported, never zero. The caller must
refresh growing operator usage before further admission; the adapter cannot discover or invoice
an unrelated operator session. Fixture zero-cost observations are not admissible live evidence.

Known completed public-test failures reach the bounded code-quality/fix path even if the
review format is unresolved. Original prose, partial findings and receipts stay preserved;
no semantic approval can override failed tests. An unparsed review with green tests remains
a gate without consuming quality failures. Capture/cleanup and readonly gates still precede
that distinction. Review markers must anchor concrete relative files, not bare directories.

`Budget.admit_launch(argv)` checks the actual launch gates, bound argv, cumulative funds and
launch capacity without starting or consuming a process. Callers use it before declaring
prelaunch ready, not while an already-admitted process is active. `launch` reuses that check.
`Budget.renew_launch_capacity(actor='human:user', mandate_ref=...)` records one next-launch
capacity binding under a caller-validated covered mandate. It never changes the original
authority file/hash, counters, charges, monetary ceiling, permissions or unresolved cost/gates.
An unused binding is idempotent; after consumption, a still-valid repair-loop mandate can
bind the next launch with its original provenance. The caller owns scope/revocation evidence:
a nonempty reference alone is not consent, and this API does not automatically retry.

`Budget.cost_report()` and new request receipts' `cost_report` distinguish priced experimental
usage, the operator estimate, combined estimate and remaining estimated headroom. Combined and
remaining values are null while either component is unreported. Reserve/launch fail closed then;
otherwise both estimates count against the cumulative ceiling. `invoice_total_usd` remains null:
SDK prices/FX/reservations are not a final bill or a provider-side hard cap. Historical request
receipts and ledgers retain their original shape/identity; they are not reinterpreted or migrated
as evidence of corrected behavior. New receipts also carry the explicit component report;
`budget_estimated_usd` still denotes only priced experimental usage, never combined cost.
No live costs were reconciled by a local fixture.

## Judge command bridge

`chain_judge.ChainJudge` is a `DecisionEngine` judge port using the same `ChainSession`.
The future caller must separately authorize loading `ticket-driver/extensions/chain-judge.ts`
via explicit Pi argv. It is not in this package's installed extension list. The command is
`/chain-judge <bound JSON>`; it is not a registered model tool. The trusted caller's grant
supplies literal permission, an already-reserved call budget and an output-token cap. That
cap is not a guarantee about input tokens, billing or total provider spend.

The opt-in extension lazily creates one `ModelRuntime` with network catalog refresh disabled
and uses its configured local stores. It does not inherit session-only extension provider
registrations. An exact provider/id lookup is mandatory; there is no alternate model or
credential retry. Native provider routing/auth and session-specific configuration still
need separate verification before use. No AgentSession or child Pi is created by the bridge.

Only the supplied question, criteria, contract and evidence enter its new system/user context;
no tools or builder transcript. Python canonical JSON bytes bind values such as 1.0 and
Unicode without cross-language reserialization assumptions. An append-only custom start
reserves the call before any await, and the custom result retains bindings, model, request
hash, text/stop/usage or sanitized failure. Custom entries are not model-facing messages.
Native `handled`, idle and exact fresh receipts are required, not a normal assistant reply.
An explicitly supplied reasoning level is passed to completeSimple and retained in the
bound receipt; the benchmark uses medium and does not silently downgrade that role.
`DecisionEngine` uses the existing final `Answer:` parser; tool/error/abort/length or malformed
answers never approve, but their returned usage remains observed or explicitly unknown.

The session ledger counts custom judge usage by stable call/entry identity. A direct native
usage alias suppresses the custom charge only after that exact native source and equal usage
are observed. Missing, multi-source or conflicting links fail closed, preserving the receipt.
All accounting is an estimate/fact trail, not an invoice. Stubbed Node backend/RPC tests
exercise the owned bridge only and do not establish live Pi/auth/model conformance.
