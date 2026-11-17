import { spawn } from 'node:child_process';
import { join } from 'node:path';
import { runtimeEnv } from './contract.mjs';

export function hybridInvocation(p, question) {
  return {
    args: [join(p.adapterDir, 'node_modules', '@tobilu', 'qmd', 'bin', 'qmd'), 'query',
      '-c', p.collection, '-n', '8', '-C', '12', '--json', '--explain', '--', question],
    env: { ...runtimeEnv(p, process.env), INDEX_PATH: p.db, QMD_CONFIG_DIR: join(p.state, 'config', 'qmd'),
      QMD_EMBED_MODEL: p.models.embed, QMD_RERANK_MODEL: p.models.rerank, QMD_GENERATE_MODEL: p.models.generate },
  };
}

export async function hybridSearch(p, question) {
  // The published CLI holds its withLLMSession guard across the whole hybrid pipeline;
  // the 2.8.3 SDK idle timer can otherwise dispose a slow CPU operation mid-query.
  const invocation = hybridInvocation(p, question);
  const output = await new Promise((resolvePromise, reject) => {
    const child = spawn(process.execPath, invocation.args, { cwd: p.root, env: invocation.env, shell: false,
      stdio: ['ignore', 'pipe', 'pipe'] });
    const chunks = [];
    child.stdout.on('data', chunk => chunks.push(chunk));
    child.stderr.on('data', chunk => process.stderr.write(chunk));
    child.on('error', reject);
    child.on('close', (code, signal) => {
      if (code !== 0) reject(new Error(`hybrid-cli-failed:${code ?? signal}`));
      else resolvePromise(Buffer.concat(chunks).toString('utf8'));
    });
  });
  const results = JSON.parse(output);
  if (!Array.isArray(results)) throw new Error('unexpected-hybrid-cli-json');
  return results;
}
