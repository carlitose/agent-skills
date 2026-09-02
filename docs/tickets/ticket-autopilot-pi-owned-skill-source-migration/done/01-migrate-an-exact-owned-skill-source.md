---
ticket_schema: 1
ticket_id: "PSM-01"
execution_mode: AFK
blocked_by: []
---

# Migrate an exact owned-skill source

## Artifact Graph

- Artifact ID: `artifact:psm-01-migrate-owned-skill-source`
- Role: `ticket`
- Parent: [Migrate the Pi owned-skill source explicitly](../../specs/ticket-autopilot-pi-owned-skill-source-migration.md)

## Parent Spec

[Migrate the Pi owned-skill source explicitly](../../specs/ticket-autopilot-pi-owned-skill-source-migration.md)

## What to Build

Implement the explicit, actor/evidence-bound migration described by the parent spec. Add
`sync-local-pi --migrate-owned-source-from <absolute-repository-root>` so one valid prior
owned-skill manifest can move from that exact source path to the current durably integrated
repository without weakening ownership, rollback, package, or replay checks. Add a separate
repeatable `--replace-drifted-owned <name>=<observed-sha256>` capability whose complete exact
set is required before any previously owned drift may be replaced.

Register the parent spec and this exact ticket in the tracked Artifact Graph as part of the
same bounded candidate. The tracked completed ticket must preserve this emitted ticket's exact
bytes; its completion receipt must bind the implementation CandidateRef and ignored source
snapshot without claiming that registration itself authorized implementation or merge.

## Acceptance Criteria

- [ ] The request and CLI accept one optional absolute, canonical, old source path; relative,
      equal-to-current, malformed, absent-target, and contradictory paths fail closed.
- [ ] Without the option, a manifest whose source differs from the current repository retains
      the exact current `Pi sync owned-skill manifest source drifted` rejection.
- [ ] With the option, migration proceeds only when the valid prior manifest names that exact
      path; previously owned digest drift remains rejected unless separately authorized by
      exact name and currently observed SHA-256.
- [ ] Drift-replacement authority is valid only with source migration and must equal the full
      observed drift set; missing, extra, duplicate, malformed, unowned, and stale entries fail
      before skill replacement or Pi invocation.
- [ ] `--adopt-existing-owned` and `--replace-package-source` do not imply or substitute for
      owned-source migration or drift replacement.
- [ ] A migration uses a deterministic successor state path derived from exact old/new source
      identities and exact drift authority; the ordinary failed state remains byte-identical.
- [ ] Historical non-migration intents and receipts that predate the optional field replay
      without rewrite or duplicate Pi install.
- [ ] Downstream install/readback failure restores the previous manifest, skills, and settings;
      completed replay performs no second install.
- [ ] Add the parent spec, its reciprocal parent edge, and this exact Ticket Envelope under the
      canonical ticket folder without introducing a new Artifact Graph error identity.
- [ ] Focused migration and CLI tests, the complete Ticket Autopilot suite, mandatory extension
      tests, compilation, exact tree/index checks, and final-tree verification pass.
- [ ] After durable integration, run the real RDR-05 sync from exact old source
      `/Users/carlogiuseppesergi/Projects/.agent-skills-runner-latest` to exact current source
      `/Users/carlogiuseppesergi/Projects/.agent-skills-rdr-remediation-20260901`, preserving
      literal prior failure and requiring `/reload` only after a completion receipt. The live
      invocation may replace exactly `llm-wiki=0879ae102441bd462065771fdb2a82c9dab8a9f4e25c9fe69a0d8fe81beb8c44`,
      `ticket-autopilot=a7488a0ec54521347699dffbfe128c2aacbc4cf1a2b848875016a8c3f8fe1526`,
      and `verification-audit=95009e118038832af28aab3abdf4f6b02c19bf321a199707483bd10d7095c97e`
      under user authority
      `pi-session://01a04e2a-0b7a-70fd-be3b-06500686244a/message/3ca3dada`.

## Frontier

Ready. The live failure, current manifest, failed state, source paths, exact integrated
head/tree, and existing ownership digests have been observed. The user explicitly authorized
replacement of the three exact drifted roots; no product or provider decision remains.

## Step-by-Step Implementation Plan

1. Extend normalized request intent with an optional exact prior owned-source path and a sorted
   exact drift-replacement set; preserve compatibility for historical intents missing those
   optional fields.
2. Derive a separate content-addressed migration state path from old/new source and exact drift
   authority while retaining the current path for ordinary synchronization.
3. Gate manifest source replacement on exact prior-source identity and actual source change;
   reject owned drift unless the complete observed name/digest set is authorized.
4. Retain the existing backup before mutation so every downstream failure restores old
   manifest bytes, skills, and settings.
5. Add matrix, exact-drift, replay, rollback, state-separation, and CLI tests plus user-facing
   contract wording.
6. Register the spec/ticket, freeze the implementation CandidateRef, add the exact tracked
   completion projection, and revalidate the final delivery tree.
7. Integrate through the normal exact-head PR path, prove fresh `origin/main` reachability, then
   invoke the live local Pi synchronization with the explicit prior source.

## Testing Plan

Run focused unit/integration tests for normalization, migration acceptance/rejection, immutable
historical state, rollback, replay, and CLI path selection. Run all Ticket Autopilot tests,
mandatory extension tests, Python compilation, raw diff/tree/index checks, Artifact Graph
audit, and repeat causal checks on the final completion-projected tree. The post-integration
live command is local environment evidence only and cannot claim active-session reload.

## Out of Scope

- Manual edits to the owned-skill manifest or Pi settings.
- Updating the Pi binary or issuing `/reload` automatically.
- Migrating arbitrary package sources, repositories, agents roots, or checkouts.
- Replacing any owned skill not named with its exact observed digest in the live authority.
- Treating source-name similarity, cleanup, Git merge authority, or prior sync authority as
  future migration authority.
- Repairing historical Artifact Graph findings or the tracked wiki binding.
