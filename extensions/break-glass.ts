import { createHash } from "node:crypto";

export const BREAK_GLASS_LEGACY_CUSTOM_TYPE = "agent-skills-break-glass-v1";
export const BREAK_GLASS_CUSTOM_TYPE = "agent-skills-break-glass-v2";
export const BREAK_GLASS_POLICY_MARKER = "<agent-skills-break-glass-v2>";
export const BREAK_GLASS_SCHEMA = 1 as const;
export const BREAK_GLASS_POLICY_VERSION = 2 as const;
export const BREAK_GLASS_TTL_MS = 15 * 60 * 1000;
export const BREAK_GLASS_TOOL_NAMES = ["read", "bash", "edit", "write"] as const;

export type BreakGlassToolName = (typeof BREAK_GLASS_TOOL_NAMES)[number];
export type BreakGlassTransition = "armed" | "expired" | "cancelled" | "consumed" | "closed";
export type BreakGlassPhase = "inactive" | "armed" | "consumed" | "expired" | "cancelled" | "closed";

export interface BreakGlassIdentity {
	sessionFile: string;
	cwd: string;
}

export interface BreakGlassEventData {
	schema: typeof BREAK_GLASS_SCHEMA;
	policyVersion: typeof BREAK_GLASS_POLICY_VERSION;
	grantId: string;
	sequence: number;
	previousDigest: string | null;
	eventDigest: string;
	transition: BreakGlassTransition;
	sessionFile: string;
	cwd: string;
	createdAt: string;
	expiresAt: string;
	recordedAt: string;
	promptSha256?: string;
	inputSource?: "interactive" | "rpc";
	priorToolNames?: string[];
	restrictedToolNames?: string[];
	turnOutcome?: "agent-end" | "session-shutdown" | "interrupted-session-restore";
	restoration?: "restored" | "already-restored" | "gated";
}

export type BreakGlassTransitionDetails =
	| {
			promptSha256: string;
			inputSource: "interactive" | "rpc";
			priorToolNames: string[];
			restrictedToolNames: string[];
	  }
	| {
			turnOutcome: "agent-end" | "session-shutdown" | "interrupted-session-restore";
			restoration: "restored" | "already-restored" | "gated";
	  }
	| Record<string, never>;

export interface BreakGlassRestoreResult {
	valid: boolean;
	phase: BreakGlassPhase;
	latest?: BreakGlassEventData;
	events: BreakGlassEventData[];
	reason?: string;
	expired: boolean;
}

export interface ToolDescriptor {
	name: string;
	sourceInfo: {
		path: string;
		source: string;
		scope: string;
		origin: string;
		baseDir?: string;
	};
}

const BASE_KEYS = [
	"createdAt",
	"cwd",
	"eventDigest",
	"expiresAt",
	"grantId",
	"policyVersion",
	"previousDigest",
	"recordedAt",
	"schema",
	"sequence",
	"sessionFile",
	"transition",
] as const;

const EXTRA_KEYS: Record<BreakGlassTransition, readonly string[]> = {
	armed: [],
	expired: [],
	cancelled: [],
	consumed: ["inputSource", "priorToolNames", "promptSha256", "restrictedToolNames"],
	closed: ["restoration", "turnOutcome"],
};

const TERMINAL_TRANSITIONS = new Set<BreakGlassTransition>(["expired", "cancelled", "closed"]);
const HEX_SHA256 = /^[0-9a-f]{64}$/;

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sortCanonical(value: unknown): unknown {
	if (value === null || typeof value === "string" || typeof value === "boolean") return value;
	if (typeof value === "number") {
		if (!Number.isFinite(value)) throw new TypeError("canonical JSON does not support non-finite numbers");
		return value;
	}
	if (Array.isArray(value)) return value.map(sortCanonical);
	if (isRecord(value)) {
		const sorted: Record<string, unknown> = {};
		for (const key of Object.keys(value).sort()) {
			if (value[key] === undefined) {
				throw new TypeError("canonical JSON does not support undefined values");
			}
			sorted[key] = sortCanonical(value[key]);
		}
		return sorted;
	}
	throw new TypeError(`canonical JSON does not support ${typeof value}`);
}

