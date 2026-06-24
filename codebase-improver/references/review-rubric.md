# Review Rubric — two reviewers

The two review subagents in `quality-loop.md` Step 4 follow this rubric. They review the branch's uncommitted diff and return structured findings. Reviewer 1 is correctness-first; Reviewer 2 is maintainability-first. They run in parallel.

---

## Reviewer 1 — Correctness (recall-biased, high effort)

Goal: catch every real bug a careful reviewer would catch in one sitting. At this level, **catching real bugs matters more than avoiding false positives** — err on the side of surfacing.

### Phase 0 — Gather the diff
`git diff @{upstream}...HEAD` (fallback `git diff main...HEAD` or `git diff HEAD~1`). If there are uncommitted changes or the range is empty, also `git diff HEAD`.

### Phase 1 — Find candidates (independent angles, parallelizable)
- **Line-by-line scan** — each hunk + its enclosing function: inverted conditions, off-by-one, null deref, missing `await`, falsy-zero, copy-pasted wrong variable, swallowed error in catch, unescaped regex metacharacters.
- **Removed-behavior auditor** — for each deleted/replaced line, name the invariant it protected and find where it's re-established. Not found → candidate.
- **Cross-file tracer** — for each changed function, grep callers and check the change breaks no call (new precondition, return shape, exception, ordering). Check callees too.
- **Reuse** — new code reimplementing something that already exists → name the helper to use.
- **Simplification** — unnecessary complexity (derivable state, copy-paste, deep nesting, dead code).
- **Efficiency** — wasted work (repeated I/O, sequential ops that could be parallel, closures keeping whole scopes alive).
- **Altitude** — is the change at the right level, or a fragile patch? Special-cases bolted onto shared infra signal the fix isn't deep enough.
- **Conventions** — locate the `CLAUDE.md` governing the changed code; flag clear violations only when you can cite the exact rule and the exact line that breaks it.

### Phase 2 — Verify (recall-biased)
Dedupe. For each candidate decide CONFIRMED / PLAUSIBLE / REFUTED.
- **PLAUSIBLE by default** — don't refute as "speculative" if the state is realistic (races, nil on a rare path, falsy-zero, off-by-one at a boundary, retry storms, unanchored regex).
- **REFUTED only if constructible from the code**: factually false, impossible by type/constant/invariant, already handled in the diff, or pure style with no observable effect.
- Keep CONFIRMED and PLAUSIBLE.

### Output
Up to **10** findings, most severe first:
```json
[{"file":"path/to/file.ext","line":123,"summary":"one-sentence bug","failure_scenario":"concrete inputs/state → wrong output/crash"}]
```
Nothing survives → `[]`.

---

## Reviewer 2 — Maintainability (thermo-nuclear, extremely strict)

Be **ambitious** about structure. Don't stop at "this could be cleaner" — actively hunt for "code judo": behavior-preserving restructurings that make the implementation dramatically simpler, smaller, more direct. Prefer **deleting** complexity over rearranging it. Prefer the solution that feels inevitable in hindsight.

### Non-negotiable standards
0. **Be ambitious about structural simplification.** Look for reframings where whole branches, helpers, modes, conditionals, or layers disappear.
1. **1000-line rule.** Do not let the diff push a file from under 1k lines to over 1k without a very strong reason. Crossing it is a presumptive blocker — prefer extracting helpers/modules first.
2. **No spaghetti growth.** Be highly suspicious of new ad-hoc conditionals / one-off branches inserted into unrelated flows. Push logic into a dedicated abstraction, helper, state machine, or module instead of tangling an existing path.
3. **Clean the design, don't just accept working code.** If behavior can stay the same while structure gets meaningfully cleaner, push for it. Prefer removing moving pieces over spreading the same complexity around.
4. **Direct, boring, maintainable over hacky/magical.** Flag thin abstractions, identity wrappers, pass-through helpers, and generic mechanisms that hide simple data-shape assumptions.
5. **Type/boundary cleanliness.** Question unnecessary optionality, `any`/`unknown`, cast-heavy code, and silent fallbacks papering over unclear invariants. Prefer explicit typed models/contracts.
6. **Canonical layer + reuse.** Flag feature logic leaking into shared paths, implementation details leaking through APIs, and bespoke helpers duplicating a canonical utility. Push code to the right module.
7. **Orchestration/atomicity.** Flag independent work serialized for no reason, and related updates that can leave state half-applied.

### Primary questions (per meaningful change)
Is there a code-judo move that makes this dramatically simpler? Can it be reframed so fewer concepts/branches/layers are needed? Does it improve or worsen local architecture? Did it add branching where an abstraction should exist? Did a cohesive module become more coupled/stateful/harder to scan? Is the logic in the right file/layer? Did it cross a healthy size boundary? Do repeated conditionals signal a missing model? Is the abstraction earning its keep or just a wrapper? Did casts/optionality obscure the real invariant?

### Preferred remedies
Delete a layer of indirection rather than polish it; reframe the state model so conditionals disappear; change the ownership boundary so the feature is a natural extension of an existing abstraction; turn special-cases into a simpler default flow; extract a helper/pure function; split a large file; replace condition chains with a typed model/dispatcher; separate orchestration from business logic; collapse duplicate branches; reuse the canonical helper; make type boundaries explicit; parallelize independent work when it also simplifies.

### Approval bar (treat as presumptive blockers unless justified)
- Preserves incidental complexity when a code-judo move would delete it.
- Pushes a file from <1000 to >1000 lines.
- Adds ad-hoc branching that tangles an existing flow.
- Scatters feature checks across shared code.
- Adds an unnecessary abstraction/wrapper/cast-heavy contract.
- Duplicates an existing helper or puts logic in the wrong layer.

### Output (priority order)
1. Structural regressions → 2. Missed dramatic-simplification / code-judo → 3. Spaghetti/branching growth → 4. Boundary/abstraction/type-contract problems → 5. File-size/decomposition → 6. Modularity/abstraction → 7. Legibility/maintainability.

Prefer a few high-conviction findings over a long list of cosmetic nits. Be direct and demanding, not rude. Don't approve merely because behavior is correct.

---

## Merge step (main agent)

Combine both reviewers' findings, dedupe by `path:line`. Keep findings at `REVIEW_BLOCKING_SEVERITY`+ (default `high`) as **blocking**; record the rest without blocking. Reviewer 2's presumptive blockers count as `high` unless the user has justified them.
