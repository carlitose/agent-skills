import { randomUUID } from "node:crypto";
import { realpathSync } from "node:fs";
import { isAbsolute } from "node:path";

import type { ExtensionAPI, ExtensionContext, ToolInfo } from "@earendil-works/pi-coding-agent";

import {
	BREAK_GLASS_CUSTOM_TYPE,
	BREAK_GLASS_TOOL_NAMES,
	appendBreakGlassPolicy,
	createArmedEvent,
	createBreakGlassTransition,
	isEligibleBreakGlassInput,
	restoreBreakGlassState,
	selectRecoveryTools,
	sha256,
	shortGrantId,
	type BreakGlassEventData,
	type BreakGlassIdentity,
	type BreakGlassRestoreResult,
	type BreakGlassTransitionDetails,
} from "./break-glass.ts";

export { BREAK_GLASS_POLICY_MARKER } from "./break-glass.ts";

export const ROUTER_COMMAND = "/skill:ask-skills";
export const POLICY_MARKER = "<mandatory-agent-skills-workflow>";
export const REQUIRED_SKILLS = [
	"ask-skills",
	"change-status-ticket",
	"to-spec",
	"to-tickets",
	"ticket-autopilot",
] as const;

const NORMAL_STATUS = "skills → disposition | spec → tickets → autopilot";
const BREAK_GLASS_STATUS_KEY = "mandatory-agent-skills";
const BLOCKED_TOOL_REASON =
	"Break-glass permits only canonical built-in read, bash, edit, and write.";

type InputSource = "interactive" | "rpc" | "extension";

export interface MandatoryAgentSkillsOptions {
	now?: () => number;
	createGrantId?: () => string;
}

interface ActiveRecoveryTurn {
	consumed: BreakGlassEventData;
	actualToolNames: string[];
	toolsApplied: boolean;
	restorationBlocked: boolean;
	closing: boolean;
}

/** Return a routed prompt, or undefined when Pi must handle the input as a command. */
export function routeNaturalLanguageInput(text: string, source: InputSource): string | undefined {
	const trimmed = text.trim();
	if (source === "extension" || trimmed === "" || trimmed.startsWith("/") || trimmed.startsWith("!")) {
		return undefined;
	}

	return `${ROUTER_COMMAND} ${text}`;
}

