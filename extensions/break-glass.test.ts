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
		details: {
			incidentClass: "source-identity",
			target: "/exact/checkout",
			reason: "mandatory routing cannot resolve the source identity",
			actor: "human:test",
		},
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
	let concurrentConfirmations = 0;
	let maxConcurrentConfirmations = 0;
	let branchEntries: any[] | undefined;
	let activeTools = [...(options.activeTools ?? ["read", "bash", "edit", "write"])];
	let allTools = options.allTools ?? ["read", "bash", "edit", "write"].map(builtinTool);
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
			select: async () => selectAnswers.shift(),
			input: async () => inputAnswers.shift(),
			confirm: async (title: string, message: string) => {
				confirmations.push({ title, message });
				concurrentConfirmations += 1;
				maxConcurrentConfirmations = Math.max(maxConcurrentConfirmations, concurrentConfirmations);
				try {
					await Promise.resolve();
					return confirmAnswers.shift() ?? false;
				} finally {
					concurrentConfirmations -= 1;
				}
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
		selectAnswers,
		inputAnswers,
		confirmAnswers,
		commands,
		emit,
		getActiveTools: () => [...activeTools],
		getMaxConcurrentConfirmations: () => maxConcurrentConfirmations,
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
	runtime.selectAnswers.push("source-identity");
	runtime.confirmAnswers.push(true);
	runtime.inputAnswers.push(
		"/exact/checkout",
		"mandatory routing cannot resolve the source identity",
		"human:test",
		`BREAK GLASS ${shortGrantId("deadbeef-0000-4000-8000-000000000001")}`,
	);
	await runtime.commands.get("break-glass")!.handler("arm", runtime.ctx);
}

test("canonical grant chains validate and reject altered history", () => {
	const currentIdentity = identity();
	const armed = arm(currentIdentity);
	const consumed = createBreakGlassTransition(armed, "consumed", {
		promptSha256: "a".repeat(64),
		inputSource: "interactive",
		priorToolNames: ["read", "bash", "edit"],
		restrictedToolNames: ["read", "bash"],
	});
	const approved = createBreakGlassTransition(consumed, "bash-approved", {
		toolCallId: "call-1",
		commandSha256: "b".repeat(64),
		effectiveCwd: currentIdentity.cwd,
		decision: "approved",
	});
	const closed = createBreakGlassTransition(approved, "closed", {
		turnOutcome: "agent-end",
		restoration: "restored",
	});

	const restored = restoreBreakGlassState([armed, consumed, approved, closed], currentIdentity);
	assert.equal(restored.valid, true);
	assert.equal(restored.phase, "closed");
	assert.equal(restored.latest?.eventDigest, digestBreakGlassEvent(restored.latest!));

	const altered = structuredClone(consumed);
	altered.target = "/different";
	const corrupt = restoreBreakGlassState([armed, altered], currentIdentity);
	assert.equal(corrupt.valid, false);
	assert.match(corrupt.reason ?? "", /digest/i);

	const duplicate = restoreBreakGlassState([armed, armed], currentIdentity);
	assert.equal(duplicate.valid, false);
	assert.match(duplicate.reason ?? "", /sequence/i);

	const malformed = { ...armed, target: " padded target " };
	malformed.eventDigest = digestBreakGlassEvent(malformed);
	const malformedResult = restoreBreakGlassState([malformed], currentIdentity);
	assert.equal(malformedResult.valid, false);
	assert.match(malformedResult.reason ?? "", /identity/i);

	assert.throws(
		() => createBreakGlassTransition(armed, "consumed", {
			promptSha256: "c".repeat(64),
			inputSource: "interactive",
			priorToolNames: ["read"],
			restrictedToolNames: ["read"],
		}, Date.parse(armed.expiresAt)),
		/expired/i,
	);
	assert.throws(
		() => createBreakGlassTransition(armed, "expired", {}, Date.parse(armed.createdAt)),
		/cannot expire early/i,
	);

	const unknown: any = { ...armed, transition: "toString" };
	unknown.eventDigest = digestBreakGlassEvent(unknown);
	const unknownResult = restoreBreakGlassState([unknown], currentIdentity);
	assert.equal(unknownResult.valid, false);
	assert.match(unknownResult.reason ?? "", /unknown transition/i);
});

