"""NON-PRODUCTION: small, adapted examples, not historical execution evidence.

Wording/heading shapes are grounded in the listed repository sources at baseline
6b8ea103d4e5bb0e188116984a64882c5d77e53e. IDs, dependencies and combinations of
sections are deliberately synthetic. No external diagnosed corpus is copied.
"""

QUESTIONS = ("intent", "acceptance", "testing", "frontier", "exclusions", "decisions", "evidence")

TICKET = '''---
ticket_schema: 1
ticket_id: "{id}"
execution_mode: AFK
blocked_by: {blockers}
---

# {title}

## Artifact Graph
- Artifact ID: `artifact:fixture-{id}`
- Role: `ticket`
- Parent: [map](../../specs/map.md)

{body}
'''

LATE_FACT = "Do not infer historical gate causes."
EDITED_FACT = "Do not install packages from this fixture."

FIXTURES = [
    {
        "path": "docs/tickets/family/01.md", "kind": "ticket",
        "source": "docs/tickets/llm-wiki-semantic-coverage/done/05-require-visible-stage-gate-causes.md",
        "text": TICKET.format(id="FX-01", blockers="[]", title="Retain precise causes", body=(
            "## What to Build\nReject blank reasons before a ledger mutation.\n\n"
            "## Acceptance Criteria\nWhitespace-only reasons leave the ledger unchanged.\n\n"
            "## Testing Plan\nRun the stage-gate regression in a temporary repository.\n\n"
            "## Frontier\nA human decision is required for historical repair.\n\n"
            "## Out of Scope\n" + "This experiment concerns only temporary local inputs. " * 9
            + LATE_FACT + "\n\n"
            "## Decisions\nPreserve recorded causes literally.\n\n"
            "## Evidence\nThese fixture statements are not live execution evidence.\n"
        )),
        "answers": {
            "intent": "Reject blank reasons before a ledger mutation.",
            "acceptance": "Whitespace-only reasons leave the ledger unchanged.",
            "testing": "Run the stage-gate regression in a temporary repository.",
            "frontier": "A human decision is required for historical repair.",
            "exclusions": LATE_FACT,
            "decisions": "Preserve recorded causes literally.",
            "evidence": "These fixture statements are not live execution evidence.",
        },
    },
    {
        "path": "docs/tickets/family/02.md", "kind": "ticket",
        "source": "docs/tickets/autopilot-practical-reliability/done/07-progressive-references.md",
        "text": TICKET.format(id="FX-02", blockers='\n  - "FX-01"', title="Retrieve the right procedure", body='''## What to Build
Move rare procedures behind explicit retrieval triggers.

## Acceptance Criteria
Each branch must resolve to one shared operator owner.

### Verification approach
Resolve every disclosed local reference.

## Frontier
This fixture does not grant publication authority.

## Out of Scope
Do not change installed skill copies.

## Decisions
Measure normalized UTF-8 bytes rather than model tokens.

## Evidence
The comparison uses a controlled installation fixture.
'''),
        "answers": {
            "intent": "Move rare procedures behind explicit retrieval triggers.",
            "acceptance": "Each branch must resolve to one shared operator owner.",
            "testing": "Resolve every disclosed local reference.",
            "frontier": "This fixture does not grant publication authority.",
            "exclusions": "Do not change installed skill copies.",
            "decisions": "Measure normalized UTF-8 bytes rather than model tokens.",
            "evidence": "The comparison uses a controlled installation fixture.",
        },
    },
    {
        "path": "docs/specs/map.md", "kind": "spec",
        "source": "docs/specs/llm-wiki-semantic-coverage-wayfinder.md",
        "text": '''# Source-grounded semantic coverage

## Artifact Graph
- Artifact ID: `artifact:fixture-map`
- Role: `wayfinder`
- Standalone: true

### Children
- [one](../tickets/family/01.md)
- [two](../tickets/family/02.md)

## Destination
A wiki reader should recover build intent without opening the source.

## Acceptance Criteria
A semantic edit must change visible page content.

## Testing Plan
Compare the same corpus under each projection.

## Frontier / Blocking Edges
The human policy decision remains unresolved.

## Out of Scope
Do not modify the production compiler in this experiment.

## Decisions So Far
Repository documents remain authoritative.

## Evidence
The production renderer currently retains metadata rather than source sections.
''',
        "answers": {
            "intent": "A wiki reader should recover build intent without opening the source.",
            "acceptance": "A semantic edit must change visible page content.",
            "testing": "Compare the same corpus under each projection.",
            "frontier": "The human policy decision remains unresolved.",
            "exclusions": "Do not modify the production compiler in this experiment.",
            "decisions": "Repository documents remain authoritative.",
            "evidence": "The production renderer currently retains metadata rather than source sections.",
        },
    },
    {
        "path": "docs/research/forward.md", "kind": "research",
        "source": "docs/research/llm-wiki-docs-only-autosync-forward-test.md",
        "text": '''# Local sync observations

## Artifact Graph
- Artifact ID: `artifact:fixture-research`
- Role: `research`
- Standalone: true

## Result
Missing wikis are never scaffolded by synchronization.

## Reproduce
Run the wiki-sync forward matrix against disposable repositories.

## Limitations
Provider participants are deterministic fakes, not live services.
''',
        "answers": {
            "intent": None, "acceptance": None, "frontier": None,
            "testing": "Run the wiki-sync forward matrix against disposable repositories.",
            "exclusions": "Provider participants are deterministic fakes, not live services.",
            "decisions": "Missing wikis are never scaffolded by synchronization.",
            "evidence": "Provider participants are deterministic fakes, not live services.",
        },
    },
    {
        "path": "docs/prototypes/sync/NOTES.md", "kind": "prototype",
        "source": "docs/prototypes/llm-wiki-docs-only-autosync/NOTES.md",
        "text": '''# Disposable synchronization experiment

## Artifact Graph
- Artifact ID: `artifact:fixture-prototype`
- Role: `prototype`
- Standalone: true

## Prototype frame
Can generated synchronization retain a separate identity?

## Run
Execute the local fixture runner without contacting a provider.

## Keep, discard, decide
A human must select the production request owner.

## Result
An integrated application identity must not be reused for wiki delivery.

## Limits
Crash recovery remains a policy gap rather than a proven behavior.
''',
        "answers": {
            "intent": "Can generated synchronization retain a separate identity?",
            "acceptance": None,
            "testing": "Execute the local fixture runner without contacting a provider.",
            "frontier": "A human must select the production request owner.",
            "exclusions": "Crash recovery remains a policy gap rather than a proven behavior.",
            "decisions": "An integrated application identity must not be reused for wiki delivery.",
            "evidence": "Crash recovery remains a policy gap rather than a proven behavior.",
        },
    },
    {
        "path": "docs/guides/context.md", "kind": "guide",
        "source": "docs/autopilot-context-cost-guide.md",
        "text": '''# Context-cost guide without a stable ID

Purpose
-------
Compare a controlled static prefix rather than session consumption.

## Reproduce
Run the controlled context-budget fixture.

## Operator behavior
Conditional references add bytes when they are loaded.

## Limits
Static UTF-8 byte counts are not observed model tokens.

```markdown
## Acceptance Criteria
This fenced heading is an example, not a real section.
```
''',
        "answers": {
            "intent": "Compare a controlled static prefix rather than session consumption.",
            "acceptance": None, "frontier": None,
            "testing": "Run the controlled context-budget fixture.",
            "exclusions": "Static UTF-8 byte counts are not observed model tokens.",
            "decisions": "Conditional references add bytes when they are loaded.",
            "evidence": "Static UTF-8 byte counts are not observed model tokens.",
        },
    },
]

# Human-readable, agent-authored fixture summaries. These are deliberately not
# generated from the query answers. Binding their original digest makes edit
# staleness observable without pretending that an LLM was invoked or audited.
AUTHORED = {
    "docs/tickets/family/01.md": "Reject blank reasons before a ledger mutation. Do not infer historical gate causes.",
    "docs/tickets/family/02.md": "Move rare procedures behind explicit retrieval triggers.",
    "docs/specs/map.md": "Repository documents remain authoritative.",
    "docs/research/forward.md": "Missing wikis are never scaffolded by synchronization.",
    "docs/prototypes/sync/NOTES.md": "A human must select the production request owner.",
    "docs/guides/context.md": "Static UTF-8 byte counts are not observed model tokens.",
}
