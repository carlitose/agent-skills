import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const checker = fileURLToPath(new URL('./check_file_limits.py', import.meta.url));
const python = process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3');

function fixture(t, files, policy) {
  const root = mkdtempSync(join(tmpdir(), 'file-limits-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'scripts'));
  writeFileSync(join(root, 'scripts/file-limits.json'), JSON.stringify(policy));
  for (const [name, content] of Object.entries(files)) writeFileSync(join(root, name), content);
  return root;
}

function check(root, cwd = root) {
  return spawnSync(python, ['-B', checker, '--root', root, '--json'], {
    cwd, encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1' },
    timeout: 10_000, maxBuffer: 1024 * 1024,
  });
}

const policy = (files, total = 10) => ({ schema: 1, files, total_line_limit: total });

test('exact limits include CRLF, unterminated lines and empty files; cwd is not ownership', (t) => {
  const root = fixture(t, { 'a.md': 'one\r\ntwo', 'empty.md': '' }, policy({ 'a.md': 2, 'empty.md': 1 }, 2));
  const result = check(root, tmpdir());
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.equal(report.total_lines, 2);
  assert.deepEqual(report.violations, []);
  assert.equal(report.files['empty.md'].lines, 0);
});

test('one extra file line fails without needing an aggregate breach', (t) => {
  const root = fixture(t, { 'a.md': 'one\ntwo\nthree\n' }, policy({ 'a.md': 2 }));
  const result = check(root);
  assert.equal(result.status, 1, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout).violations, [{ path: 'a.md', lines: 3, limit: 2 }]);
});

test('aggregate overflow fails even when each file fits', (t) => {
  const root = fixture(t, { 'a.md': 'a\nb', 'b.md': 'a\nb' }, policy({ 'a.md': 2, 'b.md': 2 }, 3));
  const result = check(root);
  assert.equal(result.status, 1, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout).violations, [{ path: '<total>', lines: 4, limit: 3 }]);
});

test('missing and invalid UTF-8 files fail closed', (t) => {
  for (const files of [{}, { 'a.md': Buffer.from([0xff]) }]) {
    const root = fixture(t, files, policy({ 'a.md': 2 }));
    const result = check(root);
    assert.equal(result.status, 2);
    assert.match(result.stderr, /file-limit error:/);
    assert.equal(result.stdout, '');
  }
});

test('malformed policies and paths outside the root fail closed', (t) => {
  const invalid = [
    policy({ 'a.md': true }), policy({ 'a.md': 0 }), policy({ 'a.md': 1.5 }),
    policy({}, 10), policy({ 'a.md': 2 }, false), policy({ '../outside.md': 2 }),
    { ...policy({ 'a.md': 2 }), schema: 2 },
  ];
  for (const config of invalid) {
    const root = fixture(t, { 'a.md': 'one' }, config);
    const result = check(root);
    assert.equal(result.status, 2, JSON.stringify(config));
    assert.match(result.stderr, /file-limit error:/);
  }
});

test('CI runs lint before profile discovery and retains bounded profile failures', () => {
  const workflow = readFileSync(new URL('../.github/workflows/local-profile.yml', import.meta.url), 'utf8');
  const manifest = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  assert.ok(workflow.indexOf('npm run lint') >= 0);
  assert.ok(workflow.indexOf('npm run lint') < workflow.indexOf('name: Resolve the required profile'));
  assert.match(manifest.scripts.lint, /check_file_limits\.py.*&&.*ruff check scripts\/check_file_limits\.py/);
  assert.match(workflow, /timeout-minutes: 15/);
  assert.match(workflow, /--timeout-seconds 900/);
  assert.match(workflow, /name: Retain the report and raw logs\s+if: always\(\)/);
});