test("expiry and identity mismatch fail closed without inheriting authority", () => {
	const parent = identity();
	const armed = arm(parent);
	const expired = restoreBreakGlassState([armed], parent, Date.parse(armed.expiresAt));
	assert.equal(expired.valid, true);
	assert.equal(expired.phase, "armed");
	assert.equal(expired.expired, true);

	const fork = identity();
	const mismatched = restoreBreakGlassState([armed], fork);
	assert.equal(mismatched.valid, false);
	assert.match(mismatched.reason ?? "", /identity/i);
});

test("only eligible natural-language input can consume a grant", () => {
	assert.equal(isEligibleBreakGlassInput("repair this checkout", "interactive"), true);
	assert.equal(isEligibleBreakGlassInput("repair this checkout", "rpc"), true);
	assert.equal(isEligibleBreakGlassInput("/reload", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("!git status", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("  ", "interactive"), false);
	assert.equal(isEligibleBreakGlassInput("internal", "extension"), false);
	assert.equal(isEligibleBreakGlassInput("queued", "interactive", "followUp"), false);
	assert.equal(isEligibleBreakGlassInput("steer", "rpc", "steer"), false);
});

test("break-glass policy is grant-bound, explicit, and idempotent", () => {
	const event = arm(identity());
	const once = appendBreakGlassPolicy(`base\n${POLICY_MARKER}`, event);
	const twice = appendBreakGlassPolicy(once, event);
	assert.equal(twice, once);
	assert.match(once, new RegExp(BREAK_GLASS_POLICY_MARKER));
	assert.match(once, /one local operational-recovery turn/);
	assert.match(once, /must not edit tracked content/);
	assert.match(once, /provider mutation, merge, terminal integration, completion, cleanup, Pi synchronization, or `\/reload`/);
	assert.throws(
		() => appendBreakGlassPolicy(once, { ...event, target: "/different/target" }),
		/different break-glass policy marker/i,
	);
});

test("tool selection accepts only exact active Pi built-ins", () => {
	const tools = [builtinTool("read"), builtinTool("bash"), builtinTool("edit")];
	assert.deepEqual(selectRecoveryTools(["read", "bash", "edit"], tools), {
		toolNames: ["read", "bash"],
		ambiguous: [],
	});

	const customRead = { ...builtinTool("read"), sourceInfo: { ...builtinTool("read").sourceInfo, source: "extension" } };
	assert.deepEqual(selectRecoveryTools(["read", "bash"], [customRead, builtinTool("bash")]), {
		toolNames: [],
		ambiguous: ["read"],
	});

	const customBash = { ...builtinTool("bash"), sourceInfo: { ...builtinTool("bash").sourceInfo, path: "/tmp/bash.ts" } };
	assert.deepEqual(selectRecoveryTools(["read", "bash"], [builtinTool("read"), customBash]), {
		toolNames: ["read"],
		ambiguous: ["bash"],
	});
});

test("ordinary routing is byte-equivalent while break-glass is inactive", async () => {
	const runtime = fakeRuntime();
	await runtime.emit("session_start", { type: "session_start", reason: "startup" });
	assert.deepEqual(await runtime.emit("input", { type: "input", text: "Fix it", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} Fix it`,
	});
	const before = await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt: "Fix it",
		systemPrompt: "base",
		systemPromptOptions: {
			skills: ["ask-skills", "change-status-ticket", "to-spec", "to-tickets", "ticket-autopilot"].map(
				(name) => ({ name }),
			),
		},
	});
	assert.match(before.systemPrompt, new RegExp(POLICY_MARKER));
	assert.doesNotMatch(before.systemPrompt, new RegExp(BREAK_GLASS_POLICY_MARKER));
	assert.equal(runtime.entries.length, 0);
});

test("a confirmed grant consumes one prompt, gates every Bash call, and restores tools", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	assert.equal(runtime.entries.at(-1).data.transition, "armed");
	assert.match(runtime.statuses.at(-1) ?? "", /BREAK GLASS/);
	const scope = runtime.confirmations[0]!;
	assert.match(scope.title, /complete one-turn scope/i);
	for (const exactValue of [
		"source-identity",
		"/exact/checkout",
		"mandatory routing cannot resolve the source identity",
		"human:test",
		runtime.ctx.sessionManager.getSessionFile(),
		runtime.ctx.cwd,
	]) {
		assert.ok(scope.message.includes(exactValue), `scope preview omitted ${exactValue}`);
	}
	assert.match(scope.message, /No tracked edits/);

	assert.deepEqual(await runtime.emit("input", { type: "input", text: "/model", source: "interactive" }), {
		action: "continue",
	});
	assert.equal(runtime.entries.at(-1).data.transition, "armed");

	const prompt = "repair the exact installed checkout";
	assert.deepEqual(await runtime.emit("input", { type: "input", text: prompt, source: "interactive" }), {
		action: "continue",
	});
	assert.equal(runtime.entries.at(-1).data.transition, "consumed");
	assert.equal(runtime.entries.at(-1).data.inputSource, "interactive");
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash"]);

	const before = await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: {
			skills: ["ask-skills", "change-status-ticket", "to-spec", "to-tickets", "ticket-autopilot"].map(
				(name) => ({ name }),
			),
		},
	});
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash"]);
	assert.match(before.systemPrompt, new RegExp(BREAK_GLASS_POLICY_MARKER));
	assert.equal((before.systemPrompt.match(new RegExp(BREAK_GLASS_POLICY_MARKER, "g")) ?? []).length, 1);

	assert.equal(await runtime.emit("tool_call", { type: "tool_call", toolName: "read", toolCallId: "read-1", input: { path: "/tmp" } }), undefined);
	assert.deepEqual(
		await runtime.emit("tool_call", { type: "tool_call", toolName: "edit", toolCallId: "edit-1", input: {} }),
		{ block: true, reason: "Break-glass permits only canonical built-in read and confirmed Bash calls.", terminate: true },
	);

	runtime.confirmAnswers.push(false, true);
	const rejected = await runtime.emit("tool_call", {
		type: "tool_call",
		toolName: "bash",
		toolCallId: "bash-1",
		input: { command: "git status" },
	});
	assert.equal(rejected.block, true);
	assert.equal(runtime.entries.at(-1).data.transition, "bash-rejected");

	const approvedInput = { command: "git rev-parse HEAD" };
	assert.equal(
		await runtime.emit("tool_call", {
			type: "tool_call",
			toolName: "bash",
			toolCallId: "bash-2",
			input: approvedInput,
		}),
		undefined,
	);
	assert.equal(runtime.entries.at(-1).data.transition, "bash-approved");
	assert.equal(Object.isFrozen(approvedInput), true);

	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write"]);
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
	assert.equal(runtime.entries.at(-1).data.restoration, "restored");

	assert.deepEqual(await runtime.emit("input", { type: "input", text: "next request", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} next request`,
	});
});

test("queued streaming input remains on the normal route and does not consume an arm", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	assert.deepEqual(
		await runtime.emit("input", {
			type: "input",
			text: "queued follow-up",
			source: "interactive",
			streamingBehavior: "followUp",
		}),
		{ action: "transform", text: `${ROUTER_COMMAND} queued follow-up` },
	);
	assert.equal(runtime.entries.at(-1).data.transition, "armed");
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write"]);
});

test("parallel Bash siblings receive independent audited decisions", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect two independent local facts";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	runtime.confirmAnswers.push(true, false);
	const [first, second] = await Promise.all([
		runtime.emit("tool_call", {
			type: "tool_call",
			toolName: "bash",
			toolCallId: "parallel-a",
			input: { command: "pwd" },
		}),
		runtime.emit("tool_call", {
			type: "tool_call",
			toolName: "bash",
			toolCallId: "parallel-b",
			input: { command: "git status --short" },
		}),
	]);
	assert.equal(first, undefined);
	assert.equal(second.block, true);
	const decisions = runtime.entries
		.map((entry) => entry.data)
		.filter((event) => event.transition === "bash-approved" || event.transition === "bash-rejected");
	assert.deepEqual(
		new Set(decisions.map((event) => event.toolCallId)),
		new Set(["parallel-a", "parallel-b"]),
	);
	assert.equal(new Set(decisions.map((event) => event.sequence)).size, 2);
	assert.equal(runtime.getMaxConcurrentConfirmations(), 1);
});

