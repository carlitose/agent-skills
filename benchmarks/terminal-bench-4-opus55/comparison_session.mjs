// One fresh SDK context per comparison phase; accounting is owned by the trial.
import { join } from 'node:path';
import { createAgentSession, createExtensionRuntime, getAgentDir,
  SessionManager, SettingsManager } from '@earendil-works/pi-coding-agent';

export async function runPhase({ model, modelRuntime, budget, dir, name, prompt, systemPrompt, tools, stream,
  canRequest = () => true }) {
  budget.setPhase(name);
  const resourceLoader = {
    getExtensions: () => ({ extensions: [], errors: [], runtime: createExtensionRuntime() }),
    getSkills: () => ({ skills: [], diagnostics: [] }),
    getPrompts: () => ({ prompts: [], diagnostics: [] }),
    getThemes: () => ({ themes: [], diagnostics: [] }),
    getAgentsFiles: () => ({ agentsFiles: [] }),
    getSystemPrompt: () => systemPrompt,
    getSystemPromptSource: () => undefined,
    getAppendSystemPrompt: () => [],
    getAppendSystemPromptSources: () => [],
    extendResources: () => {}, reload: async () => {},
  };
  const { session } = await createAgentSession({
    cwd: dir, agentDir: getAgentDir(), model, modelRuntime, thinkingLevel: 'high', resourceLoader,
    tools: tools.map(tool => tool.name), customTools: tools,
    sessionManager: SessionManager.inMemory(dir),
    settingsManager: SettingsManager.inMemory({ retry: { enabled: false }, compaction: { enabled: false } }),
  });
  let failed = false;
  const trajectory = `pi-${name}.jsonl`;
  try {
    const active = session.getActiveToolNames();
    if (JSON.stringify(active) !== JSON.stringify(tools.map(tool => tool.name))) {
      throw new Error('unexpected model tool boundary');
    }
    const counted = budget.wrap(stream ?? session.agent.streamFunction);
    session.agent.streamFunction = (...args) => {
      if (!canRequest()) throw new Error('sandbox transport is unavailable');
      return counted(...args);
    };
    session.subscribe(event => {
      if (event.type === 'message_end' && event.message?.role === 'assistant') {
        try { budget.recordAssistant(event.message); }
        catch { failed = true; } // SDK subscribers may swallow exceptions; retain the failure explicitly.
      }
    });
    try { await session.prompt(prompt); }
    catch { failed = true; }
    const assistants = session.messages.filter(message => message.role === 'assistant');
    if (!assistants.length || assistants.some(message =>
      ['error', 'aborted', 'deferred'].includes(message.stopReason))) failed = true;
    if (!budget.state().known) failed = true;
    const response = assistants.at(-1)?.content.filter(part => part.type === 'text')
      .map(part => part.text).join('\n') ?? '';
    return { type: 'phase-result', phase: name, status: failed ? 'failed' : 'completed',
      tools: active, response: response.slice(0, 16384), response_truncated: response.length > 16384,
      trajectory_file: trajectory, usage: budget.state() };
  } finally {
    // Successful and failed SDK conversations retain their own attributable file.
    try { session.exportToJsonl(join(dir, trajectory)); }
    finally { session.dispose(); }
  }
}
