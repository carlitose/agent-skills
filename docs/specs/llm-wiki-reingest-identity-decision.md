# LLM Wiki Re-ingest Identity and Change Contract

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-reingest-identity-decision`
- Role: `spec`
- Parent: [LLM Wiki as a Project History Knowledge Base](llm-wiki-project-history-wayfinder.md)

## Type

Decision spec

## Status

Accepted

## Source

`LW-10` in `docs/tickets/llm-wiki-project-history/10-reingest-identity-contract.md`.

## Context

The contract that makes the **second** ingest safe. The first ingest of a clean `docs/` tree
cannot fail this way; every ingest after it can, and the failure is silent.

The page naming observed in the reference wiki is
`wiki/sources/4-docs--4-adrs--43-2026-06-29-live-media-backpressure-boundary--1n8nezu.md`,
which encodes the **source path**. `docs/` is not static: in this repository every ticket
eventually moves, and while this plan was being executed six did — three from
`windows-text-fidelity`, then `AG-01`, `AG-04`, `AG-02`, `AG-03`, `LW-01`, `LW-02`, `LW-03` and
`LW-04`. A path-derived page name means each of those moves mints a *second* page for the same
artefact: two pages, two index entries, two contradictory lifecycle records — and
`lint_wiki.py` as it stands has no pass that would notice.

This is not hypothetical. The LLM Wiki application, running this same pattern, has already
produced the duplicate: `.llm-wiki/file-snapshot.json` in the reference wiki tracks both
`raw/sources/SPECIFICATION.md` and `raw/sources/docs/SPECIFICATION.md` — the same logical file
ingested twice under two paths.

The same class of defect bit this repository's own tooling. `AG-03` fixed
`artifact_audit._link_target` for exactly this reason: it resolved links literally, so a ticket
moved into `done/` broke both halves of its owner edge. The principle adopted there is the
principle adopted here.

### Measured corpus

Every file matched by `LW-03`'s default globs, classified by the identity key it yields:

| Key available | Files |
| --- | --- |
| `ticket_id` (Envelope v1 front matter) | 61 |
| `Artifact ID` (`## Artifact Graph` section) | 14 |
| **Neither** | **8** |

83 in total, which matches the artefact count `LW-03`'s resolver reports for this repository.

The eight without a stable key matter more than their count suggests, because five of them are
**specs**, not research notes — they predate the `## Artifact Graph` convention:

- `docs/specs/bounded-ticket-autopilot-leaf-protocol.md`
- `docs/specs/candidate-invalidation-decision.md`
- `docs/specs/ticket-autopilot-autonomous-stacked-delivery.md`
- `docs/specs/ticket-autopilot-delivery-merge-wayfinder.md`
- `docs/specs/ticket-lifecycle-disposition-decision.md`
- `docs/research/mattpocock-skills-parity.md`
- `docs/prototypes/bounded-ticket-autopilot-leaves/NOTES.md`
- `docs/prototypes/cross-host-context-rollover/NOTES.md`

So the fallback is not an edge case for two prototype notes. It covers roughly one file in ten,
and it must handle a spec with no `Artifact ID`.

## Decision

### D1 — `identity_key` per artefact kind

Exactly one key per artefact, resolved in this order:

| Kind | Key | Form |
| --- | --- | --- |
| Ticket | Envelope v1 `ticket_id`, namespaced by its folder | `ticket:<spec-slug>/<ticket_id>` |
| Spec with an Artifact Graph | `Artifact ID` verbatim | `artifact:<stable-id>` |
| Anything else | repository-relative path **at first ingest** | `path:<repo-relative-path>` |

Tickets are namespaced by folder because Envelope v1 guarantees uniqueness only *within* a
folder: `ticket_contract.py` rejects duplicate IDs during folder planning, not across the
repository. `ticket_id` must be read through `ticket-parse`, never by hand-parsing YAML.