test("same-session reload restores an arm; fork, expiry, and no UI cannot activate it", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);

	const resumed = fakeRuntime({ currentIdentity: {
		sessionFile: runtime.ctx.sessionManager.getSessionFile(),
		cwd: runtime.ctx.cwd,
	} });
	resumed.entries.push(...runtime.entries);
	await resumed.emit("session_start", { type: "session_start", reason: "reload" });
	assert.match(resumed.statuses.at(-1) ?? "", /BREAK GLASS/);
	await resumed.emit("input", { type: "input", text: "resume repair", source: "interactive" });
	assert.equal(resumed.entries.at(-1).data.transition, "consumed");

	const fork = fakeRuntime();
	fork.entries.push(...runtime.entries);
	await fork.emit("session_start", { type: "session_start", reason: "fork" });
	assert.deepEqual(await fork.emit("input", { type: "input", text: "repair", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} repair`,
	});
	assert.match(fork.statuses.at(-1) ?? "", /BLOCKED/);

	const expiring = fakeRuntime();
	await armRuntime(expiring);
	expiring.setNow(Date.parse("2026-09-03T12:00:00.000Z") + BREAK_GLASS_TTL_MS);
	assert.deepEqual(await expiring.emit("input", { type: "input", text: "too late", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} too late`,
	});
	assert.equal(expiring.entries.at(-1).data.transition, "expired");

	const unattended = fakeRuntime({ hasUI: false });
	await unattended.commands.get("break-glass")!.handler("arm", unattended.ctx);
	assert.equal(unattended.entries.length, 0);
	assert.equal(unattended.notifications.at(-1)?.type, "error");

	const resumedUnattended = fakeRuntime({
		currentIdentity: {
			sessionFile: runtime.ctx.sessionManager.getSessionFile(),
			cwd: runtime.ctx.cwd,
		},
		hasUI: false,
	});
	resumedUnattended.entries.push(...runtime.entries);
	await resumedUnattended.emit("session_start", { type: "session_start", reason: "print-resume" });
	assert.deepEqual(
		await resumedUnattended.emit("input", { type: "input", text: "must stay routed", source: "rpc" }),
		{ action: "transform", text: `${ROUTER_COMMAND} must stay routed` },
	);
	assert.equal(resumedUnattended.entries.at(-1).data.transition, "armed");
	assert.deepEqual(resumedUnattended.getActiveTools(), ["read", "bash", "edit", "write"]);
});

