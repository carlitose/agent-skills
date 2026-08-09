# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

### Tautological tests

Reject a test when it merely restates a production constant, mirrors the implementation branch or algorithm,
or asserts only mock-call choreography.
Before accepting a test, ask: **What production behavior change would make this fail?**
If the answer is only "renaming or rearranging the implementation," the
test is not causal.

### Causal RED

Given an agreed `PaymentGateway` Seam, a checkout test supplies a declined
boundary fake and expects the public result to remain `declined` with no order
confirmation. It is RED while checkout confirms every order. Changing the
decline-handling behavior makes the test fail; changing the internal call graph
does not.

### Minimal GREEN

Propagate the gateway's declined outcome through the checkout Interface and
skip confirmation. Add no call-count assertion and no extra branch beyond the
behavior required by the RED test.

```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```