The `path:` form is a **weak key** and is labelled as such on the page. It does not survive a
move, which is the whole point of the other two. `LW-11` lints for it so the weakness stays
visible rather than becoming an invisible correctness hole; the repair is to add an
`## Artifact Graph` to the source artefact, which is out of scope here.

### D2 — `source_digest`

```
source_digest = "sha256:" + sha256( read(path, encoding="utf-8", newline=None).encode("utf-8") ).hexdigest()
```

`newline=None` is universal-newline mode, so `CRLF` and lone `CR` normalize to `LF` **before**
hashing. This is not a preference; it is required for correctness on this repository's
platform, and it reuses the existing house idiom exactly —
`ticket_contract.py:245` (`read_ticket_text`) and `:252` (`ticket_source_digest`).

`WT-06` recorded why the alternative is wrong: hashing raw bytes and hashing normalized text
produce different digests on a Windows checkout for identical logical content, so a byte digest
reports every file as changed after a clone with `core.autocrlf` on.

The digest covers the whole file including its front matter. A change confined to front matter
is a real change to the artefact.

### D3 — The five transitions

Detection compares the corpus against the wiki on `identity_key`, and each transition has one
defined page action and one defined timeline event:

| Transition | Detected when | Page action | Timeline event |
| --- | --- | --- | --- |
| `unchanged` | identity in both, `source_digest` equal, `source_path` equal | **no write at all**, `updated` untouched | none |
| `new` | identity absent from the wiki | create the page, add it to `wiki/index.md` | `created` |
| `changed` | identity in both, digest differs, path equal | rewrite the page body, bump `updated` | **`amended`** |
| `moved` | identity in both, path differs | keep the page and its identity, rewrite `source_path`, bump `updated` | `disposition-changed` when the disposition changed, otherwise `moved` |
| `missing` | identity in the wiki, absent from the corpus | **tombstone**: keep the page and its last content, set `source_status: missing` | `source-removed` |

Two of these were the sharp questions, and both are answered against the axis rather than for
implementation convenience:

- **`changed` appends `amended`; it does not rewrite history in place.** A timeline that
  silently absorbs edits cannot be trusted about the past, which is the only reason the axis
  exists. The page body is current; the timeline keeps the amendment visible after the fact.
- **`missing` tombstones; it does not delete.** An artefact that existed is a historical fact.
  Deleting its page would make the timeline claim it never happened. The page stays, marked,
  with its last known content, and `LW-11` reports the dangling `source_path`.

`unchanged` writing nothing at all is the observable acceptance bar, not a nicety: it makes a
no-op re-ingest produce a zero-byte diff, which is the only cheap way to prove idempotence.

### D4 — Distinguishing `moved` from `missing` plus `new`

Classification is **set-based, never streaming**. One ingest must:

1. resolve the `identity_key` of every artefact matched by the globs, building the corpus
   identity set in full;
2. read the `identity_key` of every existing wiki source page, building the wiki identity set;
3. classify only then — intersection with a differing path is `moved`, wiki-only is `missing`,
   corpus-only is `new`.

A per-file streaming pass cannot do this: it sees the delete before the add, or the reverse,
and emits `missing` plus `new` for one artefact that merely moved.

**Declared limitation of the weak key.** For a `path:`-keyed artefact, moving the file changes
its own key, so a move is indistinguishable from a deletion plus a creation *by construction*.
Those eight files therefore lose their page identity if they move. This is a consequence of the
source artefact having no stable ID, not a defect in this contract, and it is the concrete cost
of the missing `## Artifact Graph` sections listed above.

### D5 — Where the fields live

Flat scalars in the wiki page's YAML front matter. No sidecar, and no nested maps:

```yaml
identity_key: ticket:windows-text-fidelity/WT-01
source_path: docs/tickets/windows-text-fidelity/done/01-body-round-trip-fidelity.md
source_digest: sha256:9f2c...
source_status: present        # present | missing
disposition: completed        # open | completed | canceled | on-hold | not-applicable
```

