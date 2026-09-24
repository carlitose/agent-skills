import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { createDurableBudget } from './durable_budget.mjs';

const model = { provider: 'openai-codex', id: 'gpt-6-sol', contextWindow: 272000,
  maxTokens: 128000, cost: { input: 2, output: 10, cacheRead: 0.2, cacheWrite: 2.5,
    tiers: [{ inputTokensAbove: 272000, input: 4, output: 15, cacheRead: 0.4, cacheWrite: 5 }] } };
const identity = { task: 'fixture', arm: 'pi-bare', method: 'git-overlay-v1', trial: 'fixture-1' };
const usage = { input: 10, output: 2, cacheRead: 3, cacheWrite: 0, cost: { total: 0.01 } };

function fixture(t, maxRequests = 48) {
  const dir = mkdtempSync(join(tmpdir(), 'tbf-journal-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const path = join(dir, 'usage.jsonl');
  const budget = createDurableBudget(model, { limitUsd: '57', maxRequests }, path, identity);
  return { budget, path, records: () => readFileSync(path, 'utf8').trim().split('\n').map(JSON.parse) };
}

test('request reservation is durable before the provider function is entered', t => {
  const { budget, records } = fixture(t);
  let calls = 0;
  const stream = budget.wrap(() => {
    const last = records().at(-1);
    assert.equal(last.event, 'request');
    assert.equal(last.budget.pendingRequests, 1);
    assert.equal(last.cost_usd, null);
    calls++;
    return 'fake-stream';
  });
  assert.equal(stream(model, {}), 'fake-stream');
  budget.recordAssistant({ stopReason: 'stop', usage });
  const result = budget.finish('completed');
  assert.equal(calls, 1);
  assert.equal(result.cost_usd, 0.01);
  assert.equal(result.input_tokens, 13);
  assert.equal(result.output_tokens, 2);
  assert.equal(records().at(-1).event, 'terminal');
  assert.deepEqual(records()[0].identity, identity);
  assert.throws(() => stream(model, {}), /finished/);
});

test('crash after a second request preserves first usage but total remains unknown', t => {
  const { budget, records } = fixture(t);
  const stream = budget.wrap(() => ({}));
  stream(model, {});
  budget.recordAssistant({ stopReason: 'stop', usage });
  stream(model, {});
  const snapshot = budget.finish('failed');
  assert.equal(snapshot.cost_usd, null);
  assert.equal(snapshot.budget.observedUsd, 0.01);
  assert.equal(snapshot.budget.pendingRequests, 1);
  assert.equal(snapshot.input_tokens, 13);
  assert.equal(records().at(-1).status, 'failed');
});

test('synthetic SDK error after admission rejection does not invent a provider request', t => {
  const { budget, records } = fixture(t, 1);
  let calls = 0;
  const stream = budget.wrap(() => { calls++; return {}; });
  stream(model, {});
  budget.recordAssistant({ stopReason: 'stop', usage });
  assert.throws(() => stream(model, {}), /request limit/);
  budget.recordAssistant({ stopReason: 'error', usage: { input: 0, output: 0,
    cacheRead: 0, cacheWrite: 0, cost: { total: 0 } } });
  const snapshot = budget.finish('failed');
  assert.equal(calls, 1);
  assert.equal(snapshot.cost_usd, 0.01);
  assert.ok(records().some(r => r.event === 'synthetic-error'));
});

test('a provider error with missing usage cannot be settled as free', t => {
  const { budget } = fixture(t);
  const stream = budget.wrap(() => ({}));
  stream(model, {});
  assert.throws(() => budget.recordAssistant({ stopReason: 'error', usage: {
    input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: { total: 0 } } }), /unknown/);
  assert.throws(() => stream(model, {}), /unknown/);
  assert.equal(budget.finish('failed').cost_usd, null);
});

test('malformed token receipt stops later requests and preserves a failure event', t => {
  const { budget, records } = fixture(t);
  const stream = budget.wrap(() => ({}));
  stream(model, {});
  assert.throws(() => budget.recordAssistant({ stopReason: 'stop', usage: {
    ...usage, input: -1 } }), /unknown/);
  assert.throws(() => stream(model, {}), /unknown/);
  assert.equal(budget.finish('failed').cost_usd, null);
  assert.ok(records().some(r => r.event === 'unknown-usage'));
});
