import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { parseArgs, scaffold, plan } from '../scaffold.mjs';

const SCRIPT = fileURLToPath(new URL('../scaffold.mjs', import.meta.url));

function project(t) {
  const root = mkdtempSync(join(tmpdir(), 'wiki-rag-scaffold-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'docs', 'wiki', 'concepts'), { recursive: true });
  writeFileSync(join(root, 'docs', 'wiki', 'concepts', 'gate.md'), '# Gate\n');
  return root;
}

test('scaffold writes the adapter, contract, tests and gitignore lines', t => {
  const root = project(t);
  writeFileSync(join(root, '.gitignore'), 'node_modules/');
  const result = scaffold({ root, name: 'demo', wiki: 'docs/wiki/', device: 'auto' });
  for (const rel of ['tools/demo-rag/rag.mjs', 'tools/demo-rag/contract.mjs', 'tools/demo-rag/hybrid.mjs',
    'tools/demo-rag/package.json', 'tools/demo-rag/rag.config.json', 'tools/demo-rag/README.md',
    'skills/demo-rag/SKILL.md', 'tests/demo-rag.Tests.mjs']) assert.ok(result.written.includes(rel), rel);
  assert.deepEqual(JSON.parse(readFileSync(join(root, 'tools/demo-rag/rag.config.json'), 'utf8')),
    { schema: 1, name: 'demo', wiki: 'docs/wiki', device: 'auto' });
  assert.equal(JSON.parse(readFileSync(join(root, 'tools/demo-rag/package.json'), 'utf8')).dependencies['@tobilu/qmd'], '2.8.3');
  const skill = readFileSync(join(root, 'skills/demo-rag/SKILL.md'), 'utf8');
  assert.match(skill, /- Adapter: `qmd-local-v1`/);
  assert.match(skill, /- Binding: `demo-wiki-local-v1`/);
  assert.match(skill, /exact text search over `docs\/wiki\/`/);
  assert.doesNotMatch(skill + readFileSync(join(root, 'tests/demo-rag.Tests.mjs'), 'utf8'), /\{\{\w+\}\}/);
  assert.equal(readFileSync(join(root, '.gitignore'), 'utf8'),
    'node_modules/\n/.demo-rag/\n/tools/demo-rag/node_modules/\n');
});

test('scaffold refuses to overwrite and appends gitignore lines once', t => {
  const root = project(t);
  scaffold({ root, name: 'demo', wiki: 'docs/wiki', device: 'cpu' });
  assert.throws(() => scaffold({ root, name: 'demo', wiki: 'docs/wiki', device: 'cpu' }), /refusing-to-overwrite/);
  rmSync(join(root, 'tools'), { recursive: true }); rmSync(join(root, 'skills'), { recursive: true }); rmSync(join(root, 'tests'), { recursive: true });
  const again = scaffold({ root, name: 'demo', wiki: 'docs/wiki', device: 'cpu' });
  assert.deepEqual(again.gitignore, []);
});

test('invalid name, wiki path or device is rejected before writing', t => {
  const root = project(t);
  assert.throws(() => scaffold({ root, name: 'Bad Name', wiki: 'docs/wiki', device: 'auto' }), /invalid-name/);
  assert.throws(() => scaffold({ root, name: 'demo', wiki: '../outside', device: 'auto' }), /invalid-wiki/);
  assert.throws(() => scaffold({ root, name: 'demo', wiki: root, device: 'auto' }), /invalid-wiki/);
  assert.throws(() => scaffold({ root, name: 'demo', wiki: 'docs/wiki', device: 'metal' }), /invalid-device/);
  assert.throws(() => scaffold({ root, name: 'demo', wiki: 'missing', device: 'auto' }), /wiki-not-found/);
  assert.equal(existsSync(join(root, 'tools')), false);
});

test('arguments default the device to auto and reject unknown options', () => {
  assert.equal(parseArgs(['.', '--name', 'demo', '--wiki', 'wiki']).device, 'auto');
  assert.throws(() => parseArgs(['.', '--name', 'demo', '--wiki', 'wiki', '--gpu', 'x']), /unknown option/);
  assert.throws(() => parseArgs(['--name', 'demo']), /usage/);
  assert.equal(plan({ name: 'demo', wiki: 'wiki', device: 'auto' }).length, 8);
});

test('the generated adapter tests pass without node_modules or models', t => {
  const root = project(t);
  const cli = spawnSync(process.execPath, [SCRIPT, root, '--name', 'demo', '--wiki', 'docs/wiki'], { encoding: 'utf8' });
  assert.equal(cli.status, 0, cli.stderr);
  assert.match(cli.stdout, /npm ci/);
  const run = spawnSync(process.execPath, ['--test', '--test-reporter=tap', join(root, 'tests', 'demo-rag.Tests.mjs')], { cwd: root, encoding: 'utf8',
    env: Object.fromEntries(Object.entries(process.env).filter(([key]) => key !== 'NODE_TEST_CONTEXT')) });
  assert.equal(run.status, 0, run.stdout + run.stderr);
  assert.match(run.stdout, /# fail 0/);
});
