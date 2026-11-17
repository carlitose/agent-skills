#!/usr/bin/env node
// Scaffolds the optional local retrieval adapter for an LLM Wiki into a project.
// Writes files only; never runs npm, downloads models or builds an index.
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TEMPLATES = join(dirname(fileURLToPath(import.meta.url)), '..', 'templates');
const NAME = /^[a-z][a-z0-9-]{0,39}$/;
const DEVICES = ['auto', 'cpu'];
const ADAPTER_FILES = ['rag.mjs', 'contract.mjs', 'hybrid.mjs'];
const USAGE = 'usage: scaffold.mjs <project-root> --name <name> --wiki <relative-wiki-dir> [--device auto|cpu]';

export function parseArgs(argv) {
  const options = { device: 'auto' };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (['--name', '--wiki', '--device'].includes(arg)) {
      if (i + 1 >= argv.length) throw new Error(`missing value for ${arg}`);
      options[arg.slice(2)] = argv[++i];
    } else if (arg.startsWith('--')) throw new Error(`unknown option ${arg}`);
    else positional.push(arg);
  }
  if (positional.length !== 1 || !options.name || !options.wiki) throw new Error(USAGE);
  return { root: resolve(positional[0]), ...options };
}

export function validate({ root, name, wiki, device }) {
  if (!NAME.test(name)) throw new Error('invalid-name: lowercase letters, digits and dashes, starting with a letter');
  if (isAbsolute(wiki) || wiki.split(/[\\/]/).includes('..')) throw new Error('invalid-wiki: must be relative to the project root');
  if (!DEVICES.includes(device)) throw new Error(`invalid-device: one of ${DEVICES.join(', ')}`);
  const wikiDir = join(root, wiki);
  if (!existsSync(wikiDir) || !statSync(wikiDir).isDirectory()) throw new Error(`wiki-not-found: ${wikiDir}`);
}

/** Every file the scaffold would write, as [relativePath, contentOrSourceFile]. */
export function plan({ name, wiki, device }) {
  const wikiPath = wiki.replace(/\\/g, '/').replace(/\/+$/, '');
  const values = { NAME: name, WIKI: wikiPath, BINDING: `${name}-wiki-local-v1` };
  const fill = (file) => readFileSync(join(TEMPLATES, file), 'utf8').replace(/\{\{(\w+)\}\}/g, (_, key) => values[key]);
  const tool = `tools/${name}-rag`;
  return [
    ...ADAPTER_FILES.map(file => [`${tool}/${file}`, { copy: join(TEMPLATES, 'adapter', file) }]),
    [`${tool}/rag.config.json`, JSON.stringify({ schema: 1, name, wiki: wikiPath, device }, null, 2) + '\n'],
    [`${tool}/package.json`, JSON.stringify({ name: `${name}-wiki-rag`, version: '0.1.0', private: true, type: 'module',
      engines: { node: '>=22' }, dependencies: { '@tobilu/qmd': '2.8.3' } }, null, 2) + '\n'],
    [`${tool}/README.md`, fill('adapter/README.md.tmpl')],
    [`skills/${name}-rag/SKILL.md`, fill('skill/SKILL.md.tmpl')],
    [`tests/${name}-rag.Tests.mjs`, fill('tests/rag.Tests.mjs.tmpl')],
  ];
}

export function gitignoreLines(name) {
  return [`/.${name}-rag/`, `/tools/${name}-rag/node_modules/`];
}

export function scaffold(options) {
  validate(options);
  const files = plan(options);
  const existing = files.map(([rel]) => rel).filter(rel => existsSync(join(options.root, rel)));
  if (existing.length) throw new Error(`refusing-to-overwrite: ${existing.join(', ')}`);
  for (const [rel, content] of files) {
    const target = join(options.root, rel);
    mkdirSync(dirname(target), { recursive: true });
    if (typeof content === 'string') writeFileSync(target, content);
    else copyFileSync(content.copy, target);
  }
  const ignore = join(options.root, '.gitignore');
  const current = existsSync(ignore) ? readFileSync(ignore, 'utf8') : '';
  const present = new Set(current.split(/\r?\n/));
  const missing = gitignoreLines(options.name).filter(line => !present.has(line));
  if (missing.length) appendFileSync(ignore, (current && !current.endsWith('\n') ? '\n' : '') + missing.join('\n') + '\n');
  return { written: files.map(([rel]) => rel), gitignore: missing };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = parseArgs(process.argv.slice(2));
    const result = scaffold(options);
    const tool = `tools/${options.name}-rag`;
    console.log(JSON.stringify(result, null, 2));
    console.log(['', 'Next, when you choose to (network and ~2.3 GB of models):',
      `  cd ${tool} && npm ci --no-audit --no-fund   (first time: npm install)`,
      `  node ${tool}/rag.mjs prepare`,
      `  node ${tool}/rag.mjs status`].join('\n'));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
