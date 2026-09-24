// Test-only authentication boundary. No real auth file, refresh, or model network.
import { InMemoryCredentialStore } from '@earendil-works/pi-ai';
import { ModelRuntime } from '@earendil-works/pi-coding-agent';

export async function offlineModelRuntime() {
  globalThis.fetch = async () => { throw new Error('network forbidden in offline SDK tests'); };
  const credentials = new InMemoryCredentialStore();
  await credentials.modify('openai-codex', async () => ({ type: 'oauth',
    access: 'tbf-offline-never-send', refresh: 'unused', expires: 4102444800000 }));
  return ModelRuntime.create({ credentials, modelsPath: null,
    allowModelNetwork: false, refreshOnCreate: false });
}
