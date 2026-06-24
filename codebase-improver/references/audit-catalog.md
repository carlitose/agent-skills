# Audit Catalog — whole-repo health signals

Signals to sweep across the entire codebase in Stage 2. These complement the bundled `universal-checks.md`. Every finding needs `path:line` evidence.

Detection commands assume a Unix shell. This catalog targets **Python** and **TypeScript** only. Always exclude vendored/build dirs: `node_modules`, `.venv`, `venv`, `dist`, `build`, `.next`, `__pycache__`, `.mypy_cache`, `.pytest_cache`.

## 1. God files / classes

Files or classes that accumulate too many responsibilities.

```bash
# Largest source files by line count
find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) \
  -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/dist/*' \
  -exec wc -l {} + | sort -rn | head -20
```

Threshold is a smell, not a rule: investigate files in the top decile or > ~400 lines. For classes, count methods. A service with 20+ public methods is a refactor candidate. If a blueprint exists, confirm against it — some modules legitimately have large canonical files.

## 2. Duplication clusters

Repeated logic that should be extracted.

```bash
# If jscpd is available (npx jscpd .) — reports copy-paste blocks
npx jscpd --min-lines 8 --reporters consoleFull .
```

No tool? Grep for repeated function bodies / similar signatures. Group findings: "block duplicated in A, B, C" is one theme, not three.

## 3. Dead code

Unused exports, unreachable branches, orphan modules.

- Python: `vulture .` (if available), or `ruff` with the unused-import/variable rules (`F401`, `F841`).
- TypeScript: `ts-prune` or `knip` for unused exports; `eslint` `no-unused-vars` for locals; `tsc --noUnusedLocals`.
- Fallback: search for symbols never imported anywhere.

Verify before flagging — reflection, DI registration, and dynamic dispatch hide real usage.

## 4. Cyclomatic / cognitive hotspots

Deeply nested or branch-heavy functions.

- Python: `ruff` (`C901`) or `radon cc -s -n C .`.
- TypeScript: `eslint` `complexity` rule, or `ts-complexity` / `code-complexity`.
- Fallback: look for functions with deep nesting, long `if/elif` ladders, big `switch`.

## 5. Layering leaks

Imports that cross the dependency arrow (e.g. a domain layer importing infrastructure). If a blueprint declares the direction, anchor to it; otherwise infer the intended direction from folder naming.

```bash
# Python: a domain layer importing infrastructure
grep -rn "import.*infrastructure\|from.*infrastructure" --include='*.py' <domain-path>/

# TypeScript: a domain/core layer importing an adapters/infra layer
grep -rn "from ['\"].*\(infra\|adapters\)" --include='*.ts' --include='*.tsx' <domain-path>/
```

Anchor to the blueprint's declared dependency direction if one exists; otherwise flag as a suggestion based on the inferred layering.

## 6. Configuration sprinkle

Env vars / magic values read inline instead of through a typed config object.

```bash
grep -rn "os.environ\|getenv\|process.env" --include='*.py' --include='*.ts' . \
  | grep -v -i "config\|settings"
```

## 7. Test coverage gaps

Slices or modules with no test mirror.

- Map each source module to its expected test path (mirror the source tree, or the blueprint's co-created files if one exists).
- Flag instances missing a test. These are prime "add tests before refactoring" themes.

## 8. Undocumented public API

Exported functions/classes/endpoints with no docstring or doc comment.

- Python: public functions/classes (not prefixed `_`) lacking a docstring.
- TypeScript: exported symbols lacking a TSDoc/JSDoc comment.
- If the project exposes an HTTP API and declares an OpenAPI spec in its blueprint, flag endpoints missing from the spec.

## 9. Stale dependencies / security

```bash
# Python
pip list --outdated 2>/dev/null
# TypeScript / Node
npm outdated 2>/dev/null
npm audit 2>/dev/null
```

Report outdated majors and known-vuln packages as should-fix themes. Do NOT auto-upgrade — that's a refactor theme requiring approval and tests.

---

## Turning signals into findings

For each hit:
- Record `path:line`.
- Assign a **category** (one of the above) and an **anchor** (blueprint rule if one exists, `universal`, or `none`).
- Propose a **severity**, but leave contested ones for Checkpoint A.
- Group related hits so they cluster cleanly into themes in Stage 3.
