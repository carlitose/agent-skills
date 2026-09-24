import { Type } from 'typebox';

/** The only model-visible tool: frames are relayed to Python's Harbor environment. */
export function createSandboxTool(send, receive) {
  let pending = Promise.resolve();
  let callId = 0;
  return {
    name: 'sandbox_exec',
    label: 'Sandbox shell',
    description: 'Run a shell command ONLY in the benchmark task container. No host files or shell are accessible.',
    parameters: Type.Object({
      command: Type.String({ minLength: 1, maxLength: 16384 }),
      cwd: Type.Optional(Type.Union([Type.String(), Type.Null()])),
      timeout_sec: Type.Optional(Type.Integer({ minimum: 1, maximum: 120 })),
    }),
    execute: async (_toolCallId, params) => {
      // Pi can issue parallel calls; one request/response pair owns stdio at a time.
      const action = pending.then(async () => {
        const id = String(++callId);
        send({ type: 'exec', id, command: params.command,
          cwd: params.cwd ?? null, timeout_sec: params.timeout_sec ?? 60 });
        const reply = await receive();
        if (reply.type !== 'result' || reply.id !== id ||
            !Number.isInteger(reply.return_code) ||
            (reply.stdout !== null && typeof reply.stdout !== 'string') ||
            (reply.stderr !== null && typeof reply.stderr !== 'string')) {
          throw new Error('invalid sandbox response');
        }
        return { content: [{ type: 'text', text: JSON.stringify({
          stdout: reply.stdout, stderr: reply.stderr, return_code: reply.return_code,
        }) }], details: { return_code: reply.return_code } };
      });
      pending = action.then(() => {}, () => {});
      return action;
    },
  };
}