Front matter is safe because `LW-02` established it from the application's v0.5.4 source:
`frontmatter.ts:180` copies **every** key through with no allowlist, and the parser documents
that callers editing only the body write back `rawBlock + body` so user-managed YAML survives
untouched. A sidecar is therefore unnecessary.

**Flat is mandatory, and this is the one real constraint carried over.**
`FrontmatterValue` is `string | string[]` (`frontmatter.ts:3`) and `stringifyScalar` (`:193`)
JSON-encodes anything nested, so a nested map survives on disk but is read back by the
application as a single JSON string. `LW-04` flattened date provenance into sibling scalars for
the same reason, and its `resolve_artefact_dates` already returns that shape.

`disposition` uses the vocabulary already fixed by
[ticket-lifecycle-disposition-decision.md](ticket-lifecycle-disposition-decision.md) —
`done/` → `completed`, `canceled/` → `canceled`, `hold/` → `on-hold` — and adds
`not-applicable` for artefacts that have no lifecycle, such as specs and research notes.
`LW-04`'s `disposition_of` is the implementation of that mapping; this contract consumes it and
does not define its own.

## Fixtures `LW-05` must pass

Written here so the implementation is verified against a stated bar rather than its own
behaviour:

1. **No-op.** Ingest twice over an unchanged corpus. The second run writes **zero bytes**.
2. **Disposition move.** Move a fixture ticket into `done/` and re-ingest. Exactly one page is
   updated and **zero pages are created**. This test must be shown to fail when `identity_key`
   is replaced by a path-derived name — a test that cannot fail proves nothing.
3. **Amendment.** Edit a spec's body and re-ingest. The page body updates, `updated` advances,
   and one `amended` timeline event is appended.
4. **Touch without change.** Rewrite a file with identical content and a new mtime. Nothing is
   written, because detection is by digest and not by timestamp.
5. **Line endings.** Convert a fixture from `LF` to `CRLF` with no other change. The digest is
   unchanged and the transition is `unchanged`.
6. **Removal.** Delete a fixture artefact and re-ingest. The page survives with
   `source_status: missing` and one `source-removed` event; nothing is deleted.
7. **Weak key move.** Move a `path:`-keyed artefact. The run reports `missing` plus `new` and
   says so explicitly, rather than silently producing a duplicate.

## Rejected alternatives

- **Read `.llm-wiki/ingest-cache.json`.** Its `entries` already map a repository-relative path
  to a `hash`, a `timestamp`, and `filesWritten` — very nearly this contract, for free.
  Rejected under [the independence decision](llm-wiki-app-independence-decision.md): it would
  make every ingest depend on an application-owned file whose format is not ours and whose
  absence is indistinguishable from a first run. It remains a useful design reference.
- **Key pages on the source path.** The current convention, and the defect this contract
  exists to remove.
- **Key pages on the content digest.** A digest changes on every edit, so every amendment would
  mint a new page — the same duplication failure with a different trigger.
- **Delete the page when the artefact disappears.** Rejected under D3: it makes the timeline
  claim the artefact never existed.
- **Rewrite an amended page in place with no event.** Rejected under D3: it is the failure mode
  the axis is built to prevent.
- **Store the fields in a sidecar file.** Unnecessary, since the application preserves unknown
  front-matter keys, and worse, because a sidecar can drift from the page it describes.
- **Use `mtime` for change detection.** Wrong after clone, copy, or checkout, and fixture 4
  exists to keep it out. `LW-04` reached the same conclusion for dates.

## Unresolved questions

- **Repairing the eight weak-key artefacts** by adding `## Artifact Graph` sections to them.
  That is a change to files this plan does not own, and it is worth its own ticket. Until then,
  D4's declared limitation stands.
- **Whether `wiki/index.md` entries are keyed the same way.** `LW-05` rebuilds the index and
  the existing lint enforces one entry per page; whether the entry carries `identity_key` or
  only a link is left to `LW-05`, because nothing in this contract depends on it.
