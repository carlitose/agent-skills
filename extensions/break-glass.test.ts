import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import mandatoryAgentSkills, {
	BREAK_GLASS_POLICY_MARKER,
	POLICY_MARKER,
	ROUTER_COMMAND,
} from "./mandatory-agent-skills.ts";
import {
	BREAK_GLASS_CUSTOM_TYPE,
	BREAK_GLASS_LEGACY_CUSTOM_TYPE,
	BREAK_GLASS_TTL_MS,
	appendBreakGlassPolicy,
	createArmedEvent,
	createBreakGlassTransition,
	digestBreakGlassEvent,
	isEligibleBreakGlassInput,
	restoreBreakGlassState,
	selectRecoveryTools,
	shortGrantId,
	type BreakGlassEventData,
	type BreakGlassIdentity,
} from "./break-glass.ts";

function identity(root = mkdtempSync(join(tmpdir(), "break-glass-"))): BreakGlassIdentity {
	const sessionFile = join(root, "session.jsonl");
	writeFileSync(sessionFile, "");
	return { sessionFile, cwd: root };
}

function arm(
	currentIdentity: BreakGlassIdentity,
	previous: BreakGlassEventData | undefined = undefined,
	now = Date.parse("2026-09-03T12:00:00.000Z"),
): BreakGlassEventData {
	return createArmedEvent({
		identity: currentIdentity,
		grantId: "deadbeef-0000-4000-8000-000000000001",
		now,
		previous,
	});
}

function builtinTool(name: string) {
	return {
		name,
		description: name,
		parameters: {},
		sourceInfo: {
			path: `<builtin:${name}>`,
			source: "builtin",
			scope: "temporary",
			origin: "top-level",
		},
	};
}

function fakeRuntime(options: {
	currentIdentity?: BreakGlassIdentity;
	hasUI?: boolean;
	activeTools?: string[];
	allTools?: ReturnType<typeof builtinTool>[];
	now?: number;
} = {}) {
	const currentIdentity = options.currentIdentity ?? identity();
	const handlers = new Map<string, Array<(event: any, ctx: any) => any>>();
	const commands = new Map<string, { handler: (args: string, ctx: any) => Promise<void> }>();
	const entries: any[] = [];
	const notifications: Array<{ message: string; type?: string }> = [];
	const statuses: Array<string | undefined> = [];
	const confirmations: Array<{ title: string; message: string }> = [];
	const selectAnswers: Array<string | undefined> = [];
	const inputAnswers: Array<string | undefined> = [];
	const confirmAnswers: boolean[] = [];
	let branchEntries: any[] | undefined;
	let activeTools = [...(options.activeTools ?? ["read", "bash", "edit", "write", "code"])];
	let allTools = options.allTools ?? ["read", "bash", "edit", "write", "code"].map(builtinTool);
	let now = options.now ?? Date.parse("2026-09-03T12:00:00.000Z");

	const pi: any = {
		on(name: string, handler: (event: any, ctx: any) => any) {
			handlers.set(name, [...(handlers.get(name) ?? []), handler]);
		},
		registerCommand(name: string, command: any) {
			commands.set(name, command);
		},
		appendEntry(customType: string, data: unknown) {
			entries.push({ type: "custom", customType, data });
		},
		getActiveTools() {
			return [...activeTools];
		},
		setActiveTools(names: string[]) {
			activeTools = [...names];
		},
		getAllTools() {
			return allTools;
		},
		getCommands() {
			return ["ask-skills", "change-status-ticket", "to-spec", "to-tickets", "ticket-autopilot"].map(
				(name) => ({ name: `skill:${name}`, source: "skill" }),
			);
		},
	};
	const ctx: any = {
		hasUI: options.hasUI ?? true,
		mode: options.hasUI === false ? "print" : "tui",
		cwd: currentIdentity.cwd,
		sessionManager: {
			getSessionFile: () => currentIdentity.sessionFile,
			getBranch: () => branchEntries ?? entries,
			getEntries: () => entries,
		},
		ui: {
			select: async (title: string) => {
				confirmations.push({ title, message: "select" });
				return selectAnswers.shift();
			},
			input: async (title: string) => {
				confirmations.push({ title, message: "input" });
				return inputAnswers.shift();
			},
			confirm: async (title: string, message: string) => {
				confirmations.push({ title, message });
				return confirmAnswers.shift() ?? false;
			},
			notify(message: string, type?: string) {
				notifications.push({ message, type });
			},
			setStatus(_key: string, value: string | undefined) {
				statuses.push(value);
			},
		},
	};

	mandatoryAgentSkills(pi, {
		now: () => now,
		createGrantId: () => "deadbeef-0000-4000-8000-000000000001",
	});

	async function emit(name: string, event: any) {
		let result: any;
		for (const handler of handlers.get(name) ?? []) {
			const next = await handler(event, ctx);
			if (next !== undefined) result = next;
		}
		return result;
	}

	return {
		pi,
		ctx,
		entries,
		notifications,
		statuses,
		confirmations,
		commands,
		emit,
		getActiveTools: () => [...activeTools],
		setBranchEntries: (value: any[] | undefined) => {
			branchEntries = value;
		},
		setActiveTools: (names: string[]) => {
			activeTools = [...names];
		},
		setAllTools: (tools: ReturnType<typeof builtinTool>[]) => {
			allTools = tools;
		},
		setNow: (value: number) => {
			now = value;
		},
	};
}

