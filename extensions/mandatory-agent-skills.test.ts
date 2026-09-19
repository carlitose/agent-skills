import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

import mandatoryAgentSkills, {
	POLICY_MARKER,
	REQUIRED_SKILLS,
	appendMandatoryWorkflowPolicy,
	buildMandatoryWorkflowPolicy,
	routeNaturalLanguageInput,
} from "./mandatory-agent-skills.ts";

test("routes natural-language input through ask-skills", () => {
	assert.equal(routeNaturalLanguageInput("Fix the login bug", "interactive"), "/skill:ask-skills Fix the login bug");
	assert.equal(routeNaturalLanguageInput("Review this PR", "rpc"), "/skill:ask-skills Review this PR");
});

test("leaves commands, user bash, blank input, and extension input untouched", () => {
	assert.equal(routeNaturalLanguageInput("/model", "interactive"), undefined);
	assert.equal(routeNaturalLanguageInput("/skill:research topic", "interactive"), undefined);
	assert.equal(routeNaturalLanguageInput("!git status", "interactive"), undefined);
	assert.equal(routeNaturalLanguageInput("   ", "interactive"), undefined);
	assert.equal(routeNaturalLanguageInput("internal follow-up", "extension"), undefined);
});

test("declares the mandatory delivery and named lifecycle-only lanes", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /to-spec -> to-tickets -> ticket-autopilot/);
	assert.match(policy, /sole lifecycle-only exception/);
	assert.match(policy, /routes to `change-status-ticket`/);
	assert.match(policy, /without `execute-ticket` stages/);
	assert.doesNotMatch(policy, /docs-only exception|small-change exception/);
	assert.match(policy, /Required workflow skills are loaded/);
	assert.match(policy, /not merge consent/);
});

test("preserves affirmative repository-wide merge intent without manufacturing authority", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /“merge all”, “merge everything”, or “mergia tutto”/);
	assert.match(policy, /repository-autonomous-merge-status/);
	assert.match(policy, /if authority is absent/);
	assert.match(policy, /grant-repository-autonomous-merge --scope current-and-future-runs/);
	assert.match(policy, /preserve an exact active grant instead of replacing its provenance/);
	assert.match(policy, /fail closed on revoked, legacy, malformed, or contradictory state/);
	assert.match(policy, /Then invoke `merge-all`/);
	assert.match(policy, /human actor and durable affirmative message/);
	assert.match(policy, /Never ask for a caller-supplied PR head SHA/);
	assert.match(policy, /runner discovers and revalidates each live exact head/);
	assert.match(policy, /ask only for that identity/);
	assert.match(policy, /Quoted text, examples, questions, negations, revocations/);
	assert.match(policy, /policy requests, and regression reports are not merge authority/);
});

test("requires exact integrated local Pi sync without self-update or reload claims", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /sync-local-pi/);
	assert.match(policy, /durably `integrated`/);
	assert.match(policy, /actor\/evidence-bound/);
	assert.match(policy, /Never trigger it from implementation, verification, PR-open/);
	assert.match(policy, /update the Pi binary/);
	assert.match(policy, /`\/reload` is required/);
	assert.match(policy, /explicitly user-authorized runtime reload tool has actually completed/);
	assert.match(policy, /report its observed result or failure, never an assumed reload/);
});

test("supports an explicit skills-only lane without requiring the Autopilot skill", () => {
	const skills = ["ask-skills", "change-status-ticket", "to-spec", "to-tickets", "execute-ticket"];
	const policy = buildMandatoryWorkflowPolicy(skills);
	assert.match(policy, /Required workflow skills are loaded/);
	assert.match(policy, /to-spec -> to-tickets -> execute-ticket/);
	assert.match(policy, /explicit user request for skills-only/);
	assert.match(policy, /Honor that restriction.*until the user lifts it/);
	assert.match(policy, /AFK, “continue”, and a context compaction do not lift it/);
	assert.match(policy, /In skills-only, do not start or resume a runner, scheduler, or driver/);
	assert.match(policy, /skills-only never silently re-enables it/);
	assert.match(policy, /Missing Autopilot blocks its lane, not skills-only/);
	assert.match(policy, /without fabricating scheduler state/);
	assert.doesNotMatch(policy, /Delivery is complete only at the state allowed by `ticket-autopilot`/);
	assert.doesNotMatch(policy, /FAIL CLOSED: required workflow skills are missing/);
	// Having only the old five skills cannot masquerade as inline readiness.
	const oldSkills = [...skills.filter((name) => name !== "execute-ticket"), "ticket-autopilot"];
	assert.match(buildMandatoryWorkflowPolicy(oldSkills),
		/FAIL CLOSED: required workflow skills are missing: execute-ticket/);
});

