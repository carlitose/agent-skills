import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { buildPlan, chunk, mergeReports, parseArguments, partitionSerial, refinePlan, runPlan, selectShard, summarize } from './test-local.mjs';

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
  assert.ok(parseArguments([]).jobs >= 1);
  assert.equal(parseArguments(['full', '--jobs', '4']).jobs, 4);
  assert.equal(parseArguments(['full', '--chunk-cases', '3']).chunkCases, 3);
  assert.deepEqual(parseArguments(['full', '--shard', '2/5']).shard, { index: 2, total: 5 });
  for (const args of [['slow'], ['quick', 'full'], ['--python'], ['--timeout-seconds', '0'], ['--wat'],
    ['--jobs', '0'], ['--jobs', '65'], ['--shard', '0/2'], ['--shard', '3/2'], ['--shard', 'all']]) {
    assert.throws(() => parseArguments(args), /usage|selector|requires|timeout|unknown|must be|shard/i);
  }
});

test('long suites are chunked into separately bounded invocations without losing a case', t => {
  const plan = buildPlan(fixture(t), 'full');
  const cases = Array.from({ length: 7 }, (_value, index) => `test_slow.SlowTests.test_case_${index}`);
  const refined = refinePlan(plan, { chunkCases: 3 }, ['python'], (_command, args) => {
    if (args.includes('--list')) return { status: 0, stdout: JSON.stringify({ scenario_ids: ['a', 'b', 'c', 'd'] }) };
    return { status: 0, stdout: args.at(-1) === 'test_slow.py' ? cases.join('\n') : 'test_one.OneTests.test_only\n' };
  });
  const chunks = refined.selected.filter(check => check.id.startsWith('ticket-autopilot/tests/test_slow.py'));
  assert.deepEqual(chunks.map(check => check.id), [
    'ticket-autopilot/tests/test_slow.py [1/3]', 'ticket-autopilot/tests/test_slow.py [2/3]', 'ticket-autopilot/tests/test_slow.py [3/3]']);
  assert.deepEqual(chunks.flatMap(check => check.args.filter(arg => arg.startsWith('test_slow.'))), cases);
  assert.ok(chunks.every(check => check.env.PYTHONPATH.endsWith('tests')));
  const forward = refined.selected.filter(check => check.id.startsWith('autopilot-forward-matrix'));
  assert.equal(forward.length, 2);
  assert.deepEqual(forward.flatMap(check => check.args.filter(arg => /^[a-d]$/.test(arg))), ['a', 'b', 'c', 'd']);
  assert.ok(forward.every(check => check.format === 'forward'));
});

test('wall-clock bounded suites stay unchunked and outside the parallel phase', t => {
  const plan = buildPlan(fixture(t), 'full');
  const bounded = 'ticket-autopilot/tests/test_command_bounds.py';
  plan.selected.push({ id: bounded, family: 'python', args: ['-B', '-m', 'unittest', 'discover', '-s', 'ticket-autopilot/tests', '-p', 'test_command_bounds.py', '-v'] });
  const refined = refinePlan(plan, { chunkCases: 1 }, ['python'], (_command, args) =>
    ({ status: 0, stdout: args.includes('--list') ? JSON.stringify({ scenario_ids: ['a'] }) : 'mod.Case.test_one\nmod.Case.test_two\n' }));
  assert.ok(refined.selected.some(check => check.id === bounded));
  const { parallel, serial } = partitionSerial(refined.selected);
  assert.deepEqual(serial.map(check => check.id), [bounded]);
  assert.ok(!parallel.some(check => check.id === bounded));
  assert.equal(parallel.length + serial.length, refined.selected.length);
});

test('an unlistable suite keeps its single unchunked invocation', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const refined = refinePlan(plan, { chunkCases: 1 }, ['python'], () => ({ status: 1, stdout: '', stderr: 'discovery failed' }));
  assert.deepEqual(refined.selected.map(check => check.id), plan.selected.map(check => check.id));
});

test('shards partition every refined check exactly once and merge into one report', () => {
  const checks = Array.from({ length: 11 }, (_value, index) => ({ id: 'check-' + index }));
  const shards = [1, 2, 3].map(index => selectShard(checks, index, 3));
  assert.deepEqual(shards.flat().map(check => check.id).sort(), checks.map(check => check.id).sort());
  assert.equal(new Set(shards.flat().map(check => check.id)).size, checks.length);
  assert.deepEqual(chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]]);
  const merged = mergeReports([
    { schema: 1, mode: 'full', log_directory: 'a', records: [{ id: 'one', status: 'succeeded' }], exit_code: 0 },
    { log_directory: 'b', records: [{ id: 'two', status: 'failed' }], exit_code: 1 },
  ], [{ id: 'three', status: 'not-run' }]);
  assert.equal(merged.mode, 'full');
  assert.equal(merged.exit_code, 1);
  assert.deepEqual(merged.counts, { succeeded: 1, failed: 1, errored: 0, skipped: 0, not_run: 1 });
  assert.equal(mergeReports([{ records: [], diagnostic: 'shard 1/2 produced no report' }]).exit_code, 1);
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
  assert.ok(report.records.filter(record => record.status === 'succeeded').every(record => Number.isInteger(record.duration_ms)));
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
