import { createReadStream, createWriteStream, existsSync, mkdirSync, openSync, readSync, closeSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { ADAPTER, ADAPTER_DIR, QMD_VERSION, MODEL_FILES, loadConfig, paths, storeConfig, runtimeEnv, readJson,
  assertContract, corpusManifest, inspect, canonicalResult, fallback } from './contract.mjs';
import { hybridSearch } from './hybrid.mjs';

const root = resolve(ADAPTER_DIR, '../..');
let p;
const [command = 'status', ...args] = process.argv.slice(2);
const json = (value) => console.log(JSON.stringify(value, null, 2));

async function openStore() {
  // Set before importing QMD: its module-level cache/config defaults read these.
  const env = runtimeEnv(p, process.env);
  for (const key of ['XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'QMD_EMBED_PARALLELISM', 'QMD_FORCE_CPU']) {
    if (key in env) process.env[key] = env[key]; else delete process.env[key];
  }
  const { createStore } = await import('@tobilu/qmd');
  return createStore({ dbPath: p.db, config: storeConfig(p) });
}

function validModel(path) {
  if (!existsSync(path) || statSync(path).size < 1024 * 1024) return false;
  const fd = openSync(path, 'r');
  try { const magic = Buffer.alloc(4); readSync(fd, magic, 0, 4, 0); return magic.toString() === 'GGUF'; }
  finally { closeSync(fd); }
}

async function fileHash(path) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest('hex');
}

async function downloadModels() {
  mkdirSync(join(p.state, 'models'), { recursive: true });
  const records = {};
  for (const [role, [repo, filename]] of Object.entries(MODEL_FILES)) {
    const path = p.models[role];
    const url = `https://huggingface.co/${repo}/resolve/main/${filename}`;
    if (!validModel(path)) {
      console.error(`Downloading local ${role} model: ${filename}`);
      const response = await fetch(url);
      if (!response.ok || !response.body) throw new Error(`model-download-failed:${role}:HTTP-${response.status}`);
      const partial = path + '.partial';
      await pipeline(Readable.fromWeb(response.body), createWriteStream(partial));
      if (!validModel(partial)) throw new Error(`model-download-not-gguf:${role}`);
      renameSync(partial, path);
    }
    const stat = statSync(path);
    records[role] = { source: url, bytes: stat.size, mtimeMs: stat.mtimeMs, sha256: await fileHash(path) };
    console.error(`Local ${role} model ready (${stat.size} bytes).`);
  }
  return records;
}

async function prepare() {
  assertContract(p);
  if (readJson(p.package).version !== QMD_VERSION) throw new Error('qmd-package-missing-or-incompatible');
  mkdirSync(p.state, { recursive: true });
  const corpus = corpusManifest(p.wiki);
  const models = await downloadModels();
  mkdirSync(dirname(p.cliConfig), { recursive: true });
  // JSON is a YAML subset; all paths are absolute and no hooks are configured.
  writeFileSync(p.cliConfig, JSON.stringify(storeConfig(p), null, 2) + '\n');
  const store = await openStore();
  try {
    const update = await store.update({ collections: [p.collection] });
    console.error(`Indexed ${Object.keys(corpus.files).length} canonical wiki pages.`);
    const embedding = await store.embed({ chunkStrategy: 'regex', onProgress: ({ chunksEmbedded, totalChunks }) => {
      if (chunksEmbedded === totalChunks || chunksEmbedded % 10 === 0) console.error(`Embedding ${chunksEmbedded}/${totalChunks}`);
    } });
    const status = await store.getStatus();
    if (embedding.errors || !status.hasVectorIndex || status.needsEmbedding !== 0
        || status.totalDocuments !== Object.keys(corpus.files).length) throw new Error('semantic-index-incomplete');
    if (corpusManifest(p.wiki).digest !== corpus.digest) throw new Error('wiki-changed-during-preparation');
    const manifest = { schema: 1, adapter: ADAPTER, binding: p.binding, package_version: QMD_VERSION,
      prepared_at: new Date().toISOString(), corpus, models, update, embedding, status };
    writeFileSync(p.manifest + '.tmp', JSON.stringify(manifest, null, 2) + '\n');
    renameSync(p.manifest + '.tmp', p.manifest);
    json({ ...inspect(p), update, embedding, status });
  } finally { await store.close(); }
}

const RETRIEVAL = { search: 'lexical-bm25', vector: 'vector', query: 'hybrid-expanded-reranked' };

async function query(mode, question) {
  if (!question?.trim()) throw new Error('question-required');
  const available = inspect(p);
  if (available.mode === 'compiled-markdown') { json(available); process.exitCode = 2; return; }
  const before = corpusManifest(p.wiki);
  const store = mode === 'query' ? null : await openStore();
  try {
    const results = mode === 'search' ? await store.searchLex(question, { collection: p.collection, limit: 8 })
      : mode === 'vector' ? await store.searchVector(question, { collection: p.collection, limit: 8 })
      : await hybridSearch(p, question);
    if (corpusManifest(p.wiki).digest !== before.digest) throw new Error('wiki-changed-during-query');
    const canonical = [];
    const seen = new Set();
    for (const result of results) {
      const page = canonicalResult(p, before, result);
      if (!seen.has(page.path)) { canonical.push(page); seen.add(page.path); }
    }
    json({ ...available, retrieval: RETRIEVAL[mode], question,
      reason: canonical.length ? 'retrieved-canonical-context' : 'no-matching-context', results: canonical,
      instruction: 'Read canonical pages and their sources; scores are not truth.' });
  } finally { if (store) await store.close(); }
}

try {
  p = paths(root, loadConfig(), ADAPTER_DIR);
  if (command === 'status') json(inspect(p));
  else if (command === 'models') { assertContract(p); json(await downloadModels()); }
  else if (command === 'prepare') await prepare();
  else if (command in RETRIEVAL) await query(command, args.join(' '));
  else throw new Error('usage: rag.mjs status | models | prepare | search <words> | vector <question> | query <question>');
} catch (error) {
  console.error(error.stack ?? String(error));
  json(fallback(error.message, p?.config));
  process.exitCode = 1;
}
