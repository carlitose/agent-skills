// Bounded per-trial SDK endpoint. This does not select tasks or launch Harbor.
import readline from 'node:readline';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { readFileSync } from 'node:fs';
import { getModel } from '@earendil-works/pi-ai/compat';
import { createSandboxTool } from './pi_bridge_core.mjs';
import { createDurableBudget } from './durable_budget.mjs';
import { runPhase } from './comparison_session.mjs';

export const FRAME_BYTES = 262144;
const ARMS = ['pi-bare', 'skills-only', 'ticket-driver-c1a', 'ticket-driver-c3a'];
const STANDARD = 'original-harbor-full-pi-bare';
const STANDARD_SYSTEM = 'Work only through sandbox_exec in the task environment. Complete the user task.';

// The overlay lot stays frozen at 48 requests/$57. The original method may carry a
// lot-declared policy (e.g. flat-rate tokens); the host journal still records every request.
function validBudget(budget, standard) {
  if (budget?.limit_usd === '57' && budget?.max_requests === 48) return true;
  return standard && Number.isSafeInteger(budget?.max_requests) &&
    budget.max_requests >= 1 && budget.max_requests <= 5000 &&
    typeof budget.limit_usd === 'string' && /^\d+(?:\.\d{1,2})?$/.test(budget.limit_usd);
}

const SKILLS_PREFIX = '\n\nFrozen local workflow skills:\n';

const PROMPTS = JSON.parse(readFileSync(new URL('./driver_prompts.json', import.meta.url), 'utf8'));
const DRIVER_ARMS = ['ticket-driver-c1a', 'ticket-driver-c3a'];

// The original method runs Pi bare, or a skilled arm with one snapshot bound by SHA-256.
function validOriginalArm(start) {
  if (start.arm === 'pi-bare') return start.skills_sha256 === undefined;
  return ['skills-only', ...DRIVER_ARMS].includes(start.arm) && typeof start.skills_sha256 === 'string' &&
    /^[a-f0-9]{64}$/.test(start.skills_sha256);
}

// Original-method phases form a prefix of: builder, checker, reviewer (c3a only), corrector.
// Every prompt keeps the original instruction verbatim; system prompts are fixed.
function originalPhaseAllowed(start, names, command) {
  const order = DRIVER_ARMS.includes(start.arm)
    ? ['builder', 'checker', ...(start.arm === 'ticket-driver-c3a' ? ['reviewer'] : []), 'corrector']
    : ['builder'];
  if (command.tools !== 'sandbox' || command.name !== order[names.size]) return false;
  const { prompt, system_prompt: system } = command;
  switch (command.name) {
    case 'builder': return prompt === start.instruction && originalSystem(start, system);
    case 'checker': return prompt === PROMPTS.checker_prefix + start.instruction && system === PROMPTS.checker_system;
    case 'reviewer': return prompt === PROMPTS.reviewer_prefix + start.instruction && system === PROMPTS.reviewer_system;
    default: {
      const head = start.instruction + PROMPTS.correction_marker;
      return prompt.startsWith(head) && prompt.length > head.length && originalSystem(start, system);
    }
  }
}

function originalSystem(start, system) {
  if (start.arm === 'pi-bare') return system === STANDARD_SYSTEM;
  if (typeof system !== 'string' || !system.startsWith(STANDARD_SYSTEM + SKILLS_PREFIX)) return false;
  const skills = system.slice((STANDARD_SYSTEM + SKILLS_PREFIX).length);
  return skills.length > 0 && createHash('sha256').update(skills).digest('hex') === start.skills_sha256;
}

export async function serveComparison({ receive, send, dir, stream, modelRuntime }) {
  let budget;
  let terminal = false;
  try {
    const start = await receive();
    const standard = start.method === STANDARD;
    if (start.type !== 'init' || (!standard && start.method !== 'git-overlay-v1') ||
        (standard && !validOriginalArm(start)) ||
        start.model !== 'openai-codex/gpt-6-sol' || start.thinking !== 'high' ||
        !ARMS.includes(start.arm) || typeof start.task_name !== 'string' ||
        typeof start.trial_id !== 'string' || typeof start.instruction !== 'string' ||
        !start.instruction || !validBudget(start.budget, standard)) {
      throw new Error('invalid comparison binding');
    }
    const identity = { method: start.method, task: start.task_name, arm: start.arm,
      trial: start.trial_id, model: start.model, thinking: start.thinking,
      instruction_sha256: createHash('sha256').update(start.instruction).digest('hex'),
      ...(standard && start.arm === 'skills-only' ? { skills_sha256: start.skills_sha256 } : {}) };
    const model = getModel('openai-codex', 'gpt-6-sol');
    budget = createDurableBudget(model, { limitUsd: start.budget.limit_usd, maxRequests: start.budget.max_requests },
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
      if (standard && !originalPhaseAllowed(start, names, command)) {
        throw new Error('original method phase grammar violated');
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
