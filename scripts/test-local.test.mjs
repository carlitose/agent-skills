import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { QUICK_CLI_CASES, QUICK_CLI_CHECK, baseId, buildPlan, checkTimeoutMs, chunk, estimateMs, foldHistory, forwardReleaseCheck, groupByCost, mergeReports, parseArguments, partitionSerial, readHistory, refinePlan, runPlan, selectShard, summarize } from './test-local.mjs';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'local test plan-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const path of ['extensions/example.test.ts', 'scripts/test-local.test.mjs',
    'ticket-autopilot/tests/test_ticket_contract.py', 'ticket-autopilot/tests/test_leaf_protocol.py',
    'ticket-autopilot/tests/test_history_codec.py', 'ticket-autopilot/tests/test_kernel.py',
    'ticket-autopilot/tests/test_cli.py', 'ticket-autopilot/tests/test_slow.py',
    'ticket-driver/tests/test_driver.py',
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

test('quick adds the exact approved CLI gate and kernel without changing full inventory', t => {
  const root = fixture(t);
  const quick = buildPlan(root, 'quick');
  const full = buildPlan(root, 'full');
  const exact = quick.selected.find(check => check.id === QUICK_CLI_CHECK);
  assert.ok(exact, 'quick exposes one distinct exact-case check');
  assert.deepEqual(exact.unit_ids, QUICK_CLI_CASES);
  assert.equal(new Set(exact.unit_ids).size, 10);
  assert.deepEqual(exact.args.slice(-10), QUICK_CLI_CASES);
  assert.ok(quick.selected.some(check => check.id === 'ticket-autopilot/tests/test_kernel.py'));
  assert.ok(quick.selected.some(check => check.id === 'ticket-driver/tests/test_driver.py'));
  assert.ok(!quick.selected.some(check => check.id === 'ticket-autopilot/tests/test_cli.py'));
  const omittedCli = quick.omitted.find(check => check.id === 'ticket-autopilot/tests/test_cli.py');
  assert.match(omittedCli?.omitted_reason ?? '', /remaining.*full/i);
  assert.ok(full.selected.some(check => check.id === 'ticket-autopilot/tests/test_cli.py'));
  assert.ok(!full.selected.some(check => check.id === QUICK_CLI_CHECK));
  assert.deepEqual(full.omitted.map(check => check.id), ['autopilot-forward-matrix']);
});

test('quick fails visibly when an approved CLI identifier is absent', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const available = QUICK_CLI_CASES.slice(1);
  assert.throws(() => refinePlan(plan, { chunkCases: 3 }, ['python'], (_command, args) => ({
    status: 0,
    stdout: args.at(-1) === 'test_cli.py' ? available.join('\n') : 'test_one.OneTests.test_only\n',
  })), /required quick unittest id is missing.*test_enabled_preflight/i);
});

test('quick chunks each approved CLI identifier exactly once', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const refined = refinePlan(plan, { chunkCases: 3 }, ['python'], (_command, args) => ({
    status: 0,
    stdout: args.at(-1) === 'test_cli.py'
      ? ['test_cli.CliTests.test_outside_gate', ...QUICK_CLI_CASES].join('\n')
      : 'test_one.OneTests.test_only\n',
  }));
  assert.equal(baseId(QUICK_CLI_CHECK), 'ticket-autopilot/tests/test_cli.py',
    'the partial gate reuses full-suite duration history');
  const chunks = refined.selected.filter(check => check.id.startsWith(QUICK_CLI_CHECK));
  assert.equal(chunks.length, 10, 'unmeasured e2e cases start independently so one shard cannot serialize the gate');
  assert.deepEqual(chunks.flatMap(check => check.unit_ids), QUICK_CLI_CASES);
  assert.equal(new Set(chunks.flatMap(check => check.unit_ids)).size, 10);
  assert.ok(chunks.every(check => check.env.PYTHONPATH.endsWith('ticket-autopilot\\tests')
    || check.env.PYTHONPATH.endsWith('ticket-autopilot/tests')));
  assert.ok(!chunks.flatMap(check => check.args).includes('test_cli.CliTests.test_outside_gate'));
});

