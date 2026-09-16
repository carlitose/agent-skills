#!/usr/bin/env node
/** Local Node/unittest orchestration; counts are check invocations, not subtests. */
import { spawn, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { availableParallelism, tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PYTHON_ROOTS = ['ticket-autopilot', 'llm-wiki', 'to-tickets', 'verification-audit'];
const QUICK = new Set([
  'ticket-autopilot/tests/test_ticket_contract.py',
  'ticket-autopilot/tests/test_leaf_protocol.py',
  'ticket-autopilot/tests/test_history_codec.py',
  'llm-wiki/tests/test_project_binding.py',
  'verification-audit/tests/test_verification_contract.py',
]);
const FORWARD_SCRIPT = 'ticket-autopilot/scripts/forward_test.py';
// Wall-clock-bounded suites assert sub-second deadlines, so a loaded machine fails them for
// scheduling reasons rather than for a defect. They stay unchunked and run without neighbours.
const SERIAL = new Set([
  'ticket-autopilot/tests/test_command_bounds.py',
  'ticket-autopilot/tests/test_command_capture_failures.py',
  'ticket-autopilot/tests/test_posix_command_bounds.py',
  'ticket-autopilot/tests/test_provider_command_bounds.py',
]);
// Discovery reports the exact case ids unittest would run; chunking selects from that list
// instead of guessing method names from the source text.
const LIST_CASES = 'import sys, unittest\n'
  + 'def ids(suite):\n'
  + '    for case in suite:\n'
  + '        if isinstance(case, unittest.TestSuite): yield from ids(case)\n'
  + '        else: yield case.id()\n'
  + 'start = sys.argv[1]\n'
  + 'print("\\n".join(sorted(set(ids(unittest.TestLoader().discover(start, pattern=sys.argv[2], top_level_dir=start))))))\n';
const USAGE = 'Usage: node scripts/test-local.mjs [quick|full] [--python PATH] [--timeout-seconds N]'
  + ' [--jobs N] [--chunk-cases N] [--report PATH] [--list]';

export function defaultJobs() {
  return Math.max(1, Math.min(8, (availableParallelism?.() ?? 1) - 1));
}

export function parseArguments(argv) {
  const result = { mode: 'quick', timeoutSeconds: 1800, jobs: defaultJobs(), chunkCases: 3 };
  let selected = false;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === 'quick' || arg === 'full') {
      if (selected) throw new Error('Choose one selector. ' + USAGE);
      result.mode = arg;
      selected = true;
    } else if (arg === '--list' || arg === '--help') {
      result[arg.slice(2)] = true;
    } else if (['--python', '--timeout-seconds', '--report', '--jobs', '--chunk-cases', '--plan', '--shard'].includes(arg)) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(arg + ' requires a value. ' + USAGE);
      if (arg === '--timeout-seconds') {
        if (!/^\d+$/.test(value) || Number(value) < 1 || Number(value) > 3600) throw new Error('timeout must be 1..3600 seconds');
        result.timeoutSeconds = Number(value);
      } else if (arg === '--jobs' || arg === '--chunk-cases') {
        if (!/^\d+$/.test(value) || Number(value) < 1 || Number(value) > 64) throw new Error(arg + ' must be 1..64');
        result[arg === '--jobs' ? 'jobs' : 'chunkCases'] = Number(value);
      } else if (arg === '--shard') {
        const match = /^(\d+)\/(\d+)$/.exec(value);
        if (!match || Number(match[1]) < 1 || Number(match[1]) > Number(match[2])) throw new Error('--shard must be INDEX/TOTAL with 1 <= INDEX <= TOTAL');
        result.shard = { index: Number(match[1]), total: Number(match[2]) };
      } else result[arg.slice(2)] = value;
    } else throw new Error('Unknown argument/selector: ' + arg + '. ' + USAGE);
  }
  return result;
}