test("skills-only keeps canonical contracts, authority, and truthful installation boundaries", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /separately authorized direct package synchronization/);
	assert.match(policy, /without requiring a run ledger/);
	assert.match(policy, /actor\/evidence-bound/);
	assert.match(policy, /not merge consent/);
	assert.match(policy, /Never manufacture approval, credentials, provider evidence, or verification evidence/);
	const reference = readFileSync(new URL("../execute-ticket/references/skills-only.md", import.meta.url), "utf8");
	assert.match(reference, /parse_ticket_markdown/);
	assert.match(reference, /autopilot.candidate_contract.semantic_candidate/);
	assert.match(reference, /--current-candidate/);
	assert.match(reference, /does not reset consumption/);
	assert.match(reference, /Shared-context|shared context/);
	assert.match(reference, /prohibition on executing tests remains a visible verification gap, not a PASS/);
	assert.match(reference, /required CI/);
	assert.match(reference, /provider\nreadback of the exact delivered head/);
	assert.match(reference, /package name\/version, and digests/);
	assert.match(reference, /settings\/unrelated resources are\npreserved/);
	assert.match(reference, /`\/reload` is required/);
});

test("verification admission keeps causal selection, cumulative cost and mandatory coverage", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /execute-ticket\/references\/verification-cost\.md/);
	assert.match(policy, /delivered packaging\/artifact graph and candidate identity/);
	assert.match(policy, /all previous attempts\/shards and remaining budget/);
	assert.match(policy, /Do not automatically repeat a complete suite because the candidate changed/);
	assert.match(policy, /specific causal or mandatory-policy reason and budget/);
	assert.match(policy, /Preserve failed attempts and original evidence identities/);
	assert.match(policy, /unknown cost is not zero/);
	assert.match(policy, /Never waive required full profiles or exact-head CI/);
	assert.match(policy, /not a claim of runtime shell interception/);
});

