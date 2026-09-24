import assert from 'node:assert/strict';
import test from 'node:test';
import { createAssistantMessageEventStream, getModel } from '@earendil-works/pi-ai/compat';
import { createAgentSession, createExtensionRuntime, SessionManager, SettingsManager } from '@earendil-works/pi-coding-agent';
import { createRequestBudget } from './pilot_budget.mjs';
import { offlineModelRuntime } from './offline_sdk_fixture.mjs';
const modelRuntime = await offlineModelRuntime();

const emptyResources = {
  getExtensions: () => ({ extensions: [], errors: [], runtime: createExtensionRuntime() }),
  getSkills: () => ({ skills: [], diagnostics: [] }),
  getPrompts: () => ({ prompts: [], diagnostics: [] }),
  getThemes: () => ({ themes: [], diagnostics: [] }),
  getAgentsFiles: () => ({ agentsFiles: [] }),
  getSystemPrompt: () => 'Offline stream interception test. No tools.',
  getSystemPromptSource: () => undefined,
  getAppendSystemPrompt: () => [],
  getAppendSystemPromptSources: () => [],
  extendResources: () => {},
  reload: async () => {},
};

test('ambiguous Pi message cannot trigger a second fake model stream', async () => {
  const model = getModel('openai-codex', 'gpt-6-sol');
  const { session } = await createAgentSession({
    model, modelRuntime, thinkingLevel: 'high', resourceLoader: emptyResources, tools: [],
    sessionManager: SessionManager.inMemory(process.cwd()),
    settingsManager: SettingsManager.inMemory({ retry: { enabled: false }, compaction: { enabled: false } }),
  });
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let fakeRequests = 0;
  session.agent.streamFunction = budget.wrap(() => {
    fakeRequests++;
    const stream = createAssistantMessageEventStream();
    const message = { role: 'assistant', api: model.api, provider: model.provider, model: model.id,
      content: [{ type: 'text', text: 'synthetic' }], stopReason: 'stop', timestamp: Date.now(),
      usage: { input: 1, output: 1, cacheRead: 0, cacheWrite: 0, totalTokens: 2,
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } } };
    queueMicrotask(() => {
      stream.push({ type: 'start', partial: message });
      stream.push({ type: 'done', reason: 'stop', message });
    });
    return stream;
  });
  session.subscribe(event => {
    if (event.type === 'message_end' && event.message?.role === 'assistant') budget.recordAssistant(event.message);
  });
  try {
    await session.prompt('first synthetic turn');
    assert.equal(budget.state().ambiguous, true);
    await session.prompt('second synthetic turn').catch(() => {});
    assert.equal(fakeRequests, 1);
    assert.ok(session.messages.some(message => message.role === 'assistant' && message.stopReason === 'error'));
  } finally {
    session.dispose();
  }
});

test('Pi session routes its model request through the budget wrapper, never a provider', async () => {
  const model = getModel('openai-codex', 'gpt-6-sol');
  const { session } = await createAgentSession({
    model, modelRuntime, thinkingLevel: 'high', resourceLoader: emptyResources, tools: [],
    sessionManager: SessionManager.inMemory(process.cwd()),
    settingsManager: SettingsManager.inMemory({ retry: { enabled: false }, compaction: { enabled: false } }),
  });
  const budget = createRequestBudget(model, { limitUsd: '60', maxRequests: 16 });
  let fakeRequests = 0;
  session.agent.streamFunction = budget.wrap(() => {
    fakeRequests++;
    const stream = createAssistantMessageEventStream();
    const message = { role: 'assistant', api: model.api, provider: model.provider, model: model.id,
      content: [{ type: 'text', text: 'offline' }], stopReason: 'stop', timestamp: Date.now(),
      usage: { input: 1, output: 1, cacheRead: 0, cacheWrite: 0, totalTokens: 2,
        cost: { input: 0.005, output: 0.005, cacheRead: 0, cacheWrite: 0, total: 0.01 } } };
    queueMicrotask(() => {
      stream.push({ type: 'start', partial: message });
      stream.push({ type: 'done', reason: 'stop', message });
    });
    return stream;
  });
  session.subscribe(event => {
    if (event.type === 'message_end' && event.message?.role === 'assistant') budget.recordAssistant(event.message);
  });
  try {
    await session.prompt('offline synthetic message');
    assert.equal(fakeRequests, 1);
    assert.equal(budget.state().requests, 1);
    assert.equal(budget.state().observedUsd, 0.01);
    assert.equal(session.getSessionStats().cost, 0.01);
  } finally {
    session.dispose();
  }
});
