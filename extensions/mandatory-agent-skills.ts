import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export const ROUTER_COMMAND = "/skill:ask-skills";
export const POLICY_MARKER = "<mandatory-agent-skills-workflow>";
export const REQUIRED_SKILLS = ["ask-skills", "to-spec", "to-tickets", "ticket-autopilot"] as const;

type InputSource = "interactive" | "rpc" | "extension";

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
3. **Reuse only validated artifacts.** Existing specs or canonical ticket artifacts may satisfy their owning stage, but the owning skill must validate them before the next stage. Never silently skip a stage or regenerate a valid artifact merely to appear compliant.
4. **Keep ownership deep.** \`ticket-autopilot\` owns scheduling and composes \`execute-ticket\`, review, QA, verification, PR explanation, and delivery. Do not invoke those leaves directly for a loose delivery request.
5. **Keep non-delivery work minimal.** Read-only research, diagnosis, review, QA planning, architecture discovery, peer programming, grilling, and throwaway prototypes use the smallest route selected by \`ask-skills\`. A prototype cannot be promoted to production outside the delivery lane.
6. **Preserve human authority.** Mandatory workflow is not merge consent. Keep \`ticket-autopilot\` on its manual merge policy unless the user supplies the explicit durable authorization required by that skill. Never manufacture approval, credentials, provider evidence, or verification evidence.
7. **Fail closed.** If a required skill or required canonical input is unavailable, stop before repository mutation and report the exact missing input.

Routing is complete only after a skill/composition (or no applicable skill) is explicit. Delivery is complete only at the state allowed by \`ticket-autopilot\`; an open gate is a valid stop, not permission to bypass it.

${readiness}
${POLICY_MARKER}`;
}

export function appendMandatoryWorkflowPolicy(basePrompt: string, availableSkillNames: readonly string[]): string {
	if (basePrompt.includes(POLICY_MARKER)) return basePrompt;
	return `${basePrompt}\n\n${buildMandatoryWorkflowPolicy(availableSkillNames)}`;
}

export default function mandatoryAgentSkills(pi: ExtensionAPI) {
	pi.on("input", (event) => {
		const routed = routeNaturalLanguageInput(event.text, event.source);
		if (routed === undefined) return { action: "continue" };
		return { action: "transform", text: routed };
	});

	pi.on("before_agent_start", (event) => {
		const skillNames = event.systemPromptOptions.skills?.map((skill) => skill.name) ?? [];
		return {
			systemPrompt: appendMandatoryWorkflowPolicy(event.systemPrompt, skillNames),
		};
	});

	pi.on("session_start", (_event, ctx) => {
		ctx.ui.setStatus("mandatory-agent-skills", "skills → spec → tickets → autopilot");
	});

	pi.on("session_shutdown", (_event, ctx) => {
		ctx.ui.setStatus("mandatory-agent-skills", undefined);
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
					? "Mandatory flow active: ask-skills → to-spec → to-tickets → ticket-autopilot"
					: `Mandatory flow blocked; missing skills: ${missing.join(", ")}`;
			ctx.ui.notify(message, missing.length === 0 ? "info" : "error");
		},
	});
}
