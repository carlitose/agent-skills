import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

import {
	POLICY_MARKER,
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
	const policy = buildMandatoryWorkflowPolicy([
		"ask-skills",
		"change-status-ticket",
		"to-spec",
		"to-tickets",
		"ticket-autopilot",
	]);
	assert.match(policy, /to-spec -> to-tickets -> ticket-autopilot/);
	assert.match(policy, /sole lifecycle-only exception/);
	assert.match(policy, /routes to `change-status-ticket`/);
	assert.match(policy, /without `execute-ticket` stages/);
	assert.doesNotMatch(policy, /docs-only exception|small-change exception/);
	assert.match(policy, /Required workflow skills are loaded/);
	assert.match(policy, /not merge consent/);
});

test("preserves affirmative repository-wide merge intent without manufacturing authority", () => {
	const policy = buildMandatoryWorkflowPolicy([
		"ask-skills",
		"change-status-ticket",
		"to-spec",
		"to-tickets",
		"ticket-autopilot",
	]);
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
	const policy = buildMandatoryWorkflowPolicy([
		"ask-skills",
		"change-status-ticket",
		"to-spec",
		"to-tickets",
		"ticket-autopilot",
	]);
	assert.match(policy, /sync-local-pi/);
	assert.match(policy, /durably `integrated`/);
	assert.match(policy, /actor\/evidence-bound/);
	assert.match(policy, /Never trigger it from implementation, verification, PR-open/);
	assert.match(policy, /update the Pi binary/);
	assert.match(policy, /`\/reload` is required/);
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
	assert.match(policy, /change-status-ticket, to-spec, to-tickets, ticket-autopilot/);
	assert.match(policy, /Do not mutate the repository/);
});

test("appends the policy exactly once", () => {
	const skills = ["ask-skills", "change-status-ticket", "to-spec", "to-tickets", "ticket-autopilot"];
	const once = appendMandatoryWorkflowPolicy("base", skills);
	const twice = appendMandatoryWorkflowPolicy(once, skills);
	assert.equal(twice, once);
	assert.equal(once.split(POLICY_MARKER).length - 1, 2);
});
