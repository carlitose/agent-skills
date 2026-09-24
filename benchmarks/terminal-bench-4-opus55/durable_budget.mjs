// Comparison-only usage journal. Every request reservation reaches disk before
// the stream function is called. Partial usage is evidence, never a final bill.
import { appendFileSync, closeSync, fsyncSync, openSync } from 'node:fs';
import { createRequestBudget } from './pilot_budget.mjs';

export function createDurableBudget(model, limits, path, identity) {
  const budget = createRequestBudget(model, limits);
  const boundIdentity = structuredClone(identity);
  const fd = openSync(path, 'wx', 0o600);
  let seq = 0;
  let finished = false;
  let uncertain = false;
  let inputTokens = 0;
  let outputTokens = 0;
  let messages = 0;
  let phase = 'initial';

  function snapshot() {
    const state = budget.state();
    const known = !uncertain && !state.ambiguous && state.pendingRequests === 0 &&
      messages === state.requests;
    return { budget: state, known, cost_usd: known ? state.observedUsd : null,
      input_tokens: inputTokens, output_tokens: outputTokens };
  }

  function persist(event, extra = {}) {
    if (finished) throw new Error('journal already finished');
    appendFileSync(fd, JSON.stringify({ schema: 1, seq: seq++, event, phase,
      identity: boundIdentity, ...snapshot(), ...extra }) + '\n', 'utf8');
    fsyncSync(fd);
  }

  try { persist('initial'); }
  catch (error) { closeSync(fd); throw error; }

  return {
    state: snapshot,
    setPhase(name) {
      if (typeof name !== 'string' || !/^[a-z][a-z0-9-]{0,63}$/.test(name)) {
        throw new Error('invalid phase');
      }
      phase = name;
      persist('phase');
    },
    wrap(stream) {
      const counted = budget.wrap((...args) => {
        // Failure to persist occurs before any provider request and propagates.
        persist('request');
        return stream(...args);
      });
      return (...args) => {
        if (finished) throw new Error('journal already finished');
        if (uncertain) throw new Error('unknown usage blocks model request');
        return counted(...args);
      };
    },
    recordAssistant(message) {
      if (finished) throw new Error('journal already finished');
      const usage = message?.usage;
      const tokens = ['input', 'output', 'cacheRead', 'cacheWrite'];
      const validTokens = tokens.every(key => Number.isSafeInteger(usage?.[key]) && usage[key] >= 0);
      // Pi can create a zero-usage error message when the wrapper rejects an
      // invocation before entering the provider. Do not invent an extra charge.
      if (budget.state().pendingRequests === 0 && message?.stopReason === 'error' &&
          validTokens && tokens.every(key => usage[key] === 0) && usage.cost?.total === 0) {
        persist('synthetic-error');
        return;
      }
      const reported = validTokens && Number.isFinite(usage?.cost?.total) && usage.cost.total >= 0
        ? { input_tokens: usage.input + usage.cacheRead + usage.cacheWrite,
            output_tokens: usage.output, cost_usd: usage.cost.total } : null;
      if (!validTokens || tokens.every(key => usage[key] === 0) ||
          ['error', 'aborted', 'deferred'].includes(message?.stopReason)) {
        uncertain = true;
        persist('unknown-usage', { reported_usage: reported });
        throw new Error('unknown provider usage');
      }
      try {
        budget.recordAssistant(message);
        inputTokens += usage.input + usage.cacheRead + usage.cacheWrite;
        outputTokens += usage.output;
        messages++;
        persist('usage');
      } catch (error) {
        uncertain = true;
        persist('unknown-usage');
        throw error;
      }
    },
    finish(status) {
      if (!['completed', 'failed'].includes(status)) throw new Error('invalid terminal status');
      const result = snapshot();
      try { persist('terminal', { status }); }
      finally { finished = true; closeSync(fd); }
      return result;
    },
  };
}