async function armRuntime(runtime: ReturnType<typeof fakeRuntime>) {
	await runtime.commands.get("break-glass")!.handler("", runtime.ctx);
}

async function consumeRuntime(runtime: ReturnType<typeof fakeRuntime>, prompt: string) {
	assert.deepEqual(
		await runtime.emit("input", { type: "input", text: prompt, source: "interactive" }),
		{ action: "continue" },
	);
	return runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
}

test("v2 grant chains bind one prompt and reject altered history", () => {
	const currentIdentity = identity();
	const armed = arm(currentIdentity);
	const consumed = createBreakGlassTransition(armed, "consumed", {
		promptSha256: "a".repeat(64),
		inputSource: "interactive",
		priorToolNames: ["read", "bash", "edit", "write", "code"],
		restrictedToolNames: ["read", "bash", "edit", "write"],
	});
	const closed = createBreakGlassTransition(consumed, "closed", {
		turnOutcome: "agent-end",
		restoration: "restored",
	});

	const restored = restoreBreakGlassState([armed, consumed, closed], currentIdentity);
	assert.equal(restored.valid, true);
	assert.equal(restored.phase, "closed");
	assert.equal(restored.latest?.eventDigest, digestBreakGlassEvent(restored.latest!));

	const altered = structuredClone(consumed);
	altered.promptSha256 = "b".repeat(64);
	assert.match(restoreBreakGlassState([armed, altered], currentIdentity).reason ?? "", /digest/i);
	assert.match(restoreBreakGlassState([armed, armed], currentIdentity).reason ?? "", /sequence/i);
	assert.throws(
		() => createBreakGlassTransition(armed, "consumed", {
			promptSha256: "c".repeat(64),
			inputSource: "interactive",
			priorToolNames: ["read"],
			restrictedToolNames: ["read"],
		}, Date.parse(armed.expiresAt)),
		/expired/i,
	);
});

test("expiry and active identity mismatch fail closed", () => {
	const original = identity();
	const armed = arm(original);
	const expired = restoreBreakGlassState([armed], original, Date.parse(armed.expiresAt));
	assert.equal(expired.valid, true);
	assert.equal(expired.expired, true);
	const mismatched = restoreBreakGlassState([armed], identity());
	assert.equal(mismatched.valid, false);
	assert.match(mismatched.reason ?? "", /identity/i);
});

