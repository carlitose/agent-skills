// A conservative per-attempt model request reservation. Not an invoice or
// an account-level spending cap: the host ledger must also admit/settle starts.
const FROZEN = {
  provider: 'openai-codex', id: 'gpt-6-sol', contextWindow: 272000, maxTokens: 128000,
  cost: { input: 2, output: 10, cacheRead: 0.2, cacheWrite: 2.5,
    tiers: [{ inputTokensAbove: 272000, input: 4, output: 15, cacheRead: 0.4, cacheWrite: 5 }] },
};

function assertFrozen(model) {
  if (model?.provider !== FROZEN.provider || model?.id !== FROZEN.id ||
      model?.contextWindow !== FROZEN.contextWindow || model?.maxTokens !== FROZEN.maxTokens ||
      JSON.stringify(model?.cost) !== JSON.stringify(FROZEN.cost)) {
    throw new Error('model or tariff drift');
  }
}

function cents(value) {
  if (typeof value !== 'string' || !/^\d+(?:\.\d{1,2})?$/.test(value)) {
    throw new Error('invalid budget');
  }
  const [whole, fraction = ''] = value.split('.');
  const result = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (!Number.isSafeInteger(result) || result <= 0) throw new Error('invalid budget');
  return result;
}

export function createRequestBudget(model, { limitUsd, maxRequests }) {
  assertFrozen(model);
  const limitCents = cents(limitUsd);
  if (!Number.isSafeInteger(maxRequests) || maxRequests <= 0) throw new Error('invalid budget');
  const rates = [FROZEN.cost, ...FROZEN.cost.tiers];
  // Pi's Codex adapter may apply 2x priority-tier pricing. Its cost calculator
  // also permits 2x input for long cache writes; reserve that case even here.
  const inputRate = 2 * Math.max(...rates.flatMap(rate => [
    rate.input, rate.cacheRead, rate.cacheWrite, rate.input * 2,
  ]));
  const outputRate = 2 * Math.max(...rates.map(rate => rate.output));
  const perRequestCents = Math.ceil(
    (model.contextWindow * inputRate + model.maxTokens * outputRate) / 10000);
  if (perRequestCents > limitCents) throw new Error('request budget exceeds limit');
  let requests = 0;
  let pendingRequests = 0;
  let observedUsd = 0;
  let ambiguous = false;
  return {
    wrap(stream) {
      return (selected, context, options) => {
        if (ambiguous) throw new Error('ambiguous cost blocks model request');
        assertFrozen(selected);
        if (requests >= maxRequests) throw new Error('request limit reached');
        if (observedUsd + (pendingRequests + 1) * perRequestCents / 100 > limitCents / 100 + 1e-9) {
          throw new Error('request budget exhausted');
        }
        requests++;
        pendingRequests++;
        try { return stream(selected, context, options); }
        catch (error) { ambiguous = true; throw error; }
      };
    },
    recordAssistant(message) {
      const usage = message?.usage;
      const actual = usage?.cost?.total;
      if (pendingRequests === 0 || !Number.isFinite(actual) || actual < 0 ||
          !Number.isSafeInteger(usage?.output) || usage.output < 0 ||
          (actual === 0 && [usage.input, usage.output, usage.cacheRead,
            usage.cacheWrite].some(tokens => tokens > 0))) {
        ambiguous = true;
        throw new Error('unknown model cost');
      }
      pendingRequests--;
      observedUsd += actual;
      if (actual > perRequestCents / 100 + 1e-9 ||
          observedUsd + pendingRequests * perRequestCents / 100 > limitCents / 100 + 1e-9) {
        ambiguous = true;
        throw new Error('cost exceeds reservation');
      }
    },
    state() {
      return { requests, pendingRequests, maxPerRequestUsd: perRequestCents / 100,
        reservedUsd: observedUsd + pendingRequests * perRequestCents / 100,
        observedUsd, ambiguous, maxRequests, limitUsd };
    },
  };
}
