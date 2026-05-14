#!/bin/bash
# From PowerShell use: bash -i ./ralph/afk-nodock-codex.sh <iterations> <change> [model]
set -eo pipefail

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <iterations> <change-name> [model]  (e.g. bash -i ralph/afk-nodock-codex.sh 10 my-change gpt-5.4)" >&2
  echo "Default model: Codex CLI configured default, or CODEX_MODEL if set" >&2
  echo "Warning: this script bypasses Codex approvals and sandboxing" >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI not found in PATH" >&2
  exit 1
fi

ITERATIONS="$1"
CHANGE="$2"
MODEL="${3:-${CODEX_MODEL:-}}"

model_args=()
if [ -n "$MODEL" ]; then
  model_args=(-m "$MODEL")
fi

LOG_DIR="ralph/logs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"
echo "Logs: $LOG_DIR"

PROMPT_FILE="ralph/.tmp-prompt.md"
shopt -s nullglob

ensure_clean_worktree() {
  dirty=$(git status --porcelain --untracked-files=all -- . ':(exclude)ralph/logs/**' ':(exclude)ralph/.tmp-prompt.md')
  if [ -n "$dirty" ]; then
    echo "Ralph left uncommitted changes after iteration $i. Commit or revert them before continuing." >&2
    echo "$dirty" >&2
    exit 1
  fi
}

for ((i=1; i<=ITERATIONS; i++)); do
  logfile="$LOG_DIR/iter-$(printf '%02d' "$i").log"
  finalfile="$LOG_DIR/iter-$(printf '%02d' "$i")-final.md"
  issue_files=(docs/issues/"$CHANGE"/*.md)

  if [ ${#issue_files[@]} -eq 0 ]; then
    echo "No open issues found in docs/issues/$CHANGE. Ralph complete before iteration $i."
    echo "<promise>NO MORE TASKS</promise>"
    exit 0
  fi

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  issues=$(cat "${issue_files[@]}")
  issue_list=$(printf '%s\n' "${issue_files[@]}")
  prompt=$(cat ralph/prompt.md)

  printf '%s' "$prompt

# RUNTIME CONTEXT

Requested change: $CHANGE
Allowed issue directory: docs/issues/$CHANGE
Open issue files:
$issue_list

Previous commits: $commits

Issues:
$issues" > "$PROMPT_FILE"

  echo "=== Iteration $i ==="

  echo "Log: $logfile"
  echo "Running Codex..."

  if codex exec \
    "${model_args[@]}" \
    --dangerously-bypass-approvals-and-sandbox \
    --cd "$(pwd)" \
    --output-last-message "$finalfile" \
    "Read $PROMPT_FILE and follow the instructions in it." \
    > "$logfile" 2>&1; then
    echo
    echo "=== Codex final message ==="
    if [ -s "$finalfile" ]; then
      cat "$finalfile"
      printf '\n'
    else
      echo "No final message captured. Full log: $logfile"
    fi
  else
    status=$?
    echo "Codex failed with exit code $status. Full log: $logfile" >&2
    echo "=== Last log lines ===" >&2
    tail -n 80 "$logfile" >&2
    exit "$status"
  fi

  ensure_clean_worktree

  result=$(cat "$finalfile" 2>/dev/null || true)

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
