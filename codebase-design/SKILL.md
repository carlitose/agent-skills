---
name: codebase-design
description: Shared vocabulary for designing deep, testable modules and evaluating interfaces, implementations, seams, adapters, leverage, and locality. Use when shaping a module boundary, comparing interface designs, classifying dependencies, or deciding where a test seam belongs.
---

# Codebase Design

Owns: shared codebase-design vocabulary.

Use this reference to reason consistently about module boundaries. It provides language and design exercises; it does not implement, review, schedule, or deliver changes. The calling workflow retains ownership of decisions, artifacts, and side effects.

## Vocabulary

- **Module**: a cohesive unit that owns a useful capability behind a boundary.
- **Interface**: the surface callers must understand to use a module.
- **Implementation**: the decisions and machinery hidden behind the interface.
- **Depth**: the amount of useful complexity hidden by a comparatively small interface.
- **Seam**: a deliberate boundary where behavior or a dependency can be substituted and observed.
- **Adapter**: a translation layer between a module's internal model and an external dependency or protocol.
- **Leverage**: the value delivered by each concept a caller must learn.
- **Locality**: the degree to which a change can be understood and made within one coherent place.

## Design principles

A deep module offers high leverage: callers learn a small, stable interface while the module owns substantial policy and coordination. A shallow module merely redistributes complexity, often forcing callers to understand its implementation.

Prefer boundaries that:

- group behavior that changes together;
- keep invariants and dependency policy inside the owning module;
- make the common operation easy without preventing necessary variation;
- expose seams at real dependency boundaries, not between every function;
- let tests exercise the public interface rather than reconstruct internal call chains;
- improve locality by reducing the number of files and concepts needed for one change.

Avoid abstraction for its own sake. A small implementation with no durable policy may be clearer inline. An adapter is useful when it protects the domain from a foreign model or volatile protocol; a pass-through wrapper usually adds surface without depth.

## Applying the vocabulary

1. Name the capability and the callers that need it.
2. List the policy and complexity the module should hide.
3. Sketch the smallest interface that serves real caller operations.
4. Classify dependencies and place the narrowest useful seams using [DEEPENING.md](DEEPENING.md).
5. Stress-test the boundary with contrasting designs using [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md).
6. Compare depth, leverage, locality, seam placement, and test surface before recommending a design.

Keep the vocabulary descriptive, not prescriptive: context decides whether a module should be deepened, merged, kept small, or left inline.
