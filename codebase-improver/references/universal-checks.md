# Universal Checks — language-agnostic anti-patterns

Bundled with this skill so the audit needs no external catalog. Applies to the whole repo (Python + TypeScript). Every finding needs `path:line` evidence. Exclude build/vendored dirs: `node_modules`, `.venv`, `venv`, `dist`, `build`, `.next`, `__pycache__`.

A hit is a *candidate* finding — confirm it's not a documented, deliberate choice (`CLAUDE.md`, decision spec, blueprint) before flagging.

## 1. Secrets in source

Hardcoded credentials, tokens, keys committed to the repo.

```bash
grep -rnE "(api[_-]?key|secret|token|password|passwd|aws_access_key|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}" \
  --include='*.py' --include='*.ts' --include='*.tsx' --include='*.env*' --include='*.yaml' --include='*.yml' . \
  | grep -vi "example\|placeholder\|dummy\|test\|os.environ\|process.env"
```

Real secret → **blocker**. Recommend moving to env/secret manager and rotating. Do NOT print the secret value back in full.

## 2. Dependency-direction inversion

An import that reverses the architectural arrow (e.g. a `domain`/`core` layer importing `infrastructure`/`adapters`). Strongest when a blueprint declares the direction; otherwise infer from folder names.

```bash
# Python
grep -rn "import.*\(infrastructure\|adapters\)\|from.*\(infrastructure\|adapters\)" --include='*.py' <core-or-domain-path>/
# TypeScript
grep -rnE "from ['\"].*(infra|adapters|repository)" --include='*.ts' --include='*.tsx' <core-or-domain-path>/
```

## 3. Swallowed exceptions

Catch blocks that hide errors.

```bash
# Python: bare except / except-pass
grep -rnE "except\s*:|except [A-Za-z]+\s*:\s*$" --include='*.py' .   # then inspect for `pass`
grep -rn -A1 "except" --include='*.py' . | grep -B1 "pass"
# TypeScript: empty catch
grep -rnE "catch\s*\([^)]*\)\s*\{\s*\}" --include='*.ts' --include='*.tsx' .
```

Empty/`pass` catch with no logging or re-raise → should-fix.

## 4. Type-checker / linter silencing

Suppressions added without justification.

```bash
grep -rn "# type: ignore\|# noqa" --include='*.py' .
grep -rn "@ts-ignore\|@ts-nocheck\|eslint-disable" --include='*.ts' --include='*.tsx' .
```

Each suppression should have a reason comment. Bare suppressions are findings (nit→should-fix depending on what they hide).

## 5. Security regressions / risky calls

```bash
# Python: dynamic exec, shell=True, yaml.load, pickle on untrusted input
grep -rnE "\beval\(|\bexec\(|shell\s*=\s*True|yaml\.load\(|pickle\.load" --include='*.py' .
# TypeScript: eval, dangerouslySetInnerHTML, child_process exec with interpolation
grep -rnE "\beval\(|dangerouslySetInnerHTML|child_process|exec\(" --include='*.ts' --include='*.tsx' .
```

Confirm context before flagging — some are legitimate. Untrusted input reaching these → blocker.

## 6. Missing / removed tests

- Map each source module to its expected test file. Modules with public behavior and no test are should-fix candidates ("add tests before refactoring").
- If git history is available, check whether the diff under review (or recent commits) deleted test files without a stated reason.

```bash
# Rough test presence ratio
echo "src files:"; find . -name '*.py' -o -name '*.ts' -o -name '*.tsx' | grep -vE "test|spec|node_modules|.venv" | wc -l
echo "test files:"; find . -iname '*test*' -o -iname '*spec*' | grep -vE "node_modules|.venv" | wc -l
```

## 7. Broad / unpinned dependencies

- Python: unpinned versions in `requirements.txt` (no `==`), or overly broad ranges in `pyproject.toml`.
- TypeScript: wildcard versions (`"*"`) or very loose ranges in `package.json`.

Report as should-fix; pinning is a small, safe theme.

---

## Severity guidance

| Tier | Examples |
|------|----------|
| **blocker** | live secret, untrusted input → `eval`/shell, auth/validation removed |
| **should-fix** | swallowed exceptions, dependency inversion, missing tests on core logic, unpinned deps |
| **nit** | bare lint suppression with low blast radius, minor naming inconsistency |

When a finding sits between tiers, leave it for Checkpoint A — don't finalize severity alone.
