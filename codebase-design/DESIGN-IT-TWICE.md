# Design It Twice

This exercise uses the vocabulary in [SKILL.md](SKILL.md) and the dependency guidance in [DEEPENING.md](DEEPENING.md) to compare genuinely different module boundaries before committing to one.

## Authority and execution

Generate at least three contrasting designs. Without explicit delegation authority, perform the passes serially inline and label each perspective. Shared context can influence later passes, so do not describe them as independent.

With explicit delegation authority from the user or an applicable host instruction, distinct workers may explore separate designs. Do not claim independent or parallel execution unless separate contexts or concurrency were actually observed. The calling workflow still owns any implementation, review, scheduling, or delivery.

## Prepare one brief

State the capability, callers, invariants, current coupling, dependency categories, constraints, and concrete usage examples. Give every pass the same facts while changing its design objective.

Useful perspectives include:

1. minimize the interface and optimize for the common caller;
2. maximize extensibility for known variations;
3. maximize locality by placing policy with the data and effects it governs;
4. isolate a remote or volatile dependency behind ports and adapters.

Each design must show:

- interface signatures or an equivalent precise surface;
- a caller example;
- the implementation complexity it hides;
- dependency and adapter strategy;
- test seams and representative boundary tests;
- trade-offs and failure modes.

## Compare before recommending

Compare the designs using the same criteria: depth, leverage, locality, seam placement, testability, migration cost, and operational risk. Reject cosmetic variants that preserve the same ownership boundary.

Recommend one design or a clearly specified hybrid. Explain which complexity becomes private, what callers stop knowing, and which evidence would falsify the recommendation. Do not implement the recommendation unless the calling workflow separately authorizes implementation.
