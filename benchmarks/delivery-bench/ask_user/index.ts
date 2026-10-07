/**
 * delivery-bench `ask_user` (DBH-38): the arm asks the person who made the request.
 *
 * Loaded with -e in every arm of a vague-request lot. The runner sets DBENCH_ASK_USER to
 * {"python", "script", "config"}; the tool runs `python -B simulator.py ask` with the question
 * on stdin and returns the simulated user's answer. No imports: the parameters are plain JSON
 * Schema, so the file loads from any folder.
 */
import { spawn } from 'node:child_process'

const CALL_MS = 30 * 60 * 1000 // the simulator retries a failing provider for a few minutes

type Answer = { answer?: string | null; error?: string }

function run(question: string, signal?: AbortSignal): Promise<Answer> {
  const raw = process.env.DBENCH_ASK_USER
  if (!raw) return Promise.resolve({ error: 'DBENCH_ASK_USER is not set' })
  let setup: { python: string; script: string }
  try {
    setup = JSON.parse(raw)
  } catch {
    return Promise.resolve({ error: 'DBENCH_ASK_USER is not JSON' })
  }
  return new Promise((resolve) => {
    const child = spawn(setup.python, ['-B', setup.script, 'ask'], { stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true })
    const out: Buffer[] = []
    const timer = setTimeout(() => child.kill(), CALL_MS)
    const abort = (): void => {
      child.kill()
    }
    signal?.addEventListener('abort', abort, { once: true })
    child.stdout.on('data', (chunk: Buffer) => out.push(chunk))
    child.stderr.on('data', () => {})
    child.on('error', (error) => {
      clearTimeout(timer)
      resolve({ error: String(error) })
    })
    child.on('close', () => {
      clearTimeout(timer)
      signal?.removeEventListener('abort', abort)
      try {
        resolve(JSON.parse(Buffer.concat(out).toString('utf8')))
      } catch {
        resolve({ error: 'no answer' })
      }
    })
    child.stdin.end(JSON.stringify({ question }), 'utf8')
  })
}

export default function (pi: any): void {
  pi.registerTool({
    name: 'ask_user',
    label: 'Ask user',
    description: 'Pregunta al usuario que hizo el encargo. Escribe una pregunta concreta; la respuesta llega en el momento.',
    parameters: {
      type: 'object',
      properties: { question: { type: 'string', description: 'La pregunta para el usuario' } },
      required: ['question'],
      additionalProperties: false,
    },
    executionMode: 'sequential',
    async execute(_toolCallId: string, params: { question?: string }, signal?: AbortSignal) {
      const result = await run(String(params?.question ?? ''), signal)
      if (typeof result.answer === 'string') {
        return { content: [{ type: 'text', text: result.answer }], details: { answered: true } }
      }
      return {
        content: [{ type: 'text', text: 'El usuario no ha podido responder ahora.' }],
        details: { answered: false, error: result.error ?? 'unknown' },
        isError: true,
      }
    },
  })
}
