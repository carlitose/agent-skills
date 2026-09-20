import assert from 'node:assert/strict';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { aggregateReports, createManifest, validateManifest } from './ci-profile.mjs';
import { selectShard } from './test-local.mjs';

const identity = { commit: 'a'.repeat(40), tree: 'b'.repeat(40) };
const plan = {
  root: '/fixture', mode: 'full', excluded_scopes: [],
  selected: Array.from({ length: 7 }, (_, i) => ({
    id: `check-${i}`, family: 'python', units: 1, unit_ids: [`case-${i}`],
  })),
  omitted: [{ id: 'intentional-omission', family: 'python', omitted_reason: 'existing profile contract' }],
};

function fixture() {
  const manifest = createManifest(structuredClone(plan), identity, 3);
  const reports = Array.from({ length: 3 }, (_, i) => ({
    schema: 1, mode: plan.mode, root: plan.root, exit_code: 0, diagnostic: null,
    ci: { identity, shard: i + 1, shards: 3 },
    records: selectShard(manifest.plan.selected, i + 1, 3).map(check => ({ ...check, status: 'succeeded' })),
  }));
  return { manifest, reports };
}

test('aggregate covers the complete selected plan exactly once and retains omissions', () => {
  const { manifest, reports } = fixture();
  reports[0].records[0].status = 'skipped'; // Existing platform-skip semantics remain supported.
  const result = aggregateReports(manifest, reports, identity);
  assert.equal(result.exit_code, 0);
  assert.equal(result.counts.succeeded, 6);
  assert.equal(result.counts.skipped, 1);
  assert.equal(result.counts.not_run, 1);
  assert.equal(result.records.at(-1).reason, 'existing profile contract');
});

test('missing, duplicate and foreign shard reports fail closed', () => {
  for (const mutate of [
    r => r.pop(), r => { r[1] = r[0]; }, r => { r[0].ci.shard = 9; },
    r => { r[0].ci.shards = 4; }, r => { r[0].ci.identity = { ...identity, tree: 'c'.repeat(40) }; },
    r => { r[0].root = '/other'; }, r => { r[0].mode = 'quick'; },
    r => { r[0].schema = 9; },
  ]) {
    const { manifest, reports } = fixture();
    mutate(reports);
    assert.throws(() => aggregateReports(manifest, reports, identity));
  }
});

test('failed, interrupted and partial outcomes cannot produce an aggregate pass', () => {
  for (const mutate of [
    r => { r[0].exit_code = 1; }, r => { r[0].diagnostic = 'canceled'; },
    r => { r[0].records[0].status = 'failed'; }, r => { r[0].records[0].status = 'errored'; },
    r => { r[0].records[0].status = 'not-run'; }, r => { delete r[0].records; },
  ]) {
    const { manifest, reports } = fixture();
    mutate(reports);
    assert.throws(() => aggregateReports(manifest, reports, identity));
  }
});

test('missing, duplicated, extra and altered check/unit coverage is rejected', () => {
  for (const mutate of [
    r => r[0].records.pop(), r => r[0].records.push(r[0].records[0]),
    r => { r[0].records[0].id = 'foreign-check'; },
    r => { r[0].records[0].unit_ids = []; }, r => { r[0].records[0].units = 0; },
    r => { r[0].records[0].family = 'node'; },
  ]) {
    const { manifest, reports } = fixture();
    mutate(reports);
    assert.throws(() => aggregateReports(manifest, reports, identity));
  }
});

test('manifest rejects source drift, malformed selectors and duplicate planned checks', () => {
  const { manifest } = fixture();
  assert.throws(() => validateManifest(manifest, { ...identity, commit: 'c'.repeat(40) }));
  for (const shards of [0, 9, 1.5]) assert.throws(() => createManifest(plan, identity, shards));
  assert.throws(() => createManifest({ ...plan, mode: 'other' }, identity, 3));
  assert.throws(() => createManifest({ ...plan, selected: [plan.selected[0], plan.selected[0]] }, identity, 3));
});

test('CLI prepares, executes and aggregates a real disposable fixture; dirty source fails', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'ci-profile-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const directory of ['scripts', 'extensions', 'ticket-autopilot/tests', 'llm-wiki/tests', 'to-tickets/tests', 'verification-audit/tests']) {
    mkdirSync(join(root, directory), { recursive: true });
  }
  for (const name of ['ci-profile.mjs', 'test-local.mjs']) {
    copyFileSync(new URL(name, import.meta.url), join(root, 'scripts', name));
  }
  writeFileSync(join(root, 'scripts/fixture.test.mjs'), "import test from 'node:test';\ntest('fixture', () => {});\n");
  for (const path of [
    'ticket-autopilot/tests/test_ticket_contract.py', 'ticket-autopilot/tests/test_leaf_protocol.py',
    'ticket-autopilot/tests/test_history_codec.py', 'ticket-autopilot/tests/test_kernel.py',
    'llm-wiki/tests/test_project_binding.py', 'verification-audit/tests/test_verification_contract.py',
    'to-tickets/tests/test_fixture.py',
  ]) {
    writeFileSync(join(root, path), 'import unittest\nclass Fixture(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(2 + 2, 4)\n');
  }
  const invoke = (command, args) => spawnSync(command, args, { cwd: root, encoding: 'utf8', timeout: 30_000 });
  for (const args of [['init', '-q'], ['add', '.'], ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture']]) {
    const result = invoke('git', args);
    assert.equal(result.status, 0, result.stderr);
  }
  const cli = (...args) => invoke(process.execPath, ['scripts/ci-profile.mjs', ...args]);
  const directory = join(root, 'artifacts');
  let result = cli('prepare', 'full', directory);
  assert.equal(result.status, 0, result.stderr);
  const manifest = join(directory, 'manifest.json');
  for (let i = 1; i <= 6; i++) {
    result = cli('run', manifest, String(i), join(directory, `shard-${i}.json`), '--timeout-seconds', '10');
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const report = JSON.parse(readFileSync(join(directory, `shard-${i}.json`), 'utf8'));
    assert.ok(report.records.every(record => record.timeout_ms <= 10_000));
  }
  const aggregate = join(directory, 'aggregate.json');
  result = cli('aggregate', manifest, directory, aggregate);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(readFileSync(aggregate, 'utf8')).counts.succeeded, 8);
  writeFileSync(join(root, 'scripts/fixture.test.mjs'), '// tracked source changed\n');
  result = cli('aggregate', manifest, directory, aggregate);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /CI checkout has tracked changes/);
});

test('required CI uses one refined plan, six disjoint hosts and an always-run aggregate', () => {
  const workflow = readFileSync(new URL('../.github/workflows/local-profile.yml', import.meta.url), 'utf8');
  assert.match(workflow, /shard: \[1, 2, 3, 4, 5, 6\]/);
  assert.match(workflow, /fail-fast: false/);
  assert.match(workflow, /needs: \[prepare, checks\]\s+if: always\(\)/);
  assert.match(workflow, /name: local-profile/);
  assert.match(workflow, /needs\.prepare\.result/);
  assert.match(workflow, /needs\.checks\.result/);
  assert.match(workflow, /ci-profile\.mjs aggregate/);
  const timeouts = [...workflow.matchAll(/timeout-minutes: (\d+)/g)].map(m => Number(m[1]));
  assert.equal(timeouts.length, 3);
  assert.ok(timeouts.every(value => value <= 15));
});