test("only an eligible ordinary-language input consumes the arm", () => {
	assert.equal(isEligibleBreakGlassInput("repair this run", "interactive"), true);
	assert.equal(isEligibleBreakGlassInput("repair this run", "rpc"), true);
	assert.equal(isEligibleBreakGlassInput("/status", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("!git status", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("  ", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("internal", "extension"), false);
	assert.equal(isEligibleBreakGlassInput("queued", "interactive", "followUp"), false);
	assert.equal(isEligibleBreakGlassInput("steer", "rpc", "steer"), false);
});

test("the policy authorizes direct local repair and no remote authority", () => {
	const event = arm(identity());
	const consumed = createBreakGlassTransition(event, "consumed", {
		promptSha256: "a".repeat(64),
		inputSource: "interactive",
		priorToolNames: ["read"],
		restrictedToolNames: ["read", "bash", "edit", "write"],
	});
	const once = appendBreakGlassPolicy(`base\n${POLICY_MARKER}`, consumed);
	assert.equal(appendBreakGlassPolicy(once, consumed), once);
	assert.match(once, new RegExp(BREAK_GLASS_POLICY_MARKER));
	assert.match(once, /directly inspect and modify local files/i);
	assert.match(once, /tracked files and `\.git\/ticket-autopilot` state/i);
	assert.match(once, /run.*status.*resume/is);
	assert.match(once, /no provider, PR, push, merge/i);
	assert.doesNotMatch(once, /to-spec -> to-tickets -> ticket-autopilot/);
	assert.throws(
		() => appendBreakGlassPolicy(once, { ...consumed, promptSha256: "b".repeat(64) }),
		/different break-glass policy marker/i,
	);
});

test("tool selection exposes only unique canonical local repair built-ins", () => {
	const tools = ["read", "bash", "edit", "write", "code"].map(builtinTool);
	assert.deepEqual(selectRecoveryTools(tools), {
		toolNames: ["read", "bash", "edit", "write"],
		ambiguous: [],
	});
	const customEdit = {
		...builtinTool("edit"),
		sourceInfo: { ...builtinTool("edit").sourceInfo, source: "extension" },
	};
	assert.deepEqual(
		selectRecoveryTools([builtinTool("read"), builtinTool("bash"), customEdit, builtinTool("write")]),
		{ toolNames: ["read", "bash", "write"], ambiguous: ["edit"] },
	);
	const customRead = {
		...builtinTool("read"),
		sourceInfo: { ...builtinTool("read").sourceInfo, path: "/tmp/read.ts" },
	};
	assert.deepEqual(selectRecoveryTools([customRead, builtinTool("bash")]), {
		toolNames: [],
		ambiguous: ["read"],
	});
});

test("missing canonical read exposes no tools and fails visibly", async () => {
	const runtime = fakeRuntime({
		allTools: [builtinTool("bash"), builtinTool("edit"), builtinTool("write")],
	});
	await armRuntime(runtime);
	await runtime.emit("input", {
		type: "input",
		text: "repair the stuck local run",
		source: "interactive",
	});
	assert.deepEqual(runtime.getActiveTools(), []);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /canonical read is required/i);
	assert.equal(runtime.notifications.at(-1)?.type, "error");
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write", "code"]);
});

test("ordinary routing is unchanged while inactive and historical v1 entries grant nothing", async () => {
	const runtime = fakeRuntime();
	runtime.entries.push({
		type: "custom",
		customType: BREAK_GLASS_LEGACY_CUSTOM_TYPE,
		data: { transition: "armed", policyVersion: 1 },
	});
	await runtime.emit("session_start", { type: "session_start", reason: "startup" });
	assert.deepEqual(
		await runtime.emit("input", { type: "input", text: "Fix it", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} Fix it` },
	);
	const before = await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt: "Fix it",
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	assert.match(before.systemPrompt, new RegExp(POLICY_MARKER));
	assert.doesNotMatch(before.systemPrompt, new RegExp(BREAK_GLASS_POLICY_MARKER));
	assert.equal(runtime.entries.filter((entry) => entry.customType === BREAK_GLASS_CUSTOM_TYPE).length, 0);
});

test("one command plus natural language enables direct local repair without dialogs", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	assert.equal(runtime.entries.at(-1).customType, BREAK_GLASS_CUSTOM_TYPE);
	assert.equal(runtime.entries.at(-1).data.transition, "armed");
	assert.equal(runtime.confirmations.length, 0);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /next ordinary-language prompt/i);

	const prompt = "Fix the stuck autopilot ledger, read status, and resume the run";
	const before = await consumeRuntime(runtime, prompt);
	assert.equal(runtime.entries.at(-1).data.transition, "consumed");
	assert.equal(runtime.entries.at(-1).data.promptSha256.length, 64);
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write"]);
	assert.match(before.systemPrompt, new RegExp(BREAK_GLASS_POLICY_MARKER));

	for (const [toolName, input] of [
		["read", { path: `${runtime.ctx.cwd}/.git/ticket-autopilot/runs/stuck/ledger.json` }],
		["bash", { command: "git status --short" }],
		["edit", { path: `${runtime.ctx.cwd}/tracked.txt`, edits: [{ oldText: "bad", newText: "fixed" }] }],
		["write", { path: `${runtime.ctx.cwd}/.git/ticket-autopilot/manual-repair.json`, content: "{}" }],
	] as const) {
		assert.equal(
			await runtime.emit("tool_call", { type: "tool_call", toolName, toolCallId: `call-${toolName}`, input }),
			undefined,
		);
	}
	assert.equal(runtime.confirmations.length, 0);
	assert.deepEqual(
		await runtime.emit("tool_call", {
			type: "tool_call",
			toolName: "code",
			toolCallId: "call-code",
			input: {},
		}),
		{ block: true, reason: "Break-glass permits only canonical built-in read, bash, edit, and write.", terminate: true },
	);

	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write", "code"]);
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
	assert.equal(runtime.entries.at(-1).data.restoration, "restored");
	assert.deepEqual(
		await runtime.emit("input", { type: "input", text: "continue normally", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} continue normally` },
	);
});

test("status and cancel remain explicit while bare break-glass means arm", async () => {
	const runtime = fakeRuntime();
	await runtime.commands.get("break-glass")!.handler("status", runtime.ctx);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /inactive/i);
	await armRuntime(runtime);
	await runtime.commands.get("break-glass")!.handler("status", runtime.ctx);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /armed/i);
	await runtime.commands.get("break-glass")!.handler("cancel", runtime.ctx);
	assert.equal(runtime.entries.at(-1).data.transition, "cancelled");
	await runtime.commands.get("break-glass")!.handler("wat", runtime.ctx);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /usage/i);
	assert.equal(runtime.confirmations.length, 0);
});