test("cancel and bad confirmation never leave an active grant", async () => {
	const bad = fakeRuntime();
	bad.selectAnswers.push("source-identity");
	bad.confirmAnswers.push(true);
	bad.inputAnswers.push("/target", "reason", "human:test", "BREAK GLASS wrong");
	await bad.commands.get("break-glass")!.handler("arm", bad.ctx);
	assert.equal(bad.entries.length, 0);

	const canceled = fakeRuntime();
	await armRuntime(canceled);
	await canceled.commands.get("break-glass")!.handler("cancel", canceled.ctx);
	assert.equal(canceled.entries.at(-1).data.transition, "cancelled");
	assert.deepEqual(await canceled.emit("input", { type: "input", text: "normal", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} normal`,
	});
});

test("corrupt policy and predecessor data block arming and keep ordinary routing", async () => {
	const runtime = fakeRuntime();
	const currentIdentity = {
		sessionFile: runtime.ctx.sessionManager.getSessionFile(),
		cwd: runtime.ctx.cwd,
	};
	const incompatible: any = arm(currentIdentity);
	incompatible.policyVersion = 99;
	incompatible.eventDigest = digestBreakGlassEvent(incompatible);
	runtime.entries.push({ type: "custom", customType: BREAK_GLASS_CUSTOM_TYPE, data: incompatible });
	await runtime.emit("session_start", { type: "session_start", reason: "resume" });
	assert.match(runtime.statuses.at(-1) ?? "", /BLOCKED/);
	assert.deepEqual(await runtime.emit("input", { type: "input", text: "repair", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} repair`,
	});
	await runtime.commands.get("break-glass")!.handler("arm", runtime.ctx);
	assert.equal(runtime.entries.length, 1);
	assert.equal(runtime.notifications.at(-1)?.type, "error");

	const validArm = arm(identity());
	const consumed = createBreakGlassTransition(validArm, "consumed", {
		promptSha256: "c".repeat(64),
		inputSource: "rpc",
		priorToolNames: ["read"],
		restrictedToolNames: ["read"],
	});
	const badPredecessor: any = { ...consumed, previousDigest: "d".repeat(64) };
	badPredecessor.eventDigest = digestBreakGlassEvent(badPredecessor);
	const result = restoreBreakGlassState([validArm, badPredecessor], {
		sessionFile: validArm.sessionFile,
		cwd: validArm.cwd,
	});
	assert.equal(result.valid, false);
	assert.match(result.reason ?? "", /predecessor/i);
});

