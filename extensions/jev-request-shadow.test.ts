import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import jevRequestShadow, { eligibleRequest, type ShadowOptions } from "./jev-request-shadow.ts";

type Handler = (event: any, ctx: any) => unknown;

function setup(options: Partial<ShadowOptions> = {}, reply: () => Promise<Response> = okReply(0.8)) {
	const agentDir = mkdtempSync(join(tmpdir(), "jev-shadow-"));
	const calls: { url: string; body: any; headers: any }[] = [];
	const handlers = new Map<string, Handler>();
	const commands = new Map<string, any>();
	const pending: Promise<unknown>[] = [];
	jevRequestShadow(
		{
			on(name: string, handler: Handler) { handlers.set(name, handler); },
			registerCommand(name: string, command: any) { commands.set(name, command); },
		} as any,
		{
			agentDir,
			env: { TYPESAFE_API_KEY: "k" },
			fetch: (async (url: string, init: any) => {
				calls.push({ url, body: JSON.parse(init.body), headers: init.headers });
				return reply();
			}) as any,
			track: (p) => { pending.push(p); },
			...options,
		},
	);
	const notes: string[] = [];
	const ctx = {
		ui: { notify: (text: string) => notes.push(text) },
		sessionManager: {
			getSessionId: () => "s1",
			getSessionFile: () => "/sessions/s1.jsonl",
			getBranch: () => [
				{ type: "message", message: { role: "user", content: "earlier" } },
				{ type: "message", message: { role: "assistant", content: [{ type: "text", text: "x".repeat(2000) + "Which thresholds?" }] } },
			],
		},
	};
	const command = (args: string) => commands.get("jev-shadow").handler(args, ctx);
	const input = (text: string, source = "interactive") => handlers.get("input")!({ type: "input", text, source }, ctx);
	const settle = () => Promise.all(pending);
	const log = () => {
		const file = join(agentDir, "agent-skills", "jev-request-shadow.jsonl");
		return existsSync(file) ? readFileSync(file, "utf8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l)) : [];
	};
	const done = () => rmSync(agentDir, { recursive: true, force: true });
	return { agentDir, calls, notes, command, input, settle, log, done };
}

function okReply(noul: number): () => Promise<Response> {
	return async () => new Response(JSON.stringify({
		model: "jev-latest",
		answers: { request_precise: { type: "noul", noul } },
		usage: { input_tokens: 700, output_tokens: 0 },
	}), { status: 200 });
}

test("eligible requests: strips the router prefix, skips commands, bash, blanks and extension input", () => {
	assert.equal(eligibleRequest("/skill:ask-skills fix the bug", "interactive"), "fix the bug");
	assert.equal(eligibleRequest("fix the bug", "rpc"), "fix the bug");
	for (const [text, source] of [["/model", "interactive"], ["!ls", "interactive"], ["  ", "interactive"],
		["/skill:ask-skills   ", "interactive"], ["follow-up", "extension"]] as const) {
		assert.equal(eligibleRequest(text, source), undefined, `${text} from ${source}`);
	}
});

test("off by default: nothing is sent or logged", async () => {
	const t = setup();
	assert.equal(t.input("fix the bug"), undefined);
	await t.settle();
	assert.equal(t.calls.length, 0);
	assert.deepEqual(t.log(), []);
	t.done();
});

test("on: one request with the request text and the assistant tail; the log has no text", async () => {
	const t = setup();
	await t.command("on");
	assert.equal(t.input("/skill:ask-skills vorrei anthropic 30%"), undefined, "never changes the input");
	await t.settle();
	assert.equal(t.calls.length, 1);
	const { url, body, headers } = t.calls[0];
	assert.equal(url, "https://api.typesafe.ai/v1/systemone");
	assert.equal(headers.Authorization, "Bearer k");
	assert.equal(body.model, "jev-latest");
	assert.equal(body.state.request, "vorrei anthropic 30%");
	assert.equal(body.state.context.length, 1500);
	assert.ok(body.state.context.endsWith("Which thresholds?"));
	assert.equal(body.questions.request_precise.type, "noul");
	const [line] = t.log();
	assert.equal(line.verdict, "precise");
	assert.equal(line.noul, 0.8);
	assert.equal(line.chars, 20);
	assert.equal(line.contextChars, 1500);
	assert.equal(line.inputTokens, 700);
	assert.equal(line.sessionId, "s1");
	assert.doesNotMatch(JSON.stringify(line), /anthropic|Which thresholds/);
	t.done();
});

test("the state persists across instances and off stops sending", async () => {
	const t = setup();
	await t.command("on");
	const again = setup({ agentDir: t.agentDir });
	again.input("fix the bug");
	await again.settle();
	assert.equal(again.calls.length, 1);
	await again.command("off");
	again.input("fix it again");
	await again.settle();
	assert.equal(again.calls.length, 1);
	t.done();
});

test("a vague answer, an HTTP error and a timeout are logged and never thrown", async () => {
	for (const [reply, expected] of [
		[okReply(0.2), { verdict: "vague" }],
		[async () => new Response("no", { status: 401 }), { error: "http 401" }],
		[async () => { throw Object.assign(new Error("t"), { name: "TimeoutError" }); }, { error: "timeout" }],
		[async () => new Response("{}", { status: 200 }), { error: "invalid" }],
	] as const) {
		const t = setup({}, reply as any);
		await t.command("on");
		t.input("fix the bug");
		await t.settle();
		assert.deepEqual(Object.fromEntries(Object.keys(expected).map((k) => [k, t.log()[0][k]])), expected);
		t.done();
	}
});

test("without a key nothing is sent and status says so", async () => {
	const t = setup({ env: {}, platform: "linux" });
	await t.command("on");
	t.input("fix the bug");
	await t.settle();
	assert.equal(t.calls.length, 0);
	await t.command("status");
	assert.match(t.notes.at(-1)!, /on; no TYPESAFE_API_KEY/);
	t.done();
});

test("report summarizes the log", async () => {
	const t = setup();
	await t.command("on");
	t.input("fix the bug");
	t.input("make it faster");
	await t.settle();
	await t.command("report");
	assert.match(t.notes.at(-1)!, /2 requests: 2 precise, 0 vague, 0 errors; 1400 input tokens/);
	t.done();
});