export function buildPlan(root, mode) {
  if (!['quick', 'full'].includes(mode)) throw new Error('Invalid selector: ' + mode);
  const nodeFiles = ['extensions', 'scripts'].flatMap(directory => readdirSync(join(root, directory), { withFileTypes: true })
    .filter(entry => entry.isFile() && /\.test\.(ts|mjs)$/.test(entry.name))
    .map(entry => directory + '/' + entry.name)).sort();
  if (nodeFiles.length === 0) throw new Error('No Node test files found');
  const checks = [{ id: 'node-tests', family: 'node', args: ['--experimental-strip-types', '--test', '--test-reporter=tap', ...nodeFiles] }];
  for (const directory of PYTHON_ROOTS) {
    const start = directory + '/tests';
    const files = readdirSync(join(root, start), { withFileTypes: true }).filter(entry => entry.isFile() && /^test_.*\.py$/.test(entry.name)).map(entry => entry.name).sort();
    if (!files.length) throw new Error('No Python suites found in ' + start);
    for (const file of files) checks.push({ id: start + '/' + file, family: 'python', args: ['-B', '-m', 'unittest', 'discover', '-s', start, '-p', file, '-v'] });
  }
  for (const required of QUICK) if (!checks.some(check => check.id === required)) throw new Error('Required quick suite is missing: ' + required);
  checks.push({ id: 'autopilot-forward-matrix', family: 'python', format: 'forward', args: ['-B', FORWARD_SCRIPT] });
  const included = check => mode === 'full' || check.family === 'node' || QUICK.has(check.id);
  return {
    root: resolve(root), mode,
    selected: checks.filter(included), omitted: checks.filter(check => !included(check)),
    excluded_scopes: ['Throwaway docs/prototypes experiments', 'Hosted CI and live-provider/network verification'],
  };
}

export function chunk(items, size) {
  const groups = [];
  for (let index = 0; index < items.length; index += size) groups.push(items.slice(index, index + size));
  return groups;
}

/** Split long-running checks so one invocation stays inside a single timeout allowance. */
export function refinePlan(plan, options, python, execute = spawnSync, spawnOptions = {}) {
  const size = options.chunkCases ?? 6;
  const list = args => {
    const result = execute(python[0], [...python.slice(1), ...args], { ...spawnOptions, cwd: plan.root });
    if (result.error || result.status !== 0) return null;
    return (result.stdout ?? '').split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  };
  const selected = plan.selected.flatMap(check => {
    if (check.family !== 'python' || SERIAL.has(check.id)) return [check];
    if (check.format === 'forward') {
      const listed = list(['-B', FORWARD_SCRIPT, '--list']);
      let scenarios = [];
      try { scenarios = JSON.parse((listed ?? []).join('\n')).scenario_ids ?? []; } catch { scenarios = []; }
      // One forward scenario drives several heavy integration cases, so it chunks tighter.
      const forwardSize = Math.max(1, Math.ceil(size / 2));
      if (scenarios.length <= forwardSize) return [check];
      return chunk(scenarios, forwardSize).map((group, index, groups) => ({
        ...check,
        id: `${check.id} [${index + 1}/${groups.length}]`,
        args: ['-B', FORWARD_SCRIPT, ...group.flatMap(scenario => ['--scenario', scenario])],
      }));
    }
    const start = check.args[check.args.indexOf('-s') + 1];
    const pattern = check.args[check.args.indexOf('-p') + 1];
    if (!start || !pattern) return [check];
    const cases = list(['-B', '-c', LIST_CASES, start, pattern]);
    if (!cases || cases.length <= size) return [check];
    return chunk(cases, size).map((group, index, groups) => ({
      id: `${check.id} [${index + 1}/${groups.length}]`,
      family: 'python',
      args: ['-B', '-m', 'unittest', '-v', ...group],
      env: { PYTHONPATH: resolve(plan.root, start) },
    }));
  });
  return { ...plan, selected, chunked: selected.length !== plan.selected.length };
}

export function selectShard(checks, index, total) {
  return checks.filter((_check, position) => position % total === index - 1);
}

