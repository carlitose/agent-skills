"""Python AST function hunks between observed Git trees; unsupported files stay visible."""
from __future__ import annotations

import ast
import difflib
import subprocess
from pathlib import Path

from autopilot.git_ops import candidate_files


def _functions(text: str) -> dict[str, str]:
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    result = {}

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = min([child.lineno, *(dec.lineno for dec in child.decorator_list)])
                    result[name] = "".join(lines[start-1:child.end_lineno])
                visit(child, name + ".")
            else:
                visit(child, prefix)
    visit(tree)
    return result


def changed_functions(worktree: Path, candidate) -> tuple[list[dict], list[dict]]:
    functions, unsupported = [], []
    for name in candidate_files(worktree, candidate):
        path = worktree / name
        if not name.endswith(".py"):
            unsupported.append({"path": name, "reason": "unsupported language"})
            continue
        try:
            base = subprocess.run(["git", "show", f"{candidate.base_tree_oid}:{name}"],
                                  cwd=worktree, capture_output=True, check=False, timeout=30)
            old = base.stdout.decode("utf-8") if base.returncode == 0 else ""
            new = path.read_text(encoding="utf-8") if path.is_file() else ""
            before, after = _functions(old), _functions(new)
        except (SyntaxError, UnicodeError, OSError) as error:
            unsupported.append({"path": name, "reason": f"Python AST unavailable: {type(error).__name__}"})
            continue
        for qualified in sorted(set(before) | set(after)):
            previous, current = before.get(qualified), after.get(qualified)
            if previous == current:
                continue
            kind = "deleted" if current is None else "added" if previous is None else "modified"
            hunk = "".join(difflib.unified_diff((previous or "").splitlines(keepends=True),
                (current or "").splitlines(keepends=True), fromfile=f"old/{name}:{qualified}",
                tofile=f"new/{name}:{qualified}"))
            functions.append({"path": name, "function": qualified, "change": kind, "hunk": hunk})
    return functions, unsupported
