---
name: behavior-first
description: Implement an already-authorized public coding task with vertical behavior tests, complete contract coverage and the project's mandatory checks. Use for the builder/fix roles of this benchmark; not scheduling, metadata or delivery.
---

# Behavior first

The public ticket is already authorized. Do not interview the human, regenerate specs/tickets, spawn agents, or deliver Git changes. The caller owns freezes, review/semantic decisions and accounting. This skill never authorizes editing controller artifacts or using hidden oracle data.

## Ground the contract
Read the complete current public ticket and project development guide. Identify the existing public interface and implementation seam. List each required observable behavior, negative case and persistent convention in a short checklist. Do not reduce a multi-clause task to its happy path. Preserve contracts introduced in earlier accepted requests; `required_public_commands` lists the caller-owned cumulative checks.

## Vertical implementation
For each behavior, write one small test through the real public interface, observe it fail for the intended missing behavior, implement the smallest coherent change, and observe that test pass. Repeat vertically. Do not write all imagined tests first; do not mock away the product logic. Use an existing project test runner that actually discovers the added tests. Check tricky ordering, state rollback, compatibility, error and boundary cases named in the public task.

A failure must change the implementation or test understanding, not weaken an assertion, suppress lint/types, bypass the check, or claim success from a different command. The unchanged stock suite is regression evidence only, not proof of the new feature. A review finding is an observed claim to investigate; a semantic rejection is not a detailed diagnosis.

## Before handing back
Run the targeted new behavior tests and all `required_public_commands` in the supplied environment. Inspect their real exits. Refactor only after GREEN. Return a concise account of required behaviors implemented, actual checks run and remaining failures/unknowns. Do not declare controller or benchmark acceptance. In review/analysis roles, remain read-only even if this skill is visible.
