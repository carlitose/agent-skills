# Diff-specific checks

Patterns that are easy to detect by grepping the diff itself, regardless of blueprint or project. Useful as a quick sweep before or alongside slice comparison.

These are most useful as **detection mechanics**. The actual severity and framing comes from `slice-comparison.md` (when there's a blueprint) or `universal-checks.md` (when there isn't).

---

## What to grep for in added lines

### New secret committed

```bash
# Lines that look like secrets
git diff <base>...HEAD | grep '^\+' | grep -Ei 'api[_-]?key|secret|password|token|hmac|jwt' | grep -E '[A-Za-z0-9+/]{32,}'

# Long base64-shaped strings appearing fresh
git diff <base>...HEAD | grep -E '^\+.*[A-Za-z0-9+/]{40,}={0,2}'
```

### Manifest-level dependency change

```bash
# .NET
git diff <base>...HEAD -- '*.csproj'

# JS monorepo
git diff <base>...HEAD -- 'package.json' '**/package.json'

# Go
git diff <base>...HEAD -- 'go.mod'

# Java/Maven
git diff <base>...HEAD -- 'pom.xml'
```

Read the diff against the project's declared layering rules (in BLUEPRINT.md).

### Security regression

```bash
# Permissive auth / validation removed
git diff <base>...HEAD | grep -E '^\+' | grep -E 'AllowAnyOrigin\(\)|ValidateIssuer\s*=\s*false|ValidateAudience\s*=\s*false|verify\s*=\s*False|rejectUnauthorized:\s*false'

# Wildcard permissions
git diff <base>...HEAD | grep -E '^\+' | grep -E 'chmod 777|0o777|public-read-write'

# Auth attributes removed
git diff <base>...HEAD | grep -E '^-' | grep -E '\[Authorize\]|@auth_required|requires_auth'
```

### Test removed

```bash
# Test files deleted
git diff <base>...HEAD --stat | grep -E 'test|spec' | grep -E '^-'

# Tests freshly skipped
git diff <base>...HEAD | grep -E '^\+' | grep -E 'skip\|xit\(|xdescribe|@Ignore|@pytest\.mark\.skip|t\.Skip'
```

If diff shows tests removed/skipped, read the PR description for justification. Without justification = blocker.

### Env var read sprinkled

```bash
git diff <base>...HEAD | grep -E '^\+' | grep -E 'process\.env\.|os\.environ|os\.getenv|os\.Getenv|Environment\.GetEnvironmentVariable' | grep -vE 'config|settings|options|Program\.|DependencyInjection\.|main\.py'
```

### Hardcoded default in Options / Config / Settings class

**Step 1 — Find candidate files (any language)**: filename-based, agnostic.

```bash
git diff <base>...HEAD --name-only | grep -iE \
  '(Options|Settings|Config)\.(cs|java|kt|scala|ts|js|go|rb|php|fs)$|^.*(config|settings)\.(py|toml|yaml|yml)$|appsettings.*\.json$'
```

**Step 2 — For each candidate**: read the file content. List every property/field with its literal default value. Don't rely on grep alone — defaults take many shapes per language and a grep that misses one is silent failure.

**Step 3 — Classify each default**. Flag any that fall into these categories:

- Environment name (`"production"`, `"prod"`, `"live"`, `"default"`)
- URL to external service (`https://...`)
- Sampling / capture rate ≥ 0.5
- Operational tuning that masks failure (high retries, generous timeouts, default-on dangerous features)

**Per-language syntax cheat sheet** (helpers, not exhaustive):

| Language | Default-value syntax |
|---|---|
| C# (records / props) | `public string X { get; init; } = "value";` |
| Java (Spring `@ConfigurationProperties`, fields) | `private String x = "value";` or `@Value("${x:value}")` |
| Kotlin (data class) | `val x: String = "value"` |
| Python (pydantic-settings, dataclass) | `x: str = "value"` |
| Go (struct tags, viper) | `default:"value"` in struct tags, or `viper.SetDefault("x", "value")` |
| TypeScript / JavaScript (zod, manual) | `.default("value")` or object literal `x: "value"` |
| Rust (serde) | `#[serde(default = "fn_returning_value")]` |
| PHP | `public string $x = "value";` |
| Ruby | `@x = "value"` in initializer |
| F# | `member val X = "value" with get` |
| Scala | `val x: String = "value"` |
| Elixir / Erlang | `@x "value"` module attribute, or pattern `defstruct x: "value"` |

The grep finds the file; reading finds the defaults. Don't be language-specific in detection if the language isn't yours.

### Same hardcoded value duplicated

```bash
# URLs added more than once in this diff
git diff <base>...HEAD | grep '^\+' | grep -oE 'https?://[^"]+' | sort | uniq -c | awk '$1 > 1'

# Long string literals appearing more than once
git diff <base>...HEAD | grep '^\+' | grep -oE '"[^"]{15,}"' | sort | uniq -c | awk '$1 > 1'
```

### Catch-and-swallow

```bash
# Python
git diff <base>...HEAD | grep -E '^\+' | grep -A1 'except.*:' | grep -E '^\+\s*pass$'

# Java / C# / JS / TS
git diff <base>...HEAD | grep -E '^\+.*catch.*\{\s*\}$'
```

### Type-checker / linter suppression added

```bash
git diff <base>...HEAD | grep -E '^\+' | grep -E '@ts-ignore|# type: ignore|@SuppressWarnings|# noqa|eslint-disable'
```

If the line has a justifying comment → drop to nit. Without justification → should-fix.

### Debug statements left in

```bash
git diff <base>...HEAD | grep -E '^\+' | grep -E 'console\.log|print\(|fmt\.Println|dbg!\(|System\.out\.println' | grep -v 'test\|spec'
```

### TODO / FIXME without ticket

```bash
git diff <base>...HEAD | grep -E '^\+' | grep -E 'TODO|FIXME|XXX|HACK' | grep -vE '#[0-9]+|[A-Z]+-[0-9]+'
```

---

## Reading the PR description

Always scan the PR title and body — they affect how findings are weighted:

- Stated trade-offs → finding may drop a tier (e.g., "removed validation because X" — should-fix instead of blocker)
- Ticket / decision spec links → context for variant decisions
- Title vs scope mismatch → flag for follow-up (a "fix typo" PR touching 30 files deserves a question)

This step doesn't usually produce findings on its own; it informs how to weight everything else.

---

## What this file is NOT

This file is a **toolbox of greps**, not a finding catalog. The actual decision (is this a blocker, what slice does it deviate from, what to recommend) comes from:

- **Slice comparison** when a blueprint exists (`slice-comparison.md`)
- **Universal checks** when it doesn't (`universal-checks.md`)

Grep gives evidence. Severity and framing come from the blueprint or universal rules.
