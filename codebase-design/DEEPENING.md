# Deepening Modules

This reference extends the vocabulary in [SKILL.md](SKILL.md) with dependency and testing guidance. Use [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) when one promising boundary still admits materially different interfaces.

## Dependency categories

Classify a dependency before choosing its seam:

1. **In-process** — code owned and executed in the same process. Prefer a direct call unless substitution represents a meaningful architectural boundary.
2. **Local-substitutable** — a local resource with a faithful cheap substitute, such as an in-memory repository for a filesystem-backed store. Put the seam at the capability boundary, not at every low-level operation.
3. **Remote but owned** — a service or process controlled by the same product. Use ports and adapters so the module owns domain operations while transport details remain outside.
4. **True external** — a third-party system whose behavior cannot be reproduced locally with confidence. Keep a narrow adapter, test the owned contract, and use controlled fakes or mocks for external outcomes.

## Seam discipline

A seam should correspond to a decision that can vary independently. Place it where domain language meets an external model, where nondeterminism enters, or where an expensive dependency needs a controlled substitute. Do not turn every collaborator into an interface: excessive seams expose coordination and make the module shallower.

Prefer capability-shaped operations such as `reserve_inventory` over transport-shaped operations such as `post_json`. The adapter may speak HTTP, SQL, or filesystem APIs; the module interface should speak the caller's problem.

## Test at the boundary

Test the public interface and the invariants it owns. When a deeper module replaces a cluster of shallow wrappers, replace, don't layer: retire tests coupled to the old internal call graph instead of retaining them beneath new boundary tests.

Keep targeted adapter contract tests where translation can fail. Use integration tests for the smallest boundary that proves owned components compose correctly, and reserve live external tests for risks that cannot be simulated honestly.

## Deepening check

A proposed module is probably deeper when it:

- removes concepts from callers;
- centralizes invariants that were previously repeated;
- reduces cross-file navigation for a routine change;
- supports tests through stable operations rather than internal choreography;
- can change implementation or adapters without changing ordinary callers.

If the interface grows in proportion to the hidden implementation, revisit the ownership boundary rather than adding another layer.