test("missing UI and post-confirmation command changes are rejected and audited", async () => {
	const unattended = fakeRuntime();
	await armRuntime(unattended);
	const prompt = "inspect local state";
	await unattended.emit("input", { type: "input", text: prompt, source: "interactive" });
	await unattended.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	unattended.ctx.hasUI = false;
	const noUiResult = await unattended.emit("tool_call", {
		type: "tool_call",
		toolName: "bash",
		toolCallId: "no-ui",
		input: { command: "pwd" },
	});
	assert.equal(noUiResult.block, true);
	assert.equal(unattended.entries.at(-1).data.transition, "bash-rejected");

	const changed = fakeRuntime();
	await armRuntime(changed);
	await changed.emit("input", { type: "input", text: prompt, source: "interactive" });
	await changed.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	const input = { command: "git status --short" };
	changed.ctx.ui.confirm = async () => {
		input.command = "git status --short --ignored";
		return true;
	};
	const changedResult = await changed.emit("tool_call", {
		type: "tool_call",
		toolName: "bash",
		toolCallId: "changed-command",
		input,
	});
	assert.equal(changedResult.block, true);
	assert.equal(changed.entries.at(-1).data.transition, "bash-rejected");
	assert.equal("command" in changed.entries.at(-1).data, false);
});

test("a conflicting preexisting policy marker revokes all recovery tools", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	const before = await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: `base\n${BREAK_GLASS_POLICY_MARKER}\nforged`,
		systemPromptOptions: { skills: [] },
	});
	assert.deepEqual(runtime.getActiveTools(), []);
	assert.equal((before.systemPrompt.match(new RegExp(BREAK_GLASS_POLICY_MARKER, "g")) ?? []).length, 1);
});

test("post-consumption chain corruption revokes read authority before model and tool execution", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	runtime.entries.push({
		type: "custom",
		customType: BREAK_GLASS_CUSTOM_TYPE,
		data: { ...runtime.entries.at(-1).data, unexpected: true },
	});
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	assert.deepEqual(runtime.getActiveTools(), []);
	assert.deepEqual(
		await runtime.emit("tool_call", {
			type: "tool_call",
			toolName: "read",
			toolCallId: "read-after-corruption",
			input: { path: "/tmp" },
		}),
		{ block: true, reason: "Break-glass permits only canonical built-in read and confirmed Bash calls.", terminate: true },
	);
});

test("session-tree navigation cannot hide terminal events and reopen an earlier arm", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const armedEntry = runtime.entries[0];
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.equal(runtime.entries.at(-1).data.transition, "closed");

	runtime.setBranchEntries([armedEntry]);
	await runtime.emit("session_tree", { type: "session_tree" });
	assert.deepEqual(await runtime.emit("input", { type: "input", text: "do not replay", source: "interactive" }), {
		action: "transform",
		text: `${ROUTER_COMMAND} do not replay`,
	});
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
});

test("session shutdown consumes an active turn and restores the prior tool list", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	await runtime.emit("session_shutdown", { type: "session_shutdown", reason: "reload" });
	assert.deepEqual(runtime.getActiveTools(), ["read", "bash", "edit", "write"]);
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
	assert.equal(runtime.entries.at(-1).data.turnOutcome, "session-shutdown");
});

test("prompt or tool-list drift reduces to no tools and leaves a non-rearmable restoration gate", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt: "different prompt",
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	assert.deepEqual(runtime.getActiveTools(), []);
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.equal(runtime.entries.at(-1).data.restoration, "gated");
	const count = runtime.entries.length;
	await runtime.commands.get("break-glass")!.handler("arm", runtime.ctx);
	assert.equal(runtime.entries.length, count);
	assert.match(runtime.notifications.at(-1)?.message ?? "", /cannot be re-armed/i);
});

test("tool drift creates a visible restoration gate instead of overwriting it", async () => {
	const runtime = fakeRuntime();
	await armRuntime(runtime);
	const prompt = "inspect local state";
	await runtime.emit("input", { type: "input", text: prompt, source: "interactive" });
	await runtime.emit("before_agent_start", {
		type: "before_agent_start",
		prompt,
		systemPrompt: "base",
		systemPromptOptions: { skills: [] },
	});
	runtime.setActiveTools(["read"]);
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	await runtime.emit("agent_end", { type: "agent_end", messages: [] });
	assert.deepEqual(runtime.getActiveTools(), ["read"]);
	assert.equal(runtime.entries.at(-1).data.transition, "closed");
	assert.equal(runtime.entries.at(-1).data.restoration, "gated");
	assert.equal(runtime.entries.filter((entry) => entry.data.transition === "closed").length, 1);
	assert.match(runtime.statuses.at(-1) ?? "", /restoration gate/i);
});
