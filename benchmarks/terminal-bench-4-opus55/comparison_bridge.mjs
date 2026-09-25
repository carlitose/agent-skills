// Bounded per-trial SDK endpoint. This does not select tasks or launch Harbor.
import readline from 'node:readline';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { getModel } from '@earendil-works/pi-ai/compat';
import { createSandboxTool } from './pi_bridge_core.mjs';
import { createDurableBudget } from './durable_budget.mjs';
import { runPhase } from './comparison_session.mjs';

export const FRAME_BYTES = 262144;
const ARMS = ['pi-bare', 'skills-only', 'ticket-driver-c1a', 'ticket-driver-c3a'];
const STANDARD = 'original-harbor-full-pi-bare';
const STANDARD_SYSTEM = 'Work only through sandbox_exec in the task environment. Complete the user task.';

export async function serveComparison({ receive, send, dir, stream, modelRuntime }) {
  let budget;
  let terminal = false;
  try {
    const start = await receive();
    const standard = start.method === STANDARD;
    if (start.type !== 'init' || (!standard && start.method !== 'git-overlay-v1') ||
        (standard && start.arm !== 'pi-bare') ||
        start.model !== 'openai-codex/gpt-6-sol' || start.thinking !== 'high' ||
        !ARMS.includes(start.arm) || typeof start.task_name !== 'string' ||
        typeof start.trial_id !== 'string' || typeof start.instruction !== 'string' ||
        !start.instruction || start.budget?.limit_usd !== '57' || start.budget?.max_requests !== 48) {
      throw new Error('invalid comparison binding');
    }
    const identity = { method: start.method, task: start.task_name, arm: start.arm,
      trial: start.trial_id, model: start.model, thinking: start.thinking,
      instruction_sha256: createHash('sha256').update(start.instruction).digest('hex') };
    const model = getModel('openai-codex', 'gpt-6-sol');
    budget = createDurableBudget(model, { limitUsd: '57', maxRequests: 48 },
      join(dir, 'model-usage.jsonl'), identity);
    const baseTool = createSandboxTool(send, receive);
    let transportAvailable = true;
    const tool = { ...baseTool, async execute(...args) {
      try { return await baseTool.execute(...args); }
      catch (error) { transportAvailable = false; throw error; }
    } };
    const names = new Set();
    let lastStatus = 'completed';
    send({ type: 'ready', identity });
    for (let n = 0; n < 9; n++) {
      const command = await receive();
      if (command.type === 'finish') {
        const status = command.status === 'completed' && lastStatus === 'completed' ? 'completed' : 'failed';
        const usage = budget.finish(status);
        terminal = true;
        send({ type: 'final', identity, status, usage });
        return;
      }
      if (command.type !== 'phase' || typeof command.prompt !== 'string' || !command.prompt ||
          typeof command.system_prompt !== 'string' || typeof command.name !== 'string' ||
          !['sandbox', 'none'].includes(command.tools) || names.has(command.name) ||
          lastStatus !== 'completed' || !budget.state().known) {
        throw new Error('invalid phase command or preceding phase failed');
      }
      if (standard && (names.size !== 0 || command.name !== 'builder' || command.tools !== 'sandbox' ||
          command.prompt !== start.instruction || command.system_prompt !== STANDARD_SYSTEM)) {
        throw new Error('original method requires one unchanged bare task phase');
      }
      names.add(command.name);
      const result = await runPhase({ model, modelRuntime, budget, dir, name: command.name,
        prompt: command.prompt, systemPrompt: command.system_prompt,
        tools: command.tools === 'sandbox' ? [tool] : [], stream,
        canRequest: () => transportAvailable });
      lastStatus = result.status;
      send(result);
    }
    throw new Error('phase bound exceeded');
  } finally {
    if (budget && !terminal) budget.finish('failed');
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const input = readline.createInterface({ input: process.stdin, terminal: false });
  const iterator = input[Symbol.asyncIterator]();
  try {
    await serveComparison({ dir: process.cwd(),
      send(value) {
        const line = JSON.stringify(value) + '\n';
        if (Buffer.byteLength(line) > FRAME_BYTES) throw new Error('oversized outgoing frame');
        process.stdout.write(line);
      },
      async receive() {
        const { value, done } = await iterator.next();
        if (done || Buffer.byteLength(value) > FRAME_BYTES) throw new Error('missing or oversized frame');
        return JSON.parse(value);
      },
    });
  } catch {
    // No provider exception text or credentials in protocol/stderr.
    console.error('Comparison endpoint failed; inspect the usage journal.');
    process.exitCode = 1;
  } finally { input.close(); }
}