export function partitionSerial(checks) {
  return {
    parallel: checks.filter(check => !SERIAL.has(check.id)),
    serial: checks.filter(check => SERIAL.has(check.id)),
  };
}

export function mergeReports(reports, extra = []) {
  const records = [...reports.flatMap(report => report.records ?? []), ...extra];
  const diagnostic = reports.map(report => report.diagnostic).filter(Boolean).join('; ') || null;
  return {
    ...(reports[0] ?? {}), records, diagnostic, counts: summarize(records),
    log_directory: reports.map(report => report.log_directory).filter(Boolean).join(', '),
    exit_code: diagnostic || records.some(record => ['failed', 'errored'].includes(record.status)) ? 1 : 0,
  };
}

export function summarize(records) {
  const counts = { succeeded: 0, failed: 0, errored: 0, skipped: 0, not_run: 0 };
  for (const record of records) counts[record.status.replace('-', '_')] += 1;
  return counts;
}

function classify(result, format) {
  const output = (result.stdout ?? '') + '\n' + (result.stderr ?? '');
  if (result.error || result.signal || result.status === null) return {
    status: 'errored', diagnostic: result.error?.message ?? ('Process terminated: ' + result.signal),
  };
  if (result.status !== 0) return {
    status: /FAILED \([^)]*errors=[1-9]/.test(output) ? 'errored' : 'failed',
    diagnostic: 'Runner exited ' + result.status + '; inspect the retained stdout/stderr logs.',
  };
  if (format === 'forward') {
    try {
      const report = JSON.parse(result.stdout);
      const successfulGroup = group => group && typeof group === 'object' && !Array.isArray(group)
        && Object.keys(group).length > 0 && Object.values(group).every(value => value?.result === 'pass');
      if (report.schema !== 1 || report.result !== 'pass' || !successfulGroup(report.scenarios) || !successfulGroup(report.command_results)) {
        throw new Error('missing or contradictory scenario/command results');
      }
      return { status: 'succeeded' };
    } catch (error) { return { status: 'errored', diagnostic: 'Invalid forward report: ' + error.message }; }
  }
  const runs = [...output.matchAll(/(?:Ran (\d+) tests?|^# tests (\d+))/gm)];
  if (!runs.length || Number(runs.at(-1)[1] ?? runs.at(-1)[2]) === 0) return { status: 'errored', diagnostic: 'Runner did not report any executed tests.' };
  const ran = Number(runs.at(-1)[1] ?? runs.at(-1)[2]);
  const skipped = [...output.matchAll(/(?:OK \([^)]*skipped=(\d+)|^# skipped (\d+))/gm)];
  const skipCount = skipped.length ? Number(skipped.at(-1)[1] ?? skipped.at(-1)[2]) : 0;
  return { status: skipCount === ran ? 'skipped' : 'succeeded', framework_counts: { tests_run: ran, skipped: skipCount } };
}

export function baseSpawnOptions(root) {
  const environment = { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONDONTWRITEBYTECODE: '1' };
  // An independently launched test CLI must not inherit its caller's node:test
  // child-v8 transport; otherwise --test emits IPC bytes instead of TAP.
  delete environment.NODE_TEST_CONTEXT;
  return { cwd: root, env: environment, shell: false, encoding: 'utf8', windowsHide: true, timeout: 30_000, maxBuffer: 16 * 1024 * 1024, killSignal: 'SIGKILL' };
}

export function resolveToolchain(options, spawnOptions, execute = spawnSync) {
  const [major, minor] = process.versions.node.split('.').map(Number);
  if (major < 22 || (major === 22 && minor < 6)) return { diagnostic: 'Node >=22.6 is required by the existing native TypeScript test command.' };
  const git = execute('git', ['--version'], spawnOptions);
  if (git.error || git.status !== 0) return { diagnostic: 'Git is required. Install Git or fix PATH; no test checks were run.' };
  const explicitPython = options.python ?? process.env.PYTHON;
  const candidates = explicitPython ? [[explicitPython]] : [['python3'], ['python'], ...(process.platform === 'win32' ? [['py', '-3']] : [])];
  for (const candidate of candidates) {
    const probe = execute(candidate[0], [...candidate.slice(1), '-c', 'import json,sys; print(json.dumps(list(sys.version_info[:3])))'], spawnOptions);
    try {
      const version = JSON.parse(probe.stdout);
      if (!probe.error && probe.status === 0 && Array.isArray(version) && version[0] === 3 && version[1] >= 12) {
        return { python: candidate, pythonVersion: version.join('.'), gitVersion: git.stdout.trim() };
      }
    } catch { /* Try the next auto-discovered interpreter, not an extension-only fallback. */ }
  }
  return { diagnostic: 'Python >=3.12 is required. Select its executable with --python PATH (or PYTHON); Python is never silently omitted.' };
}

export function runPlan(plan, options = {}, execute = spawnSync) {
  const directory = options.logDirectory ?? mkdtempSync(join(tmpdir(), 'agent-skills-tests-'));
  mkdirSync(directory, { recursive: true });
  const spawnOptions = baseSpawnOptions(plan.root);
  const records = [...plan.selected, ...plan.omitted].map(check => ({ id: check.id, family: check.family, status: 'not-run', reason: plan.omitted.includes(check) ? 'Omitted by quick profile' : 'Prerequisites not satisfied' }));
  const report = { schema: 1, mode: plan.mode, platform: process.platform, node_version: process.versions.node, root: plan.root, log_directory: directory, count_unit: 'check invocations, not individual test cases or subtests', excluded_scopes: plan.excluded_scopes, records };
  const finish = diagnostic => ({ ...report, diagnostic, counts: summarize(records), exit_code: diagnostic || records.some(record => ['failed', 'errored'].includes(record.status)) ? 1 : 0 });
  const toolchain = resolveToolchain(options, spawnOptions, execute);
  if (toolchain.diagnostic) return finish(toolchain.diagnostic);
  report.git_version = toolchain.gitVersion;
  report.python_version = toolchain.pythonVersion;
  report.python_command = toolchain.python;
  for (const [index, check] of plan.selected.entries()) {
    const command = check.family === 'node' ? [process.execPath, ...check.args] : [...toolchain.python, ...check.args];
    const started = Date.now();
    let result;
    try {
      result = execute(command[0], command.slice(1), {
        ...spawnOptions, timeout: (options.timeoutSeconds ?? 900) * 1000,
        env: check.env ? { ...spawnOptions.env, ...check.env } : spawnOptions.env,
      });
    } catch (error) { result = { error, status: null }; }
    const log = join(directory, String(index + 1).padStart(3, '0'));
    writeFileSync(log + '.stdout.log', result.stdout ?? '', 'utf8');
    writeFileSync(log + '.stderr.log', result.stderr ?? '', 'utf8');
    Object.assign(records[index], classify(result, check.format), { command, exit_code: result.status ?? null, signal: result.signal ?? null, duration_ms: Date.now() - started, stdout_log: log + '.stdout.log', stderr_log: log + '.stderr.log' });
    delete records[index].reason;
    options.onCheck?.(records[index]);
  }
  return finish(null);
}

function progress(record) {
  const seconds = record.duration_ms === undefined ? '' : ` (${(record.duration_ms / 1000).toFixed(1)}s)`;
  return `${record.status}: ${record.id}${seconds}${record.diagnostic ? ' — ' + record.diagnostic : ''}`;
}

/** Run one refined plan across independent shard processes so a long check never hides progress. */
async function runShards(plan, options, python) {
  const directory = mkdtempSync(join(tmpdir(), 'agent-skills-tests-'));
  const planPath = join(directory, 'plan.json');
  const { parallel, serial } = partitionSerial(plan.selected);
  writeFileSync(planPath, JSON.stringify({ ...plan, selected: parallel }), 'utf8');
  const jobs = Math.max(1, Math.min(options.jobs, parallel.length));
  const environment = { ...process.env };
  delete environment.NODE_TEST_CONTEXT;
  const shards = await Promise.all(Array.from({ length: jobs }, (_value, index) => new Promise(done => {
    const reportPath = join(directory, `shard-${index + 1}.json`);
    const args = [fileURLToPath(import.meta.url), '--plan', planPath, '--shard', `${index + 1}/${jobs}`,
      '--report', reportPath, '--timeout-seconds', String(options.timeoutSeconds),
      // A multi-part launcher such as `py -3` is rediscovered by the shard instead of
      // being flattened into one unusable executable path.
      ...(python?.length === 1 ? ['--python', python[0]] : [])];
    const child = spawn(process.execPath, args, { cwd: plan.root, env: environment, stdio: ['ignore', 'inherit', 'inherit'], windowsHide: true });
    child.on('close', () => {
      try { done(JSON.parse(readFileSync(reportPath, 'utf8'))); }
      catch (error) { done({ records: [], diagnostic: `Shard ${index + 1}/${jobs} produced no report: ${error.message}` }); }
    });
  })));
  const omitted = plan.omitted.map(check => ({ id: check.id, family: check.family, status: 'not-run', reason: 'Omitted by quick profile' }));
  const bounded = serial.length
    ? [runPlan({ ...plan, selected: serial, omitted: [] }, { ...options, onCheck: record => console.log(progress(record)) })]
    : [];
  return mergeReports([...shards, ...bounded], omitted);
}

async function main(argv) {
  try {
    const options = parseArguments(argv);
    if (options.help) { console.log(USAGE); return 0; }
    const spawnOptions = baseSpawnOptions(ROOT);
    if (options.shard) {
      const refined = JSON.parse(readFileSync(options.plan, 'utf8'));
      const shard = { ...refined, selected: selectShard(refined.selected, options.shard.index, options.shard.total), omitted: [] };
      const report = runPlan(shard, { ...options, onCheck: record => console.log(progress(record)) });
      writeFileSync(resolve(options.report), JSON.stringify(report, null, 2) + '\n', 'utf8');
      return report.exit_code;
    }
    const plan = buildPlan(ROOT, options.mode);
    if (options.list) { console.log(JSON.stringify(plan, null, 2)); return 0; }
    const toolchain = options.jobs > 1 ? resolveToolchain(options, spawnOptions) : {};
    if (toolchain.python) console.log(`Listing cases for ${plan.selected.length} discovered suites before scheduling...`);
    const refined = toolchain.python ? refinePlan(plan, options, toolchain.python, spawnSync, spawnOptions) : plan;
    console.log(`${plan.mode}: ${refined.selected.length} selected checks; ${plan.omitted.length} not run by this profile.`);
    console.log('Included:', plan.selected.map(check => check.id).join(', '));
    console.log('Omitted:', plan.omitted.map(check => check.id).join(', ') || 'none within the declared supported test roots');
    if (toolchain.python) console.log(`Running ${Math.min(options.jobs, refined.selected.length)} checks in parallel; per-check timeout ${options.timeoutSeconds}s.`);
    const report = toolchain.python
      ? await runShards(refined, options, toolchain.python)
      : runPlan(plan, { ...options, onCheck: record => console.log(progress(record)) });
    const destination = resolve(options.report ?? join((report.log_directory || tmpdir()).split(', ')[0], 'report.json'));
    mkdirSync(dirname(destination), { recursive: true });
    writeFileSync(destination, JSON.stringify(report, null, 2) + '\n', 'utf8');
    console.log('Check counts:', JSON.stringify(report.counts));
    if (report.diagnostic) console.error(report.diagnostic);
    console.log('Raw framework case/subtest results and platform skips remain in each check log. Report:', destination);
    console.log('Local tests only; not live-provider verification. Timeouts do not prove descendant cleanup or effect-freedom.');
    return report.exit_code;
  } catch (error) { console.error(error.message); return 1; }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) process.exitCode = await main(process.argv.slice(2));