test('quick CLI chunks use full-suite case history for cost-aware shard distribution', t => {
  const plan = buildPlan(fixture(t), 'quick');
  const unit_ms = Object.fromEntries(QUICK_CLI_CASES.map(id => [id, 60_000]));
  const history = { 'ticket-autopilot/tests/test_cli.py': { duration_ms: 600_000, units: 10, unit_ms } };
  const refined = refinePlan(plan, { chunkCases: 3, chunkSeconds: 120, history }, ['python'], (_command, args) => ({
    status: 0,
    stdout: args.at(-1) === 'test_cli.py' ? QUICK_CLI_CASES.join('\n') : 'test_one.OneTests.test_only\n',
  }));
  const chunks = refined.selected.filter(check => check.id.startsWith(QUICK_CLI_CHECK));
  assert.equal(chunks.length, 5);
  assert.ok(chunks.every(check => check.estimated_ms === 120_000));
  const occupied = Array.from({ length: 8 }, (_value, index) =>
    selectShard(refined.selected, index + 1, 8).some(check => check.id.startsWith(QUICK_CLI_CHECK)));
  assert.equal(occupied.filter(Boolean).length, 5, 'priced e2e chunks cannot collapse onto one apparently empty shard');
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
  plan.selected.push(forwardReleaseCheck());
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

test('an unlistable ordinary suite keeps its single unchunked invocation', t => {
  const plan = buildPlan(fixture(t), 'full');
  const refined = refinePlan(plan, { chunkCases: 1 }, ['python'], () => ({ status: 1, stdout: '', stderr: 'discovery failed' }));
  assert.deepEqual(refined.selected.map(check => check.id), plan.selected.map(check => check.id));
});

test('a measured plan splits by cost, packs longest-first, and sizes its own allowance', t => {
  const plan = buildPlan(fixture(t), 'full');
  const cases = Array.from({ length: 8 }, (_value, index) => `test_slow.SlowTests.test_case_${index}`);
  // 8 cases observed at 60s each: by count they would ride three to an invocation.
  const history = { 'ticket-autopilot/tests/test_slow.py': { duration_ms: 480_000, units: 8 } };
  const refined = refinePlan(plan, { chunkCases: 3, chunkSeconds: 120, history }, ['python'], (_command, args) => {
    if (args.includes('--list')) return { status: 0, stdout: JSON.stringify({ scenario_ids: ['a', 'b'] }) };
    return { status: 0, stdout: args.at(-1) === 'test_slow.py' ? cases.join('\n') : 'test_one.OneTests.test_only\n' };
  });
  const chunks = refined.selected.filter(check => baseId(check.id) === 'ticket-autopilot/tests/test_slow.py');
  assert.equal(refined.scheduling, 'measured');
  assert.equal(chunks.length, 4, 'two 60s cases fill a 120s target, not three');
  assert.deepEqual(chunks.flatMap(check => check.args.filter(arg => arg.startsWith('test_slow.'))), cases);
  assert.ok(chunks.every(check => check.estimated_ms === 120_000));
  assert.deepEqual(chunks[0].unit_ids, cases.slice(0, 2), 'a chunk names the units it runs');
  // Four times a 120s estimate, so a loaded machine is not killed at its own average.
  assert.equal(checkTimeoutMs(chunks[0], 1800), 480_000);
  assert.equal(checkTimeoutMs({ id: 'unpriced' }, 1800), 1_800_000, 'an unpriced check keeps the flat allowance');
  assert.equal(checkTimeoutMs({ estimated_ms: 1000 }, 1800), 300_000, 'a tiny estimate still gets the floor');
});

test('one heavy unit among trivial ones is priced by its own cost, not by the average', () => {
  // Thirty-one scenarios at ~1s and one at 277s: the average (~10s) would give the heavy
  // one a 40s allowance and kill it. This is the exact shape that timed out.
  const scenarios = Array.from({ length: 32 }, (_value, index) => `scenario-${index}`);
  const unit_ms = Object.fromEntries(scenarios.map(id => [id, 1000]));
  unit_ms['scenario-7'] = 277_000;
  const suite = { duration_ms: 31_000 + 277_000, units: 32, unit_ms };
  const groups = groupByCost(scenarios, suite, 120_000);
  const heavy = groups.find(group => group.includes('scenario-7'));
  assert.deepEqual(heavy, ['scenario-7'], 'the heavy scenario runs alone');
  assert.equal(groups.flat().length, 32, 'no scenario is lost');
  assert.ok(groups.length < 32, 'trivial scenarios still share an invocation');
  const check = { id: 'autopilot-forward-matrix [3/9]', units: 1, unit_ids: ['scenario-7'] };
  assert.equal(estimateMs(check, { 'autopilot-forward-matrix': suite }), 277_000);
  assert.equal(checkTimeoutMs({ ...check, estimated_ms: 277_000 }, 1800), 1_108_000);
  // A unit never measured alone falls back to the suite average.
  assert.equal(estimateMs({ id: 'autopilot-forward-matrix', units: 1, unit_ids: ['unseen'] },
    { 'autopilot-forward-matrix': suite }), Math.round(308_000 / 32));
});

test('longest-first packing balances shards that round-robin would leave lopsided', () => {
  const checks = [
    { id: 'huge', estimated_ms: 900_000 }, { id: 'small-a', estimated_ms: 1000 },
    { id: 'big', estimated_ms: 800_000 }, { id: 'small-b', estimated_ms: 1000 },
  ];
  const shards = [1, 2].map(index => selectShard(checks, index, 2));
  assert.deepEqual(shards.flat().map(check => check.id).sort(), ['big', 'huge', 'small-a', 'small-b']);
  const load = shard => shard.reduce((total, check) => total + check.estimated_ms, 0);
  // Round-robin by position put huge and big in the same shard; cost-aware packing cannot.
  assert.ok(Math.abs(load(shards[0]) - load(shards[1])) < 200_000, 'shard loads stay within one small check');
  assert.ok(!shards.some(shard => shard.length === 4));
});

test('an absent, corrupt, or unit-less history degrades to the unmeasured profile', t => {
  const plan = buildPlan(fixture(t), 'full');
  const listing = (_command, args) => ({ status: 0, stdout: args.includes('--list')
    ? JSON.stringify({ scenario_ids: ['a', 'b'] })
    : Array.from({ length: 7 }, (_value, index) => `test_slow.SlowTests.test_case_${index}`).join('\n') });
  for (const history of [null, readHistory(join(tmpdir(), 'absent-history-file.json')),
    readHistory('ignored', () => '{not json'),
    readHistory('ignored', () => JSON.stringify({ schema: 1, suites: { 'a.py': { duration_ms: 10, units: 0 } } })),
    readHistory('ignored', () => JSON.stringify({ schema: 2, suites: { 'a.py': { duration_ms: 10, units: 2 } } }))]) {
    assert.equal(history, null);
    const refined = refinePlan(plan, { chunkCases: 3, history }, ['python'], listing);
    assert.equal(refined.scheduling, 'unmeasured');
    const chunks = refined.selected.filter(check => baseId(check.id) === 'ticket-autopilot/tests/test_slow.py');
    assert.equal(chunks.length, 3, 'seven cases in threes, exactly as before');
    assert.ok(chunks.every(check => check.estimated_ms === undefined));
  }
  // A stale history naming suites that no longer exist prices nothing and cannot fail a run.
  const stale = { 'ticket-autopilot/tests/test_deleted.py': { duration_ms: 500, units: 5 } };
  assert.equal(refinePlan(plan, { chunkCases: 3, history: stale }, ['python'], listing).scheduling, 'unmeasured');
  assert.equal(estimateMs({ id: 'ticket-autopilot/tests/test_slow.py [1/3]', units: 3 }, stale), null);
});

test('history folds observed cost per suite and per lone unit, and a kill becomes a lower bound', () => {
  const folded = foldHistory([
    { id: 'suite.py [1/3]', status: 'succeeded', duration_ms: 1000, units: 2, unit_ids: ['a', 'b'] },
    { id: 'suite.py [2/3]', status: 'failed', duration_ms: 3000, units: 4, unit_ids: ['c', 'd', 'e', 'f'] },
    { id: 'suite.py [3/3]', status: 'succeeded', duration_ms: 90_000, units: 1, unit_ids: ['heavy'] },
    { id: 'killed.py [1/2]', status: 'errored', duration_ms: 365_900, timeout_ms: 366_000, units: 1, unit_ids: ['slow'] },
    { id: 'killed.py [2/2]', status: 'succeeded', duration_ms: 500, units: 1, unit_ids: ['quick'] },
    { id: 'gone.py', status: 'errored', duration_ms: 1_800_000, timeout_ms: 1_800_000, units: 9 },
    { id: 'unpriced.py', status: 'succeeded', duration_ms: 50 },
  ], { 'old.py': { duration_ms: 7, units: 1, unit_ms: { x: 7 } } });
  assert.equal(folded.suites['suite.py'].duration_ms, 94_000, 'chunks of one suite add up');
  assert.equal(folded.suites['suite.py'].units, 7);
  assert.deepEqual(folded.suites['suite.py'].unit_ms, { heavy: 90_000 }, 'only a unit that ran alone gets its own price');
  assert.equal(folded.suites['killed.py'].unit_ms.slow, 366_000, 'a killed unit is priced at least at the ceiling that killed it');
  assert.equal(folded.suites['killed.py'].duration_ms, 500, 'the kill does not pollute the suite average');
  assert.ok(!('gone.py' in folded.suites), 'a killed multi-unit chunk prices nothing');
  assert.ok(!('unpriced.py' in folded.suites));
  assert.deepEqual(folded.suites['old.py'], { duration_ms: 7, units: 1, unit_ms: { x: 7 } }, 'unseen suites keep their prior cost');
  const firstRunKill = foldHistory([
    { id: 'solo.py', status: 'errored', duration_ms: 299_900, timeout_ms: 300_000, units: 1, unit_ids: ['only'] },
  ], null);
  assert.deepEqual(firstRunKill.suites['solo.py'], {
    duration_ms: 300_000, units: 1, unit_ms: { only: 300_000 },
  }, 'a first-ever lone timeout remains a usable lower bound instead of being discarded');
  assert.equal(estimateMs({ id: 'suite.py [1/9]', units: 3 }, folded.suites), Math.round(94_000 / 7 * 3));
  assert.equal(estimateMs({ id: 'killed.py [1/9]', units: 1, unit_ids: ['slow'] }, folded.suites), 366_000,
    'the next plan gives the killed unit at least its former ceiling');
  const reread = readHistory('x', () => JSON.stringify(folded));
  assert.deepEqual(reread['killed.py'].unit_ms, { slow: 366_000, quick: 500 }, 'unit prices survive a round trip');
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
  assert.deepEqual(full.omitted.map(c => c.id), ['autopilot-forward-matrix']);
  const quickWholeSuites = quick.selected.filter(c => c.id !== QUICK_CLI_CHECK);
  assert.equal(full.selected.length,
    quickWholeSuites.length + quick.omitted.filter(c => c.id !== 'autopilot-forward-matrix').length);
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
  assert.equal(report.counts.not_run, plan.omitted.length);
  assert.equal(report.counts.succeeded, plan.selected.length - 3);
});

test('the forward matrix is release-only and never runs inside a profile', t => {
  for (const mode of ['quick', 'full']) {
    const plan = buildPlan(fixture(t), mode);
    assert.ok(!plan.selected.some(check => check.id === 'autopilot-forward-matrix'),
      mode + ' must not re-run the forward matrix');
    const omitted = plan.omitted.find(check => check.id === 'autopilot-forward-matrix');
    assert.ok(omitted, mode + ' must still declare the matrix as omitted');
    assert.match(omitted.omitted_reason, /release/i);
    assert.equal(omitted.format, 'forward');
  }
  const plan = buildPlan(fixture(t), 'quick');
  const report = runPlan(plan, { logDirectory: join(plan.root, 'logs') }, (command, args) => prerequisites(command, args) ?? success(args));
  const record = report.records.find(entry => entry.id === 'autopilot-forward-matrix');
  assert.equal(record.status, 'not-run');
  assert.match(record.reason, /release/i);
});

test('incomplete or contradictory forward reports cannot produce a full-profile pass', t => {
  const plan = buildPlan(fixture(t), 'full');
  plan.selected.push(forwardReleaseCheck());
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
  for (const check of plan.selected.filter(check => check.family === 'python' && check.id !== QUICK_CLI_CHECK)) {
    writeFileSync(join(root, check.id), "import unittest\nclass NativeCheck(unittest.TestCase):\n    def test_unicode(self):\n        self.assertEqual('à β', 'à β')\n", 'utf8');
  }
  const cliMethods = QUICK_CLI_CASES.map(id => `    def ${id.split('.').at(-1)}(self):\n        self.assertTrue(True)\n`).join('');
  writeFileSync(join(root, 'ticket-autopilot/tests/test_cli.py'), `import unittest\nclass CliTests(unittest.TestCase):\n${cliMethods}`, 'utf8');
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
