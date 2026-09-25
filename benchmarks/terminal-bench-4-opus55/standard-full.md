# Original Terminal-Bench with our Pi

Implementation scope: [TBF-06](../../docs/tickets/terminal-bench-4-opus55/06-adapt-original-harbor-to-pi.md). This is an adapter, **not an executed full benchmark or a new spending grant**. Historical standard/modified receipts are unchanged.

## What runs

`standard_full:FullStandardPiHarborAgent` is a native Harbor `BaseAgent`. It discovers the task from Harbor's `environment_dir` public metadata, checks it against all **66** entries of `manifest.json`, and compares the original environment configuration and instruction. It then runs one host Pi session (`openai-codex/gpt-6-sol`, high), exposing only `sandbox_exec`. The proven subprocess transport, in-container command timeout and fsynced usage journal are reused from the comparison code, **not its Git setup, public smoke or semantic gates**. No tool/skill/helper is uploaded, no Git is created/removed, and there is no `/app` assumption. Original environments with existing Git are valid.

Harbor still owns setup resources, artifact export, original verifier and reward. Agent completion is not a passing reward. Unsupported original task features (multi-step, non-Linux, *added agent-side* MCP/skills, missing digest-pinned image or GNU timeout) stop explicitly rather than changing the task. Harbor forwards task-declared `skills_dir` and MCP server metadata to the agent; these are accepted only when they exactly match the frozen original task configuration. Pi still exposes **only `sandbox_exec`**: it does not mount task skills into its own host SDK or register task MCP servers as Pi tools. Those resources remain in the native task environment; functional access, especially to the `medical-claims-processing` Playwright MCP server, is unverified. Metadata is checked without opening solution/test contents. The adapter does not install or upgrade Pi or Harbor.

## Invocation and admission

Use the pinned benchmark Node dependencies and Harbor `0.23.0`; make this directory importable via `PYTHONPATH` and set `PYTHONUTF8=1` on Windows so Harbor's default instruction decoder matches the frozen UTF-8 bytes. A **new, human-authorized** external lot file and ledger are required. No current live lot file is supplied. Native Harbor can configure this agent once for the entire dataset; no per-task driver or replacement scheduler is needed.

The following is **configuration inspection only**, not a launch:

```bash
harbor run --print-config \
  -d terminal-bench/terminal-bench@sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732 \
  -a standard_full:FullStandardPiHarborAgent \
  -m openai-codex/gpt-6-sol -n 1 -k 1 --max-retries 0 \
  --ak repetition=1 \
  --ak lot_path=/external/approved-lot.json \
  --ak authority_path=/external/human-message.txt \
  --ak ledger_path=/external/new-ledger.jsonl
```

Select the authorized GPU-capable sandbox before a real full launch. Do not override task CPU/memory/GPU, timeouts, instruction or verifier; do not inject skills, environment credentials, prior trajectories or tests. Credentials remain in the host Pi auth store, not the task container. Both single-task and dataset jobs infer identity from the actual environment metadata; a caller cannot substitute a different task directory in agent options.

The outside-Git lot JSON contains:

- `schema: 1`, `method: "original-harbor-full-pi-bare"`, frozen `model` and `thinking: "high"`;
- `manifest_sha256`: SHA-256 of newline-normalized frozen manifest bytes;
- `repetitions`: explicit integer 1–5; every task × repetition is a distinct predeclared cell;
- optional `excluded_tasks`: unique manifest names that the human mandate leaves out. Their cells are removed from the ledger header and cannot be admitted; they remain **lost coverage**, never substitutes or a full-set claim;
- `cap_usd`: approved estimated lot ceiling as a decimal string; `prior_commitment_usd`: the exact frozen historical admission commitment `123.58286105200000007`, not a claim that two original-pilot unknown costs became known;
- `actor`, `authority_sha256`: actual human actor and SHA-256 of the external affirmative message, not generated consent;
- `prior_evidence`: **exactly two** `{ "path": "external receipt path", "sha256": "exact digest" }` entries for the historical standard-pilot ledger (`ce4b46c7…`) and modified-comparison ledger (`6ae0764f…`). Both bytes are checked at admission.

- optional flat-rate policy, only with explicit human authority: `agent_policy` (`max_requests` 1–5000, `limit_usd` ≥ $9, replacing the default 48 requests/$57 per start), `project_ceiling_usd` (replacing $1,000), `unknown_cost_blocks` (default `true`) and `max_in_flight` (1–16, default 1, matching Harbor `-n`). When any of them is present the ledger header records all four. Estimated USD stays an estimate: with flat-rate tokens it is not an invoice.

The lot binds all 66 tasks except explicitly declared exclusions; no exclusion silently becomes full coverage. `StandardLot` only records reserve/start/settlement and blocks duplicate cells, concurrent admission, altered bindings, unknown costs and aggregate overruns under the existing $1,000 project ceiling. It never launches another trial. A fresh file is not authority to reset consumption. Launch callers must verify mandate scope and prior amounts; file hashes alone do not prove consent.

After admission, any agent-side failure (request limit, context exhaustion, model or transport error) is settled in the ledger and then raised as Harbor's `NonZeroAgentExitCodeError`, the same class installed agents use for a non-zero exit, so Harbor **still runs the original verifier** on the final sandbox state. Pre-admission binding or setup errors never start the agent and are not verified. In the first capped live cell the 48-request limit ended the agent with a plain `RuntimeError`, and Harbor skipped the verifier entirely; that behavior is fixed here.

By default each invocation has the disclosed **agent policy of 48 model requests and $57 estimated model budget**, inherited from the tested transport, with no Jev. This is not Terminal-Bench's default or a provider hard cap. Failures retain attributable usage in `standard-receipt.json`, `model-usage.jsonl`, `host-status.json` and Harbor's agent context. A pending request remains unknown; no next start is admitted. Context-window exhaustion is an agent failure, not an automatic compaction or retry.

## Complete coverage remains a separate launch gate

The [official 4.0 instructions](https://www.tbench.ai/docs) require GPU-capable sandboxes and illustrate `-k 5`. Our manifest includes `fp8-rmsnorm-gemm`, `jax-speedrun-gpu` and `math-eval-grader`; omitting them gives **63/66, not a complete score**. Five fixed repetitions would mean 330 starts, not 66. With this adapter, run each authorized repetition as a native `-k 1` job with explicit `--ak repetition=N`; `-k 5` with a fixed repetition would correctly reject duplicate cells. No automatic retry is permitted.

A read-only check of all 66 pinned public Harbor package-version configurations found 3 agent+verifier GPU tasks and two original non-default features: `cumulative-layout-shift` declares a native `skills_dir`; `medical-claims-processing` declares a Playwright SSE MCP server. This verifies metadata availability, **not** full image availability or Pi's functional use of those resources. The preparation host had AMD integrated graphics and no NVIDIA device; the later TBF-04 host has a 4 GB laptop NVIDIA GPU but no validated GPU sandbox, so the authorized lot excludes the GPU tasks. Several CPU tasks request 16 GiB and up to 16 CPUs. Before removing `--print-config`, TBF-04 requires: all original packages/images available, compatibility check for every task including native skill/MCP access, GPU environment and its separately accounted infrastructure cost, explicit repetition count/new lot budget and estimate-risk acceptance, exact-head CI and current launch authority. No leaderboard parity/publication claim follows merely from using official task files.
