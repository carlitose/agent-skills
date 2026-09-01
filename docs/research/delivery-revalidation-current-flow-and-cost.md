# Delivery Revalidation Current-Flow and Cost Seed

## Artifact Graph
- Artifact ID: `artifact:delivery-revalidation-current-flow-and-cost`
- Role: `research`
- Parent: [DRV-01 — Map the completion-to-delivery revalidation flow](../tickets/delivery-revalidation-efficiency/01-map-current-flow-and-cost.md)

## Status
Seed evidence only. DRV-01 owns the complete call-graph, replay, failure, and cost investigation.

## Bounded Question
Which exact state transitions and completion effects force delivery revalidation today, and which
parts of the repeated quality cycle are causally necessary for an exact final-tree claim?

## Initial Primary Anchors

- [`Kernel.prepare_delivery_revalidation`](../../ticket-autopilot/scripts/autopilot/kernel.py)
  resets a verified ticket to `review`, retains only `implement` and `simplify`, invalidates leaf
  artifacts, increments artifact generation, and clears stale delivery outputs.
- [`delivery-revalidate` handling](../../ticket-autopilot/scripts/autopilot/cli.py) derives and
  binds the changed CandidateRef before invoking the kernel transition.
- [`Kernel._invalidate_leaf_artifacts`](../../ticket-autopilot/scripts/autopilot/kernel.py)
  removes the review/QA/verification handoff state that cannot be reused automatically.
- [`test_kernel.py`](../../ticket-autopilot/tests/test_kernel.py),
  [`test_cli.py`](../../ticket-autopilot/tests/test_cli.py), and
  [`test_ticket_sources.py`](../../ticket-autopilot/tests/test_ticket_sources.py) own current
  state, CLI, tracked/ignored completion, grant, replay, and tamper fixtures.

## Initial Observation
The current transition is conservative and coherent: a changed CandidateRef cannot inherit a
final-tree claim without revalidation. The duplicated broad suite is not itself the invariant;
it is the consequence of lacking a narrower, versioned proof for runner-authored deterministic
completion effects.

In the local OHR-02 case, both the implementation tree and completion-projected delivery tree ran
702 Ticket Autopilot, 76 verification-audit, 165 llm-wiki, 24 Artifact Graph, and 6 extension
tests. The second tree added completion movement, receipt, and link repoints. This is a single
local prioritization datum, not a general benchmark or proof that every test was redundant.

## Evidence Still Required

- Full call/effect graph through finalizer, tracked and ignored ticket sources, reconciliation,
  recovery, provider mutation, terminal proof, replay, and wiki/Pi post-integration boundaries.
- Exact tree/path/blob/mode deltas for representative completion topologies.
- Causal mapping from each repeated review/QA/verification check to changed or unchanged segments.
- Historical-ledger and crash-checkpoint constraints.
- Multiple real-run cost samples and a stable measurement method.
- Negative examples that resemble projection but must trigger full revalidation.

## Non-Conclusion
No design, proof schema, test-selection rule, compatibility policy, or optimization threshold is
selected by this seed.
