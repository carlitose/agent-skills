import { ModelRuntime, type ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { installJudge } from './chain-judge-core.ts';

// Load only through the future caller's explicit authorized -e argv. No installation,
// session creation, network refresh, default model, or credential fallback is performed.
export default function chainJudge(pi: ExtensionAPI) {
  let backend: Promise<ModelRuntime> | undefined;
  installJudge(pi, () => backend ??= ModelRuntime.create({
    refreshOnCreate: false,
    allowModelNetwork: false,
  }));
}
