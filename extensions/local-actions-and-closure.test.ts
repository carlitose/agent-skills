import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";
import { REQUIRED_SKILLS, buildMandatoryWorkflowPolicy } from "./mandatory-agent-skills.ts";

// Structural policy checks only: no deletion, authority classifier or model-obedience proof.
const referencePath = "ask-skills/LOCAL-ACTIONS-AND-CLOSURE.md";
const doc = (path: string) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8").replace(/\s+/g, " ");
const reference = () => doc(referencePath);

function includesAll(text: string, phrases: string[]) {
	for (const phrase of phrases) assert.ok(text.toLowerCase().includes(phrase.toLowerCase()), phrase);
}

test("every injected lane reaches the shared actions/closure procedure", () => {
	const defaults = doc("ask-skills/OPERATING-DEFAULTS.md");
	const policy = buildMandatoryWorkflowPolicy(REQUIRED_SKILLS);
	assert.ok(defaults.includes("LOCAL-ACTIONS-AND-CLOSURE.md"));
	assert.ok(policy.includes("LOCAL-ACTIONS-AND-CLOSURE.md"));
	assert.doesNotMatch(policy, /always remove its worktree/);
	assert.match(policy, /recoverability/);
	includesAll(reference(), ["PR is merged or closed", "session ends", "every delivery lane", "open PR", "active handoff"]);
});

test("necessary actions have a bounded mandate, including the explicit PR exception", () => {
	includesAll(reference(), ["necessary", "local and reversible", "connected phone", "emulator",
		"development dependencies", "development server", "branches and commits", "open PRs",
		"remote exception", "report", "runtime refusal", "explicit restriction"]);
	assert.match(reference(), /necessary[^.]*not[^.]*authority/);
});

test("merge, public effects and user data still require their own authority", () => {
	includesAll(reference(), ["merge", "store or production", "spending", "credentials and accounts",
		"other people's data", "messages to others", "not issue publication", "personal device data",
		"publicly", "Pi synchronization or reload"]);
});

test("recoverability covers unique commits, binary changes and untracked files", () => {
	includesAll(reference(), ["[gone]", "not proof", "binary patch", "base commit", "untracked files",
		"unique commits", "bundle", "outside the removal target", "verify recovery", "keep it"]);
	assert.match(reference(), /empty patch[^.]*unique commits/);
	assert.match(reference(), /runner[^.]*refusal[^.]*not[^.]*bypass/);
});

test("cleanup protects primary, private, active and ambiguous resources", () => {
	includesAll(reference(), ["user data", "`.git/private`", "`node_modules`", "`.venv`",
		"primary checkout", "ownership", "symlinks or junctions", "locks", "interrupted Git",
		"No force removal", "ordinary `git worktree remove`", "fast-forward", "unrelated changes"]);
});

test("disk alarm uses actual Git-common state, bounded ranking and honest measurements", () => {
	includesAll(reference(), ["git rev-parse --git-common-dir", "1,000,000,000", "five largest",
		"immediate subdirectories", "before/after", "partial", "not zero", "not extra deletion authority"]);
});

test("14 days applies to regenerable heavy copies, never to ledger expiration", () => {
	includesAll(reference(), ["more than 14 days", "integration timestamp", "not mtime",
		"ledger", "history", "manifests", "receipts", "unique evidence", "not an expiry",
		"source archives", "copied environments", "referenced", "replay", "exactly regenerated"]);
});

test("all changed procedure links resolve and historical clutter needs a folder proposal", () => {
	for (const file of [referencePath, "ask-skills/OPERATING-DEFAULTS.md",
		"execute-ticket/references/skills-only.md", "ticket-autopilot/references/worktrees.md"]) {
		const base = new URL(`../${file}`, import.meta.url);
		for (const match of readFileSync(base, "utf8").matchAll(/\[[^\]]+\]\(([^)#]+)(?:#[^)]*)?\)/g)) {
			if (!/^[a-z]+:/i.test(match[1])) assert.ok(existsSync(new URL(match[1], base)), `${file}: ${match[1]}`);
		}
	}
	includesAll(reference(), ["existing clutter", "folder-by-folder proposal", "not a shell interceptor"]);
});