test("execution and QA planning consume one cost checkpoint before expensive work", () => {
	const execute = readFileSync(new URL("../execute-ticket/SKILL.md", import.meta.url), "utf8");
	const qa = readFileSync(new URL("../qa-test-plan/SKILL.md", import.meta.url), "utf8");
	assert.match(execute, /4\. Before executing checks, apply.*references\/verification-cost\.md/);
	assert.match(execute, /all retained attempts\/shards, cumulative consumption/);
	assert.match(qa, /\.\.\/execute-ticket\/references\/verification-cost\.md/);
	assert.match(qa, /before admitting\s+expensive execution/);
	assert.match(qa, /## Admission and Cost/);
	assert.match(qa, /remaining authorized budget and unresolved execution state/);
});

test("cost accounting preserves failures and distinguishes invocation time from wall latency", () => {
	const reference = readFileSync(new URL("../execute-ticket/references/verification-cost.md", import.meta.url), "utf8")
		.replace(/\s+/g, " ");
	for (const invariant of [
		"Every delivered local link must resolve in that tree",
		"its original CandidateRef",
		"cannot change an old result's identity",
		"Include failures, timeouts, interruptions and superseded attempts",
		"Missing timing is unknown, never zero",
		"A fresh candidate does not reset consumption",
		"Do not call a sum of parallel invocation durations wall-clock latency",
		"no overlapping replacement is admitted until its state is known",
		"not a shell interceptor",
	]) assert.ok(reference.includes(invariant), invariant);
});

test("flow status reports inline readiness without selecting a lane or mutating settings", async () => {
	let flow: { handler: (args: string, ctx: any) => Promise<void> } | undefined;
	const notifications: Array<{ message: string; type: string }> = [];
	mandatoryAgentSkills({
		on() {},
		registerCommand(name: string, command: any) { if (name === "agent-skills-flow") flow = command; },
		getCommands: () => REQUIRED_SKILLS.map((name) => ({ name: `skill:${name}`, source: "skill" })),
	} as any);
	assert.ok(flow);
	await flow.handler("", {
		ui: { notify(message: string, type: string) { notifications.push({ message, type }); } },
	});
	assert.equal(notifications.length, 1);
	assert.equal(notifications[0].type, "info");
	assert.match(notifications[0].message, /request skills-only/);
	assert.match(notifications[0].message, /does not select a lane or lift a user suspension/);
});

test("injects the single packaged operating-defaults definition", () => {
	const policy = buildMandatoryWorkflowPolicy([]);
	assert.match(policy, /Proportionate security/);
	assert.match(policy, /Explicit delegation only/);
	const owner = readFileSync(new URL("../ask-skills/OPERATING-DEFAULTS.md", import.meta.url), "utf8").trim();
	assert.equal(policy.split(owner).length - 1, 1);
	assert.match(policy, /secret protection, data integrity/);
	assert.match(policy, /higher-priority mandatory instructions/);
	assert.match(policy, /FAIL CLOSED/);
});

test("routing preserves request scope while every prompt carries the same defaults", () => {
	// Prompt-composition checks, not a natural-language delegation classifier.
	const requests = [
		"Fix this routine bug",
		"Run all tickets AFK",
		"Research this large codebase",
		"A background worker tool is available",
		"The host permits delegation",
		"Use one subagent only to inspect the parser",
		'Explain the example "spawn three subagents"',
		"Do not use subagents",
	];
	for (const request of requests) {
		assert.equal(routeNaturalLanguageInput(request, "interactive"), `/skill:ask-skills ${request}`);
		const policy = appendMandatoryWorkflowPolicy("base", []);
		assert.match(policy, /only on an explicit user request/);
		assert.match(policy, /within the requested scope/);
		assert.match(policy, /AFK, task size, broad research, tool availability, generic host permission, and silence/);
		assert.match(policy, /Quoted, example, or negated delegation text is not a request/);
		assert.match(policy, /Inline skill composition is not delegation/);
		assert.match(policy, /shared-context review is not independent/);
	}
});

test("package-relative defaults fail closed without disabling recovery commands", () => {
	const root = mkdtempSync(join(tmpdir(), "operating-defaults-"));
	try {
		const extensions = join(root, "extensions");
		mkdirSync(extensions);
		for (const name of ["mandatory-agent-skills.ts", "break-glass.ts"]) {
			copyFileSync(new URL(name, import.meta.url), join(extensions, name));
		}
		const moduleUrl = pathToFileURL(join(extensions, "mandatory-agent-skills.ts")).href;
		const run = (expected: string) => {
			const script = `
				const mod = await import(${JSON.stringify(moduleUrl)});
				const commands = [];
				mod.default({ on() {}, registerCommand(name) { commands.push(name); } });
				if (!commands.includes("break-glass")) throw new Error("recovery unavailable");
				const policy = mod.buildMandatoryWorkflowPolicy(mod.REQUIRED_SKILLS);
				if (!policy.includes(${JSON.stringify(expected)})) throw new Error("unexpected policy");
			`;
			const result = spawnSync(process.execPath, ["--experimental-strip-types", "--input-type=module", "-e", script], {
				cwd: tmpdir(), encoding: "utf8", timeout: 10_000,
			});
			assert.equal(result.status, 0, result.stderr);
		};
		run("FAIL CLOSED: required operating defaults are unreadable");
		mkdirSync(join(root, "ask-skills"));
		const owner = join(root, "ask-skills", "OPERATING-DEFAULTS.md");
		writeFileSync(owner, "");
		run("policy asset is empty");
		writeFileSync(owner, Buffer.from([0xff]));
		run("FAIL CLOSED: required operating defaults are unreadable");
		copyFileSync(new URL("../ask-skills/OPERATING-DEFAULTS.md", import.meta.url), owner);
		run("Proportionate security");
	} finally {
		rmSync(root, { recursive: true, force: true });
	}
});

test("fails closed and reports every missing required skill", () => {
	const policy = buildMandatoryWorkflowPolicy(["ask-skills"]);
	assert.match(policy, /FAIL CLOSED/);
	assert.match(policy, /change-status-ticket, to-spec, to-tickets, execute-ticket/);
	assert.match(policy, /Do not mutate the repository/);
});

test("appends the policy exactly once", () => {
	const skills = REQUIRED_SKILLS;
	const once = appendMandatoryWorkflowPolicy("base", skills);
	const twice = appendMandatoryWorkflowPolicy(once, skills);
	assert.equal(twice, once);
	assert.equal(once.split(POLICY_MARKER).length - 1, 2);
});