export function buildMandatoryWorkflowPolicy(availableSkillNames: readonly string[]): string {
	const available = new Set(availableSkillNames);
	const missing = REQUIRED_SKILLS.filter((name) => !available.has(name));
	const readiness =
		missing.length === 0
			? "Required workflow skills are loaded."
			: `FAIL CLOSED: required workflow skills are missing: ${missing.join(", ")}. Do not mutate the repository; report the missing skills and ask the user to restore the package.`;

	return `${POLICY_MARKER}
## Mandatory agent-skills workflow

This package policy has priority over default skill auto-selection and applies to every agent turn.

1. **Route first.** Treat every natural-language request as an \`ask-skills\` routing request. Before substantive work, state the selected skill or smallest composition and load its \`SKILL.md\`. If no skill applies, say so briefly and handle the request normally.
2. **Use the delivery lane.** Any request whose intended outcome is a shippable implementation, fix, refactor, or change to code, tests, configuration, documentation, dependencies, or generated assets must follow \`to-spec -> to-tickets -> ticket-autopilot\`. Do not edit the deliverable directly from the loose request.
3. **Use the named lifecycle-only lane.** Only an explicit request to hold, cancel, reopen, or set one exact ticket's administrative disposition to \`open\`, \`on-hold\`, or \`canceled\` routes to \`change-status-ticket\`. This is the sole lifecycle-only exception to the delivery lane: it composes the repository transaction without \`execute-ticket\` stages. Bare ticket paths, implementation/completion requests, run pause/unpause, blocked/stopped/waiting/gated/readiness states, and lifecycle questions do not use it.
4. **Honor affirmative repository-wide merge intent.** An unambiguous affirmative “merge all”, “merge everything”, or “mergia tutto” for one known repository routes to \`ticket-autopilot\`. Inspect \`repository-autonomous-merge-status\`: if authority is absent, use the human actor and durable affirmative message to invoke \`grant-repository-autonomous-merge --scope current-and-future-runs\`; preserve an exact active grant instead of replacing its provenance; fail closed on revoked, legacy, malformed, or contradictory state. Then invoke \`merge-all\`. Never ask for a caller-supplied PR head SHA or narrow the instruction to one displayed PR; the runner discovers and revalidates each live exact head. If repository identity is ambiguous, ask only for that identity. Quoted text, examples, questions, negations, revocations, policy requests, and regression reports are not merge authority and cause no provider mutation.
5. **Reuse only validated artifacts.** Existing specs or canonical ticket artifacts may satisfy their owning stage, but the owning skill must validate them before the next stage. Never silently skip a stage or regenerate a valid artifact merely to appear compliant.
6. **Keep ownership deep.** \`ticket-autopilot\` owns scheduling and composes \`execute-ticket\`, review, QA, verification, PR explanation, and delivery. Do not invoke those leaves directly for a loose delivery request.
7. **Keep non-delivery work minimal.** Read-only research, diagnosis, review, QA planning, architecture discovery, peer programming, grilling, and throwaway prototypes use the smallest route selected by \`ask-skills\`. A prototype cannot be promoted to production outside the delivery lane.
8. **Preserve human authority.** Mandatory workflow is not merge consent. Keep \`ticket-autopilot\` on its manual merge policy unless the user supplies the explicit durable authorization required by that skill. Never manufacture approval, credentials, provider evidence, or verification evidence.
9. **Fail closed.** If a required skill or required canonical input is unavailable, stop before repository mutation and report the exact missing input.
10. **Refresh local Pi only after integration.** When an \`agent-skills\` ticket is durably \`integrated\` and an actor/evidence-bound local-sync configuration exists, run Ticket Autopilot's \`sync-local-pi\` command for that exact integrated head. Never trigger it from implementation, verification, PR-open, or a merge attempt. A sync failure is a visible post-integration local gate; it does not rewrite Git integration. Never infer this authority, update the Pi binary, or claim an active session reloaded; report that \`/reload\` is required.

Routing is complete only after a skill/composition (or no applicable skill) is explicit. Delivery is complete only at the state allowed by \`ticket-autopilot\`; an open gate is a valid stop, not permission to bypass it.

${readiness}
${POLICY_MARKER}`;
}

export function appendMandatoryWorkflowPolicy(basePrompt: string, availableSkillNames: readonly string[]): string {
	if (basePrompt.includes(POLICY_MARKER)) return basePrompt;
	return `${basePrompt}\n\n${buildMandatoryWorkflowPolicy(availableSkillNames)}`;
}

function sameNames(left: readonly string[], right: readonly string[]): boolean {
	return left.length === right.length && left.every((name, index) => name === right[index]);
}

function bounded(value: string, limit = 160): string {
	return value.length <= limit ? value : `${value.slice(0, limit - 1)}…`;
}

function sessionIdentity(ctx: ExtensionContext): BreakGlassIdentity | undefined {
	const sessionFile = ctx.sessionManager.getSessionFile();
	if (!sessionFile || !isAbsolute(sessionFile)) return undefined;
	try {
		return {
			sessionFile: realpathSync(sessionFile),
			cwd: realpathSync(ctx.cwd),
		};
	} catch {
		return undefined;
	}
}

function breakGlassPayloads(ctx: ExtensionContext): unknown[] {
	return ctx.sessionManager
		.getEntries()
		.filter(
			(entry): entry is typeof entry & { type: "custom"; customType: string; data?: unknown } =>
				entry.type === "custom" && entry.customType === BREAK_GLASS_CUSTOM_TYPE,
		)
		.map((entry) => entry.data);
}

function consumedEvent(state: BreakGlassRestoreResult): BreakGlassEventData | undefined {
	if (!state.latest) return undefined;
	return [...state.events]
		.reverse()
		.find((event) => event.grantId === state.latest!.grantId && event.transition === "consumed");
}

