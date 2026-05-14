# Universal checks — project-independent observations

Things to look for in any codebase regardless of its declared architecture. Emit these **only when the user explicitly asks for a universal sweep** — by default, the blueprint is descriptive and these are not part of it.

When emitted, they go to chat as ephemeral output, **not** to a persistent `UNIVERSAL_NOTES.md` file. The blueprint is the only persistent artifact.

---

## When to run universal checks

The user asks something like:
- *"Run a universal sweep on this project"*
- *"Are there any anti-patterns regardless of architecture?"*
- *"Security / config / coupling check"*

Otherwise: don't run. Stay descriptive.

---

## Categories

### Manifest-level dependency direction

Read every manifest (`*.csproj`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml`...). Build the inter-module dependency graph. Compare against:
- The pattern the project labels itself with (if it claims Hexagonal/Clean/Onion, arrows must point inward)
- Common sense: a "Domain" module should not declare references to "Infrastructure"

**Severity**: high. Manifest-level inversions hold for every file in the module, not just one.

```bash
# .NET
grep -rn 'ProjectReference Include=".*Application' src/Infrastructure/ 2>/dev/null
grep -rn 'ProjectReference Include=".*Infrastructure' src/Domain/ 2>/dev/null
```

---

### Secrets in repository

High-entropy strings in committed files. Includes `.env` files (not `.env.example`), config files with full keys, hardcoded credentials.

```bash
git log --all --full-history -- .env 2>/dev/null | head
grep -rEn '[A-Za-z0-9+/]{40,}={0,2}' src/**/appsettings*.json 2>/dev/null
grep -rEn 'password\s*=\|api_key\s*=\|secret\s*=' --include='*.py' --include='*.ts' --include='*.cs' .
```

Recognizable formats (Azure keys, full HMAC, JWT secrets, AWS keys) get indexed by secret scanners.

**Severity**: high.

---

### Hardcoded defaults in centralized config classes

When a project uses typed Options / Settings classes, the defaults baked into source are hidden config. Each default should answer: *"is this safe if not overridden at boot?"*

Dangerous defaults:
- Environment names (`"production"`, `"prod"`, `"live"`, `"default"`)
- URLs to external services
- Sampling rates ≥ 0.5
- High retry counts, generous timeouts masking failure

**Step 1 — Find candidate files** by name (any language):

```bash
find . -type f \( \
  -iname '*Options.*' -o -iname '*Settings.*' -o -iname '*Config.*' \
  -o -name 'config.py' -o -name 'settings.py' \
  -o -name 'config.ts' -o -name 'config.js' -o -name 'config.go' \
  -o -name 'appsettings*.json' \
\) -not -path '*/node_modules/*' -not -path '*/bin/*'
```

**Step 2 — For each candidate**: read the file. List every property/field with its literal default. Don't rely on grep alone; defaults take many shapes per language.

**Per-language syntax cheat sheet** (helpers, not exhaustive):

| Language | Default-value syntax |
|---|---|
| C# (records / props) | `public string X { get; init; } = "value";` |
| Java (Spring) | `private String x = "value";` or `@Value("${x:value}")` |
| Kotlin (data class) | `val x: String = "value"` |
| Python (pydantic-settings, dataclass) | `x: str = "value"` |
| Go (struct tags, viper) | `default:"value"` or `viper.SetDefault("x", "value")` |
| TypeScript / JavaScript (zod, manual) | `.default("value")` or `x: "value"` |
| Rust (serde) | `#[serde(default = "fn_returning_value")]` |
| PHP | `public string $x = "value";` |
| Ruby | `@x = "value"` in initializer |
| F# | `member val X = "value" with get` |
| Scala | `val x: String = "value"` |
| Elixir | `defstruct x: "value"` |

**Severity**: medium, escalate to high when a default has security weight.

---

### Same value duplicated across files

The same URL / magic string / number in 2+ places — usually Options default + DI fallback + maybe inline. Future changes must touch all.

```bash
# URLs appearing more than once
grep -rE 'https?://[^"]+' src/ | grep -oE 'https?://[^"]+' | sort | uniq -c | awk '$1 > 1'
```

**Severity**: low to medium.

---

### Env vars sprinkled outside the config module

`process.env`, `os.environ`, `Environment.GetEnvironmentVariable` accessed inside business logic, adapters, or domain — when the project uses centralized typed config elsewhere.

```bash
grep -rn "process\.env\|os\.environ\|os\.getenv\|Environment\.GetEnvironmentVariable" \
  --include='*.cs' --include='*.py' --include='*.ts' --include='*.go' \
  src/ | grep -vE 'config|settings|options|Program\.|DependencyInjection\.'
```

**Severity**: medium.

---

### Catch-and-swallow

Empty exception handlers — silent failures hide bugs.

```bash
grep -rn 'except.*:\s*pass\|catch.*{\s*}' --include='*.py' --include='*.cs' --include='*.ts' .
```

**Severity**: high.

---

### Type-checker / linter suppressions without justification

`@ts-ignore`, `# type: ignore`, `@SuppressWarnings`, `# noqa`, `eslint-disable` without a comment explaining why.

```bash
grep -rEn '@ts-ignore|# type: ignore|@SuppressWarnings|# noqa|eslint-disable' src/ | grep -vE '#.*because|#.*reason|//.*because'
```

**Severity**: low to medium.

---

### Disabled tests

Tests marked skipped/ignored without justification in the test name or comment.

```bash
grep -rn 'skip\|xit\(\|xdescribe\|@Ignore\|@pytest\.mark\.skip\|t\.Skip' tests/ test/ __tests__/ 2>/dev/null
```

**Severity**: medium.

---

### Hidden side effects on module import

Top-level code in modules that opens DB connections, hits HTTP endpoints, mutates global state.

Read the top of each module — anything beyond imports and definitions is a side effect.

**Severity**: medium to high — makes testing miserable, hides ordering dependencies.

---

### Mutable static state in DI-managed code

Singleton classes with mutable static fields (instead of singleton-instance fields). Defeats DI: replacing the implementation in tests doesn't help because consumers read the static.

**Severity**: medium to high depending on what state.

---

## Format of the output

When the user asks for a universal sweep:

```markdown
## Universal sweep — <project name>

Run on <date>. These findings are independent of the project's declared
architecture. They are emitted to chat only; not saved as a file.

### Category 1: <name>
<findings, with file:line>

### Category 2: <name>
<findings>

### Summary
- High: N
- Medium: M
- Low: K

Want me to save this as a markdown file in `docs/architecture/universal-sweep-<date>.md`?
Otherwise it stays in chat history only.
```

Only save if the user explicitly says yes. The default is ephemeral.

---

## What this is NOT

This file is **not** a catalog of slice anti-patterns or project-specific issues. Those belong in the blueprint's slice constraints (what's required) and in the PR review's slice deviation findings (what's wrong vs blueprint).

This file is **universal noise** — things worth pointing out regardless of how the project is structured.
