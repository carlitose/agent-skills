import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { buildPlan, parseArguments, summarize, runPlan } from './test-local.mjs';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'local test plan-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const path of ['extensions/example.test.ts', 'scripts/test-local.test.mjs',
    'ticket-autopilot/tests/test_ticket_contract.py', 'ticket-autopilot/tests/test_leaf_protocol.py',
    'ticket-autopilot/tests/test_history_codec.py', 'ticket-autopilot/tests/test_slow.py',
    'llm-wiki/tests/test_project_binding.py', 'llm-wiki/tests/test_other.py',
    'verification-audit/tests/test_verification_contract.py', 'to-tickets/tests/test_finalize_batch.py']) {
    mkdirSync(join(root, path, '..'), { recursive: true });
    writeFileSync(join(root, path), '', 'utf8');
  }
  return root;
}

const success = (args = []) => ({ status: 0, signal: null, stdout: args.includes('ticket-autopilot/scripts/forward_test.py')
  ? JSON.stringify({ schema: 1, result: 'pass', scenarios: { local: { result: 'pass' } }, command_results: { check: { result: 'pass' } } })
  : args.includes('--test') ? '# tests 2\n# pass 2\n# skipped 0\n' : 'Ran 2 tests in 0.01s\n\nOK\n', stderr: '' });
const prerequisites = (command, args) => {
  if (command === 'git') return { ...success(), stdout: 'git version fixture\n' };
  if (args.includes('-c')) return { ...success(), stdout: '[3,12,10]\n' };
  return null;
};

test('npm test selects combined quick scope and exposes full scope explicitly', () => {
  const manifest = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  assert.equal(manifest.scripts.test, 'node scripts/test-local.mjs quick');
  assert.equal(manifest.scripts['test:full'], 'node scripts/test-local.mjs full');
});

test('selectors are explicit and malformed arguments fail before execution', () => {
  assert.equal(parseArguments([]).mode, 'quick');
  assert.equal(parseArguments(['full']).mode, 'full');
  assert.equal(parseArguments(['quick', '--python', 'C:/Python with spaces/python.exe']).python, 'C:/Python with spaces/python.exe');
  for (const args of [['slow'], ['quick', 'full'], ['--python'], ['--timeout-seconds', '0'], ['--wat']]) {
    assert.throws(() => parseArguments(args), /usage|selector|requires|timeout|unknown/i);
  }
});

test('quick includes Node and Python, full includes every supported discovered suite', t => {
  const root = fixture(t);
  const quick = buildPlan(root, 'quick');
  const full = buildPlan(root, 'full');
  assert.ok(quick.selected.some(c => c.family === 'node'));
  assert.ok(quick.selected.some(c => c.family === 'python'));
  assert.ok(quick.omitted.some(c => c.id.includes('test_slow.py')));
  assert.equal(full.omitted.length, 0);
  assert.equal(full.selected.length, quick.selected.length + quick.omitted.length);
  assert.ok(full.selected.some(c => c.id.includes('to-tickets')));
  writeFileSync(join(root, 'llm-wiki/tests/test_new.py'), '', 'utf8');
  assert.equal(buildPlan(root, 'full').selected.length, full.selected.length + 1);
});

test('missing required Python is an error, not an extension-only success', t => {
  const plan = buildPlan(fixture(t), 'quick');
  let testsRun = 0;
  const report = runPlan(plan, { python: 'missing-python', logDirectory: join(plan.root, 'logs') }, (command, args) => {
    if (args.includes('-c')) return { error: Object.assign(new Error('missing'), { code: 'ENOENT' }), status: null };
    if (command === 'git') return prerequisites(command, args);
    testsRun += 1;
    return success();
  });
  assert.notEqual(report.exit_code, 0);
  assert.match(report.diagnostic, /Python.*--python/i);
  assert.equal(testsRun, 0);
  assert.equal(report.counts.not_run, plan.selected.length + plan.omitted.length);
});

test('missing Git and incompatible or malformed explicit Python fail without fallback', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const missingGit = runPlan(plan, { logDirectory: join(plan.root, 'logs') }, () => ({ error: new Error('missing git'), status: null }));
  assert.equal(missingGit.exit_code, 1);
  assert.match(missingGit.diagnostic, /Git.*PATH/);
  for (const version of ['[3,11,9]', 'not-json']) {
    let probes = 0;
    const report = runPlan(plan, { python: 'chosen-python', logDirectory: join(plan.root, 'logs') }, (command, args) => {
      if (command === 'git') return prerequisites(command, args);
      probes += 1;
      return { ...success(), stdout: version };
    });
    assert.equal(probes, 1);
    assert.equal(report.exit_code, 1);
    assert.equal(report.counts.succeeded, 0);
  }
});

test('argument arrays preserve spaced interpreter paths and never invoke a shell', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const calls = [];
  const report = runPlan(plan, { python: 'C:/spaced Python/python.exe', logDirectory: join(plan.root, 'logs') }, (command, args, options) => {
    calls.push({ command, args, options });
    return prerequisites(command, args) ?? success(args);
  });
  assert.equal(report.exit_code, 0);
  assert.ok(calls.some(c => c.command === 'C:/spaced Python/python.exe' && c.args.includes('unittest')));
  assert.ok(calls.every(c => c.options.shell === false));
});

