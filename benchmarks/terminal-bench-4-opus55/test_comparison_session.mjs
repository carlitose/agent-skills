import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { createAssistantMessageEventStream, getModel } from '@earendil-works/pi-ai/compat';
import { createDurableBudget } from './durable_budget.mjs';
import { runPhase } from './comparison_session.mjs';
import { offlineModelRuntime } from './offline_sdk_fixture.mjs';

const modelRuntime = await offlineModelRuntime();
const model = getModel('openai-codex', 'gpt-6-sol');
function fakeStream(observe, stopReason = 'stop') {
  return (_model, context) => {
    observe(context);
    const stream = createAssistantMessageEventStream();
    const message = { role: 'assistant', api: model.api, provider: model.provider, model: model.id,
      content: [{ type: 'text', text: 'synthetic response' }], stopReason, timestamp: Date.now(),
      usage: { input: 1, output: 1, cacheRead: 0, cacheWrite: 0, totalTokens: 2,
        cost: { input: 0.005, output: 0.005, cacheRead: 0, cacheWrite: 0, total: 0.01 } } };
    queueMicrotask(() => {
      stream.push({ type: 'start', partial: message });
      if (stopReason === 'error') stream.push({ type: 'error', reason: 'error', error: message });
      else stream.push({ type: 'done', reason: 'stop', message });
    });
    return stream;
  };
}
function fixture(t, maxRequests = 48) {
  const dir = mkdtempSync(join(tmpdir(), 'tbf-phase-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const budget = createDurableBudget(model, { limitUsd: '57', maxRequests }, join(dir, 'usage.jsonl'),
    { task: 'fake', arm: 'ticket-driver-c3a', method: 'git-overlay-v1', trial: 'fake' });
  return { dir, budget };
}

test('fresh SDK phases share one durable budget; read-only phase has no tools', async t => {
  const { dir, budget } = fixture(t);
  const contexts = [];
  for (const name of ['builder', 'reviewer']) {
    const result = await runPhase({ model, modelRuntime, budget, dir, name, prompt: name + ' marker',
      systemPrompt: 'Offline test', tools: [], stream: fakeStream(c => contexts.push(c)) });
    assert.equal(result.status, 'completed');
    assert.deepEqual(result.tools, []);
    assert.ok(readFileSync(join(dir, result.trajectory_file), 'utf8').includes(name + ' marker'));
  }
  assert.equal(contexts.length, 2);
  assert.ok(!JSON.stringify(contexts[1].messages).includes('builder marker'));
  assert.equal(budget.finish('completed').cost_usd, 0.02);
});

test('request exhaustion exports failed phase and retains known usage without another provider call', async t => {
  const { dir, budget } = fixture(t, 1);
  let calls = 0;
  const options = { model, modelRuntime, budget, dir, systemPrompt: 'Offline test', tools: [],
    stream: fakeStream(() => calls++) };
  assert.equal((await runPhase({ ...options, name: 'builder', prompt: 'one' })).status, 'completed');
  assert.equal((await runPhase({ ...options, name: 'reviewer', prompt: 'two' })).status, 'failed');
  assert.equal(calls, 1);
  assert.equal(budget.finish('failed').cost_usd, 0.01);
});

test('provider error exports the partial trajectory but does not settle its cost', async t => {
  const { dir, budget } = fixture(t);
  const result = await runPhase({ model, modelRuntime, budget, dir, name: 'builder', prompt: 'test',
    systemPrompt: 'Offline test', tools: [], stream: fakeStream(() => {}, 'error') });
  assert.equal(result.status, 'failed');
  assert.ok(readFileSync(join(dir, result.trajectory_file), 'utf8').includes('synthetic response'));
  assert.equal(budget.finish('failed').cost_usd, null);
});