export function canonicalJson(value: unknown): string {
	return JSON.stringify(sortCanonical(value));
}

export function sha256(value: string): string {
	return createHash("sha256").update(value, "utf8").digest("hex");
}

export function digestBreakGlassEvent(event: BreakGlassEventData): string {
	const { eventDigest: _eventDigest, ...payload } = event;
	return sha256(canonicalJson(payload));
}

function withDigest(event: Omit<BreakGlassEventData, "eventDigest">): BreakGlassEventData {
	const pending = { ...event, eventDigest: "" } as BreakGlassEventData;
	return { ...pending, eventDigest: digestBreakGlassEvent(pending) };
}

function isoTime(value: number): string {
	if (!Number.isFinite(value)) throw new TypeError("break-glass time must be finite");
	return new Date(value).toISOString();
}

function isExactText(value: unknown): value is string {
	return (
		typeof value === "string" &&
		value !== "" &&
		value.length <= 4096 &&
		value.trim() === value &&
		!/[\u0000-\u001f\u007f]/u.test(value)
	);
}

function requireExactText(name: string, value: string): void {
	if (!isExactText(value)) {
		throw new TypeError(
			`${name} must be bounded, non-empty exact single-line text without surrounding whitespace`,
		);
	}
}

export function shortGrantId(grantId: string): string {
	return grantId.replace(/[^A-Za-z0-9]/g, "").slice(0, 8);
}

export function createArmedEvent(options: {
	identity: BreakGlassIdentity;
	grantId: string;
	now: number;
	previous?: BreakGlassEventData;
}): BreakGlassEventData {
	const { identity, grantId, now, previous } = options;
	requireExactText("session file", identity.sessionFile);
	requireExactText("cwd", identity.cwd);
	requireExactText("grant id", grantId);
	if (previous && !TERMINAL_TRANSITIONS.has(previous.transition)) {
		throw new TypeError("cannot arm while a break-glass grant is active");
	}
	if (previous?.grantId === grantId) throw new TypeError("grant id cannot be reused");
	if (previous && now < Date.parse(previous.recordedAt)) {
		throw new TypeError("new grant cannot predate the previous break-glass event");
	}

	const createdAt = isoTime(now);
	return withDigest({
		schema: BREAK_GLASS_SCHEMA,
		policyVersion: BREAK_GLASS_POLICY_VERSION,
		grantId,
		sequence: previous ? previous.sequence + 1 : 1,
		previousDigest: previous?.eventDigest ?? null,
		transition: "armed",
		sessionFile: identity.sessionFile,
		cwd: identity.cwd,
		createdAt,
		expiresAt: isoTime(now + BREAK_GLASS_TTL_MS),
		recordedAt: createdAt,
	});
}

function transitionAllowed(previous: BreakGlassTransition, next: BreakGlassTransition): boolean {
	if (previous === "armed") return next === "expired" || next === "cancelled" || next === "consumed";
	if (previous === "consumed") return next === "closed";
	return false;
}

