---
name: issues-to-openspec
description: Convert a PRD and its issue files into an OpenSpec change folder with proposal, specs, design, and tasks. Use when user wants to convert issues to OpenSpec format, create an OpenSpec change from a PRD, or migrate planning docs to spec-driven development.
---

# Issues to OpenSpec

Convert a PRD (from `write-a-prd`) and its issue breakdown (from `prd-to-issues`) into an OpenSpec change folder following the spec-driven schema.

## Process

### 1. Locate the source files

Ask the user for:
- The PRD file path (e.g. `docs/prds/<slug>.md`)
- The issues directory path (e.g. `docs/issues/<prd-slug>/`)

Read the PRD and all issue files if not already in context.

### 2. Research and exploration

Before generating the OpenSpec artifacts:

- **Explore the codebase** to understand existing domain boundaries, architecture, and which areas the change touches.
- **Research with `mcp__context7`**: Use `resolve-library-id` and `query-docs` to look up current documentation for any libraries, frameworks, or services mentioned in the PRD or issues. This ensures the design and specs reflect up-to-date APIs, best practices, and available features.
- **Search the web** (`WebSearch`) for the latest technologies, patterns, or approaches relevant to the change. Check if there are newer/better solutions than what the PRD assumed.
- Incorporate any findings into the generated artifacts (especially `design.md` and `specs/`).

### 3. Create the OpenSpec change folder

Create the change folder at `openspec/changes/<change-name>/` where `<change-name>` is a kebab-case name derived from the PRD slug. Create the `openspec/` directory structure if it doesn't exist.

Generate the following artifacts:

#### 3.1 `.openspec.yaml`

```yaml
schema: spec-driven
created: "<today's date YYYY-MM-DD>"
```

#### 3.2 `proposal.md`

Map the PRD content to the OpenSpec proposal format:

```markdown
## Why

<!-- From PRD: Problem Statement -->

## What Changes

<!-- From PRD: Solution — describe what new capabilities are being added or modified -->

## Capabilities

### New Capabilities

<!-- For each major feature area identified in the PRD and issues, list as:
- `<capability-slug>` — <one-line description> (becomes `specs/<capability-slug>/spec.md`)
-->

### Modified Capabilities

<!-- If the change modifies existing system behavior, list here. Otherwise omit this section. -->

## Impact

<!-- From PRD: Implementation Decisions — summarize affected code areas, APIs, dependencies.
     Enrich with findings from context7 and web research. -->
```

#### 3.3 `specs/<domain>/spec.md`

Group the issues by domain/feature area. For each domain, create a spec file:

```markdown
## ADDED Requirements

### Requirement: <requirement-name>
<!-- Derive from the issue's "What to build" section. Write as a behavior statement using RFC 2119 keywords (MUST, SHOULD, MAY). -->

#### Scenario: <scenario-name>
- **WHEN** <condition from acceptance criteria>
- **THEN** <expected outcome from acceptance criteria>

<!-- Create one Requirement per issue (or per logical group of closely related issues).
     Create one Scenario per acceptance criterion. -->
```

**Important format rules:**
- Requirements use `###` (3 hashtags)
- Scenarios use `####` (4 hashtags)
- Use WHEN/THEN format for scenarios
- Each requirement MUST have at least one scenario

#### 3.4 `design.md`

```markdown
## Context

<!-- From PRD: relevant background, current state of the system.
     Include findings from context7 docs and web research about current best practices
     and latest available features of the technologies involved. -->

## Goals / Non-Goals

<!-- Goals: from PRD Solution + User Stories
     Non-Goals: from PRD Out of Scope -->

## Decisions

<!-- From PRD: Implementation Decisions + Testing Decisions.
     Frame as architectural decisions with rationale.
     Reference current library docs (from context7) to justify technology choices.
     If research revealed better approaches than what the PRD assumed, note them here. -->

## Risks / Trade-offs

<!-- Any risks identified in the PRD or issues, dependency chains between issues.
     Include deprecation warnings or breaking changes found in library docs. -->
```

#### 3.5 `tasks.md`

Convert each issue into a task group. Use the issue dependency order (the NN- prefix numbering). Each issue becomes a numbered group, and its acceptance criteria become checkbox tasks:

```markdown
## 1. <Issue title>

- [ ] 1.1 <acceptance criterion 1>
- [ ] 1.2 <acceptance criterion 2>
- [ ] 1.3 <acceptance criterion 3>

## 2. <Issue title>

- [ ] 2.1 <acceptance criterion 1>
- [ ] 2.2 <acceptance criterion 2>
```

**Rules:**
- Respect the dependency order from the issue files (blocked-by relationships)
- Every task MUST use checkbox format (`- [ ]`) or it won't be tracked
- Tasks should be completable in one session
- Use hierarchical numbering (1.1, 1.2, 2.1, etc.)

### 4. Present the result

Tell the user the complete list of created files and the change folder path. Summarize:

- How many spec domains were identified
- How many requirements and scenarios were generated
- How many task groups and individual tasks were created
- Key findings from documentation/web research that influenced the artifacts
- Any content from the PRD that didn't map cleanly and may need manual review

### 5. Do NOT modify the original PRD or issue files
