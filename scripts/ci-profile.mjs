import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { buildPlan, mergeReports, parseArguments, refinePlan, resolveToolchain, runPlan, selectShard } from './test-local.mjs';

// CI composition only: the local harness still owns selection, execution and classification.
function identity(root) {
  const result = spawnSync('git', ['rev-parse', 'HEAD', 'HEAD^{tree}'], {
    cwd: root, encoding: 'utf8', shell: false, timeout: 10_000,
  });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  const [commit, tree] = result.stdout.trim().split(/\r?\n/);
  const clean = spawnSync('git', ['diff', '--quiet', 'HEAD', '--'], { cwd: root, timeout: 10_000 });
  assert.equal(clean.status, 0, 'CI checkout has tracked changes');
  return { commit, tree };
}

function writeJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  const temporary = `${path}.tmp`;
  writeFileSync(temporary, JSON.stringify(value, null, 2) + '\n');
  renameSync(temporary, path);
}

const readJson = path => JSON.parse(readFileSync(path, 'utf8'));

export function validateManifest(manifest, current) {
  assert.equal(manifest.schema, 1, 'Unknown CI manifest schema');
  assert.deepEqual(manifest.identity, current, 'CI source identity drift');
  assert.match(current.commit, /^[0-9a-f]{40}$/);
  assert.match(current.tree, /^[0-9a-f]{40}$/);
  assert.ok(Number.isInteger(manifest.shards) && manifest.shards >= 1 && manifest.shards <= 8);
  const { plan } = manifest;
  assert.ok(['quick', 'full'].includes(plan.mode));
  assert.equal(typeof plan.root, 'string');
  assert.ok(Array.isArray(plan.selected) && plan.selected.length > 0);
  assert.ok(Array.isArray(plan.omitted));
  const ids = plan.selected.map(check => {
    assert.ok(typeof check.id === 'string' && check.id.length > 0);
    return check.id;
  });
  assert.equal(new Set(ids).size, ids.length, 'Duplicate planned check');
  return manifest;
}

export function createManifest(plan, source, shards = 6) {
  return validateManifest({ schema: 1, identity: source, shards, plan }, source);
}

export function aggregateReports(manifest, reports, current) {
  validateManifest(manifest, current);
  assert.equal(reports.length, manifest.shards, 'Missing or extra shard report');
  const seen = new Set();
  for (const report of reports) {
    const index = report.ci?.shard;
    assert.ok(Number.isInteger(index) && index >= 1 && index <= manifest.shards);
    assert.ok(!seen.has(index), 'Duplicate shard report');
    seen.add(index);
    assert.equal(report.schema, 1);
    assert.deepEqual(report.ci.identity, current, 'Foreign shard source');
    assert.equal(report.ci.shards, manifest.shards);
    assert.equal(report.mode, manifest.plan.mode);
    assert.equal(report.root, manifest.plan.root);
    assert.equal(report.exit_code, 0, 'Unsuccessful shard');
    assert.equal(report.diagnostic, null, 'Interrupted or invalid shard');
    const expected = selectShard(manifest.plan.selected, index, manifest.shards);
    assert.ok(Array.isArray(report.records), 'Partial report');
    assert.deepEqual(report.records.map(record => record.id), expected.map(check => check.id), 'Incomplete or duplicate check coverage');
    for (const [position, record] of report.records.entries()) {
      const check = expected[position];
      assert.equal(record.family, check.family);
      assert.equal(record.units, check.units);
      assert.deepEqual(record.unit_ids ?? [], check.unit_ids ?? [], 'Altered unit coverage');
      assert.ok(['succeeded', 'skipped'].includes(record.status), 'Unsuccessful selected check');
    }
  }
  // Preserve the harness's intentional omissions, not omissions introduced by CI partitioning.
  const omitted = manifest.plan.omitted.map(check => ({
    id: check.id, family: check.family, status: 'not-run',
    reason: check.omitted_reason ?? 'Omitted by quick profile',
  }));
  return { ...mergeReports(reports, omitted), ci: { identity: current, shards: manifest.shards, complete: true } };
}

function main([command, ...args]) {
  const root = process.cwd();
  const source = identity(root);
  if (command === 'prepare') {
    const [mode, directory] = args;
    const options = parseArguments([mode, '--timeout-seconds', '900']);
    const env = { ...process.env };
    delete env.NODE_TEST_CONTEXT;
    const spawnOptions = { cwd: root, env, shell: false, encoding: 'utf8', timeout: 30_000, maxBuffer: 16 * 1024 * 1024 };
    const toolchain = resolveToolchain(options, spawnOptions);
    assert.ok(toolchain.python, toolchain.diagnostic);
    const plan = refinePlan(buildPlan(root, mode), options, toolchain.python, spawnSync, spawnOptions);
    assert.deepEqual(identity(root), source, 'Source changed while preparing plan');
    const manifest = createManifest(plan, source);
    writeJson(join(directory, 'manifest.json'), manifest);
    console.log(`${mode}: one refined plan, ${plan.selected.length} selected, ${plan.omitted.length} intentional omissions, ${manifest.shards} shards`);
    return;
  }
  if (command === 'run') {
    const [manifestPath, rawIndex, reportPath, ...flags] = args;
    const manifest = validateManifest(readJson(manifestPath), source);
    assert.equal(manifest.plan.root, root, 'Checkout path differs from prepared plan');
    const index = Number(rawIndex);
    assert.ok(Number.isInteger(index) && index >= 1 && index <= manifest.shards);
    const options = parseArguments(flags);
    assert.ok(options.timeoutSeconds <= 900, 'CI per-check allowance exceeds 900 seconds');
    const selected = selectShard(manifest.plan.selected, index, manifest.shards);
    const ci = { identity: source, shard: index, shards: manifest.shards };
    const completed = [];
    const report = runPlan({ ...manifest.plan, selected, omitted: [] }, {
      ...options,
      onCheck(record) {
        completed.push(record);
        writeJson(`${reportPath}.partial.json`, { ci, complete: false, expected: selected.length, completed });
        console.log(`${record.status}: ${record.id} (${record.duration_ms} ms)`);
      },
    });
    assert.deepEqual(identity(root), source, 'Source changed during shard execution');
    writeJson(reportPath, { ...report, ci });
    process.exitCode = report.exit_code;
    return;
  }
  if (command === 'aggregate') {
    const [manifestPath, directory, destination] = args;
    const manifest = validateManifest(readJson(manifestPath), source);
    const reports = Array.from({ length: manifest.shards }, (_, i) => readJson(join(directory, `shard-${i + 1}.json`)));
    const result = aggregateReports(manifest, reports, source);
    writeJson(destination, result);
    console.log(JSON.stringify({ counts: result.counts, ci: result.ci, exit_code: result.exit_code }));
    return;
  }
  throw new Error('Usage: ci-profile.mjs prepare MODE DIR | run MANIFEST INDEX REPORT --timeout-seconds 900 | aggregate MANIFEST REPORTS_DIR DEST');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
