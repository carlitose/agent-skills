import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { createHash } from 'node:crypto';
import { createAssistantMessageEventStream, getModel } from '@earendil-works/pi-ai/compat';
import { serveComparison } from './comparison_bridge.mjs';
import { offlineModelRuntime } from './offline_sdk_fixture.mjs';
const modelRuntime = await offlineModelRuntime();

const init = { type: 'init', method: 'git-overlay-v1', model: 'openai-codex/gpt-6-sol',
  thinking: 'high', arm: 'pi-bare', task_name: 'html-js-filter', trial_id: 'offline',
  instruction: 'Public instruction', budget: { limit_usd: '57', max_requests: 48 } };
const phase = { type: 'phase', name: 'builder', prompt: 'offline', system_prompt: 'Synthetic test', tools: 'sandbox' };
const model = getModel('openai-codex', 'gpt-6-sol');
function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), 'tbf-protocol-'));
  t.after(() => rmSync(dir, { force: true, recursive: true }));
  return { dir, journal: () => readFileSync(join(dir, 'model-usage.jsonl'), 'utf8').trim().split('\n').map(JSON.parse) };
}
function response(toolCall) {
  const stream = createAssistantMessageEventStream();
  const message = { role: 'assistant', api: model.api, provider: model.provider, model: model.id,
    content: toolCall ? [{ type: 'toolCall', id: 'fake-call', name: 'sandbox_exec',
      arguments: { command: 'sleep 90', timeout_sec: 1 } }] : [{ type: 'text', text: 'finished' }],
    stopReason: toolCall ? 'toolUse' : 'stop', timestamp: Date.now(),
    usage: { input: 1, output: 1, cacheRead: 0, cacheWrite: 0, totalTokens: 2,
      cost: { input: 0.005, output: 0.005, cacheRead: 0, cacheWrite: 0, total: 0.01 } } };
  queueMicrotask(() => {
    stream.push({ type: 'start', partial: message });
    stream.push({ type: 'done', reason: message.stopReason, message });
  });
  return stream;
}

test('a timed-out tool result reaches the SDK and the same trial can finish', async t => {
  const { dir, journal } = fixture(t);
  const queue = [init, phase, { type: 'finish', status: 'completed' }];
  const output = [];
  let calls = 0;
  await serveComparison({ dir, modelRuntime, receive: async () => queue.shift(), send(value) {
    output.push(value);
    if (value.type === 'exec') queue.unshift({ type: 'result', id: value.id,
      stdout: 'partial', stderr: 'timed out', return_code: 124 });
  }, stream(_model, context) {
    assert.equal(journal().at(-1).event, 'request');
    calls++;
    if (calls === 2) assert.ok(JSON.stringify(context.messages).includes('124'));
    return response(calls === 1);
  } });
  assert.equal(calls, 2);
  assert.equal(output.find(r => r.type === 'phase-result').status, 'completed');
  assert.equal(output.at(-1).usage.cost_usd, 0.02);
  assert.equal(journal().at(-1).status, 'completed');
});

test('parent disconnect retains a terminal failed record and the completed usage', async t => {
  const { dir, journal } = fixture(t);
  const queue = [init, { ...phase, tools: 'none' }];
  await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => {
    if (!queue.length) throw new Error('disconnected');
    return queue.shift();
  }, stream: () => response(false) }), /disconnected/);
  assert.equal(journal().at(-1).event, 'terminal');
  assert.equal(journal().at(-1).status, 'failed');
  assert.equal(journal().at(-1).cost_usd, 0.01);
});

test('a lost tool transport cannot trigger another model request', async t => {
  const { dir, journal } = fixture(t);
  const queue = [init, phase];
  let calls = 0;
  await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => {
    if (!queue.length) throw new Error('lost transport');
    return queue.shift();
  }, stream: () => { calls++; return response(calls === 1); } }), /lost transport/);
  assert.equal(calls, 1);
  assert.equal(journal().at(-1).status, 'failed');
  assert.equal(journal().at(-1).cost_usd, 0.01);
});

