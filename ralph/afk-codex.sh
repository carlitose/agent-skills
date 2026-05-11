#!/bin/bash
set -eo pipefail

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <iterations> <change-name> [model]  (e.g. bash ralph/afk-codex.sh 10 my-change gpt-5.4)" >&2
  echo "Default model: Codex CLI configured default, or CODEX_MODEL if set" >&2
  echo "Default sandbox: danger-full-access so Codex can write .git; override with CODEX_SANDBOX" >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI not found in PATH" >&2
  exit 1
fi

ITERATIONS="$1"
CHANGE="$2"
MODEL="${3:-${CODEX_MODEL:-}}"
CODEX_SANDBOX="${CODEX_SANDBOX:-danger-full-access}"
CODEX_APPROVAL="${CODEX_APPROVAL:-never}"

model_args=()
if [ -n "$MODEL" ]; then
  model_args=(-m "$MODEL")
fi

LOG_DIR="ralph/logs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"
echo "Logs: $LOG_DIR"

PROMPT_FILE="ralph/.tmp-prompt.md"

for ((i=1; i<=ITERATIONS; i++)); do
  logfile="$LOG_DIR/iter-$(printf '%02d' "$i").log"
  finalfile="$LOG_DIR/iter-$(printf '%02d' "$i")-final.md"

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  issues=$(cat "docs/issues/$CHANGE"/*.md 2>/dev/null || echo "No issues found")
  prompt=$(cat ralph/prompt.md)

  printf '%s' "Previous commits: $commits Issues: $issues $prompt" > "$PROMPT_FILE"

  echo "=== Iteration $i ==="

  echo "Log: $logfile"
  echo "Running Codex..."

  if codex --ask-for-approval "$CODEX_APPROVAL" exec \
    "${model_args[@]}" \
    --sandbox "$CODEX_SANDBOX" \
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

  result=$(cat "$finalfile" 2>/dev/null || true)

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
