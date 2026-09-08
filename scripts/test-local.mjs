#!/usr/bin/env node
/** Local Node/unittest orchestration; counts are check invocations, not subtests. */
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
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
const USAGE = 'Usage: node scripts/test-local.mjs [quick|full] [--python PATH] [--timeout-seconds N] [--report PATH] [--list]';

export function parseArguments(argv) {
  const result = { mode: 'quick', timeoutSeconds: 300 };
  let selected = false;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === 'quick' || arg === 'full') {
      if (selected) throw new Error('Choose one selector. ' + USAGE);
      result.mode = arg;
      selected = true;
    } else if (arg === '--list' || arg === '--help') {
      result[arg.slice(2)] = true;
    } else if (['--python', '--timeout-seconds', '--report'].includes(arg)) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(arg + ' requires a value. ' + USAGE);
      if (arg === '--timeout-seconds') {
        if (!/^\d+$/.test(value) || Number(value) < 1 || Number(value) > 3600) throw new Error('timeout must be 1..3600 seconds');
        result.timeoutSeconds = Number(value);
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
  checks.push({ id: 'autopilot-forward-matrix', family: 'python', format: 'forward', args: ['-B', 'ticket-autopilot/scripts/forward_test.py'] });
  const included = check => mode === 'full' || check.family === 'node' || QUICK.has(check.id);
  return {
    root: resolve(root), mode,
    selected: checks.filter(included), omitted: checks.filter(check => !included(check)),
    excluded_scopes: ['Throwaway docs/prototypes experiments', 'Hosted CI and live-provider/network verification'],
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

export function runPlan(plan, options = {}, execute = spawnSync) {
  const directory = options.logDirectory ?? mkdtempSync(join(tmpdir(), 'agent-skills-tests-'));
  mkdirSync(directory, { recursive: true });
  const environment = { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONDONTWRITEBYTECODE: '1' };
  // An independently launched test CLI must not inherit its caller's node:test
  // child-v8 transport; otherwise --test emits IPC bytes instead of TAP.
  delete environment.NODE_TEST_CONTEXT;
  const spawnOptions = { cwd: plan.root, env: environment, shell: false, encoding: 'utf8', windowsHide: true, timeout: 30_000, maxBuffer: 16 * 1024 * 1024, killSignal: 'SIGKILL' };
  const records = [...plan.selected, ...plan.omitted].map(check => ({ id: check.id, family: check.family, status: 'not-run', reason: plan.omitted.includes(check) ? 'Omitted by quick profile' : 'Prerequisites not satisfied' }));
  const report = { schema: 1, mode: plan.mode, platform: process.platform, node_version: process.versions.node, root: plan.root, log_directory: directory, count_unit: 'check invocations, not individual test cases or subtests', excluded_scopes: plan.excluded_scopes, records };
  const finish = diagnostic => ({ ...report, diagnostic, counts: summarize(records), exit_code: diagnostic || records.some(record => ['failed', 'errored'].includes(record.status)) ? 1 : 0 });
  const [major, minor] = process.versions.node.split('.').map(Number);
  if (major < 22 || (major === 22 && minor < 6)) return finish('Node >=22.6 is required by the existing native TypeScript test command.');
  const git = execute('git', ['--version'], spawnOptions);
  if (git.error || git.status !== 0) return finish('Git is required. Install Git or fix PATH; no test checks were run.');
  report.git_version = git.stdout.trim();
  const explicitPython = options.python ?? process.env.PYTHON;
  const candidates = explicitPython ? [[explicitPython]] : [['python3'], ['python'], ...(process.platform === 'win32' ? [['py', '-3']] : [])];
  let python;
  for (const candidate of candidates) {
    const probe = execute(candidate[0], [...candidate.slice(1), '-c', 'import json,sys; print(json.dumps(list(sys.version_info[:3])))'], spawnOptions);
    try {
      const version = JSON.parse(probe.stdout);
      if (!probe.error && probe.status === 0 && Array.isArray(version) && version[0] === 3 && version[1] >= 12) {
        python = candidate;
        report.python_version = version.join('.');
        break;
      }
    } catch { /* Try the next auto-discovered interpreter, not an extension-only fallback. */ }
  }
  if (!python) return finish('Python >=3.12 is required. Select its executable with --python PATH (or PYTHON); Python is never silently omitted.');
  report.python_command = python;
  for (const [index, check] of plan.selected.entries()) {
    const command = check.family === 'node' ? [process.execPath, ...check.args] : [...python, ...check.args];
    let result;
    try {
      result = execute(command[0], command.slice(1), { ...spawnOptions, timeout: (options.timeoutSeconds ?? 300) * 1000 });
    } catch (error) { result = { error, status: null }; }
    const log = join(directory, String(index + 1).padStart(3, '0'));
    writeFileSync(log + '.stdout.log', result.stdout ?? '', 'utf8');
    writeFileSync(log + '.stderr.log', result.stderr ?? '', 'utf8');
    Object.assign(records[index], classify(result, check.format), { command, exit_code: result.status ?? null, signal: result.signal ?? null, stdout_log: log + '.stdout.log', stderr_log: log + '.stderr.log' });
    delete records[index].reason;
    options.onCheck?.(records[index]);
  }
  return finish(null);
}

function main(argv) {
  try {
    const options = parseArguments(argv);
    if (options.help) { console.log(USAGE); return 0; }
    const plan = buildPlan(ROOT, options.mode);
    if (options.list) { console.log(JSON.stringify(plan, null, 2)); return 0; }
    console.log(`${plan.mode}: ${plan.selected.length} selected checks; ${plan.omitted.length} not run by this profile.`);
    console.log('Included:', plan.selected.map(check => check.id).join(', '));
    console.log('Omitted:', plan.omitted.map(check => check.id).join(', ') || 'none within the declared supported test roots');
    const report = runPlan(plan, { ...options, onCheck: record => console.log(`${record.status}: ${record.id}${record.diagnostic ? ' — ' + record.diagnostic : ''}`) });
    const destination = resolve(options.report ?? join(report.log_directory, 'report.json'));
    mkdirSync(dirname(destination), { recursive: true });
    writeFileSync(destination, JSON.stringify(report, null, 2) + '\n', 'utf8');
    console.log('Check counts:', JSON.stringify(report.counts));
    if (report.diagnostic) console.error(report.diagnostic);
    console.log('Raw framework case/subtest results and platform skips remain in each check log. Report:', destination);
    console.log('Local tests only; not live-provider verification. Timeouts do not prove descendant cleanup or effect-freedom.');
    return report.exit_code;
  } catch (error) { console.error(error.message); return 1; }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) process.exitCode = main(process.argv.slice(2));