test('original dataset method uses exactly the original prompt in one bare phase', async t => {
  const { dir, journal } = fixture(t);
  const start = { ...init, method: 'original-harbor-full-pi-bare', task_name: 'not-in-pilot' };
  const queue = [start, { ...phase, prompt: start.instruction,
    system_prompt: 'Work only through sandbox_exec in the task environment. Complete the user task.' },
  { type: 'finish', status: 'completed' }];
  let calls = 0;
  await serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream(_model, context) {
      calls++;
      assert.equal(context.messages[0].content, start.instruction);
      return response(false);
    } });
  assert.equal(calls, 1);
  assert.equal(journal().at(-1).identity.method, start.method);
});

test('original method honours a declared flat-rate agent policy', async t => {
  const { dir, journal } = fixture(t);
  const start = { ...init, method: 'original-harbor-full-pi-bare', budget: { limit_usd: '9000', max_requests: 1000 } };
  const queue = [start, { ...phase, prompt: start.instruction,
    system_prompt: 'Work only through sandbox_exec in the task environment. Complete the user task.' },
  { type: 'finish', status: 'completed' }];
  await serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream() { return response(false); } });
  const last = journal().at(-1);
  assert.equal(last.budget.maxRequests, 1000);
  assert.equal(last.budget.limitUsd, '9000');
  assert.equal(last.known, true);
});

test('overlay method keeps its frozen policy and invalid standard policies are refused', async t => {
  for (const start of [{ ...init, budget: { limit_usd: '9000', max_requests: 1000 } },
    { ...init, method: 'original-harbor-full-pi-bare', budget: { limit_usd: '9000', max_requests: 5001 } },
    { ...init, method: 'original-harbor-full-pi-bare', budget: { limit_usd: 'lots', max_requests: 10 } }]) {
    const { dir } = fixture(t);
    const queue = [start];
    await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
      stream() { throw new Error('must not call a model'); } }), /binding/);
  }
});

const SKILLS = 'frozen skill text';
const SKILLS_SHA = createHash('sha256').update(SKILLS).digest('hex');
const BASE_SYSTEM = 'Work only through sandbox_exec in the task environment. Complete the user task.';

test('original method runs the skills-only arm only with its hashed snapshot', async t => {
  const { dir, journal } = fixture(t);
  const start = { ...init, method: 'original-harbor-full-pi-bare', arm: 'skills-only', skills_sha256: SKILLS_SHA };
  const queue = [start, { ...phase, prompt: start.instruction,
    system_prompt: BASE_SYSTEM + '\n\nFrozen local workflow skills:\n' + SKILLS }, { type: 'finish', status: 'completed' }];
  let calls = 0;
  await serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream() { calls++; return response(false); } });
  assert.equal(calls, 1);
  const last = journal().at(-1);
  assert.equal(last.identity.arm, 'skills-only');
  assert.equal(last.identity.skills_sha256, SKILLS_SHA);
});

test('skills-only original arm refuses a missing hash or a different snapshot', async t => {
  const noHash = { ...init, method: 'original-harbor-full-pi-bare', arm: 'skills-only' };
  await assert.rejects(serveComparison({ dir: fixture(t).dir, modelRuntime, send() {},
    receive: (q => async () => q.shift())([noHash]), stream() { throw new Error('no model'); } }), /binding/);
  const { dir, journal } = fixture(t);
  const start = { ...noHash, skills_sha256: SKILLS_SHA };
  const queue = [start, { ...phase, prompt: start.instruction,
    system_prompt: BASE_SYSTEM + '\n\nFrozen local workflow skills:\n' + 'other text' }];
  await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream() { throw new Error('must not call a model'); } }), /original/);
  assert.equal(journal().at(-1).budget.requests, 0);
});

test('original method refuses injected instructions before any model request', async t => {
  const { dir, journal } = fixture(t);
  const queue = [{ ...init, method: 'original-harbor-full-pi-bare' }, phase];
  await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream() { throw new Error('must not call a model'); } }), /original/);
  assert.equal(journal().at(-1).budget.requests, 0);
});

test('a phase identity cannot be reused to overwrite its trajectory', async t => {
  const { dir, journal } = fixture(t);
  const queue = [init, { ...phase, tools: 'none' }, phase];
  let calls = 0;
  await assert.rejects(serveComparison({ dir, modelRuntime, send() {}, receive: async () => queue.shift(),
    stream: () => { calls++; return response(false); } }), /invalid phase/);
  assert.equal(calls, 1);
  assert.equal(journal().at(-1).status, 'failed');
});