export function createBreakGlassTransition(
	previous: BreakGlassEventData,
	transition: Exclude<BreakGlassTransition, "armed">,
	details: BreakGlassTransitionDetails = {},
	now = Date.parse(previous.recordedAt),
): BreakGlassEventData {
	if (!transitionAllowed(previous.transition, transition)) {
		throw new TypeError(`invalid break-glass transition: ${previous.transition} -> ${transition}`);
	}
	if (now < Date.parse(previous.recordedAt)) {
		throw new TypeError("break-glass transition cannot predate its predecessor");
	}
	if (transition === "consumed" && now >= Date.parse(previous.expiresAt)) {
		throw new TypeError("expired break-glass grant cannot be consumed");
	}
	if (transition === "expired" && now < Date.parse(previous.expiresAt)) {
		throw new TypeError("break-glass grant cannot expire early");
	}
	const common = {
		schema: BREAK_GLASS_SCHEMA,
		policyVersion: BREAK_GLASS_POLICY_VERSION,
		grantId: previous.grantId,
		sequence: previous.sequence + 1,
		previousDigest: previous.eventDigest,
		transition,
		sessionFile: previous.sessionFile,
		cwd: previous.cwd,
		createdAt: previous.createdAt,
		expiresAt: previous.expiresAt,
		recordedAt: isoTime(now),
	};

	let event: BreakGlassEventData;
	if (transition === "consumed") {
		const value = details as Extract<BreakGlassTransitionDetails, { promptSha256: string }>;
		event = withDigest({ ...common, transition, ...value });
	} else if (transition === "closed") {
		const value = details as Extract<BreakGlassTransitionDetails, { turnOutcome: string }>;
		event = withDigest({ ...common, transition, ...value });
	} else {
		event = withDigest({ ...common, transition });
	}
	const shapeError = validateShape(event);
	if (shapeError) throw new TypeError(`invalid break-glass ${transition} event: ${shapeError}`);
	return event;
}

function validIso(value: unknown): value is string {
	if (typeof value !== "string") return false;
	const millis = Date.parse(value);
	return Number.isFinite(millis) && new Date(millis).toISOString() === value;
}

function validToolNames(value: unknown): value is string[] {
	return Array.isArray(value) && value.every(isExactText) && new Set(value).size === value.length;
}

function validRestrictedTools(value: unknown): value is string[] {
	if (!validToolNames(value)) return false;
	const expected = BREAK_GLASS_TOOL_NAMES.filter((name) => value.includes(name));
	if (expected.length !== value.length || expected.some((name, index) => name !== value[index])) {
		return false;
	}
	return value.length === 0 || value[0] === "read";
}

function validateShape(value: unknown): string | undefined {
	if (!isRecord(value)) return "entry payload is not an object";
	if (typeof value.transition !== "string" || !Object.hasOwn(EXTRA_KEYS, value.transition)) {
		return "unknown transition";
	}
	const transition = value.transition as BreakGlassTransition;
	const expectedKeys = [...BASE_KEYS, ...EXTRA_KEYS[transition]].sort();
	const actualKeys = Object.keys(value).sort();
	if (canonicalJson(expectedKeys) !== canonicalJson(actualKeys)) {
		return `unexpected fields for ${transition}`;
	}
	if (value.schema !== BREAK_GLASS_SCHEMA || value.policyVersion !== BREAK_GLASS_POLICY_VERSION) {
		return "incompatible schema or policy version";
	}
	if (
		!Number.isInteger(value.sequence) ||
		(value.sequence as number) < 1 ||
		(value.previousDigest !== null &&
			(typeof value.previousDigest !== "string" || !HEX_SHA256.test(value.previousDigest))) ||
		typeof value.eventDigest !== "string" ||
		!HEX_SHA256.test(value.eventDigest) ||
		!isExactText(value.grantId) ||
		!isExactText(value.sessionFile) ||
		!isExactText(value.cwd) ||
		!validIso(value.createdAt) ||
		!validIso(value.expiresAt) ||
		!validIso(value.recordedAt)
	) {
		return "invalid identity or timestamp field";
	}
	if (Date.parse(value.expiresAt) - Date.parse(value.createdAt) !== BREAK_GLASS_TTL_MS) {
		return "grant expiry is not exactly 15 minutes";
	}
	if (Date.parse(value.recordedAt) < Date.parse(value.createdAt)) {
		return "transition predates grant creation";
	}
	if (transition === "consumed" && Date.parse(value.recordedAt) >= Date.parse(value.expiresAt)) {
		return "expired grant was consumed";
	}
	if (transition === "expired" && Date.parse(value.recordedAt) < Date.parse(value.expiresAt)) {
		return "grant expired before its deadline";
	}
	if (transition === "consumed") {
		if (
			typeof value.promptSha256 !== "string" ||
			!HEX_SHA256.test(value.promptSha256) ||
			(value.inputSource !== "interactive" && value.inputSource !== "rpc") ||
			!validToolNames(value.priorToolNames) ||
			!validRestrictedTools(value.restrictedToolNames)
		) {
			return "invalid consumption evidence";
		}
	}
	if (transition === "closed") {
		if (
			!(
				["agent-end", "session-shutdown", "interrupted-session-restore"] as unknown[]
			).includes(value.turnOutcome) ||
			!(["restored", "already-restored", "gated"] as unknown[]).includes(value.restoration)
		) {
			return "invalid closure evidence";
		}
	}
	return undefined;
}

