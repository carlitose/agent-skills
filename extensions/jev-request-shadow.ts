/**
 * Shadow mode: ask Jev whether each user request is precise or vague and log the answer.
 * Off by default; it never changes the input, the prompt or the tools.
 */
import { execFileSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const ENDPOINT = "https://api.typesafe.ai/v1/systemone";
const ROUTER_PREFIX = "/skill:ask-skills ";
const CONTEXT_CHARS = 1500;
const REQUEST_CHARS = 4000;
const TIMEOUT_MS = 8000;
const PRECISE_AT = 0.4;
const USD_PER_INPUT_TOKEN = 0.042 / 1_000_000;
const QUESTIONS = {
	request_precise: {
		type: "noul",
		instructions:
			"Given the context, the request states the expected behavior precisely enough that it can be implemented " +
			"and checked without asking the user any question.",
	},
};

/** Pi's agent directory: PI_CODING_AGENT_DIR, else ~/.pi/agent (as Pi's getAgentDir). */
function defaultAgentDir(env: Record<string, string | undefined>): string {
	const dir = env.PI_CODING_AGENT_DIR;
	if (!dir) return join(homedir(), ".pi", "agent");
	return dir === "~" ? homedir() : dir.startsWith("~/") ? join(homedir(), dir.slice(2)) : dir;
}

export interface ShadowOptions {
	agentDir: string;
	env: Record<string, string | undefined>;
	platform: string;
	fetch: typeof fetch;
	now: () => number;
	/** Receives each background request; tests await them. */
	track: (pending: Promise<unknown>) => void;
}

/** The user request to judge, or undefined when the input is not a natural-language request. */
export function eligibleRequest(text: string, source: string): string | undefined {
	if (source === "extension") return undefined;
	const request = (text.startsWith(ROUTER_PREFIX) ? text.slice(ROUTER_PREFIX.length) : text).trim();
	if (!request || request.startsWith("/") || request.startsWith("!")) return undefined;
	return request;
}

function lastAssistantText(ctx: ExtensionContext): string {
	const branch = ctx.sessionManager.getBranch();
	for (let i = branch.length - 1; i >= 0; i--) {
		const entry = branch[i] as { type?: string; message?: { role?: string; content?: unknown } };
		if (entry.type !== "message" || entry.message?.role !== "assistant") continue;
		const content = entry.message.content;
		if (typeof content === "string") return content;
		if (!Array.isArray(content)) return "";
		return content
			.filter((part) => part && part.type === "text" && typeof part.text === "string")
			.map((part) => part.text)
			.join("\n");
	}
	return "";
}

export default function jevRequestShadow(pi: ExtensionAPI, overrides: Partial<ShadowOptions> = {}) {
	const options: ShadowOptions = {
		agentDir: overrides.agentDir ?? defaultAgentDir(process.env),
		env: overrides.env ?? process.env,
		platform: overrides.platform ?? process.platform,
		fetch: overrides.fetch ?? fetch,
		now: overrides.now ?? Date.now,
		track: overrides.track ?? (() => {}),
	};
	const dir = join(options.agentDir, "agent-skills");
	const stateFile = join(dir, "jev-request-shadow.json");
	const logFile = join(dir, "jev-request-shadow.jsonl");
	let cachedKey: string | undefined | null = null;

	function enabled(): boolean {
		try {
			return JSON.parse(readFileSync(stateFile, "utf8")).enabled === true;
		} catch {
			return false;
		}
	}

	function setEnabled(value: boolean): void {
		mkdirSync(dir, { recursive: true });
		writeFileSync(stateFile, `${JSON.stringify({ enabled: value })}\n`);
	}

	function apiKey(): string | undefined {
		if (cachedKey !== null) return cachedKey;
		cachedKey = options.env.TYPESAFE_API_KEY || undefined;
		if (!cachedKey && options.platform === "win32") {
			// A key set as a user variable after Pi started is not in Pi's environment.
			try {
				const out = execFileSync("reg", ["query", "HKCU\\Environment", "/v", "TYPESAFE_API_KEY"], {
					encoding: "utf8", timeout: 2000, windowsHide: true, stdio: ["ignore", "pipe", "ignore"],
				});
				cachedKey = /TYPESAFE_API_KEY\s+REG_\w+\s+(\S+)/.exec(out)?.[1];
			} catch {
				cachedKey = undefined;
			}
		}
		return cachedKey;
	}

	function record(line: Record<string, unknown>): void {
		try {
			mkdirSync(dir, { recursive: true });
			appendFileSync(logFile, `${JSON.stringify({ schema: 1, at: new Date(options.now()).toISOString(), ...line })}\n`);
		} catch {
			// Shadow mode must never reach the turn.
		}
	}

	async function judge(request: string, context: string, base: Record<string, unknown>, key: string): Promise<void> {
		const started = options.now();
		try {
			const response = await options.fetch(ENDPOINT, {
				method: "POST",
				headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
				body: JSON.stringify({ state: { context, request }, model: "jev-latest", questions: QUESTIONS }),
				signal: AbortSignal.timeout(TIMEOUT_MS),
			});
			if (!response.ok) {
				record({ ...base, error: `http ${response.status}`, ms: options.now() - started });
				return;
			}
			const result = (await response.json()) as {
				answers?: { request_precise?: { noul?: unknown } };
				usage?: { input_tokens?: unknown };
			};
			const noul = result.answers?.request_precise?.noul;
			if (typeof noul !== "number" || noul < 0 || noul > 1) {
				record({ ...base, error: "invalid", ms: options.now() - started });
				return;
			}
			const inputTokens = typeof result.usage?.input_tokens === "number" ? result.usage.input_tokens : null;
			record({ ...base, noul, verdict: noul >= PRECISE_AT ? "precise" : "vague", inputTokens, ms: options.now() - started });
		} catch (error) {
			const name = (error as { name?: string })?.name;
			record({ ...base, error: name === "TimeoutError" || name === "AbortError" ? "timeout" : "invalid", ms: options.now() - started });
		}
	}

	pi.on("input", (event, ctx) => {
		try {
			const request = eligibleRequest(event.text, event.source);
			if (request === undefined || !enabled()) return undefined;
			const key = apiKey();
			if (!key) return undefined;
			const text = request.slice(0, REQUEST_CHARS);
			const context = lastAssistantText(ctx).slice(-CONTEXT_CHARS);
			const base = {
				sessionId: ctx.sessionManager.getSessionId(),
				sessionFile: ctx.sessionManager.getSessionFile() ?? null,
				chars: text.length,
				contextChars: context.length,
			};
			options.track(judge(text, context, base, key));
		} catch {
			// Never block or change the input.
		}
		return undefined;
	});

	function report(): string {
		if (!existsSync(logFile)) return "Jev shadow log is empty.";
		const lines = readFileSync(logFile, "utf8").split("\n").filter(Boolean).map((line) => {
			try {
				return JSON.parse(line) as Record<string, unknown>;
			} catch {
				return {};
			}
		});
		const count = (verdict: string) => lines.filter((line) => line.verdict === verdict).length;
		const tokens = lines.reduce((sum, line) => sum + (typeof line.inputTokens === "number" ? line.inputTokens : 0), 0);
		const errors = lines.filter((line) => typeof line.error === "string").length;
		return `Jev shadow: ${lines.length} requests: ${count("precise")} precise, ${count("vague")} vague, ${errors} errors; ` +
			`${tokens} input tokens (about $${(tokens * USD_PER_INPUT_TOKEN).toFixed(4)}). Log: ${logFile}`;
	}

	pi.registerCommand("jev-shadow", {
		description: "Jev shadow mode: log whether each request is precise or vague (on | off | status | report)",
		handler: async (args, ctx) => {
			const action = args.trim() || "status";
			if (action === "on" || action === "off") setEnabled(action === "on");
			else if (action === "report") return void ctx.ui.notify(report(), "info");
			else if (action !== "status") return void ctx.ui.notify("Usage: /jev-shadow on | off | status | report", "error");
			const state = enabled() ? "on" : "off";
			const key = apiKey() ? "key found" : "no TYPESAFE_API_KEY, nothing is sent";
			ctx.ui.notify(`Jev shadow ${state}; ${key}. Each eligible request and the tail of the previous answer go to TypeSafe; the log keeps no text.`, "info");
		},
	});
}
