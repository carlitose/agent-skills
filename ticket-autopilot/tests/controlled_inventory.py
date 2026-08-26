"""The controlled skill inventory shared by the context-budget baseline tests.

`test_context_budget` and `test_token_reduction_guide` both install every repository
skill into a temporary root except the names below, so the documented baseline does not
depend on an operator's changing personal installation. The set lived in both modules as
separate literals until one of them was updated and the other was not, which left the
guide assertions red while the inventory assertions passed. One definition prevents that.

`llm-wiki` is vendored in the repository and installed nowhere, so it belongs here with the
others. Installing it would raise the composed total to 166,855 normalized UTF-8 bytes and
move the ceiling status to `exceeded`, which is a deliberate budget decision rather than a
side effect of vendoring.
"""

from __future__ import annotations

REPOSITORY_ONLY_SKILLS = frozenset(
    {
        "peer-programming",
        "pr-antipattern-review",
        "project-blueprint",
        "llm-wiki",
    }
)