function sameGrantIdentity(first: BreakGlassEventData, event: BreakGlassEventData): boolean {
	return (
		first.sessionFile === event.sessionFile &&
		first.cwd === event.cwd &&
		first.createdAt === event.createdAt &&
		first.expiresAt === event.expiresAt
	);
}

function phaseFor(transition: BreakGlassTransition | undefined): BreakGlassPhase {
	return transition ?? "inactive";
}

export function restoreBreakGlassState(
	payloads: readonly unknown[],
	identity: BreakGlassIdentity,
	now = Date.now(),
): BreakGlassRestoreResult {
	const events: BreakGlassEventData[] = [];
	let previous: BreakGlassEventData | undefined;
	let grantFirst: BreakGlassEventData | undefined;
	const seenGrantIds = new Set<string>();

	for (const payload of payloads) {
		const shapeError = validateShape(payload);
		if (shapeError) {
			return { valid: false, phase: "inactive", events, reason: shapeError, expired: false };
		}
		const event = payload as unknown as BreakGlassEventData;
		if (digestBreakGlassEvent(event) !== event.eventDigest) {
			return {
				valid: false,
				phase: "inactive",
				events,
				reason: "event digest disagreement",
				expired: false,
			};
		}
		if (event.sequence !== (previous?.sequence ?? 0) + 1) {
			return {
				valid: false,
				phase: "inactive",
				events,
				reason: "duplicate or non-monotonic sequence",
				expired: false,
			};
		}
		if (event.previousDigest !== (previous?.eventDigest ?? null)) {
			return {
				valid: false,
				phase: "inactive",
				events,
				reason: "missing or contradictory predecessor digest",
				expired: false,
			};
		}
		if (previous && Date.parse(event.recordedAt) < Date.parse(previous.recordedAt)) {
			return {
				valid: false,
				phase: "inactive",
				events,
				reason: "non-monotonic transition time",
				expired: false,
			};
		}

		if (!previous || event.grantId !== previous.grantId) {
			if (event.transition !== "armed") {
				return {
					valid: false,
					phase: "inactive",
					events,
					reason: "new grant does not begin with armed",
					expired: false,
				};
			}
			if (previous && !TERMINAL_TRANSITIONS.has(previous.transition)) {
				return {
					valid: false,
					phase: "inactive",
					events,
					reason: "new grant overlaps an active grant",
					expired: false,
				};
			}
			if (seenGrantIds.has(event.grantId)) {
				return {
					valid: false,
					phase: "inactive",
					events,
					reason: "grant id was reused",
					expired: false,
				};
			}
			seenGrantIds.add(event.grantId);
			grantFirst = event;
		} else {
			if (!grantFirst || !sameGrantIdentity(grantFirst, event)) {
				return {
					valid: false,
					phase: "inactive",
					events,
					reason: "grant identity changed",
					expired: false,
				};
			}
			if (!transitionAllowed(previous.transition, event.transition)) {
				return {
					valid: false,
					phase: "inactive",
					events,
					reason: "contradictory state transition",
					expired: false,
				};
			}
		}
		events.push(event);
		previous = event;
	}

	if (!previous) return { valid: true, phase: "inactive", events, expired: false };
	const phase = phaseFor(previous.transition);
	if (
		(phase === "armed" || phase === "consumed") &&
		(previous.sessionFile !== identity.sessionFile || previous.cwd !== identity.cwd)
	) {
		return {
			valid: false,
			phase: "inactive",
			events,
			latest: previous,
			reason: "active grant identity does not match this session file and cwd",
			expired: false,
		};
	}
	return {
		valid: true,
		phase,
		events,
		latest: previous,
		expired: phase === "armed" && now >= Date.parse(previous.expiresAt),
	};
}

