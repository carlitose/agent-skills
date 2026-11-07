import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { REQUIRED_SKILLS, buildMandatoryWorkflowPolicy } from "./mandatory-agent-skills.ts";

const doc = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8").replace(/\r\n?/g, "\n");
const planPath = "execute-ticket/references/plan-execution.md";

test("injected policy advertises plan intake within skills-only, not another delivery lane", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.match(policy, /one of three lanes/);
	assert.match(policy, /requirements-and-plan intake/);
	assert.ok(policy.includes(planPath));
	assert.match(policy, /one cohesive deliverable/);
	assert.match(policy, /canonical ticket intake/);
	assert.doesNotMatch(policy, /caller supplies validated canonical inputs to `execute-ticket`/);
});

test("router selects by clarity and delivery boundaries rather than a second size threshold", () => {
	const router = doc("ask-skills/SKILL.md");
	assert.match(router, /requirements-and-plan/);
	assert.match(router, /one cohesive deliverable/);
	assert.match(router, /independently deliverable/);
	assert.match(router, /grilling -> to-spec/);
	assert.match(router, /One canonical ticket Markdown file/);
	assert.ok(router.includes("../" + planPath));
	const plan = doc(planPath);
	assert.match(plan, /not a file or line threshold/);
	assert.match(plan, /explicit or existing ticket/);
	assert.match(plan, /malformed or blocked ticket/);
});

test("plan intake reuses the source and carries criteria, scope, authority and one plan", () => {
	const plan = doc(planPath);
	for (const term of ["TASK.md", "acceptance criteria", "allowed paths", "authority", "one plan", "No new spec, ticket, CandidateRef or Verification Record"])
		assert.ok(plan.includes(term), term);
	assert.match(plan, /session context or an existing document/);
	assert.match(plan, /never manufacture a ticket digest/);
	assert.match(plan, /budget, time and maximum attempts/);
});

test("both intakes reach the same quality loop and standalone leaves", () => {
	const execute = doc("execute-ticket/SKILL.md");
	assert.match(execute, /## Ticket intake/);
	assert.match(execute, /## Requirements-and-plan intake/);
	assert.equal(execute.match(/## Quality loop/g)?.length, 1);
	for (const stage of ["code-simplification", "code-review", "qa-test-plan", "verification-cost.md"])
		assert.ok(execute.includes(stage), stage);
	assert.match(execute, /Both intakes/);
	assert.match(execute, /standalone intake/);
	assert.match(execute, /only after GREEN/);
	assert.match(execute, /relevant stage/);
	assert.match(doc("qa-test-plan/SKILL.md"), /CandidateRef or standalone scope identity/);
	assert.match(doc("code-simplification/SKILL.md"), /standalone scope identity/);
});

test("standalone identity includes new files and preserves old evidence on drift", () => {
	const plan = doc(planPath);
	for (const term of ["base/head", "SHA-256", "untracked", "deleted", "requirements", "invalidate", "original identities"])
		assert.ok(plan.includes(term), term);
	assert.match(plan, /same source, scope and candidate/);
	assert.match(plan, /do not regenerate/);
});

test("full audit promotes through canonical owners instead of inventing a schema", () => {
	const plan = doc(planPath);
	assert.match(plan, /full Verification Record/);
	assert.match(plan, /to-spec/);
	assert.match(plan, /to-tickets/);
	assert.match(plan, /release, live, production or security claim/);
	assert.match(plan, /not relabel/);
	assert.match(plan, /implementation-complete/);
	assert.match(plan, /failed, skipped and not-run/);
});

test("plan intake preserves explicit authority and canonical contract references", () => {
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	for (const term of ["only when the user explicitly asks for Autopilot", "not merge consent", "Money movement", "without fabricating scheduler state"])
		assert.ok(policy.includes(term), term);
	const inline = doc("execute-ticket/references/skills-only.md");
	assert.ok(inline.includes("plan-execution.md"));
	for (const term of ["parse_ticket_markdown", "semantic_candidate", "--current-candidate", "Separately authorized delivery"])
		assert.ok(inline.includes(term), term);
	assert.match(doc(planPath), /no delegation, runner, Git\/provider delivery, installation or reload authority/);
	assert.match(policy, /selected intake\x27s attributed gates/);
	assert.match(doc("execute-ticket/references/verification-cost.md"), /plan\x27s attributed limits/);
	assert.match(doc("execute-ticket/agents/openai.yaml"), /requirements-and-plan intake/);
});

test("packaged plan entry links resolve and README describes the same two intakes", () => {
	const plan = doc(planPath);
	for (const match of plan.matchAll(/\]\(([^)#]+)(?:#[^)]*)?\)/g)) {
		assert.ok(readFileSync(new URL(`../execute-ticket/references/${match[1]}`, import.meta.url)).length);
	}
	const manifest = JSON.parse(doc("package.json"));
	assert.ok(manifest.pi.skills.includes("./*/SKILL.md"));
	assert.match(doc("README.md"), /requirements-and-plan intake/);
	assert.match(doc("README.md"), /canonical ticket intake/);
});
