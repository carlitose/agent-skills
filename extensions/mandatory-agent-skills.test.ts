import assert from "node:assert/strict";
import test from "node:test";

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

test("declares the mandatory delivery lane when required skills are loaded", () => {
	const policy = buildMandatoryWorkflowPolicy(["ask-skills", "to-spec", "to-tickets", "ticket-autopilot"]);
	assert.match(policy, /to-spec -> to-tickets -> ticket-autopilot/);
	assert.match(policy, /Required workflow skills are loaded/);
	assert.match(policy, /not merge consent/);
});

test("fails closed and reports every missing required skill", () => {
	const policy = buildMandatoryWorkflowPolicy(["ask-skills"]);
	assert.match(policy, /FAIL CLOSED/);
	assert.match(policy, /to-spec, to-tickets, ticket-autopilot/);
	assert.match(policy, /Do not mutate the repository/);
});

test("appends the policy exactly once", () => {
	const skills = ["ask-skills", "to-spec", "to-tickets", "ticket-autopilot"];
	const once = appendMandatoryWorkflowPolicy("base", skills);
	const twice = appendMandatoryWorkflowPolicy(once, skills);
	assert.equal(twice, once);
	assert.equal(once.split(POLICY_MARKER).length - 1, 2);
});