function currentState(ctx: ExtensionContext, now: number): {
	identity?: BreakGlassIdentity;
	state: BreakGlassRestoreResult;
} {
	const identity = sessionIdentity(ctx);
	const payloads = breakGlassPayloads(ctx);
	if (!identity) {
		return {
			state:
				payloads.length === 0
					? { valid: true, phase: "inactive", events: [], expired: false }
					: {
							valid: false,
							phase: "inactive",
							events: [],
							expired: false,
							reason: "durable canonical session identity is unavailable",
						},
		};
	}
	return { identity, state: restoreBreakGlassState(payloads, identity, now) };
}

function statusText(state: BreakGlassRestoreResult): string {
	if (!state.valid) return `BREAK GLASS BLOCKED · ${bounded(state.reason ?? "invalid session state", 96)}`;
	const latest = state.latest;
	if (state.phase === "armed" && latest) {
		return `BREAK GLASS · ${shortGrantId(latest.grantId)} · next prompt`;
	}
	if (state.phase === "consumed" && latest) {
		return `BREAK GLASS ACTIVE · ${shortGrantId(latest.grantId)}`;
	}
	if (state.phase === "closed" && latest?.restoration === "gated") {
		return `${NORMAL_STATUS} · tool restoration gate`;
	}
	return NORMAL_STATUS;
}

function updateStatus(ctx: ExtensionContext, state: BreakGlassRestoreResult): void {
	ctx.ui.setStatus(BREAK_GLASS_STATUS_KEY, statusText(state));
}

function statusMessage(state: BreakGlassRestoreResult): { message: string; type: "info" | "warning" | "error" } {
	if (!state.valid) {
		return { message: `Break-glass blocked: ${state.reason ?? "invalid session state"}`, type: "error" };
	}
	const latest = state.latest;
	if (state.phase === "armed" && latest) {
		return {
			message: `Break-glass armed (${shortGrantId(latest.grantId)}). The next ordinary-language prompt is the one-turn local repair scope.`,
			type: "warning",
		};
	}
	if (state.phase === "consumed" && latest) {
		return { message: `Break-glass recovery turn is active (${shortGrantId(latest.grantId)}).`, type: "warning" };
	}
	if (state.phase === "closed" && latest?.restoration === "gated") {
		return { message: "Break-glass is closed, but exact tool restoration could not be proven.", type: "error" };
	}
	return { message: `Break-glass is ${state.phase}. Ordinary mandatory routing is active.`, type: "info" };
}

function canonicalRecoveryToolAvailable(name: string, tools: readonly ToolInfo[]): boolean {
	return selectRecoveryTools(tools).toolNames.includes(name);
}

function matchesConsumedGrant(
	ctx: ExtensionContext,
	turn: ActiveRecoveryTurn,
	now: number,
): boolean {
	const snapshot = currentState(ctx, now);
	if (
		!snapshot.identity ||
		!snapshot.state.valid ||
		snapshot.state.phase !== "consumed" ||
		snapshot.state.latest?.grantId !== turn.consumed.grantId
	) {
		return false;
	}
	return consumedEvent(snapshot.state)?.eventDigest === turn.consumed.eventDigest;
}

