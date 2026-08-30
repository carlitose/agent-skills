# Project Purpose

## Goal

Maintain a durable, navigable history of the Agent Skills project from its accepted documentation and ticket artefacts, augmented by privacy-bounded agent-session pointers and attributed digests. The wiki exists so decisions, implementation slices, lifecycle changes, and their provenance can be inspected through ordinary Markdown without depending on an editor or retrieval service.

## Key Questions

1. Which accepted decisions and specifications shaped the current skill and Ticket Autopilot contracts?
2. How did each ticket move through its lifecycle, and what source or session evidence supports the recorded dates?
3. Which sessions touched a project concept or ticket, without treating an agent transcript's claims as project facts?
4. Where are the unresolved dates, source gaps, and warning families that a future maintainer should investigate?

## Scope

**In scope:**

- tracked project specifications, ticket mirrors, research notes, and prototype notes selected by `llm-wiki-project.json`;
- identity-stable source summaries, graph links, disposition, and provenance-bearing dates compiled from those artefacts;
- local agent sessions represented only by external pointers and bounded attributed digest pages;
- lifecycle timelines, ordinary Markdown indexes, and the human correction channel under `audit/`.

**Out of scope:**

- complete transcripts, secrets, credentials, private-file contents, provider databases, and environment dumps;
- local Downloads material, including the separate Obsidian and hybrid-retrieval notes;
- embeddings, vector databases, BM25 services, inferred graph edges, query caches, HTTP, MCP, editor plugins, and application-private state;
- assertions that an attributed session summary is independently verified project truth.

## Thesis

> A useful and auditable project history can remain application-independent Markdown when artefact identity, lifecycle provenance, source attribution, and privacy boundaries are explicit and mechanically checked.
