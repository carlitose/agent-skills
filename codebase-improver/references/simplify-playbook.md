# Simplify Playbook — clarity-first transformations

Make code **simpler to read**, even if that means **more lines**. The goal is clarity, never line count: don't minimize lines, and don't pad them either. Every transformation here is **behavior-preserving** and must keep the test suite green. If the touched code has no tests, write characterization tests *first* (capture current behavior), then simplify.

Guiding rule: a longer, obvious implementation beats a short, dense one. This is about the code *inside* a module — the module's public interface still stays small.

## When to apply

- The audit flagged a complexity/cognitive hotspot, or
- You're implementing a refactor (Stage 3.6) and the code you touch is dense/clever, or
- The user asks for a dedicated "simplify pass".

## Transformations

### 1. Name intermediate values

Replace nested or chained expressions with sequential, well-named steps.

```python
# before
return [u.email for u in users if u.active and u.age >= 18 and not u.banned]

# after
def eligible(u):
    is_adult = u.age >= 18
    return u.active and is_adult and not u.banned

eligible_users = [u for u in users if eligible(u)]
return [u.email for u in eligible_users]
```

### 2. Unroll dense comprehensions / one-liners

A comprehension that does filtering + transformation + side conditions is often clearer as an explicit loop.

```python
# before
result = {k: f(v) for k, v in data.items() if v is not None and g(k)}

# after
result = {}
for key, value in data.items():
    if value is None:
        continue
    if not g(key):
        continue
    result[key] = f(value)
```

### 3. Split compound conditionals into named booleans / guard clauses

```typescript
// before
if (user && user.subscription && user.subscription.active && !user.subscription.expired) {
  grantAccess();
}

// after
const hasSubscription = Boolean(user && user.subscription);
const isActive = hasSubscription && user.subscription.active;
const notExpired = hasSubscription && !user.subscription.expired;
if (isActive && notExpired) {
  grantAccess();
}
```

### 4. Early returns instead of deep nesting

```python
# before
def process(order):
    if order is not None:
        if order.items:
            if order.paid:
                ship(order)

# after
def process(order):
    if order is None:
        return
    if not order.items:
        return
    if not order.paid:
        return
    ship(order)
```

### 5. Make implicit behavior explicit

Replace clever tricks (truthiness, ternary chains, bitwise hacks, implicit coercion) with explicit forms.

```typescript
// before
const port = config.port || 8080;            // hides 0 being overridden
// after
const port = config.port === undefined ? 8080 : config.port;
```

### 6. One statement, one thing

Break a line that does several things into several lines that each do one.

```python
# before
total = sum(x.price * x.qty for x in cart) * (1 - discount) + shipping
# after
subtotal = sum(item.price * item.qty for item in cart)
discounted = subtotal * (1 - discount)
total = discounted + shipping
```

### 7. Extract well-named helpers

When a block needs a comment to explain *what* it does, that comment is usually a function name. Extract it. (This keeps the caller's interface small — consistent with deep modules.)

## What NOT to do

- **Don't pad for line count.** Adding blank steps or trivial variables that don't aid understanding is noise, not simplicity.
- **Don't change behavior.** No "while I'm here" fixes. Edge cases (`0`, `""`, `None`/`undefined`, empty collections, exceptions) must behave exactly as before.
- **Don't inflate the interface.** Internal verbosity is fine; a sprawling public API is not.
- **Don't remove tests** that still describe behavior. (Per `deep-module-reference.md`, only delete shallow-module tests once boundary tests replace them.)

## Verification

After each simplification: run the relevant tests (`pytest` / the `package.json` test script). If anything goes red, the change was not behavior-preserving — revert and reconsider. Report the diff with `path:line` and the test result.