export default function mandatoryAgentSkills(pi: ExtensionAPI, options: MandatoryAgentSkillsOptions = {}) {
	const now = options.now ?? Date.now;
	const createGrantId = options.createGrantId ?? randomUUID;
	let activeTurn: ActiveRecoveryTurn | undefined;
	let transitionQueue: Promise<void> = Promise.resolve();

	function serialize<T>(operation: () => T | Promise<T>): Promise<T> {
		const result = transitionQueue.then(operation, operation);
		transitionQueue = result.then(
			() => undefined,
			() => undefined,
		);
		return result;
	}

	function append(event: BreakGlassEventData): BreakGlassEventData {
		pi.appendEntry(BREAK_GLASS_CUSTOM_TYPE, event);
		return event;
	}

	function revokeTurnTools(turn: ActiveRecoveryTurn): void {
		turn.restorationBlocked = true;
		try {
			pi.setActiveTools([]);
			turn.actualToolNames = [];
			turn.toolsApplied = sameNames(pi.getActiveTools(), []);
		} catch {
			turn.actualToolNames = [];
			turn.toolsApplied = false;
		}
	}

	async function refresh(ctx: ExtensionContext): Promise<ReturnType<typeof currentState>> {
		return serialize(() => {
			let snapshot = currentState(ctx, now());
			if (snapshot.state.valid && snapshot.state.phase === "armed" && snapshot.state.expired) {
				append(createBreakGlassTransition(snapshot.state.latest!, "expired", {}, now()));
				snapshot = currentState(ctx, now());
			}
			return snapshot;
		});
	}

	async function appendTransition(
		ctx: ExtensionContext,
		grantId: string,
		transition: Exclude<BreakGlassEventData["transition"], "armed">,
		details: BreakGlassTransitionDetails,
	): Promise<BreakGlassEventData> {
		return serialize(() => {
			const snapshot = currentState(ctx, now());
			if (!snapshot.state.valid || !snapshot.state.latest) {
				throw new Error(snapshot.state.reason ?? "break-glass state is unavailable");
			}
			if (snapshot.state.latest.grantId !== grantId) throw new Error("break-glass grant identity changed");
			return append(createBreakGlassTransition(snapshot.state.latest, transition, details, now()));
		});
	}

	async function restoreTools(turn: ActiveRecoveryTurn): Promise<"restored" | "already-restored" | "gated"> {
		if (turn.restorationBlocked) return "gated";
		const prior = turn.consumed.priorToolNames ?? [];
		const current = pi.getActiveTools();
		if (sameNames(current, prior)) return "already-restored";
		if (!turn.toolsApplied || !sameNames(current, turn.actualToolNames)) return "gated";
		try {
			pi.setActiveTools(prior);
			return sameNames(pi.getActiveTools(), prior) ? "restored" : "gated";
		} catch {
			return "gated";
		}
	}

	async function closeTurn(
		ctx: ExtensionContext,
		turnOutcome: "agent-end" | "session-shutdown" | "interrupted-session-restore",
	): Promise<void> {
		const turn = activeTurn;
		if (!turn || turn.closing) return;
		turn.closing = true;
		const restoration = await restoreTools(turn);
		try {
			await appendTransition(ctx, turn.consumed.grantId, "closed", { turnOutcome, restoration });
		} catch (error) {
			ctx.ui.notify(`Break-glass closure could not be persisted: ${bounded(String(error))}`, "error");
		}
		activeTurn = undefined;
		const snapshot = currentState(ctx, now()).state;
		updateStatus(ctx, snapshot);
		if (restoration === "gated") {
			ctx.ui.notify("Break-glass closed with a tool restoration gate; no prior tool configuration was asserted.", "error");
		}
	}

	async function recoverInterruptedTurn(ctx: ExtensionContext, state: BreakGlassRestoreResult): Promise<void> {
		const consumed = consumedEvent(state);
		if (!consumed) return;
		activeTurn = {
			consumed,
			actualToolNames: [...(consumed.restrictedToolNames ?? [])],
			toolsApplied: sameNames(pi.getActiveTools(), consumed.restrictedToolNames ?? []),
			restorationBlocked: false,
			closing: false,
		};
		await closeTurn(ctx, "interrupted-session-restore");
	}

	async function restoreSession(ctx: ExtensionContext): Promise<void> {
		activeTurn = undefined;
		const snapshot = await refresh(ctx);
		if (snapshot.state.valid && snapshot.state.phase === "consumed") {
			await recoverInterruptedTurn(ctx, snapshot.state);
			return;
		}
		updateStatus(ctx, snapshot.state);
	}

	pi.on("input", async (event, ctx) => {
		const snapshot = await refresh(ctx);
		if (
			snapshot.identity &&
			snapshot.state.valid &&
			snapshot.state.phase === "armed" &&
			isEligibleBreakGlassInput(event.text, event.source, event.streamingBehavior)
		) {
			const priorToolNames = pi.getActiveTools();
			const selection = selectRecoveryTools(pi.getAllTools());
			const consumed = await appendTransition(ctx, snapshot.state.latest!.grantId, "consumed", {
				promptSha256: sha256(event.text),
				inputSource: event.source as "interactive" | "rpc",
				priorToolNames,
				restrictedToolNames: selection.toolNames,
			});
			const turn: ActiveRecoveryTurn = {
				consumed,
				actualToolNames: [],
				toolsApplied: false,
				restorationBlocked: false,
				closing: false,
			};
			activeTurn = turn;
			try {
				pi.setActiveTools(selection.toolNames);
				turn.actualToolNames = [...selection.toolNames];
				turn.toolsApplied = sameNames(pi.getActiveTools(), selection.toolNames);
			} catch {
				turn.toolsApplied = false;
			}
			if (!turn.toolsApplied) {
				turn.restorationBlocked = true;
				try {
					pi.setActiveTools([]);
					turn.actualToolNames = [];
					turn.toolsApplied = sameNames(pi.getActiveTools(), []);
				} catch {
					turn.toolsApplied = false;
				}
			}
			const omittedTools = BREAK_GLASS_TOOL_NAMES.filter(
				(name) => !selection.toolNames.includes(name),
			);
			if (omittedTools.length > 0) {
				const message = `Break-glass omitted unavailable or ambiguous canonical tools: ${omittedTools.join(", ")}.`;
				ctx.ui.notify(
					selection.toolNames.includes("read")
						? message
						: `${message} Canonical read is required, so no repair tools were exposed.`,
					selection.toolNames.includes("read") ? "warning" : "error",
				);
			}
			updateStatus(ctx, currentState(ctx, now()).state);
			return { action: "continue" } as const;
		}

		const routed = routeNaturalLanguageInput(event.text, event.source);
		if (routed === undefined) return { action: "continue" } as const;
		return { action: "transform", text: routed } as const;
	});

	pi.on("before_agent_start", (event, ctx) => {
		const skillNames = event.systemPromptOptions.skills?.map((skill) => skill.name) ?? [];
		let systemPrompt = appendMandatoryWorkflowPolicy(event.systemPrompt, skillNames);
		const turn = activeTurn;
		if (!turn) return { systemPrompt };

		const current = pi.getActiveTools();
		const selection = selectRecoveryTools(pi.getAllTools());
		const exact =
			turn.toolsApplied &&
			matchesConsumedGrant(ctx, turn, now()) &&
			sha256(event.prompt) === turn.consumed.promptSha256 &&
			sameNames(current, turn.actualToolNames) &&
			sameNames(selection.toolNames, turn.actualToolNames);
		if (!exact) revokeTurnTools(turn);

		try {
			systemPrompt = appendBreakGlassPolicy(systemPrompt, turn.consumed);
		} catch {
			revokeTurnTools(turn);
		}
		return { systemPrompt };
	});

	pi.on("tool_call", async (event, ctx) => {
		const turn = activeTurn;
		if (!turn) return undefined;
		if (turn.closing || !turn.actualToolNames.includes(event.toolName)) {
			return { block: true, reason: BLOCKED_TOOL_REASON, terminate: true };
		}
		if (
			!matchesConsumedGrant(ctx, turn, now()) ||
			!sameNames(pi.getActiveTools(), turn.actualToolNames) ||
			!canonicalRecoveryToolAvailable(event.toolName, pi.getAllTools())
		) {
			revokeTurnTools(turn);
			return { block: true, reason: BLOCKED_TOOL_REASON, terminate: true };
		}
		return undefined;
	});

	pi.on("agent_end", async (_event, ctx) => closeTurn(ctx, "agent-end"));

	pi.on("session_start", async (_event, ctx) => restoreSession(ctx));
	pi.on("session_tree", async (_event, ctx) => restoreSession(ctx));

	pi.on("session_shutdown", async (_event, ctx) => {
		if (activeTurn) await closeTurn(ctx, "session-shutdown");
		ctx.ui.setStatus(BREAK_GLASS_STATUS_KEY, undefined);
	});

	pi.registerCommand("agent-skills-flow", {
		description: "Show mandatory agent-skills workflow status",
		handler: async (_args, ctx) => {
			const skillNames = new Set(
				pi
					.getCommands()
					.filter((command) => command.source === "skill")
					.map((command) => command.name.replace(/^skill:/, "")),
			);
			const missing = REQUIRED_SKILLS.filter((name) => !skillNames.has(name));
			const message =
				missing.length === 0
					? "Mandatory flow active: ask-skills → change-status-ticket | to-spec → to-tickets → ticket-autopilot"
					: `Mandatory flow blocked; missing skills: ${missing.join(", ")}`;
			ctx.ui.notify(message, missing.length === 0 ? "info" : "error");
		},
	});

	pi.registerCommand("break-glass", {
		description: "Arm one natural-language local repair turn, or inspect/cancel it",
		handler: async (args, ctx) => {
			const action = args.trim() || "arm";
			if (action !== "status" && action !== "arm" && action !== "cancel") {
				ctx.ui.notify("Usage: /break-glass [status|cancel]", "error");
				return;
			}
			const snapshot = await refresh(ctx);
			if (action === "status") {
				const status = statusMessage(snapshot.state);
				ctx.ui.notify(status.message, status.type);
				updateStatus(ctx, snapshot.state);
				return;
			}
			if (!snapshot.state.valid) {
				ctx.ui.notify(`Break-glass blocked: ${snapshot.state.reason}`, "error");
				updateStatus(ctx, snapshot.state);
				return;
			}
			if (action === "cancel") {
				if (snapshot.state.phase !== "armed" || !snapshot.state.latest) {
					ctx.ui.notify("No armed break-glass grant to cancel.", "info");
					return;
				}
				await appendTransition(ctx, snapshot.state.latest.grantId, "cancelled", {});
				const state = currentState(ctx, now()).state;
				updateStatus(ctx, state);
				ctx.ui.notify("Break-glass canceled. Ordinary mandatory routing remains active.", "info");
				return;
			}
			if (!snapshot.identity) {
				ctx.ui.notify("Break-glass requires a durable canonical session file and working directory.", "error");
				return;
			}
			if (snapshot.state.phase === "armed" || snapshot.state.phase === "consumed") {
				ctx.ui.notify("Break-glass is already active; cancel or consume it first.", "error");
				return;
			}
			if (
				snapshot.state.latest?.transition === "closed" &&
				snapshot.state.latest.restoration === "gated"
			) {
				ctx.ui.notify(
					"Break-glass cannot be re-armed while the exact tool-restoration gate is unresolved.",
					"error",
				);
				return;
			}

			const grantId = createGrantId();
			await serialize(() => {
				const latest = currentState(ctx, now());
				if (!latest.state.valid || latest.state.phase === "armed" || latest.state.phase === "consumed") {
					throw new Error(latest.state.reason ?? "another break-glass grant became active");
				}
				if (
					latest.state.latest?.transition === "closed" &&
					latest.state.latest.restoration === "gated"
				) {
					throw new Error("the exact tool-restoration gate became unresolved while arming");
				}
				if (
					!latest.identity ||
					latest.identity.sessionFile !== snapshot.identity!.sessionFile ||
					latest.identity.cwd !== snapshot.identity!.cwd
				) {
					throw new Error("session identity changed while arming break-glass");
				}
				append(
					createArmedEvent({
						identity: latest.identity,
						grantId,
						now: now(),
						previous: latest.state.latest,
					}),
				);
			});
			const state = currentState(ctx, now()).state;
			updateStatus(ctx, state);
			ctx.ui.notify(
				`BREAK GLASS armed (${shortGrantId(grantId)}). Write the local repair normally; the next ordinary-language prompt is the complete one-turn scope.`,
				"warning",
			);
		},
	});
}