export function isEligibleBreakGlassInput(
	text: string,
	source: "interactive" | "rpc" | "extension",
	streamingBehavior?: "steer" | "followUp",
): boolean {
	const trimmed = text.trim();
	return (
		streamingBehavior === undefined &&
		source !== "extension" &&
		trimmed !== "" &&
		!trimmed.startsWith("/") &&
		!trimmed.startsWith("!")
	);
}

function isCanonicalBuiltin(tool: ToolDescriptor, name: BreakGlassToolName): boolean {
	return (
		tool.name === name &&
		tool.sourceInfo.path === `<builtin:${name}>` &&
		tool.sourceInfo.source === "builtin" &&
		tool.sourceInfo.scope === "temporary" &&
		tool.sourceInfo.origin === "top-level"
	);
}

export function selectRecoveryTools(
	tools: readonly ToolDescriptor[],
): { toolNames: string[]; ambiguous: string[] } {
	const canonical = new Set<string>();
	const ambiguous: string[] = [];
	for (const name of BREAK_GLASS_TOOL_NAMES) {
		const matches = tools.filter((tool) => tool.name === name);
		if (matches.length === 0) continue;
		if (matches.length === 1 && isCanonicalBuiltin(matches[0]!, name)) canonical.add(name);
		else ambiguous.push(name);
	}
	if (!canonical.has("read") || ambiguous.includes("read")) {
		return { toolNames: [], ambiguous };
	}
	return {
		toolNames: BREAK_GLASS_TOOL_NAMES.filter((name) => canonical.has(name)),
		ambiguous,
	};
}

export function appendBreakGlassPolicy(basePrompt: string, grant: BreakGlassEventData): string {
	if (grant.transition !== "consumed" || !grant.promptSha256) {
		throw new TypeError("break-glass policy requires a consumed prompt-bound grant");
	}
	const policy = `${BREAK_GLASS_POLICY_MARKER}
## One-turn natural-language local repair

Grant: \`${grant.grantId}\`
Prompt SHA-256: \`${grant.promptSha256}\`
Working directory: \`${grant.cwd}\`

The user deliberately left the mandatory Agent Skills delivery lane for this one turn. Treat the exact natural-language prompt as the complete repair scope. Do not route this turn through ask-skills, to-spec, to-tickets, or Ticket Autopilot scheduling before performing the repair.

- You may directly inspect and modify local files needed by the prompt, including tracked files and \`.git/ticket-autopilot\` state, using only canonical built-in read, bash, edit, and write.
- Make the smallest repair that exits the named deadlock. When replacing local control-plane state, preserve its prior bytes first when practical and never fabricate evidence, authority, or successful history.
- Read back the resulting files and run the applicable Ticket Autopilot \`status\` or \`resume\` command. Claim local recovery only when that normal command accepts the result; otherwise report the exact remaining failure.
- Candidate drift is allowed and must return to normal invalidation, review, QA, and verification after this turn. Do not claim a ticket completed, verified, integrated, or synchronized from the edit alone.
- This grant supplies no provider, PR, push, merge, remote-history, wiki-publication, cleanup, Pi-sync, secret-disclosure, or \`/reload\` authority. Stop before any such boundary unless it is separately authorized through its normal mechanism.

At the end of this turn the prior tool set and mandatory routing return automatically. The exception is consumed even if the repair fails or is aborted.
</agent-skills-break-glass-v2>`;
	if (basePrompt.includes(policy)) return basePrompt;
	if (basePrompt.includes(BREAK_GLASS_POLICY_MARKER)) {
		throw new TypeError("system prompt contains a different break-glass policy marker");
	}
	return `${basePrompt}\n\n${policy}`;
}
