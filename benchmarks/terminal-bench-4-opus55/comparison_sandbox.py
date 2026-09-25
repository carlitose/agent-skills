"""Task-local Git/source observations. Executed inside the comparison container."""
import ast
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MAX_DIFF = 16384


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), "-c", "core.autocrlf=false",
                                    "-c", "core.hooksPath=/dev/null", *args],
                                   stderr=subprocess.PIPE, timeout=30)


def owned(root, base):
    if (not re.fullmatch(r"[a-f0-9]{40}", base) or not (root / ".git/tbf-owned").is_file()
            or (root / ".git").is_symlink()
            or git(root, "rev-parse", "HEAD").decode().strip() != base):
        raise ValueError("task Git ownership or baseline changed")


def fingerprint(root, base):
    root = Path(root)
    owned(root, base)
    files, directories = [], []
    for directory, dirs, names in os.walk(root, followlinks=False):
        if Path(directory) == root:
            dirs[:] = [name for name in dirs if name != ".git"]
        for name in list(dirs):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                dirs.remove(name)
                names.append(name)
            else:
                directories.append(relative)
        for name in sorted(names):
            path = Path(directory) / name
            if path.is_symlink():
                digest = {"link": os.readlink(path)}
            elif path.is_file():
                h = hashlib.sha256()
                with path.open("rb") as source:
                    while block := source.read(1048576):
                        h.update(block)
                digest = {"sha256": h.hexdigest(), "mode": path.stat().st_mode & 0o777}
            else:
                raise ValueError("unsupported task filesystem entry")
            files.append({"path": path.relative_to(root).as_posix(), **digest})
            if len(files) > 10000:
                raise ValueError("task file bound exceeded")
    git(root, "add", "-f", "-A")
    manifest = json.dumps(sorted(files, key=lambda row: row["path"]), sort_keys=True).encode()
    return {"head": base, "tree": git(root, "write-tree").decode().strip(),
            "source_sha256": hashlib.sha256(manifest).hexdigest(),
            "directories": sorted(directories), "files": len(files)}


def rollback(root, base, directories):
    root = Path(root)
    owned(root, base)
    if any(not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts for name in directories):
        raise ValueError("unsafe baseline directory")
    git(root, "reset", "--hard", base)
    git(root, "clean", "-ffdx")
    for name in directories:
        (root / name).mkdir(parents=True, exist_ok=True)


def functions(text):
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    found = {}
    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = min([child.lineno, *(item.lineno for item in child.decorator_list)])
                    found[name] = "".join(lines[start - 1:child.end_lineno])
                visit(child, name + ".")
            else:
                visit(child, prefix)
    visit(tree)
    return found


def collect_changes(root, base):
    root = Path(root)
    fingerprint(root, base)
    diff = git(root, "diff", "--cached", "--no-ext-diff", "--no-textconv", base, "--").decode("utf8")
    if len(diff.encode()) > MAX_DIFF:
        raise ValueError("candidate diff exceeds declared 16-KiB semantic review bound")
    names = git(root, "diff", "--cached", "--name-only", "-z", base, "--").decode().split("\0")
    changed, unsupported = [], []
    for name in filter(None, names):
        if not name.endswith(".py"):
            unsupported.append({"path": name, "reason": "not a Python function"})
            continue
        path = root / name
        try:
            try:
                old = git(root, "show", f"{base}:{name}").decode("utf8")
            except subprocess.CalledProcessError:
                old = ""
            new = path.read_text(encoding="utf8") if path.is_file() and not path.is_symlink() else ""
            before, after = functions(old.replace("\r\n", "\n")), functions(new.replace("\r\n", "\n"))
            file_changes = 0
            for function in sorted(set(before) | set(after)):
                if before.get(function) == after.get(function):
                    continue
                hunk = "".join(difflib.unified_diff(before.get(function, "").splitlines(keepends=True),
                    after.get(function, "").splitlines(keepends=True), fromfile=f"old/{name}:{function}",
                    tofile=f"new/{name}:{function}"))
                changed.append({"path": name, "function": function, "hunk": hunk})
                file_changes += 1
            # Function inventory is not whole-file coverage. The reviewer also gets
            # the full bounded diff, including imports, constants and class bodies.
            unsupported.append({"path": name, "reason": "whole-file context outside function inventory",
                                "changed_functions": file_changes})
        except (SyntaxError, UnicodeError, OSError):
            unsupported.append({"path": name, "reason": "Python source unavailable"})
    if len(changed) > 32 or sum(len(row["hunk"].encode()) for row in changed) > MAX_DIFF:
        raise ValueError("function risk inventory exceeds declared bound")
    return {"diff": diff, "functions": changed, "unsupported": unsupported}


if __name__ == "__main__":
    operation, base = sys.argv[1:3]
    root = Path("/app")
    if operation == "fingerprint":
        result = fingerprint(root, base)
    elif operation == "changes":
        result = collect_changes(root, base)
    elif operation == "rollback":
        rollback(root, base, json.loads(sys.argv[3]))
        result = fingerprint(root, base)
    else:
        raise ValueError("unknown sandbox observation")
    print(json.dumps(result, sort_keys=True))
