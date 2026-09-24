import assert from 'node:assert/strict';
import test from 'node:test';
import { getModel } from '@earendil-works/pi-ai/compat';
import { createRequestBudget } from './pilot_budget.mjs';

const model = getModel('openai-codex', 'gpt-6-sol');

test('frozen GPT tariff and model limits admit at most sixteen bounded calls', () => {
  assert.ok(model);
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let invoked = 0;
  const stream = budget.wrap((selected) => { invoked++; assert.equal(selected, model); return { fake: true }; });
  for (let i = 0; i < 16; i++) {
    assert.deepEqual(stream(model, {}), { fake: true });
    budget.recordAssistant({ usage: { input: 1, output: 1, cacheRead: 0, cacheWrite: 0,
      cost: { total: 3.28 } } });
  }
  assert.equal(invoked, 16);
  assert.equal(budget.state().pendingRequests, 0);
  assert.equal(budget.state().reservedUsd, budget.state().observedUsd);
  assert.ok(budget.state().reservedUsd <= 60);
  assert.equal(budget.state().requests, 16);
  assert.throws(() => stream(model, {}), /request limit/);
  assert.equal(invoked, 16);
});

test('priority-tier-sized calls stop at the $60 ceiling without losing the three-cell pilot', () => {
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  const perCall = budget.state().maxPerRequestUsd;
  assert.equal(perCall, 8.2);
  let invoked = 0;
  const stream = budget.wrap(() => { invoked++; return {}; });
  for (let i = 0; i < 7; i++) {
    stream(model, {});
    budget.recordAssistant({ usage: { input: 1, output: 1, cacheRead: 0,
      cacheWrite: 0, cost: { total: perCall } } });
  }
  assert.ok(Math.abs(budget.state().observedUsd - 57.4) < 1e-8);
  assert.throws(() => stream(model, {}), /request budget exhausted/);
  assert.equal(invoked, 7);
  assert.ok(budget.state().reservedUsd <= 60);
});

test('tariff or model drift rejects before any model request', () => {
  assert.throws(() => createRequestBudget({ ...model, maxTokens: model.maxTokens + 1 },
    { limitUsd: '60', maxRequests: 16 }), /model or tariff drift/);
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let invoked = 0;
  const stream = budget.wrap(() => { invoked++; return {}; });
  assert.throws(() => stream({ ...model, id: 'other' }, {}), /model or tariff drift/);
  assert.equal(invoked, 0);
});

test('unknown or excessive usage blocks the next model request', () => {
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let invoked = 0;
  const stream = budget.wrap(() => { invoked++; return {}; });
  stream(model, {});
  assert.throws(() => budget.recordAssistant({ usage: { output: 1, cost: { total: 0 } } }),
    /unknown model cost/);
  assert.throws(() => stream(model, {}), /ambiguous cost/);
  assert.equal(invoked, 1);
  const other = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  other.wrap(() => ({}))(model, {});
  assert.throws(() => other.recordAssistant({ usage: { output: 10, cost: { total: 99 } } }),
    /cost exceeds reservation/);
});

test('nonzero input with zero reported cost is ambiguous', () => {
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let invoked = 0;
  const stream = budget.wrap(() => { invoked++; return {}; });
  stream(model, {});
  assert.throws(() => budget.recordAssistant({ usage: {
    input: 50, output: 0, cacheRead: 0, cacheWrite: 0, cost: { total: 0 },
  } }), /unknown model cost/);
  assert.throws(() => stream(model, {}), /ambiguous cost/);
  assert.equal(invoked, 1);
});

test('budget and request count must both be explicit', () => {
  assert.throws(() => createRequestBudget(model, { limitUsd: '0', maxRequests: 16 }), /budget/);
  assert.throws(() => createRequestBudget(model, { limitUsd: '60', maxRequests: 0 }), /budget/);
  assert.throws(() => createRequestBudget(model, { limitUsd: '1', maxRequests: 16 }), /budget/);
});