test('failed, errored and all-skipped checks stay distinct and do not stop later checks', t => {
  const plan = buildPlan(fixture(t), 'full');
  let index = 0;
  const report = runPlan(plan, { logDirectory: join(plan.root, 'logs') }, (command, args) => {
    const probe = prerequisites(command, args);
    if (probe) return probe;
    index += 1;
    if (index === 1) return { ...success(), status: 1, stderr: 'assertion failed' };
    if (index === 2) return { error: new Error('spawn failed'), status: null };
    if (index === 3) return { ...success(), stderr: 'Ran 2 tests in 0.01s\n\nOK (skipped=2)\n', stdout: '' };
    return success(args);
  });
  assert.equal(index, plan.selected.length);
  assert.equal(report.exit_code, 1);
  assert.equal(report.counts.failed, 1);
  assert.equal(report.counts.errored, 1);
  assert.equal(report.counts.skipped, 1);
  assert.equal(report.counts.not_run, 0);
  assert.equal(report.counts.succeeded, plan.selected.length - 3);
});

test('incomplete or contradictory forward reports cannot produce a full-profile pass', t => {
  const plan = buildPlan(fixture(t), 'full');
  const valid = JSON.parse(success(['ticket-autopilot/scripts/forward_test.py']).stdout);
  for (const payload of [
    { ...valid, scenarios: { missingOutcome: {} } },
    { ...valid, scenarios: { failed: { result: 'fail' } } },
    { ...valid, scenarios: 'not-an-object' },
    { ...valid, command_results: {} },
    { ...valid, command_results: { failed: { result: 'fail' } } },
    { ...valid, schema: 2 },
  ]) {
    const report = runPlan(plan, { logDirectory: join(plan.root, 'logs') }, (command, args) =>
      prerequisites(command, args) ?? (args.includes('ticket-autopilot/scripts/forward_test.py')
        ? { ...success(), stdout: JSON.stringify(payload) } : success(args)));
    assert.equal(report.exit_code, 1);
    assert.equal(report.counts.errored, 1);
  }
});

test('zero-test, signaled and incomplete bounded results cannot pass', t => {
  const plan = buildPlan(fixture(t), 'quick');
  for (const result of [
    { ...success(), stdout: 'Ran 0 tests in 0.0s\n\nOK\n' },
    { ...success(), status: null, signal: 'SIGTERM' },
    { ...success(), error: Object.assign(new Error('timeout'), { code: 'ETIMEDOUT' }) },
    { ...success(), error: Object.assign(new Error('output limit'), { code: 'ENOBUFS' }) },
  ]) {
    const report = runPlan(plan, { logDirectory: join(plan.root, 'logs') }, (command, args) => prerequisites(command, args) ?? result);
    assert.equal(report.exit_code, 1);
    assert.equal(report.counts.succeeded, 0);
    assert.equal(report.counts.errored, plan.selected.length);
  }
});

test('real Node and Python checks execute from a spaced fixture root', t => {
  const root = fixture(t);
  writeFileSync(join(root, 'package.json'), JSON.stringify({ type: 'module' }));
  writeFileSync(join(root, 'extensions/example.test.ts'), "import test from 'node:test'; const text: string = 'à β'; test('native TS', () => { if (!text) throw Error('missing'); });\n", 'utf8');
  writeFileSync(join(root, 'scripts/test-local.test.mjs'), "import test from 'node:test'; test('native JS', () => {});\n", 'utf8');
  const plan = buildPlan(root, 'quick');
  for (const check of plan.selected.filter(check => check.family === 'python')) {
    writeFileSync(join(root, check.id), "import unittest\nclass NativeCheck(unittest.TestCase):\n    def test_unicode(self):\n        self.assertEqual('à β', 'à β')\n", 'utf8');
  }
  const parentTransport = process.env.NODE_TEST_CONTEXT;
  const report = runPlan(plan, { logDirectory: join(root, 'retained logs'), timeoutSeconds: 30 });
  assert.equal(process.env.NODE_TEST_CONTEXT, parentTransport);
  assert.equal(report.exit_code, 0, JSON.stringify(report));
  assert.equal(report.counts.succeeded, plan.selected.length);
  assert.ok(report.records.filter(record => record.status === 'succeeded').every(record => record.framework_counts.tests_run > 0));
});

test('real hanging and noisy local children produce errors, not partial success', t => {
  const root = fixture(t);
  const plan = { root, mode: 'full', omitted: [], excluded_scopes: [], selected: [
    { id: 'hanging-child', family: 'node', args: ['-e', 'setInterval(() => {}, 1000)'] },
    { id: 'noisy-child', family: 'node', args: ['-e', 'process.stdout.write("x".repeat(20 * 1024 * 1024))'] },
  ] };
  const report = runPlan(plan, { logDirectory: join(root, 'bounded logs'), timeoutSeconds: 1 });
  assert.equal(report.exit_code, 1);
  assert.equal(report.counts.errored, 2);
  assert.equal(report.counts.succeeded, 0);
  assert.match(report.records[0].diagnostic, /ETIMEDOUT/);
  assert.match(report.records[1].diagnostic, /ENOBUFS/);
});

test('check counts do not pretend to be unittest subtest counts', () => {
  assert.deepEqual(summarize([{ status: 'succeeded' }, { status: 'failed' }, { status: 'errored' }, { status: 'skipped' }, { status: 'not-run' }]), {
    succeeded: 1, failed: 1, errored: 1, skipped: 1, not_run: 1,
  });
});
