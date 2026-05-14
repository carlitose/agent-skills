#!/bin/bash
# From PowerShell use: bash -i ./ralph/once-codex.sh <change> [model]

set -eo pipefail

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

CHANGE="${1:-$CHANGE}"
MODEL="${2:-${CODEX_MODEL:-}}"
CODEX_SANDBOX="${CODEX_SANDBOX:-danger-full-access}"

if [ -z "$CHANGE" ]; then
  echo "Usage: $0 <change-name> [model]  (e.g. bash ralph/once-codex.sh my-change gpt-5.4)" >&2
  echo "Default model: Codex CLI configured default, or CODEX_MODEL if set" >&2
  echo "Default sandbox: danger-full-access so Codex can write .git; override with CODEX_SANDBOX" >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI not found in PATH" >&2
  exit 1
fi

model_args=()
if [ -n "$MODEL" ]; then
  model_args=(-m "$MODEL")
fi

shopt -s nullglob
issue_files=(docs/issues/"$CHANGE"/*.md)

if [ ${#issue_files[@]} -eq 0 ]; then
  echo "No open issues found in docs/issues/$CHANGE."
  echo "<promise>NO MORE TASKS</promise>"
  exit 0
fi

issues=$(cat "${issue_files[@]}")
issue_list=$(printf '%s\n' "${issue_files[@]}")
commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

LOG_DIR="ralph/logs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"
logfile="$LOG_DIR/once.log"
finalfile="$LOG_DIR/once-final.md"
PROMPT_FILE="ralph/.tmp-prompt.md"

printf '%s' "$prompt

# RUNTIME CONTEXT

Requested change: $CHANGE
Allowed issue directory: docs/issues/$CHANGE
Open issue files:
$issue_list

Previous commits: $commits

Issues:
$issues" > "$PROMPT_FILE"

echo "Change: $CHANGE"
echo "Model: ${MODEL:-Codex default}"
echo "Sandbox: $CODEX_SANDBOX"
echo "Log: $logfile"
echo "Running Codex..."

if codex --ask-for-approval never exec \
  "${model_args[@]}" \
  --sandbox "$CODEX_SANDBOX" \
  --cd "$(pwd)" \
  --output-last-message "$finalfile" \
  - \
  < "$PROMPT_FILE" \
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
