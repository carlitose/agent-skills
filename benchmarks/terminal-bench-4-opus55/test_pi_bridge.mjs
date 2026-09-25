import assert from 'node:assert/strict';
import test from 'node:test';
import { createSandboxTool } from './pi_bridge_core.mjs';

test('tool forwards only bounded commands over the sandbox protocol', async () => {
  const frames = [];
  const tool = createSandboxTool(frame => frames.push(frame), async () => ({
    type: 'result', id: String(frames.length), return_code: 0, stdout: 'inside', stderr: '',
  }));
  const result = await tool.execute('tool-id', { command: 'pwd' });
  assert.deepEqual(frames, [{ type: 'exec', id: '1', command: 'pwd', cwd: null, timeout_sec: 60 }]);
  assert.equal(JSON.parse(result.content[0].text).stdout, 'inside');
  assert.equal(result.details.return_code, 0);
});

test('parallel Pi tool calls serialize their requests and matching results', async () => {
  const frames = [];
  const tool = createSandboxTool(frame => frames.push(frame), async () => ({
    type: 'result', id: String(frames.length), return_code: 0, stdout: '', stderr: '',
  }));
  await Promise.all([
    tool.execute('one', { command: 'ls', cwd: '/task', timeout_sec: 5 }),
    tool.execute('two', { command: 'pwd' }),
  ]);
  assert.deepEqual(frames.map(frame => frame.id), ['1', '2']);
  assert.deepEqual(frames.map(frame => frame.command), ['ls', 'pwd']);
});

test('unmatched result fails without treating a host operation as successful', async () => {
  const tool = createSandboxTool(() => {}, async () => ({
    type: 'result', id: 'wrong', return_code: 0, stdout: '', stderr: '',
  }));
  await assert.rejects(tool.execute('one', { command: 'pwd' }), /invalid sandbox response/);
});
