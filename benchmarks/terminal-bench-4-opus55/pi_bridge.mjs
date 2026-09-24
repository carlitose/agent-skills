// External Pi process. Its only model-visible tool forwards to Harbor's environment.exec.
// This is not a pilot launcher: only a task-bound standard Pi-bare start may
// reach this process with a reserved ledger. Modified four-arm routes remain gated.
import readline from 'node:readline';
import { getModel } from '@earendil-works/pi-ai/compat';
import { createSandboxTool } from './pi_bridge_core.mjs';
import { createRequestBudget } from './pilot_budget.mjs';
import {
  createAgentSession,
  createExtensionRuntime,
  getAgentDir,
  SessionManager,
  SettingsManager,
} from '@earendil-works/pi-coding-agent';

const input = readline.createInterface({ input: process.stdin, terminal: false });
const iterator = input[Symbol.asyncIterator]();
const send = value => process.stdout.write(JSON.stringify(value) + '\n');
const receive = async () => {
  const { value, done } = await iterator.next();
  if (done || value.length > 65536) throw new Error('bridge response missing or oversized');
  return JSON.parse(value);
};

let session;
try {
  const start = await receive();
  if (start.type !== 'start' || start.model !== 'openai-codex/gpt-6-sol' ||
      start.thinking !== 'high' || typeof start.instruction !== 'string' ||
      !['pi-bare', 'skills-only'].includes(start.arm) ||
      (start.method !== undefined && (start.method !== 'standard' || start.arm !== 'pi-bare'))) {
    throw new Error('invalid frozen Pi configuration');
  }
  if (start.arm === 'skills-only' &&
      (!Array.isArray(start.skills) || start.skills.length === 0 ||
       start.skills.some(s => typeof s !== 'string' || !s))) {
    throw new Error('skills-only requires a frozen skill snapshot');
  }
  const sandboxTool = createSandboxTool(send, receive);
  const resourceLoader = {
    getExtensions: () => ({ extensions: [], errors: [], runtime: createExtensionRuntime() }),
    getSkills: () => ({ skills: [], diagnostics: [] }),
    getPrompts: () => ({ prompts: [], diagnostics: [] }),
    getThemes: () => ({ themes: [], diagnostics: [] }),
    getAgentsFiles: () => ({ agentsFiles: [] }),
    getSystemPrompt: () => 'You work only inside a Harbor task container. Use sandbox_exec for every file or shell operation. Do not use host paths.' +
      (start.arm === 'skills-only' ? '\n\nFrozen skills:\n' + start.skills.join('\n\n') : ''),
    getSystemPromptSource: () => undefined,
    getAppendSystemPrompt: () => [],
    getAppendSystemPromptSources: () => [],
    extendResources: () => {},
    reload: async () => {},
  };
  const model = getModel('openai-codex', 'gpt-6-sol');
  if (!model) throw new Error('frozen model not present in Pi catalog');
  const requestBudget = start.method === 'standard'
    ? createRequestBudget(model, { limitUsd: start.budget?.limit_usd,
      maxRequests: start.budget?.max_requests }) : null;
  ({ session } = await createAgentSession({
    cwd: process.cwd(), agentDir: getAgentDir(), model, thinkingLevel: 'high',
    resourceLoader, tools: ['sandbox_exec'], customTools: [sandboxTool],
    sessionManager: SessionManager.inMemory(process.cwd()),
    settingsManager: SettingsManager.inMemory({ retry: { enabled: false }, compaction: { enabled: false } }),
  }));
  if (requestBudget) {
    session.agent.streamFunction = requestBudget.wrap(session.agent.streamFunction);
    session.subscribe(event => {
      if (event.type === 'message_end' && event.message?.role === 'assistant') {
        requestBudget.recordAssistant(event.message);
      }
    });
  }
  const toolNames = session.getActiveToolNames();
  if (toolNames.length !== 1 || toolNames[0] !== 'sandbox_exec') {
    throw new Error('host tool unexpectedly active');
  }
  if (process.argv.includes('--offline-preflight')) {
    send({ type: 'preflight', tools: toolNames, model: session.model?.id,
      thinking: session.thinkingLevel, budget_active: requestBudget !== null });
  } else if (process.argv.includes('--offline-probe-tool')) {
    const result = await sandboxTool.execute('offline-probe', {
      command: 'printf sandbox-ok > /tmp/tbf-pi-probe && cat /tmp/tbf-pi-probe', timeout_sec: 10,
    });
    send({ type: 'final', instruction: start.instruction, arm: start.arm,
      task_name: start.task_name, method: start.method, budget: requestBudget?.state(),
      offline_probe: true, response: JSON.parse(result.content[0].text),
      usage: { input_tokens: 0, output_tokens: 0, cost_usd: 0 } });
  } else {
    await session.prompt(start.instruction);
    const assistants = session.messages.filter(m => m.role === 'assistant');
    if (!assistants.length || assistants.some(m => m.stopReason === 'error' ||
        m.stopReason === 'aborted' || m.stopReason === 'deferred')) {
      throw new Error('Pi did not complete the agent run');
    }
    const stats = session.getSessionStats();
    if (!Number.isFinite(stats.cost) || (requestBudget && requestBudget.state().requests > 0 && stats.cost <= 0)) {
      throw new Error('unknown model cost is not zero');
    }
    session.exportToJsonl('pi-session.jsonl');
    send({ type: 'final', instruction: start.instruction, arm: start.arm,
      task_name: start.task_name, method: start.method, budget: requestBudget?.state(),
      usage: { input_tokens: stats.tokens.input + stats.tokens.cacheRead + stats.tokens.cacheWrite,
        output_tokens: stats.tokens.output, cost_usd: stats.cost },
      trajectory_file: 'pi-session.jsonl' });
  }
} catch (error) {
  console.error('Pi sandbox bridge failed:', error instanceof Error ? error.message : 'unknown');
  process.exitCode = 1;
} finally {
  session?.dispose();
  input.close();
}