test("slash, shell, and queued input do not consume an arm", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	for (const event of [
		{ type: "input", text: "/model", source: "interactive" },
		{ type: "input", text: "!git status", source: "interactive" },
		{ type: "input", text: "queued", source: "interactive", streamingBehavior: "followUp" },
	]) {
		await runtime.emit("input", event);
		assert.equal(runtime.entries.at(-1).data.transition, "armed");
	}
});

test("same-session reload restores an arm while fork and expiry do not", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const resumed = fakeRuntime({
		currentIdentity: {
			sessionFile: runtime.ctx.sessionManager.getSessionFile(),
			cwd: runtime.ctx.cwd,
		},
	});
	resumed.entries.push(...runtime.entries);
	await resumed.emit("session_start", { type: "session_start", reason: "reload" });
	await consumeRuntime(resumed, "repair after reload");
	assert.equal(resumed.entries.at(-1).data.transition, "consumed");

	const fork = fakeRuntime();
	fork.entries.push(...runtime.entries);
	await fork.emit("session_start", { type: "session_start", reason: "fork" });
	assert.deepEqual(
		await fork.emit("input", { type: "input", text: "must route", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} must route` },
	);
	assert.match(fork.statuses.at(-1) ?? "", /blocked/i);

	const expiring = fakeRuntime();
	await armRuntime(expiring);
	expiring.setNow(Date.parse("2026-09-03T12:00:00.000Z") + BREAK_GLASS_TTL_MS);
	assert.deepEqual(
		await expiring.emit("input", { type: "input", text: "too late", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} too late` },
	);
	assert.equal(expiring.entries.at(-1).data.transition, "expired");
});

