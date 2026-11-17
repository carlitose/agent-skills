import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync, realpathSync, statSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ADAPTER = 'qmd-local-v1';
export const QMD_VERSION = '2.8.3';
export const DEVICES = ['auto', 'cpu'];
export const MODEL_FILES = {
  embed: ['ggml-org/embeddinggemma-300M-GGUF', 'embeddinggemma-300M-Q8_0.gguf'],
  rerank: ['ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF', 'qwen3-reranker-0.6b-q8_0.gguf'],
  generate: ['tobil/qmd-query-expansion-1.7B-gguf', 'qmd-query-expansion-1.7B-q4_k_m.gguf'],
};
export const sha256 = (data) => createHash('sha256').update(data).digest('hex');
export const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

const NAME = /^[a-z][a-z0-9-]{0,39}$/;
export const ADAPTER_DIR = dirname(fileURLToPath(import.meta.url));

/** Reads and validates rag.config.json, the only per-project setting of the adapter. */
export function loadConfig(adapterDir = ADAPTER_DIR) {
  const config = readJson(join(adapterDir, 'rag.config.json'));
  if (config.schema !== 1 || !NAME.test(config.name ?? '') || typeof config.wiki !== 'string'
      || !config.wiki || isAbsolute(config.wiki) || config.wiki.split(/[\\/]/).includes('..')
      || !DEVICES.includes(config.device)) {
    throw new Error('invalid-rag-config');
  }
  return config;
}

export const bindingId = (config) => `${config.name}-wiki-local-v1`;
export const fallback = (reason, config) => ({ mode: 'compiled-markdown', reason,
  binding: config ? bindingId(config) : null, results: [] });

/** Every path the adapter touches, derived from the project root and the config. */
export function paths(root, config, adapterDir = join(root, 'tools', `${config.name}-rag`)) {
  const state = join(root, `.${config.name}-rag`);
  return { root, config, adapterDir, collection: config.name, binding: bindingId(config),
    wiki: join(root, config.wiki), contract: join(root, 'skills', `${config.name}-rag`, 'SKILL.md'),
    state, db: join(state, 'index.sqlite'), manifest: join(state, 'manifest.json'),
    cliConfig: join(state, 'config', 'qmd', 'index.yml'),
    package: join(adapterDir, 'node_modules', '@tobilu', 'qmd', 'package.json'),
    models: Object.fromEntries(Object.entries(MODEL_FILES).map(([role, [, file]]) => [role, join(state, 'models', file)])),
  };
}

export function storeConfig(p) {
  return { collections: { [p.collection]: { path: p.wiki, pattern: '**/*.md' } }, models: p.models };
}

/** QMD environment: local state only; CPU forced only when the config asks for it. */
export function runtimeEnv(p, base = {}) {
  const env = { ...base, XDG_CACHE_HOME: join(p.state, 'cache'), XDG_CONFIG_HOME: join(p.state, 'config'),
    QMD_EMBED_PARALLELISM: '1' };
  if (p.config.device === 'cpu') env.QMD_FORCE_CPU = '1';
  else delete env.QMD_FORCE_CPU;
  return env;
}

export function assertContract(p) {
  const contract = readFileSync(p.contract, 'utf8');
  if (!contract.includes(`- Adapter: \`${ADAPTER}\``) || !contract.includes(`- Binding: \`${p.binding}\``)) {
    throw new Error('unsupported-active-contract');
  }
}

export function corpusManifest(wiki) {
  const files = {};
  function visit(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
      const path = join(dir, entry.name);
      if (entry.isSymbolicLink()) throw new Error('symlink-in-wiki-corpus');
      if (entry.isDirectory()) visit(path);
      else if (entry.isFile() && entry.name.endsWith('.md')) {
        files[relative(wiki, path).split(sep).join('/')] = sha256(readFileSync(path));
      }
    }
  }
  visit(wiki);
  if (!Object.keys(files).length) throw new Error('empty-wiki-corpus');
  return { files, digest: sha256(JSON.stringify(files)) };
}

/** Read-only probe: never installs, downloads or indexes. */
export function inspect(p) {
  try {
    assertContract(p);
    if (!existsSync(p.package) || readJson(p.package).version !== QMD_VERSION) return fallback('qmd-package-missing-or-incompatible', p.config);
    if (!existsSync(p.db) || !statSync(p.db).size || !existsSync(p.manifest)) return fallback('semantic-index-missing', p.config);
    const m = readJson(p.manifest);
    if (m.adapter !== ADAPTER || m.binding !== p.binding || m.package_version !== QMD_VERSION) return fallback('index-binding-mismatch', p.config);
    if (!existsSync(p.cliConfig) || JSON.stringify(readJson(p.cliConfig)) !== JSON.stringify(storeConfig(p))) return fallback('local-cli-config-missing-or-changed', p.config);
    if (!m.status?.hasVectorIndex || m.status.needsEmbedding !== 0 || m.status.totalDocuments < 1) return fallback('semantic-index-incomplete', p.config);
    const corpus = corpusManifest(p.wiki);
    if (corpus.digest !== m.corpus.digest) return fallback('semantic-index-stale', p.config);
    for (const [role, path] of Object.entries(p.models)) {
      if (!existsSync(path) || lstatSync(path).isSymbolicLink() || !m.models[role]
          || statSync(path).size !== m.models[role].bytes || statSync(path).mtimeMs !== m.models[role].mtimeMs) {
        return fallback('local-model-missing-or-changed', p.config);
      }
    }
    return { mode: `rag/hybrid:${ADAPTER}`, binding: p.binding, device: p.config.device,
      corpus_digest: corpus.digest, documents: Object.keys(corpus.files).length };
  } catch (error) {
    return fallback(error.code === 'ENOENT' ? 'contract-or-corpus-missing' : error.message, p.config);
  }
}

/** Maps a QMD hit back to the canonical page and refuses anything outside the bound corpus. */
export function canonicalResult(p, manifest, result) {
  const prefix = `qmd://${p.collection}/`;
  const uri = result.filepath ?? result.file;
  if (typeof uri !== 'string' || !uri.startsWith(prefix)) throw new Error('unexpected-retrieval-path');
  const name = uri.slice(prefix.length);
  const path = resolve(p.wiki, name);
  const rel = relative(p.wiki, path);
  if (rel.startsWith('..') || isAbsolute(rel) || !name.endsWith('.md')
      || realpathSync(path) !== path || !Object.hasOwn(manifest.files, name)) throw new Error('retrieval-outside-bound-corpus');
  const content = readFileSync(path, 'utf8');
  const hash = sha256(readFileSync(path));
  if (hash !== manifest.files[name]) throw new Error('canonical-page-changed-during-query');
  return { path: `${p.config.wiki.replace(/\\/g, '/').replace(/\/$/, '')}/${name}`, citation: `[[${name.slice(0, -3)}]]`,
    sha256: hash, title: result.title, score: result.score, snippet: result.snippet ?? result.body?.slice(0, 1200),
    content };
}