test("corrupt v2 state blocks re-arm and keeps ordinary routing", async () => {
	const runtime = fakeRuntime();
	const corrupt: any = arm({
		sessionFile: runtime.ctx.sessionManager.getSessionFile(),
		cwd: runtime.ctx.cwd,
	});
	corrupt.policyVersion = 99;
	corrupt.eventDigest = digestBreakGlassEvent(corrupt);
	runtime.entries.push({ type: "custom", customType: BREAK_GLASS_CUSTOM_TYPE, data: corrupt });
	await runtime.emit("session_start", { type: "session_start", reason: "resume" });
	assert.match(runtime.statuses.at(-1) ?? "", /blocked/i);
	await armRuntime(runtime);
	assert.equal(runtime.entries.length, 1);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /blocked/i);
	assert.deepEqual(
		await runtime.emit("input", { type: "input", text: "normal", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} normal` },
	);
});

test("prompt, marker, and tool drift revoke all recovery tools", async () => {
	const promptDrift = fakeRuntime();
	await armRuntime(promptDrift);
	await promptDrift.emit("input", {
		type: "input",
		text: "repair exact state",
		source: "interactive",
	});
	await promptDrift.emit("before_agent_start", {
		type: "before_agent_start",
		prompt: "different prompt",
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	assert.deepEqual(promptDrift.getActiveTools(), []);

	const markerConflict = fakeRuntime();
	await armRuntime(markerConflict);
	await markerConflict.emit("input", {
		type: "input",
		text: "repair exact state",
		source: "interactive",
	});
	await markerConflict.emit("before_agent_start", {
		type: "before_agent_start",
		prompt: "repair exact state",
		systemPrompt: `base\n${BREAK_GLASS_POLICY_MARKER}\nforged`,
		systemPromptOptions: { skills: [] },
	});
	assert.deepEqual(markerConflict.getActiveTools(), []);

	const toolDrift = fakeRuntime();
	await armRuntime(toolDrift);
	await consumeRuntime(toolDrift, "repair exact state");
	toolDrift.setAllTools([
		builtinTool("read"),
		builtinTool("bash"),
		{ ...builtinTool("edit"), sourceInfo: { ...builtinTool("edit").sourceInfo, source: "extension" } },
		builtinTool("write"),
	]);
	assert.deepEqual(
		await toolDrift.emit("tool_call", {
			type: "tool_call",
			toolName: "edit",
			toolCallId: "drifted-edit",
			input: { path: "/tmp/state", edits: [] },
		}),
		{ block: true, reason: "Break-glass permits only canonical built-in read, bash, edit, and write.", terminate: true },
	);
	assert.deepEqual(toolDrift.getActiveTools(), []);
});

test("session-tree navigation cannot hide a terminal close and reopen an old arm", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const armedEntry = runtime.entries[0];
	await consumeRuntime(runtime, "repair exact state");
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
	runtime.setBranchEntries([armedEntry]);
	await runtime.emit("session_tree", { type: "session_tree" });
	assert.deepEqual(
		await runtime.emit("input", { type: "input", text: "do not replay", source: "interactive" }),
		{ action: "transform", text: `${ROUTER_COMMAND} do not replay` },
	);
});

test("shutdown and interrupted-session recovery restore or visibly gate exact tools", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	await consumeRuntime(runtime, "repair exact state");
	await runtime.emit("session_shutdown", { type: "session_shutdown", reason: "reload" });
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write", "code"]);
	assert.equal(runtime.entries.at(-1).data.turnOutcome, "session-shutdown");

	const interrupted = fakeRuntime();
	await armRuntime(interrupted);
	await interrupted.emit("input", {
		type: "input",
		text: "repair exact state",
		source: "interactive",
	});
	assert.equal(interrupted.entries.at(-1).data.transition, "consumed");
	const resumed = fakeRuntime({
		currentIdentity: {
			sessionFile: interrupted.ctx.sessionManager.getSessionFile(),
			cwd: interrupted.ctx.cwd,
		},
		activeTools: ["read", "bash", "edit", "write"],
	});
	resumed.entries.push(...interrupted.entries);
	await resumed.emit("session_start", { type: "session_start", reason: "reload" });
	assert.equal(resumed.entries.at(-1).data.transition, "closed");
	assert.equal(resumed.entries.at(-1).data.turnOutcome, "interrupted-session-restore");
	assert.deepEqual(resumed.getActiveTools(), ["read", "bash", "edit", "write", "code"]);
});

test("restoration drift closes with a visible non-rearmable gate", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	await consumeRuntime(runtime, "repair exact state");
	runtime.setActiveTools(["read"]);
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.equal(runtime.entries.at(-1).data.restoration, "gated");
	assert.deepEqual(runtime.getActiveTools(), ["read"]);
	assert.match(runtime.statuses.at(-1) ?? "", /restoration gate/i);
	const count = runtime.entries.length;
	await armRuntime(runtime);
	assert.equal(runtime.entries.length, count);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /cannot be re-armed/i);
});

test("short grant ids remain compact and stable", () => {
	assert.equal(shortGrantId("deadbeef-0000-4000-8000-000000000001"), "deadbeef");
});
